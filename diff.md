*** a/report_ui.py
--- b/report_ui.py
***************
*** 1,30 ****
  # report_ui.py - 布局完美修复版 (修复文字遮挡，保留梯形阶梯效果)
  
  import sys
  import os
  import numpy as np
  import matplotlib
  matplotlib.use('Qt5Agg') # 显式指定后端
  import matplotlib.pyplot as plt
  from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
  from matplotlib.figure import Figure
  from matplotlib.patches import FancyBboxPatch
  
  from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
     ...
  )
--- 1,30 ----
  # report_ui.py - 布局完美修复版 (修复文字遮挡，保留梯形阶梯效果)
  
  import sys
  import os
  import numpy as np
  import matplotlib
  matplotlib.use('Qt5Agg') # 显式指定后端
  import matplotlib.pyplot as plt
  from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
  from matplotlib.figure import Figure
  from matplotlib.patches import FancyBboxPatch
  
  from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
     ...
  )
+ 
+ # 说明：本补丁新增 4 张“客户版必备卡片”
+ # - SummaryCard（置顶结论卡片）
+ # - ActionAdviceCard（≤3条可执行建议）
+ # - ProfessionalHelpCard（何时需专业帮助）
+ # - DisclaimerPrivacyCard（免责声明与隐私）
***************
*** 12037,12040 ****
  class TwoColumnModule(QFrame):
