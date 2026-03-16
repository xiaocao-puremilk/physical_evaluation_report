import os
import json
import urllib.parse
from datetime import datetime
from dotenv import load_dotenv
import time

import requests
import oss2

# 加载 .env 文件
load_dotenv()

class AliyunOSSUploader:
    """
    阿里云 OSS 上传服务类
    说明：
    - 调用对方 /file-svc/api/file/uploadFileByRole 接口上传文件
    - 维持原有的返回值结构，方便后续 Platform3Notifier 继续使用 oss_result["data"]["key"]
    """

    def __init__(self, is_prod=None):
        if is_prod is None:
            self.is_prod = os.getenv("IS_PROD") == "1"
        else:
            self.is_prod = is_prod
        if self.is_prod:
            self.endpoint = "https://openapi.health-100.cn"
            self.mnappid = "CIMIN_OSS_UPLOAD"
            self.mnappsecret = "sfm4mvtyez6ctevmuvzup5nn9j1z949uu9z7e5jfkoxxom25jab513dnnllo851s"
            self.bucket_name = "mn-ciming-report"
            self.role_arn = "cimingOssUpload_fSeKbHwA"
        else:
            self.endpoint = "https://openapi-test.health-100.cn"
            self.mnappid = "CIMING_FILE_UPLOAD"
            self.mnappsecret = "ihzrfgq30g5l5cerguxgyoogozr3f53ibcxso5hy7zmtjmaz44c48dsh0gvgif57"
            self.bucket_name = "mn-ciming-report"
            self.role_arn = "ciming_qrTnPVj5"

    def _generate_sign(self, timestamp):
        import hashlib
        # mnsign = sha256HexString(mnappid + mntimestamp + "" + mnappsecret)
        raw_str = f"{self.mnappid}{timestamp}{self.mnappsecret}"
        return hashlib.sha256(raw_str.encode('utf-8')).hexdigest()

    def upload_pdf(self, file_path, source_name=None, retries=2, folder_prefix=None, person_info=None):
        if source_name is None:
            source_name = "formal" if self.is_prod else "test"

        """
        通过角色上传文件
        接口地址：/file-svc/api/file/uploadFileByRole

        说明：
        1. 强制不使用系统代理，避免 requests 走代理导致 10054 / 握手异常
        2. fileDir 先使用纯日期格式，尽量贴近对方提供的成功示例
        3. 保留对方文档要求的 multipart 参数和签名头
        """
        if not os.path.exists(file_path):
            return {"code": "error", "msg": f"文件不存在: {file_path}"}

        upload_url = f"{self.endpoint}/file-svc/api/file/uploadFileByRole"


        # 先按对方文档/截图，尽量使用简单日期目录
        # 如果后续确认支持自定义子目录，再恢复 reports/<folder_prefix>
        file_dir = datetime.now().strftime("%Y/%m/%d")

        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)

        for attempt in range(retries + 1):
            timestamp = str(int(time.time() * 1000))
            sign = self._generate_sign(timestamp)

            session = requests.Session()
            session.trust_env = False  # 强制忽略系统代理/环境代理

            headers = {
                "mnappid": self.mnappid,
                "mntimestamp": timestamp,
                "mnsign": sign,
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json",
                "Connection": "close",
            }

            data = {
                "fileDir": file_dir,
                "bucketName": self.bucket_name,
                "roleArn": self.role_arn,
                "source": source_name,   # 测试环境建议传 test
            }

            try:
                print(f"[OSS] 正在上传 (尝试 {attempt + 1}): {file_path}")
                print(f"[OSS] upload_url={upload_url}")
                print(f"[OSS] fileDir={file_dir}")
                print(f"[OSS] bucketName={self.bucket_name}")
                print(f"[OSS] roleArn={self.role_arn}")
                print(f"[OSS] source={source_name}")
                print(f"[OSS] fileName={file_name}")
                print(f"[OSS] fileSize={file_size}")
                print(f"[OSS] mnappid={self.mnappid}")
                print(f"[OSS] mntimestamp={timestamp}")
                print(f"[OSS] mnsign={sign[:16]}...")

                with open(file_path, "rb") as f:
                    files = {
                        "multipartFile": (file_name, f, "application/pdf")
                    }

                    response = session.post(
                        upload_url,
                        headers=headers,
                        data=data,
                        files=files,
                        timeout=(15, 60),   # connect timeout, read timeout
                        verify=True
                    )

                print(f"[OSS] HTTP状态码: {response.status_code}")
                print(f"[OSS] 响应前200字符: {response.text[:200]}")

                response.raise_for_status()

                try:
                    result = response.json()
                except Exception:
                    return {
                        "code": "error",
                        "msg": f"接口返回非JSON响应: HTTP {response.status_code}, body={response.text[:300]}"
                    }

                print(f"[OSS] 业务响应: {json.dumps(result, ensure_ascii=False)}")
                return result

            except requests.exceptions.ConnectTimeout as e:
                print(f"[OSS] 连接超时: {e}")
            except requests.exceptions.ReadTimeout as e:
                print(f"[OSS] 读取超时: {e}")
            except requests.exceptions.SSLError as e:
                print(f"[OSS] SSL/TLS 错误: {e}")
            except requests.exceptions.ConnectionError as e:
                print(f"[OSS] 连接错误: {e}")
            except requests.exceptions.HTTPError as e:
                body = ""
                try:
                    body = e.response.text[:300]
                except Exception:
                    pass
                print(f"[OSS] HTTP错误: {e}, body={body}")
                return {
                    "code": "error",
                    "msg": f"HTTP错误: {e}, body={body}"
                }
            except Exception as e:
                print(f"[OSS] 未知异常: {type(e).__name__}: {e}")
                return {
                    "code": "error",
                    "msg": f"{type(e).__name__}: {str(e)}"
                }
            finally:
                session.close()

            if attempt < retries:
                wait_seconds = 2 * (attempt + 1)
                print(f"[OSS] 第 {attempt + 1} 次失败，等待 {wait_seconds} 秒后重试...")
                time.sleep(wait_seconds)

        return {
            "code": "error",
            "msg": f"上传重试 {retries} 次后仍失败，疑似网络/白名单/网关/TLS拦截问题"
        }



