# main.py - 客户版先展示；导出或关闭后展示专业版

import sys
import json
import os
import argparse
import numpy as np
import pandas as pd

import PyQt5
qt_dir = os.path.dirname(PyQt5.__file__)
plugin_path = os.path.join(qt_dir, 'Qt5', 'plugins')
if not os.path.exists(plugin_path):
    plugin_path = os.path.join(qt_dir, 'Qt', 'plugins')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer

from report_ui import MentalReportPage
from report_ui_pro import ProfessionalReportPage
from eeg_data_processor import EEGProcessor
from cloud_services import handle_upload_and_notify

def load_algorithm_config(csv_path):
    """从CSV加载算法配置权重"""
    try:
        df = pd.read_csv(csv_path)
        config = {}
        for _, row in df.iterrows():
            config[row['index_name']] = {
                'weight_activity': float(row['weight_activity']),
                'weight_bias': float(row['weight_bias']),
                'weight_attention': float(row['weight_attention']),
                'offset': float(row['offset']),
                'min_score': float(row['min_score']),
                'max_score': float(row['max_score'])
            }
        return config
    except Exception as e:
        print(f"[WARN] 无法加载算法配置 {csv_path}: {e}。将使用默认内置逻辑。")
        return None

def populate_report(page, processor, person_info, scores, erp_lists, band_lists, feature_values):
    # 个人信息
    page.set_person_info(
        name=person_info["name"],
        age=person_info["age"],
        report_id=person_info["report_id"],
        location=person_info["location"],
        collect_dt=person_info["collect_dt"],
        gen_dt=person_info["gen_dt"],
        device_ver=person_info["device_ver"],
        operator=person_info["operator"],
        signature_text=person_info["signature_text"],
    )

    # 分数
    page.set_scores(
        s1=scores["depression_score"],
        t1=scores["depression_tag"],
        s2=scores["anxiety_score"],
        t2=scores["anxiety_tag"],
    )

    # 技术数据（客户版会自动忽略技术图表，但仍可用于结论生成）
    try:
        neutral_erp_list, positive_erp_list, negative_erp_list = erp_lists
        page.set_erp_data(neutral_erp_list, positive_erp_list, negative_erp_list)
    except Exception:
        pass

    try:
        neutral_bands, negative_bands, positive_bands = band_lists
        page.set_emotion_wave_data(neutral_bands, negative_bands, positive_bands)
    except Exception:
        pass

    try:
        brain_activity, emotion_bias, attention_concentration = feature_values
        page.set_feature_data(brain_activity, emotion_bias, attention_concentration)
    except Exception:
        pass

    # 采集质量 (专业版)
    try:
        q = processor.get_quality_metrics()
        if q and hasattr(page, "set_quality_data"):
            page.set_quality_data(
                q["duration_sec"],
                q["valid_data_ratio"],
                q["artifact_removal_ratio"],
                q["electrode_contact"]
            )
    except Exception:
        pass

    # 结论
    try:
        auto_conclusion = page.generate_auto_conclusion()
        page.set_conclusion(auto_conclusion)
    except Exception:
        page.set_conclusion("数据处理中出现问题，请检查数据质量。")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--meta", type=str, default=None, help="Path to acquisition meta.json")
    args, _ = parser.parse_known_args()

    app = QApplication(sys.argv)

    print("=" * 60)
    print("正在加载心理评估报告界面（客户版→专业版）...")
    print("=" * 60)

    eeg_file_path = "20251216_H_2_s.csv"
    if not os.path.exists(eeg_file_path):
        QMessageBox.critical(None, "错误",
                             f"未找到脑电数据文件：{eeg_file_path}\n请确保CSV文件在程序目录下。")
        sys.exit(1)

    try:
        processor = EEGProcessor(eeg_file_path, fs=250)
        print("[OK] 数据加载成功")
    except Exception as e:
        QMessageBox.critical(None, "错误", f"数据加载失败：{str(e)}")
        sys.exit(1)

    # =========================
    # 预先计算一次数据，供两份报告复用
    # =========================

    # 默认值（没有 meta.json 也能跑）
    person_info = {
        "name": "张三",
        "age": "25岁",
        "report_id": "A001",
        "location": "A体检中心",
        "collect_dt": "2026-01-03 10:30",
        "gen_dt": "2026-01-03 11:10",
        "device_ver": "设备A+软件v2.6",
        "operator": "李四（工号001）",
        # 采集端暂时不提供也没关系，这里留默认
        "signature_text": "本报告为算法自动生成结果，未进行医师审核签署"
    }

    # 如果提供了 --meta，则用采集端输出覆盖默认值
    if args.meta:
        try:
            with open(args.meta, "r", encoding="utf-8") as f:
                meta = json.load(f)
            if isinstance(meta, dict):
                # 只覆盖我们需要的字段，避免 JSON 里多字段影响
                for k in [
                    "name", "gender", "age", "person_id", "report_id", "location",
                    "collect_dt", "gen_dt", "device_ver", "operator"
                ]:
                    if k in meta and meta[k] not in (None, ""):
                        person_info[k] = meta[k]

                # 可选：采集端不提供签署也行
                if "signature_text" in meta and meta["signature_text"] not in (None, ""):
                    person_info["signature_text"] = meta["signature_text"]

            print(f"[OK] Loaded meta from JSON: {args.meta}")
        except Exception as e:
            print(f"[WARN] Failed to load meta JSON: {args.meta} | {e}")

    # ERP
    try:
        neutral_erp, positive_erp, negative_erp = processor.process_all_erp()
        erp_lists = (neutral_erp.tolist(), positive_erp.tolist(), negative_erp.tolist())
        print("[OK] ERP 计算完成")
    except Exception as e:
        print(f"[WARN] ERP 计算失败: {e}")
        erp_lists = ([0]*1500, [0]*1500, [0]*1500)
    finally:
        print(f"[DEBUG] ERP 数据长度: {[len(x) for x in erp_lists]}")

    # 频带分布
    try:
        neutral_bands, negative_bands, positive_bands = processor.process_band_powers_by_emotion()
        band_lists = (neutral_bands, negative_bands, positive_bands)
        print("[OK] 频带分布计算完成")
    except Exception as e:
        print(f"[WARN] 频带分布计算失败: {e}")
        band_lists = ([20,20,20,20,20],[20,20,20,20,20],[20,20,20,20,20])

    # 特征指标
    try:
        brain_activity, emotion_bias, attention_concentration = processor.compute_feature_indices()
        feature_values = (brain_activity, emotion_bias, attention_concentration)
        print("[OK] 特征指标计算完成")
    except Exception as e:
        print(f"[WARN] 特征指标计算失败: {e}")
        feature_values = (0.5, 0.5, 0.5)
        brain_activity, emotion_bias, attention_concentration = feature_values

    # =========================
    # 2) 计算得分（从分析结果推导，不再 hardcode）
    # =========================
    config_path = "algorithm_config.csv"
    algo_config = load_algorithm_config(config_path)

    if algo_config:
        # 使用配置文件的线性加权算法
        print(f"[OK] 使用来自 {config_path} 的自定义算法配置")
        
        d_cfg = algo_config['depression']
        depression_val = (d_cfg['weight_activity'] * brain_activity + 
                          d_cfg['weight_bias'] * emotion_bias + 
                          d_cfg['weight_attention'] * attention_concentration + 
                          d_cfg['offset'])
        depression_score = int(np.clip(depression_val, d_cfg['min_score'], d_cfg['max_score']))

        a_cfg = algo_config['anxiety']
        anxiety_val = (a_cfg['weight_activity'] * brain_activity + 
                       a_cfg['weight_bias'] * emotion_bias + 
                       a_cfg['weight_attention'] * attention_concentration + 
                       a_cfg['offset'])
        anxiety_score = int(np.clip(anxiety_val, a_cfg['min_score'], a_cfg['max_score']))
    else:
        # 兜底默认算法：抑郁风险与活跃度负相关，与负面偏向正相关
        depression_score = int(np.clip((1.0 - brain_activity) * 60 + (1.0 - emotion_bias) * 40, 20, 95))
        # 焦虑风险与注意力/稳定性负相关，与活跃度正相关
        anxiety_score = int(np.clip((1.0 - attention_concentration) * 50 + (brain_activity) * 50, 20, 95))

    def _get_tag(s):
        if s >= 75: return "重度风险"
        if s >= 65: return "中度风险"
        if s >= 50: return "轻度风险"
        return "正常范围"

    scores = {
        "depression_score": depression_score,
        "depression_tag": _get_tag(depression_score),
        "anxiety_score": anxiety_score,
        "anxiety_tag": _get_tag(anxiety_score),
    }

    # =========================
    # 0) 准备导出目录
    # =========================
    # 根据 CSV 文件名创建子文件夹，例如 report/20251216_H_2_s/
    csv_basename = os.path.splitext(os.path.basename(eeg_file_path))[0]
    subject_report_dir = os.path.join("report", csv_basename)
    if not os.path.exists(subject_report_dir):
        os.makedirs(subject_report_dir)
        print(f"[Main] 已创建被试者报告目录: {subject_report_dir}")

    client_pdf_path = os.path.join(subject_report_dir, "心理健康评估报告-用户版.pdf")
    pro_pdf_path = os.path.join(subject_report_dir, "心理健康评估报告-专业版.pdf")

    # =========================
    # 1) 先展示客户版
    # =========================
    client_page = MentalReportPage(mode="client")
    populate_report(client_page, processor, person_info, scores, erp_lists, band_lists, feature_values)

    state = {"professional_shown": False}
    professional_page_holder = {"page": None}

    def on_all_finished():
        print("[Main] 全流程完成，程序即将退出。")
        QTimer.singleShot(2000, app.quit)

    # 收集两份上传结果，最后统一通知平台3
    upload_results = {"client": None, "pro": None}

    def do_final_notify():
        """两份都上传完后，统一通知平台3"""
        client_res = upload_results.get("client")
        pro_res = upload_results.get("pro")
        print("=" * 60)
        print(f"[DEBUG] do_final_notify 触发")
        print(f"[DEBUG] upload_results['client'] = {json.dumps(client_res, ensure_ascii=False) if client_res else 'None'}")
        print(f"[DEBUG] upload_results['pro']    = {json.dumps(pro_res, ensure_ascii=False) if pro_res else 'None'}")
        print("=" * 60)
        if client_res and client_res.get("code") == "000000":
            from cloud_services import Platform3Notifier
            notifier = Platform3Notifier()
            folder = f"reports/{csv_basename}"
            print(f"[DEBUG] 准备同步到平台3，folder={folder}")
            sync_res = notifier.notify_success(
                person_info, client_res,
                oss_result_pro=pro_res,
                oss_folder=folder
            )
            print(f"[Main] 平台3同步结果: {json.dumps(sync_res, ensure_ascii=False)}")
        else:
            print(f"[WARN] 用户版上传结果无效或为 None，跳过平台3同步！")
        on_all_finished()

    def do_upload_and_sync(filename, p_info, report_type="client", next_step=None):
        """执行上传，结果保存到 upload_results，完成后执行 next_step"""
        print(f"[Main] 准备上传 ({report_type}): {filename}")
        def _run():
            res = handle_upload_and_notify.__wrapped__(filename, p_info, is_prod=False, folder_prefix=csv_basename) \
                if hasattr(handle_upload_and_notify, '__wrapped__') \
                else _upload_only(filename, p_info)
            upload_results[report_type] = res
            print(f"[Main] 上传结果 ({report_type}): {json.dumps(res, ensure_ascii=False)}")
            if next_step:
                QTimer.singleShot(500, next_step)
        QTimer.singleShot(1000, _run)

    def _upload_only(filename, p_info):
        """只做 OSS 上传，不做通知（最后统一通知）"""
        from cloud_services import AliyunOSSUploader
        uploader = AliyunOSSUploader(is_prod=False)
        return uploader.upload_pdf(filename, person_info=p_info, folder_prefix=csv_basename)

    def show_professional_auto():
        if state["professional_shown"]:
            return
        state["professional_shown"] = True

        print("[Main] 自动启动专业版生成...")
        pro_page = ProfessionalReportPage(mode="professional")
        populate_report(pro_page, processor, person_info, scores, erp_lists, band_lists, feature_values)
        professional_page_holder["page"] = pro_page

        def on_pro_finished(reason, filename):
            if reason == "exported":
                # 上传专业版，完成后统一通知平台3
                def _upload_pro():
                    res = _upload_only(filename, person_info)
                    upload_results["pro"] = res
                    print(f"[Main] 专业版上传结果: {json.dumps(res, ensure_ascii=False)}")
                    QTimer.singleShot(500, do_final_notify)
                QTimer.singleShot(1000, _upload_pro)
            elif reason == "closed":
                do_final_notify()

        pro_page.flow_finished.connect(on_pro_finished)
        pro_page.show()
        QTimer.singleShot(1000, lambda: pro_page.export_pdf(pro_pdf_path))

    def on_client_finished(reason, filename):
        if reason == "exported":
            # 上传用户版，完成后开启专业版
            def _upload_client():
                res = _upload_only(filename, person_info)
                upload_results["client"] = res
                print(f"[Main] 用户版上传结果: {json.dumps(res, ensure_ascii=False)}")
                QTimer.singleShot(500, show_professional_auto)
            QTimer.singleShot(1000, _upload_client)
        elif reason == "closed":
            show_professional_auto()

    client_page.flow_finished.connect(on_client_finished)
    client_page.show()

    print(f"[Main] 开始自动导出客户版 PDF: {client_pdf_path}")
    QTimer.singleShot(1000, lambda: client_page.export_pdf(client_pdf_path))

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