--- 12037,12380 ----
+ 
+ # ==========================================
+ # 新增：客户版四大卡片（按现有风格：QFrame + 阴影 + QLabel）
+ # 放置位置建议：插在 ExplanationCard 之后、TwoColumnModule 之前
+ # ==========================================
+ 
+ class SummaryCard(QFrame):
+     """
+     结论卡片（置顶）
+     - 抑郁风险：等级 + 分数
+     - 焦虑风险：等级 + 分数
+     - 重点提示：1句（非诊断措辞）
+     """
+     def __init__(self, parent=None):
+         super().__init__(parent)
+         self.setObjectName("SummaryCard")
+         self.setStyleSheet(f"""
+             QFrame#SummaryCard {{
+                 background-color: {CARD_COLOR};
+                 border: 2px solid {CARD_BORDER};
+                 border-radius: 16px;
+             }}
+             QLabel {{
+                 background: transparent;
+                 font-family: "{GLOBAL_FONT}";
+             }}
+         """)
+ 
+         shadow = QGraphicsDropShadowEffect()
+         shadow.setBlurRadius(26)
+         shadow.setColor(QColor(*SHADOW_RGBA))
+         shadow.setOffset(0, 10)
+         self.setGraphicsEffect(shadow)
+ 
+         layout = QVBoxLayout(self)
+         layout.setContentsMargins(18, 16, 18, 16)
+         layout.setSpacing(10)
+ 
+         self.dep_line = QLabel("抑郁风险：--（--分）")
+         self.dep_line.setStyleSheet(f"font-size: 18px; font-weight: 900; color: {TEXT_COLOR_PRIMARY};")
+         layout.addWidget(self.dep_line)
+ 
+         self.anx_line = QLabel("焦虑风险：--（--分）")
+         self.anx_line.setStyleSheet(f"font-size: 18px; font-weight: 900; color: {TEXT_COLOR_PRIMARY};")
+         layout.addWidget(self.anx_line)
+ 
+         line = QFrame()
+         line.setFixedHeight(1)
+         line.setStyleSheet(f"background-color: {DIVIDER_COLOR};")
+         layout.addWidget(line)
+ 
+         self.key_hint = QLabel("重点提示：--")
+         self.key_hint.setWordWrap(True)
+         self.key_hint.setStyleSheet(
+             f"font-size: 14px; font-weight: 700; color: {TEXT_COLOR_SECONDARY}; line-height: 1.35;"
+         )
+         layout.addWidget(self.key_hint)
+ 
+     @staticmethod
+     def level_3(score: float) -> str:
+         """
+         客户版 3 档：低/中/高
+         这里沿用你文件中已出现的 45/58 分界逻辑骨架（后续可配置化）。
+         """
+         if score >= 58:
+             return "高"
+         if score >= 45:
+             return "中"
+         return "低"
+ 
+     def set_scores(self, dep_score: float, anx_score: float, key_hint: str = ""):
+         dep_level = self.level_3(dep_score)
+         anx_level = self.level_3(anx_score)
+ 
+         self.dep_line.setText(f"抑郁风险：{dep_level}（{dep_score:.0f}分）")
+         self.anx_line.setText(f"焦虑风险：{anx_level}（{anx_score:.0f}分）")
+ 
+         if key_hint:
+             self.key_hint.setText(f"重点提示：{key_hint}")
+             return
+ 
+         # 默认提示：取更高风险作为关注点（非诊断措辞）
+         if anx_score >= dep_score:
+             self.key_hint.setText("重点提示：近期压力/紧张相关信号偏高，建议关注作息与压力管理。")
+         else:
+             self.key_hint.setText("重点提示：近期情绪低落相关信号偏高，建议关注睡眠与情绪调节。")
+ 
+ 
+ class ActionAdviceCard(QFrame):
+     """
+     行动建议（≤3条，带频次/时长）
+     先给骨架与默认建议库，后续可外置配置化。
+     """
+     def __init__(self, parent=None):
+         super().__init__(parent)
+         self.setObjectName("ActionAdviceCard")
+         self.setStyleSheet(f"""
+             QFrame#ActionAdviceCard {{
+                 background-color: {CARD_COLOR};
+                 border: 2px solid {CARD_BORDER};
+                 border-radius: 16px;
+             }}
+             QLabel {{
+                 background: transparent;
+                 font-family: "{GLOBAL_FONT}";
+             }}
+         """)
+ 
+         shadow = QGraphicsDropShadowEffect()
+         shadow.setBlurRadius(26)
+         shadow.setColor(QColor(*SHADOW_RGBA))
+         shadow.setOffset(0, 10)
+         self.setGraphicsEffect(shadow)
+ 
+         layout = QVBoxLayout(self)
+         layout.setContentsMargins(18, 16, 18, 16)
+         layout.setSpacing(10)
+ 
+         self.tips = []
+         for i in range(3):
+             lb = QLabel(f"{i+1}. --")
+             lb.setWordWrap(True)
+             lb.setStyleSheet(f"font-size: 14px; font-weight: 650; color: {TEXT_COLOR_PRIMARY}; line-height: 1.4;")
+             layout.addWidget(lb)
+             self.tips.append(lb)
+ 
+         self.set_advice([])  # 初始化隐藏空项
+ 
+     def set_advice(self, items):
+         items = (items or [])[:3]
+         for i, lb in enumerate(self.tips):
+             if i < len(items):
+                 lb.setText(f"{i+1}. {items[i]}")
+                 lb.show()
+             else:
+                 lb.hide()
+ 
+     def set_by_risk(self, risk_level: str):
+         """
+         risk_level: "low" | "mid" | "high"
+         """
+         if risk_level == "high":
+             self.set_advice([
+                 "睡眠：连续7天固定上床/起床时间；睡前60分钟减少屏幕刺激（每天）",
+                 "运动：每周≥3次中等强度运动，每次20–30分钟（持续2–4周）",
+                 "压力：每天10分钟呼吸放松/正念练习，并记录压力源与情绪波动（持续2周）",
+             ])
+         elif risk_level == "mid":
+             self.set_advice([
+                 "睡眠：固定作息，避免熬夜；睡前30–60分钟减少刺激（每天）",
+                 "运动：每周2–3次快走/骑行，每次20分钟（持续2周）",
+                 "压力：每天5–10分钟呼吸放松或拉伸（持续2周）",
+             ])
+         else:
+             self.set_advice([
+                 "睡眠：保持规律作息，尽量固定上床与起床时间（每天）",
+                 "运动：每周2次轻中强度运动，每次20分钟（持续2周）",
+                 "压力：每周1–2次放松活动（散步/冥想/兴趣活动）（持续2周）",
+             ])
+ 
+ 
+ class ProfessionalHelpCard(QFrame):
+     """
+     需要专业帮助的提示（必备）
+     - 触发条件清单 + 推荐科室
+     """
+     def __init__(self, parent=None):
+         super().__init__(parent)
+         self.setObjectName("ProfessionalHelpCard")
+         self.setStyleSheet(f"""
+             QFrame#ProfessionalHelpCard {{
+                 background-color: {CARD_COLOR};
+                 border: 2px solid {CARD_BORDER};
+                 border-radius: 16px;
+             }}
+             QLabel {{
+                 background: transparent;
+                 font-family: "{GLOBAL_FONT}";
+             }}
+         """)
+ 
+         shadow = QGraphicsDropShadowEffect()
+         shadow.setBlurRadius(26)
+         shadow.setColor(QColor(*SHADOW_RGBA))
+         shadow.setOffset(0, 10)
+         self.setGraphicsEffect(shadow)
+ 
+         layout = QVBoxLayout(self)
+         layout.setContentsMargins(18, 16, 18, 16)
+         layout.setSpacing(10)
+ 
+         self.title = QLabel("如出现以下情况，建议尽快寻求专业帮助：")
+         self.title.setStyleSheet(f"font-size: 15px; font-weight: 900; color: {TEXT_COLOR_PRIMARY};")
+         layout.addWidget(self.title)
+ 
+         triggers = [
+             "情绪低落或兴趣下降持续 ≥2 周",
+             "明显影响工作/学习效率或日常生活",
+             "人际退缩、回避社交、持续紧张不适",
+             "严重失眠或躯体不适（心悸、胸闷等）持续存在",
+         ]
+         self.trigger_label = QLabel("• " + "\n• ".join(triggers))
+         self.trigger_label.setWordWrap(True)
+         self.trigger_label.setStyleSheet(
+             f"font-size: 14px; font-weight: 650; color: {TEXT_COLOR_SECONDARY}; line-height: 1.45;"
+         )
+         layout.addWidget(self.trigger_label)
+ 
+         self.route = QLabel("建议就诊/咨询：精神科 / 心理科 / 心理咨询（可先完成简短问卷复筛，再做专业评估）")
+         self.route.setWordWrap(True)
+         self.route.setStyleSheet(
+             f"font-size: 13px; font-weight: 650; color: {TEXT_COLOR_PRIMARY}; line-height: 1.4;"
+         )
+         layout.addWidget(self.route)
+ 
+ 
+ class DisclaimerPrivacyCard(QFrame):
+     """
+     免责声明与隐私条款（客户版页尾必备）
+     """
+     def __init__(self, parent=None):
+         super().__init__(parent)
+         self.setObjectName("DisclaimerPrivacyCard")
+         self.setStyleSheet(f"""
+             QFrame#DisclaimerPrivacyCard {{
+                 background-color: {CARD_COLOR};
+                 border: 2px solid {CARD_BORDER};
+                 border-radius: 16px;
+             }}
+             QLabel {{
+                 background: transparent;
+                 font-family: "{GLOBAL_FONT}";
+             }}
+         """)
+ 
+         shadow = QGraphicsDropShadowEffect()
+         shadow.setBlurRadius(26)
+         shadow.setColor(QColor(*SHADOW_RGBA))
+         shadow.setOffset(0, 10)
+         self.setGraphicsEffect(shadow)
+ 
+         layout = QVBoxLayout(self)
+         layout.setContentsMargins(18, 16, 18, 16)
+         layout.setSpacing(8)
+ 
+         text = (
+             "风险告知与免责声明：本报告用于体检场景的心理状态风险筛查/提示与健康管理参考，不等同于医学诊断或临床结论。\n"
+             "复测建议：一次测量不代表长期状态，建议结合近2–4周的主观感受与行为表现综合判断；如需观察趋势，可在作息调整后同条件复测。\n"
+             "影响因素：睡眠不足、咖啡因/酒精、药物、紧张状态、测量环境、佩戴/电极接触等可能影响结果。\n"
+             "隐私与数据使用：数据用于本次报告生成与质量管理/产品改进（如适用），按授权范围处理并设置保存期限；如需撤回授权请联系服务方。\n"
+             "签署说明：本报告为算法自动生成结果，未进行医师审核签署。"
+         )
+ 
+         self.body = QLabel(text)
+         self.body.setWordWrap(True)
+         self.body.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {TEXT_COLOR_SECONDARY}; line-height: 1.45;")
+         layout.addWidget(self.body)
+ 
+     def set_text(self, text: str):
+         self.body.setText(text)
+ 
  class TwoColumnModule(QFrame):