class Platform3Notifier:
    """
    平台 3 (Cloudflare D1) 同步服务类
    设置环境变量 USE_LOCAL_SERVER=1 可切换到本地 Wrangler (http://localhost:8787) 进行调试
    """
    def __init__(self):
        if os.getenv("USE_LOCAL_SERVER") == "1":
            domain = "http://localhost:8787"
            print("[Platform3] 使用本地 Wrangler (http://localhost:8787)")
        else:
            domain = "https://ciming.pages.dev"
        self.api_url = f"{domain}/api/sync-record"

    def notify_success(self, person_info, oss_result, oss_result_pro=None, oss_folder=None):
        """
        通知平台 3 同步数据
        oss_result: 用户版 OSS 上传结果
        oss_result_pro: 专业版 OSS 上传结果 (可选)
        oss_folder: OSS 文件夹前缀 (csv_basename), 如 "reports/20251216_H_2_s"
        """
        if oss_result.get("code") != "000000":
            return {"code": "error", "msg": "OSS 上传未成功，跳过通知平台 3"}

        data = {
            "personId": (
                person_info.get("personId")
                or person_info.get("person_id")
                or person_info.get("report_id")  # 最后备选：用报告编号作为 ID
            ),
            "name": person_info.get("name"),
            "gender": person_info.get("gender", "男"),
            "age": str(person_info.get("age", "")).replace("岁", ""),
            "department": person_info.get("location", "体检中心"),
            "status": "已完成",
            "ossKey": oss_result.get("data", {}).get("key"),
            "number": person_info.get("report_id"),
            "ossFolder": oss_folder or f"reports/{person_info.get('report_id', 'unknown')}",
        }

        # 如果专业版上传成功，追加专业版 key
        if oss_result_pro and oss_result_pro.get("code") == "000000":
            data["ossKeyPro"] = oss_result_pro.get("data", {}).get("key")

        try:
            print("-" * 40)
            print(f"[Platform3] 正在同步到 D1... (ID: {data['personId']})")
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                self.api_url,
                headers=headers,
                data=json.dumps(data, ensure_ascii=False),
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            print(f"[Platform3] 同步结果: {json.dumps(result, ensure_ascii=False)}")
            print("-" * 40)
            return result
        except Exception as e:
            print(f"[Platform3] 同步失败: {e}")
            return {"code": "error", "msg": str(e)}


def handle_upload_and_notify(file_path, person_info, is_prod=None, folder_prefix=None):
    """
    统一入口：上传 PDF 并通知平台 3
    """
    uploader = AliyunOSSUploader(is_prod=is_prod)
    oss_res = uploader.upload_pdf(file_path, person_info=person_info, folder_prefix=folder_prefix)

    if oss_res.get("code") == "000000":
        notifier = Platform3Notifier()
        sync_res = notifier.notify_success(person_info, oss_res)
        return {"oss": oss_res, "sync": sync_res}
    else:
        return {"oss": oss_res, "sync": None}
