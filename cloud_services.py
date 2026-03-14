import os
import json
import urllib.parse
from datetime import datetime
from dotenv import load_dotenv

import requests
import oss2

# 加载 .env 文件
load_dotenv()

class AliyunOSSUploader:
    """
    阿里云 OSS 上传服务类
    说明：
    - 这里改成“直传你自己的阿里云 OSS”
    - 不再调用对方 /file-svc/api/file/uploadFileByRole
    - 返回结构尽量兼容旧逻辑，方便后续 Platform3Notifier 继续使用 oss_result["data"]["key"]
    """

    def __init__(self, is_prod=False):
        # 从环境变量读取配置
        self.endpoint = os.getenv("OSS_ENDPOINT", "https://oss-cn-beijing.aliyuncs.com")
        self.bucket_name = os.getenv("OSS_BUCKET_NAME", "ciming-data-test-oss")
        self.access_key_id = os.getenv("OSS_ACCESS_KEY_ID")
        self.access_key_secret = os.getenv("OSS_ACCESS_KEY_SECRET")

        if not self.access_key_id or not self.access_key_secret:
            raise ValueError("未在 .env 中找到 OSS_ACCESS_KEY_ID 或 OSS_ACCESS_KEY_SECRET")

        auth = oss2.Auth(self.access_key_id, self.access_key_secret)
        self.bucket = oss2.Bucket(auth, self.endpoint, self.bucket_name)

    def _build_object_key(self, file_path, person_info=None, folder_prefix=None):
        """
        生成 OSS object key
        支持：reports/<folder_prefix>/<filename> 或 reports/YYYY/MM/DD/<filename>
        """
        if folder_prefix:
            date_dir = f"reports/{folder_prefix}/"
        else:
            date_dir = datetime.now().strftime("reports/%Y/%m/%d/")
            
        filename = os.path.basename(file_path)

        report_id = ""
        if isinstance(person_info, dict):
            report_id = str(person_info.get("report_id", "")).strip()

        safe_filename = filename.replace("\\", "_").replace("/", "_")

        if report_id:
            return f"{date_dir}{report_id}-{safe_filename}"
        return f"{date_dir}{safe_filename}"

    def upload_pdf(self, file_path, source_name="Platform2", retries=2, person_info=None, folder_prefix=None):
        """
        上传 PDF 到你自己的阿里云 OSS
        """
        if not os.path.exists(file_path):
            return {"code": "error", "msg": f"文件不存在: {file_path}"}

        object_key = self._build_object_key(file_path, person_info, folder_prefix)

        for attempt in range(retries + 1):
            try:
                file_size = os.path.getsize(file_path)
                print(f"[OSS] 正在上传 (尝试 {attempt + 1}): {file_path}")
                print(f"[OSS] 目标路径: {object_key}")

                result = self.bucket.put_object_from_file(object_key, file_path)

                if result.status == 200:
                    encoded_key = urllib.parse.quote(object_key)
                    public_url = f"https://{self.bucket_name}.{self.endpoint.replace('https://', '')}/{encoded_key}"

                    signed_url = self.bucket.sign_url(
                        method="GET",
                        key=object_key,
                        expires=3600
                    )

                    response = {
                        "code": "000000",
                        "msg": "成功",
                        "data": {
                            "key": object_key,
                            "fileName": os.path.basename(object_key),
                            "url": public_url,
                            "signedUrl": signed_url,
                            "bucket": self.bucket_name,
                            "endpoint": self.endpoint,
                            "source": source_name
                        }
                    }

                    print(f"[OSS] 上传成功！Key: {object_key}")
                    return response

                return {
                    "code": "error",
                    "msg": f"上传失败，HTTP状态码: {result.status}"
                }

            except Exception as e:
                print(f"[OSS] 尝试 {attempt + 1} 失败: {type(e).__name__}: {e}")
                if attempt == retries:
                    return {
                        "code": "error",
                        "msg": f"上传重试 {retries} 次后仍然失败: {str(e)}"
                    }

        return {"code": "error", "msg": "未知上传失败"}


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


def handle_upload_and_notify(file_path, person_info, is_prod=False, folder_prefix=None):
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