***************
*** 40089,40100 ****
  class MentalReportPage(QWidget):
-     def __init__(self):
+     def __init__(self):
          super().__init__()
          self.setWindowTitle("心理健康风险评估报告")
          self.resize(1100, 1000)
          self.setStyleSheet(f"background-color: {BG_COLOR}; font-family: '{GLOBAL_FONT}';")
  
          self.scores_data = {'depression': 0, 'anxiety': 0}
--- 40089,40122 ----
  class MentalReportPage(QWidget):
      def __init__(self):
          super().__init__()
          self.setWindowTitle("心理健康风险评估报告")
          self.resize(1100, 1000)
          self.setStyleSheet(f"background-color: {BG_COLOR}; font-family: '{GLOBAL_FONT}';")
  
          self.scores_data = {'depression': 0, 'anxiety': 0}
+         # 客户版新增四卡（置顶三卡 + 页尾免责声明卡）
+         self.summary_card = None
+         self.action_card = None
+         self.help_card = None
+         self.disclaimer_card = None
***************
*** 43170,43210 ****
          # main_layout 只加叠层容器（不要再单独加 header/content_container）
          self.main_layout.addWidget(self.header_stack)
  
          # 1. 风险指数 (Card) —— 改成：双仪表盘卡片 + 气泡说明 + 分段状态条
          risk_content_layout = QVBoxLayout()
          risk_content_layout.setSpacing(14)
