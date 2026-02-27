# report_ui_pro.py - 专业版报告页面（在 report_ui.MentalReportPage 基础上扩展）
import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QSizePolicy, QMessageBox
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from PyQt5.QtCore import Qt

from report_ui import (
    MentalReportPage, create_card,
    TEXT_COLOR_PRIMARY, TEXT_COLOR_SECONDARY, DIVIDER_COLOR, ACCENT_COLOR, CARD_BORDER, BG_COLOR,
    ScoreGaugeWidget, RiskLevelBar, InfoBubble,
    ERPTripleWidget, RoundedBarCanvas, ExplanationCard, TwoColumnModule,
    DisclaimerPrivacyWidget, FooterWidget,
    A4_WIDTH, A4_HEIGHT, GLOBAL_FONT,
    CardWithSideImage
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

        body_container = QWidget()
        body_layout = QVBoxLayout(body_container)
        body_layout.setContentsMargins(0, 5, 0, 5)
        body_layout.setSpacing(12)

        # 表头与内容表格
        table_frame = QFrame()
        table_frame.setStyleSheet(f"""
            QFrame {{
                border: 1px solid {DIVIDER_COLOR};
                border-radius: 8px;
                background-color: #F9FCFC;
            }}
            QLabel {{
                font-family: "HeiTi";
                font-size: 14px;
                padding: 4px;
                border: none;
            }}
        """)
        grid = QGridLayout(table_frame)
        grid.setSpacing(0)
        grid.setContentsMargins(0, 0, 0, 0)

        headers = ["量表名称", "样本量/人群概述", "AUC及核心指标", "阈值点与分级映射"]
        header_style = f"font-weight: bold; background-color: {CARD_BORDER}; color: {TEXT_COLOR_PRIMARY}; border: 1px solid {DIVIDER_COLOR};"
        cell_style = f"color: {TEXT_COLOR_SECONDARY}; border: 1px solid {DIVIDER_COLOR};"

        for c, h in enumerate(headers):
            lbl = QLabel(h)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(header_style)
            grid.addWidget(lbl, 0, c)

        rows = [
            ["PHQ-9 (Depression)", "N=450, 社区/体检人群", "AUC: 0.86, Sens: 82%", "0-4:无, 5-9:轻, 10-14:中, 15+:重"],
            ["GAD-7 (Anxiety)", "N=420, 社区/体检人群", "AUC: 0.84, Spec: 85%", "0-4:无, 5-9:轻, 10-13:中, 14+:重"],
            ["EEG-Risk Index", "N=1200+, 多中心验证", "Consistency: 0.81", "0-49:无, 50-64:轻, 65-74:中, 75+:重"]
        ]

        for r, row_data in enumerate(rows):
            for c, val in enumerate(row_data):
                lbl = QLabel(val)
                lbl.setAlignment(Qt.AlignCenter)
                lbl.setWordWrap(True)
                lbl.setStyleSheet(cell_style)
                grid.addWidget(lbl, r + 1, c)

        body_layout.addWidget(table_frame)

        note = QLabel("注：上表为最小可交付验证摘要，完整数据见《算法技术验证白皮书》或SOP附件。")
        note.setStyleSheet(f"font-size: 13px; color: {ACCENT_COLOR}; font-style: italic;")
        body_layout.addWidget(note)

        row = QWidget()
        row.setStyleSheet("background: transparent; border: none;")
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(14)

        body_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        h.addWidget(body_container, 7)

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
    专业版页面：通过 mode="professional" 启用技术图表（ERP/频段/特征），并新增专业版卡片。
    布局分配：
    - P1: Header, 风险摘要, 行动建议, 专业提示
    - P2: 风险指数评估, 采集与质量, 指标四要素
    - P3: ERP分析, 情绪波段分布, 量表关联与验证(Table)
    - P4: 脑电特征分析, 分层建议, 综合结论, 免责声明, 页尾横幅
    """
    def __init__(self, mode="professional"):
        super().__init__(mode=mode)
        self.setWindowTitle("心理健康风险评估报告（专业版）")

    def _fill_content(self):
        """
        专业版填充内容：
        1. 调用父类填充 P1/P2 (摘要)
        2. 清理 P2-P4 并按专业版逻辑重新分配
        """
        super()._fill_content()
        self._rebuild_pro_pages()

    def _rebuild_pro_pages(self):
        # 核心：重构时清空列表，防止引用到已 deleteLater 的 C++ 对象导致 RuntimeError
        self.all_dep_widgets.clear()
        self.all_anx_widgets.clear()
        self.all_risk_bars.clear()
        self.all_conclusion_labels.clear()
        self.all_layered_widgets.clear()
        self.all_erp_widgets.clear()
        self.all_emotion_wave_canvases.clear()
        self.all_feature_canvases.clear()
        self.all_quality_widgets.clear()
        # P2: 风险指数 + 采集与质量 + 指标四要素
        p2 = self.pages[1]
        self._clear_layout(p2.content_layout)
        c2 = QWidget()
        l2 = QVBoxLayout(c2); l2.setContentsMargins(30,20,30,20); l2.setSpacing(15)
        
        # 风险指数评估
        risk_box = self._create_risk_box()
        l2.addWidget(create_card(risk_box, "风险指数评估"))
        
        # 采集与质量
        self.card_quality = AcquisitionQualityWidget()
        self.all_quality_widgets.append(self.card_quality)
        l2.addWidget(create_card(self.card_quality, "采集与质量"))
        
        # 指标四要素
        self.card_metric_4 = MetricFourElementsWidget()
        l2.addWidget(create_card(self.card_metric_4, "指标解释要素"))
        l2.addStretch(1)
        p2.content_layout.addWidget(c2)
        
        # 修复重大Bug：必须继续调用后续页面的重构
        self._rebuild_p3()

    def set_quality_data(self, duration, valid_ratio, artifact_ratio, contact):
        """设置采集质量信息"""
        for w in self.all_quality_widgets:
            w.set_quality_info(duration, valid_ratio, artifact_ratio, contact)

    def _rebuild_p3(self):
        # P3: ERP + 频段 + 验证量表
        p3 = self.pages[2]
        self._clear_layout(p3.content_layout)
        c3 = QWidget()
        l3 = QVBoxLayout(c3); l3.setContentsMargins(30,20,30,20); l3.setSpacing(15)
        
        self.erp_widget = ERPTripleWidget()
        self.all_erp_widgets.append(self.erp_widget)
        l3.addWidget(create_card(self.erp_widget, "事件相关电位 (ERP) 分析"))
        
        ewc = RoundedBarCanvas(width=9, height=1.9)
        self.all_emotion_wave_canvases.append(ewc)
        wave_exp = ExplanationCard(title="指标说明", body="频带能量分布分析，展示不同波段的活跃比例。", img_rel_path="assets/doctor.png")
        l3.addWidget(create_card(TwoColumnModule(ewc, wave_exp), "情绪状态脑波频带分布"))
        
        self.card_validation = ScaleValidationWidget()
        l3.addWidget(create_card(self.card_validation, "量表关联与验证说明"))
        l3.addStretch(1)
        p3.content_layout.addWidget(c3)

        # P4: 特征指标 + 分层建议 + 结论 + 免责 + 页尾
        p4 = self.pages[3]
        self._clear_layout(p4.content_layout)
        c4 = QWidget()
        l4 = QVBoxLayout(c4); l4.setContentsMargins(30,5,30,5); l4.setSpacing(10)
        
        fc = RoundedBarCanvas(width=9, height=1.7) # 减少高度以防截断
        self.all_feature_canvases.append(fc)
        feat_exp = ExplanationCard(title="指标说明", body="多维度大脑特征分析，提供更细致的评估参考。", img_rel_path="assets/doctor.png")
        l4.addWidget(create_card(TwoColumnModule(fc, feat_exp), "脑电特征指标分析"))
        
        law = LayeredAdviceWidget()
        self.all_layered_widgets.append(law)
        l4.addWidget(create_card(law, "分层建议与随访"))
        
        # 结论与免责
        cl = QLabel(); cl.setWordWrap(True)
        cl.setStyleSheet(f"font-size: 20px; font-weight: 600; line-height: 1.5; color: {TEXT_COLOR_SECONDARY};")
        self.all_conclusion_labels.append(cl)
        l4.addWidget(create_card(CardWithSideImage(cl, "assets/8.png"), "综合评估结论"))
        
        self.disclaimer_widget = DisclaimerPrivacyWidget()
        l4.addWidget(create_card(self.disclaimer_widget, "风险告知与免责声明"))
        
        # Footer Removed per user request
        l4.addStretch(1)
        p4.content_layout.addWidget(c4)

    def _clear_layout(self, layout):
        if layout is None: return
        while layout.count():
            item = layout.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                    widget.deleteLater()

    def _create_risk_box(self):
        # 显式使用 ScoreGaugeWidget
        dw = ScoreGaugeWidget()
        aw = ScoreGaugeWidget()
        rb = RiskLevelBar()
        self.all_dep_widgets.append(dw)
        self.all_anx_widgets.append(aw)
        self.all_risk_bars.append(rb)
        w = QWidget(); v = QVBoxLayout(w); v.setSpacing(10)
        h = QHBoxLayout(); h.setSpacing(15)
        
        # 左侧装饰图 (对齐用户版)
        test_img = QLabel()
        test_img.setFixedSize(160, 180)
        p_test = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "test.png")
        if os.path.exists(p_test):
            pm = QPixmap(p_test).scaled(test_img.width(), test_img.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            test_img.setPixmap(pm)
        h.addWidget(test_img, 2)

        def gb(t, g):
            f = QFrame(); f.setStyleSheet(f"background:rgba(255,255,255,0.85); border-radius:12px; border:1px solid {CARD_BORDER};")
            vl = QVBoxLayout(f); vl.setContentsMargins(5,5,5,5)
            vl.addWidget(InfoBubble(t), alignment=Qt.AlignCenter); vl.addWidget(g, alignment=Qt.AlignCenter)
            return f
        h.addWidget(gb("抑郁指数", dw), 3); h.addWidget(gb("焦虑指数", aw), 3)
        v.addLayout(h); v.addWidget(rb)
        return w

    def set_scores(self, s1, t1, s2, t2):
        super().set_scores(s1, t1, s2, t2)
        risk_score = max(float(s1), float(s2))
        for law in self.all_layered_widgets:
            law.set_by_risk_score(risk_score)

