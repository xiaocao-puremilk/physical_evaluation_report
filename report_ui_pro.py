# report_ui_pro.py - 专业版报告页面（在 report_ui.MentalReportPage 基础上扩展）
import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QSizePolicy
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from PyQt5.QtCore import Qt

from report_ui import (
    MentalReportPage, create_card,
    TEXT_COLOR_PRIMARY, TEXT_COLOR_SECONDARY, DIVIDER_COLOR
)

class AcquisitionQualityWidget(QWidget):
    """采集与质量（专业版固定模块）"""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)

        self.title = QLabel("采集与质量摘要")
        self.title.setStyleSheet(f"font-size: 22px; font-weight: 900; color: {TEXT_COLOR_PRIMARY};")
        layout.addWidget(self.title)

        row = QWidget()
        row.setStyleSheet("background: transparent; border: none;")
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(14)

        self.body = QLabel()
        self.body.setWordWrap(True)
        self.body.setStyleSheet(
            f"font-size: 20px; font-weight: 600; color: {TEXT_COLOR_SECONDARY}; line-height: 1.45;"
        )
        self.body.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        h.addWidget(self.body, 7)

        img = QLabel()
        img.setStyleSheet("background: transparent; border: none;")
        img.setAlignment(Qt.AlignRight | Qt.AlignTop)
        img.setFixedSize(210, 160)

        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "10.png")
        if os.path.exists(p):
            from PyQt5.QtGui import QPixmap
            pm = QPixmap(p)
            if not pm.isNull():
                pm = pm.scaled(img.width(), img.height(),
                            Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img.setPixmap(pm)

        h.addWidget(img, 3)
        layout.addWidget(row)

        self.set_quality_info(
            recording_duration_sec=None,
            valid_data_ratio=None,
            artifact_removal_ratio=None,
            electrode_contact=None
        )

    def set_quality_info(self, recording_duration_sec, valid_data_ratio, artifact_removal_ratio, electrode_contact):
        # 这些字段在当前工程里未必都有，允许缺省；缺省时提供合理提示
        def fmt_duration(sec):
            if sec is None:
                return "—"
            m = int(sec) // 60
            s = int(sec) % 60
            return f"{m}分{s:02d}秒"

        vd = "—" if valid_data_ratio is None else f"{valid_data_ratio*100:.0f}%"
        ar = "—" if artifact_removal_ratio is None else f"{artifact_removal_ratio*100:.0f}%"
        ec = electrode_contact or "—"

        text = (
            f"采集时长：{fmt_duration(recording_duration_sec)}；有效数据比例：{vd}；伪迹去除/清洗通过率：{ar}；电极接触：{ec}。\n"
            "解读提示：若有效数据比例偏低或电极接触不佳，结果可能波动，建议在同一时段、相近睡眠条件下复测。"
        )
        self.body.setText(text)


class MetricFourElementsWidget(QWidget):
    """指标四要素说明（专业版固定模块）"""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(10)

        title = QLabel("指标解释要素（抑郁/焦虑指数）")
        title.setStyleSheet(f"font-size: 22px; font-weight: 900; color: {TEXT_COLOR_PRIMARY};")
        layout.addWidget(title)

        body = QLabel(
            "1）指标含义：指数用于反映近期情绪低落/压力紧张相关的风险信号强弱（筛查提示）。\n"
            "2）分数范围与方向性：默认 0–100，分数越高表示风险信号越强。\n"
            "3）分级阈值与依据：默认采用低(0–44) / 中(45–57) / 高(≥58) 三级；阈值应在产品验证中校准并版本化管理。\n"
            "4）参考与误差来源：睡眠不足、咖啡因/酒精、药物、紧张状态、测量环境、佩戴/电极接触等会影响结果，建议结合近2–4周表现综合判断。"
        )
        body.setWordWrap(True)
        body.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {TEXT_COLOR_SECONDARY}; line-height: 1.5;")

        row = QWidget()
        row.setStyleSheet("background: transparent; border: none;")
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(14)

        body.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        h.addWidget(body, 7)

        img = QLabel()
        img.setStyleSheet("background: transparent; border: none;")
        img.setAlignment(Qt.AlignRight | Qt.AlignTop)
        img.setFixedSize(210, 160)

        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "11.png")
        if os.path.exists(p):
            from PyQt5.QtGui import QPixmap
            pm = QPixmap(p)
            if not pm.isNull():
                pm = pm.scaled(img.width(), img.height(),
                            Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img.setPixmap(pm)

        h.addWidget(img, 3)

        layout.addWidget(row)

        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background-color: {DIVIDER_COLOR};")
        layout.addWidget(line)

        note = QLabel("提示：上述阈值为报告展示口径骨架，最终口径应以训练/验证数据、量表对照与外部验证结果为准。")
        note.setWordWrap(True)
        note.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {TEXT_COLOR_SECONDARY};")
        layout.addWidget(note)


class ScaleValidationWidget(QWidget):
    """量表关联与验证说明（专业版固定模块）"""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)

        title = QLabel("量表关联与验证说明")
        title.setStyleSheet(f"font-size: 22px; font-weight: 900; color: {TEXT_COLOR_PRIMARY};")
        layout.addWidget(title)

        body = QLabel(
            "• 关联对象：可与常用抑郁/焦虑量表（如 PHQ-9、GAD-7）或临床访谈结论进行对照，用于阈值校准与外部验证。\n"
            "• 映射逻辑：脑电特征（频段、ERP、特征指数等）经模型融合输出风险指数/等级；风险等级用于提示后续行动与是否建议进一步评估。\n"
            "• 验证指标：建议在验证集/外部验证中报告一致性、判别能力（如 AUC/敏感度/特异度）、校准情况与分层偏差（年龄/性别/测量条件）。\n"
            "• 可追溯信息：在报告中保留模型/算法版本、数据版本、设备与采集参数，便于审计与复核。"
        )
        body.setWordWrap(True)
        body.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {TEXT_COLOR_SECONDARY}; line-height: 1.5;")

        row = QWidget()
        row.setStyleSheet("background: transparent; border: none;")
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(14)

        body.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        h.addWidget(body, 7)

        img = QLabel()
        img.setStyleSheet("background: transparent; border: none;")
        img.setAlignment(Qt.AlignRight | Qt.AlignTop)
        img.setFixedSize(210, 160)

        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "12.png")
        if os.path.exists(p):
            from PyQt5.QtGui import QPixmap
            pm = QPixmap(p)
            if not pm.isNull():
                pm = pm.scaled(img.width(), img.height(),
                            Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img.setPixmap(pm)

        h.addWidget(img, 3)

        layout.addWidget(row)

class LayeredAdviceWidget(QWidget):
    """分层建议（专业版固定模块）"""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)

        title = QLabel("分层建议与随访（专业版）")
        title.setStyleSheet(f"font-size: 22px; font-weight: 900; color: {TEXT_COLOR_PRIMARY};")
        layout.addWidget(title)

        row = QWidget()
        row.setStyleSheet("background: transparent; border: none;")
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(14)

        self.body = QLabel()
        self.body.setWordWrap(True)
        self.body.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {TEXT_COLOR_SECONDARY}; line-height: 1.5;")
        self.body.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        h.addWidget(self.body, 7)

        img = QLabel()
        img.setStyleSheet("background: transparent; border: none;")
        img.setAlignment(Qt.AlignRight | Qt.AlignTop)
        img.setFixedSize(210, 160)

        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "13.png")
        if os.path.exists(p):
            from PyQt5.QtGui import QPixmap
            pm = QPixmap(p)
            if not pm.isNull():
                pm = pm.scaled(img.width(), img.height(),
                            Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img.setPixmap(pm)

        h.addWidget(img, 3)

        layout.addWidget(row)

        self.set_by_risk_score(0.0)

    def set_by_risk_score(self, risk_score: float):
        if risk_score >= 58:
            text = (
                "• 7天内：优先修复睡眠与节律（固定作息、减少夜间刺激），每日进行放松训练。\n"
                "• 2–4周：规律运动与压力管理（每周≥3次中等强度运动，结合正念/呼吸训练）；建议完成简短问卷复筛。\n"
                "• 转介：如症状持续≥2周或影响功能，建议精神科/心理科/心理咨询进一步评估；如出现自伤自杀想法等紧急情况，建议尽快就医。"
            )
        elif risk_score >= 45:
            text = (
                "• 7天内：调整作息（避免熬夜、规律起床），减少咖啡因/酒精与过度压力源。\n"
                "• 2–4周：每周2–3次运动 + 放松训练；如症状持续或加重，建议问卷复筛或专业评估。\n"
                "• 随访：建议在作息调整后同条件复测，观察趋势变化。"
            )
        else:
            text = (
                "• 7天内：保持规律作息与适度运动，维持稳定的社交与兴趣活动。\n"
                "• 2–4周：若出现持续紧张、情绪低落或睡眠明显下降，建议完成问卷复筛并考虑同条件复测。\n"
                "• 提示：一次测量不代表长期状态，建议结合近期主观体验综合判断。"
            )
        self.body.setText(text)


class ProfessionalReportPage(MentalReportPage):
    """
    专业版页面：通过 mode="professional" 启用技术图表（ERP/频段/特征），并新增 4 张专业版卡片：
    - 采集与质量
    - 指标四要素说明
    - 量表关联与验证说明
    - 分层建议
    """
    def __init__(self, mode="professional"):
        super().__init__(mode=mode)
        self.setWindowTitle("心理健康风险评估报告（专业版）")

        # 仅在 professional 模式下添加
        if self.mode == "professional":
            self._setup_professional_cards()

    def _setup_professional_cards(self):
        # 插入位置：置顶三卡之后（summary/action/help），风险指数之前
        insert_pos = 3

        self.card_quality = AcquisitionQualityWidget()
        self.content_layout.insertWidget(insert_pos, create_card(self.card_quality, "采集与质量"))
        insert_pos += 1

        self.card_metric_4 = MetricFourElementsWidget()
        self.content_layout.insertWidget(insert_pos, create_card(self.card_metric_4, "指标四要素说明"))
        insert_pos += 1

        self.card_validation = ScaleValidationWidget()
        self.content_layout.insertWidget(insert_pos, create_card(self.card_validation, "量表关联与验证说明"))
        insert_pos += 1

        self.card_layered = LayeredAdviceWidget()
        self.content_layout.insertWidget(insert_pos, create_card(self.card_layered, "分层建议"))
        insert_pos += 1

    # 覆写 set_scores：除基类行为外，刷新“分层建议”
    def set_scores(self, s1, t1, s2, t2):
        super().set_scores(s1, t1, s2, t2)
        risk_score = max(float(s1), float(s2))
        if getattr(self, "card_layered", None) is not None:
            self.card_layered.set_by_risk_score(risk_score)