--- 43192,43260 ----
          # main_layout 只加叠层容器（不要再单独加 header/content_container）
          self.main_layout.addWidget(self.header_stack)
  
+         # ======================================================
+         # 0) 客户版置顶四卡（按修订意见：先结论—行动—专业帮助）
+         #    注意：免责声明建议放在结论卡片之后、页尾横幅之前（见下方另一个改动点）
+         # ======================================================
+         self.summary_card = SummaryCard()
+         self.content_layout.addWidget(create_card(self.summary_card, "结论卡片（筛查提示）"))
+ 
+         self.action_card = ActionAdviceCard()
+         self.content_layout.addWidget(create_card(self.action_card, "行动建议（建议先做）"))
+ 
+         self.help_card = ProfessionalHelpCard()
+         self.content_layout.addWidget(create_card(self.help_card, "需要专业帮助的提示"))
+ 
+         # 免责声明卡：先创建，稍后插到“综合评估结论”之后、页尾横幅之前
+         self.disclaimer_card = DisclaimerPrivacyCard()
+ 
          # 1. 风险指数 (Card) —— 改成：双仪表盘卡片 + 气泡说明 + 分段状态条
          risk_content_layout = QVBoxLayout()
          risk_content_layout.setSpacing(14)
***************
*** 48890,48920 ****
          self.content_layout.addWidget(create_card(self.conclusion_text, "综合评估结论"))
  
          # —— 6. 页尾 Footer Banner（新增，不改原结论内容）——
          self.footer_banner = FooterWidget(
              bg_rel_path="assets/footer_bg.png",
              headline_text="正向刺激投入度高",
              desc_text="您的脑电表现显示，在积极情绪条件下注意力与投入度较高，具备良好的情绪调节与恢复能力。建议继续保持规律作息与适度运动，巩固积极状态。"
          )
--- 48940,48985 ----
          self.content_layout.addWidget(create_card(self.conclusion_text, "综合评估结论"))
+ 
+         # —— 5.5 客户版免责声明与隐私（页尾必备，放在横幅之前）——
+         if self.disclaimer_card is not None:
+             self.content_layout.addWidget(create_card(self.disclaimer_card, "风险告知与免责声明"))
  
          # —— 6. 页尾 Footer Banner（新增，不改原结论内容）——
          self.footer_banner = FooterWidget(
              bg_rel_path="assets/footer_bg.png",
              headline_text="正向刺激投入度高",
              desc_text="您的脑电表现显示，在积极情绪条件下注意力与投入度较高，具备良好的情绪调节与恢复能力。建议继续保持规律作息与适度运动，巩固积极状态。"
          )
***************
*** 52009,52020 ****
  def set_scores(self, s1, t1, s2, t2):
          self.dep_widget.set_score(s1, t1)
          self.anx_widget.set_score(s2, t2)
  
-         avg_score = (s1 + s2) / 2
-         self.risk_bar.set_value(avg_score)
+         # 客户版建议：风险条展示更高风险的一项，避免平均值掩盖风险
+         risk_score = max(s1, s2)
+         self.risk_bar.set_value(risk_score)
  
          self.scores_data = {'depression': s1, 'anxiety': s2}
+ 
+         # 更新置顶结论卡
+         if self.summary_card is not None:
+             self.summary_card.set_scores(s1, s2)
+ 
+         # 更新行动建议（按风险档位）
+         if self.action_card is not None:
+             if risk_score >= 58:
+                 self.action_card.set_by_risk("high")
+             elif risk_score >= 45:
+                 self.action_card.set_by_risk("mid")
+             else:
+                 self.action_card.set_by_risk("low")
