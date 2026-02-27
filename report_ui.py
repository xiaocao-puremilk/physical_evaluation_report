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

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QFrame, QScrollArea, QPushButton, QFileDialog,
                             QGraphicsDropShadowEffect, QApplication, QSizePolicy, QMessageBox, QStackedLayout)
from PyQt5.QtCore import Qt, QRectF, QPointF, QTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient, QRadialGradient, QBrush, QPolygonF, QPainterPath, QPixmap, QImageReader, QFontDatabase
from PyQt5.QtPrintSupport import QPrinter

# ==========================================
# 1. 全局配置
# ==========================================
GLOBAL_FONT = "HeiTi"  # 全局字体
# Source Han Sans CN  ||  PingFang SC
# 医疗蓝绿色：更干净、柔和、对比更稳
BG_COLOR = "#EAF6F7"              # 页面背景：淡蓝绿
CARD_COLOR = "#FFFFFF"            # 卡片底：纯白更清爽
CARD_BORDER = "#D6EEF1"           # 卡片边框：浅蓝绿
DIVIDER_COLOR = "#CFE9EC"         # 分割线
TEXT_COLOR_PRIMARY = "#184A4E"    # 主文字：深青
TEXT_COLOR_SECONDARY = "#4F7A7F"  # 次文字：灰青
ACCENT_COLOR = "#2BB6B1"          # 强调色：医疗青绿

SHADOW_RGBA = (0, 80, 90, 28)     # 阴影带点青色，视觉更“医疗”


A4_WIDTH = 1050
A4_HEIGHT = 1485

HEADER_GRADIENT_START = "#66A6FF"
HEADER_GRADIENT_END = "#89F7FE"
TITLE_GRADIENT_START = "#2980B9"
TITLE_GRADIENT_END = "#6DD5FA"

WAVE_COLORS = {
    "Delta": "#00CEC9", "Theta": "#00B894", "Alpha": "#0984E3", "Beta":  "#FDCB6E", "Gamma": "#E17055"
}

# 字体层级定义
FONT_SIZE_H1 = 44
FONT_SIZE_H2 = 24
FONT_SIZE_H3 = 20
FONT_SIZE_BODY = 18
FONT_SIZE_SMALL = 14

class ReportPage(QFrame):
    """单页 A4 容器"""
    def __init__(self, page_num=1, total_pages=1, parent=None):
        super().__init__(parent)
        self.setFixedSize(A4_WIDTH, A4_HEIGHT)
        self.setObjectName("ReportPage")
        self.setStyleSheet(f"QFrame#ReportPage {{ background-color: {BG_COLOR}; border: none; }}")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # 内容区域
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(15)
        self.layout.addWidget(self.content_widget)
        
        self.layout.addStretch(1)
        
        # 页码
        self.page_footer = QLabel(f"第 {page_num} 页 / 共 {total_pages} 页")
        self.page_footer.setAlignment(Qt.AlignCenter)
        self.page_footer.setStyleSheet(f"font-size: {FONT_SIZE_SMALL}px; color: {TEXT_COLOR_SECONDARY}; padding-bottom: 20px;")
        self.layout.addWidget(self.page_footer)

    def add_widget(self, widget):
        self.content_layout.addWidget(widget)

# ==========================================
# 2. UI 组件
# ==========================================

class HeaderWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(500)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 20, 40, 20)
        
        # 加载背景图片
        self.bg_pixmap = None
        bg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "background.png")
        if os.path.exists(bg_path):
            self.bg_pixmap = QPixmap(bg_path)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # 如果有背景图片，则绘制图片
        if self.bg_pixmap and not self.bg_pixmap.isNull():
            # 按照控件宽度缩放图片，并保持比例
            scaled_pixmap = self.bg_pixmap.scaled(
                self.width(), 
                self.height(), 
                Qt.KeepAspectRatioByExpanding, 
                Qt.SmoothTransformation
            )
            
            # 居中绘制
            x_offset = (self.width() - scaled_pixmap.width()) // 2
            y_offset = (self.height() - scaled_pixmap.height()) // 2
            
            painter.drawPixmap(x_offset, y_offset, scaled_pixmap)
        else:
            # 如果没有找到图片，则使用原来的渐变背景作为备用
            gradient = QLinearGradient(0, 0, self.width(), self.height())
            gradient.setColorAt(0, QColor(HEADER_GRADIENT_START))
            gradient.setColorAt(1, QColor(HEADER_GRADIENT_END))
            painter.setBrush(gradient)
            painter.setPen(Qt.NoPen)
            painter.drawRect(self.rect())

            painter.setBrush(QColor(255, 255, 255, 30))
            painter.drawEllipse(self.width() - 100, -50, 200, 200)
            painter.drawEllipse(self.width() - 250, 50, 100, 100)

class FooterWidget(QFrame):
    """
    页尾 Banner：以“宽度”为基准等比缩放背景图，自动调整高度，保证图片完整显示（不裁剪）
    叠字：大标题 + 解释（无徽章）
    """
    def __init__(
        self,
        parent=None,
        bg_rel_path="assets/footer_bg.png",
        headline_text="正向刺激投入度高",
        desc_text="您的脑电表现显示，在积极情绪条件下注意力与投入度较高，具备良好的情绪调节与恢复能力。建议继续保持规律作息与适度运动，巩固积极状态。"
    ):
        super().__init__(parent)
        self.setObjectName("FooterWidget")

        self.bg_rel_path = bg_rel_path
        self.bg_pixmap = None
        self._load_bg()

        # ✅ 关键：不要固定高度，让它能跟随图片比例变化
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # 叠字层
        self.overlay = QWidget(self)
        self.overlay.setAttribute(Qt.WA_TranslucentBackground, True)
        self.overlay.setStyleSheet("background: transparent; border: none;")

        v = QVBoxLayout(self.overlay)

        FOOTER_SIDE_MARGIN = 200
        FOOTER_TOP_MARGIN = 150
        FOOTER_BOTTOM_MARGIN = 16
        self._footer_side_margin = FOOTER_SIDE_MARGIN

        v.setContentsMargins(FOOTER_SIDE_MARGIN, FOOTER_TOP_MARGIN, FOOTER_SIDE_MARGIN, FOOTER_BOTTOM_MARGIN)

        # ✅ 这里 spacing 只负责“标题和正文之间的基础间距”
        v.setSpacing(40)

        # ✅ 不要整体居中，否则会把大块文字“夹在中间”显得离得远
        # v.setAlignment(Qt.AlignCenter)

        # -------- 标题 --------
        FOOTER_HEADLINE_PX = 40  # 标题字号在这里调
        self.headline = QLabel(headline_text)
        self.headline.setAlignment(Qt.AlignCenter)
        self.headline.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.headline.setStyleSheet(f"""
            QLabel {{
                font-family: "{GLOBAL_FONT}";
                font-size: {FOOTER_HEADLINE_PX}px;
                font-weight: 900;
                color: {TEXT_COLOR_PRIMARY};
                background: transparent;
                margin: 0px;          /* ✅ 防止额外外边距 */
                padding: 0px;
            }}
        """)
        v.addWidget(self.headline)

        # -------- 正文 --------
        FOOTER_DESC_PX = 20  # 正文字号在这里调
        self.desc = QLabel(desc_text)
        self.desc.setWordWrap(True)
        self.desc.setAlignment(Qt.AlignCenter)
        self.desc.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # ✅ 关键：限制正文最大宽度，让它少换行 → 高度变小 → 看起来更靠近标题
        #    这里先给一个“相对宽”的比例，你也可以改成固定值比如 760
        self._desc_width_ratio = 0.72  # 0.65~0.80 都可，越大越不换行
        # 先给个初始值（resizeEvent 里会动态更新）
        self.desc.setMaximumWidth(760)

        self.desc.setStyleSheet(f"""
            QLabel {{
                font-family: "{GLOBAL_FONT}";
                font-size: {FOOTER_DESC_PX}px;
                font-weight: 600;
                color: rgba(40, 70, 75, 0.85);
                background: transparent;
                line-height: 1.5;
                margin: 0px;          /* ✅ 防止额外外边距 */
                padding: 0px;
            }}
        """)
        v.addWidget(self.desc)

        # ✅ 关键：把剩余空间都丢到底部，这样标题+正文会“贴着上方”排，不会被居中拉开
        v.addStretch(1)


        # 初次根据图片比例刷新高度
        self._sync_height_to_image()

    def _abs_bg_path(self) -> str:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), self.bg_rel_path)

    def _load_bg(self):
        self.bg_pixmap = None
        p = self._abs_bg_path()
        if os.path.exists(p):
            pm = QPixmap(p)
            if not pm.isNull():
                self.bg_pixmap = pm

    def _sync_height_to_image(self):
        """
        ✅ 核心：按当前控件宽度等比计算应该显示的高度，让图片完整显示（不裁剪）
        """
        pm = getattr(self, "bg_pixmap", None)
        if pm is None or pm.isNull():
            # 没图就给一个兜底高度
            desired_h = 180
        else:
            w = max(1, self.width())
            desired_h = int(w * pm.height() / max(1, pm.width()))

        # 防止 resizeEvent 里反复 setFixedHeight 触发抖动
        if self.height() != desired_h:
            self.setFixedHeight(desired_h)

    def set_text(self, headline_text=None, desc_text=None):
        if headline_text is not None:
            self.headline.setText(headline_text)
        if desc_text is not None:
            self.desc.setText(desc_text)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # ✅ 宽度变化时：自动拉高/变矮，保证整张图完整显示
        self._sync_height_to_image()
        self.overlay.setGeometry(self.rect())

        
        max_w = max(1, self.width() - 2 * self._footer_side_margin)
        self.desc.setMaximumWidth(max_w)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        pm = getattr(self, "bg_pixmap", None)
        if pm is None or pm.isNull():
            painter.fillRect(self.rect(), QColor(245, 250, 250))
            return

        # ✅ 不裁剪：按宽度等比缩放后直接画（控件高度已经同步成刚好容纳整图）
        w = self.width()
        scaled = pm.scaledToWidth(w, Qt.SmoothTransformation)
        painter.drawPixmap(0, 0, scaled)

class InfoTag(QLabel):
    def __init__(self, text, icon=""):
        super().__init__(f"{icon}  {text}")
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-family: "HeiTi";
                font-weight: bold;
                font-size: 16px; 
                background-color: transparent;
                border: 1px dashed rgba(255, 255, 255, 0.8);
                border-radius: 14px;
                padding: 5px 14px;
            }
        """)
        # 信息栏样式表

class InfoPillItem(QLabel):
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet(f"""
            QLabel {{
                color: rgba(15,15,15,0.92);
                font-family: "{GLOBAL_FONT}";
                font-size: 20px;
                font-weight: 900;
                background: transparent;
                padding: 0px 10px;
            }}
        """)

class ExplanationCard(QFrame):
    """
    右侧解释卡（统一样式，内容可变）
    - 插画：只放主体 PNG
    - 外框/圆角/阴影：用 Qt 控制
    """
    def __init__(self, title="个性化解释", body="", img_rel_path="assets/doctor.png", parent=None):
        super().__init__(parent)
        self.setObjectName("ExplanationCard")
        self.setMinimumWidth(260)

        self.setStyleSheet(f"""
            QFrame#ExplanationCard {{
                background-color: {CARD_COLOR};
                border: 2px solid {CARD_BORDER};
                border-radius: 16px;
            }}
            QLabel {{
                background: transparent;
                color: {TEXT_COLOR_PRIMARY};
                font-family: "{GLOBAL_FONT}";
            }}
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(26)
        shadow.setColor(QColor(*SHADOW_RGBA))
        shadow.setOffset(0, 10)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"""
            font-size: 17px;
            font-weight: 900;
            color: {TEXT_COLOR_PRIMARY};
        """)
        layout.addWidget(self.title_label)

        # 插画
        self.image_label = QLabel()
        self.image_label.setFixedHeight(150)
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)

        # 文案
        self.body_label = QLabel(body)
        self.body_label.setWordWrap(True)
        self.body_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {TEXT_COLOR_SECONDARY};
            line-height: 1.35;
        """)
        layout.addWidget(self.body_label)
        layout.addStretch()

        self.set_image(img_rel_path)

    def set_text(self, title: str, body: str):
        self.title_label.setText(title)
        self.body_label.setText(body)

    def set_image(self, img_rel_path: str):
        if not img_rel_path:
            self.image_label.clear()
            return
        abs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), img_rel_path)
        if os.path.exists(abs_path):
            pm = QPixmap(abs_path)
            if not pm.isNull():
                pm = pm.scaled(self.image_label.width() or 240, self.image_label.height(),
                               Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_label.setPixmap(pm)
                return
        self.image_label.clear()
class CardWithSideImage(QWidget):
    """
    通用：左正文 + 右图片
    - 图片在标题下方、正文右侧
    - 不负责外框（外框由 create_card 提供）
    """
    def __init__(
        self,
        content_widget: QWidget,
        img_rel_path: str,
        img_width: int = 180,
        parent=None
    ):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        # 左侧正文
        content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(content_widget, 1)

        # 右侧图片
        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.img_label.setStyleSheet("background: transparent; border: none;")
        self.img_label.setFixedWidth(img_width)

        self._set_image(img_rel_path)

        layout.addWidget(self.img_label, 0)

    def _set_image(self, img_rel_path: str):
        if not img_rel_path:
            return
        abs_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            img_rel_path
        )
        if os.path.exists(abs_path):
            pm = QPixmap(abs_path)
            if not pm.isNull():
                pm = pm.scaledToWidth(
                    self.img_label.width(),
                    Qt.SmoothTransformation
                )
                self.img_label.setPixmap(pm)

class TwoColumnModule(QWidget):
    """
    左内容 + 右解释卡 的通用模块容器
    """
    def __init__(self, left_widget: QWidget, explanation_card: ExplanationCard, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        left_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        explanation_card.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        layout.addWidget(left_widget, 7)      # 左侧占比大
        layout.addWidget(explanation_card, 3) # 右侧解释卡

class InfoPillBar(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("InfoPillBar")

        # 尺寸保持不变（你原来就是 44 / 680）
        self.setFixedHeight(44)
        self.setMinimumWidth(680)

        # ✅ 去掉“玻璃遮罩感”：背景透明、边框弱化/或直接无边框
        self.setStyleSheet("""
            QFrame#InfoPillBar {
                background-color: rgba(255, 255, 255, 0.0);
                border: 1px solid rgba(255, 255, 255, 0.25);
                border-radius: 22px;
            }
        """)

        # ✅ 去掉阴影（阴影扩散会让标题区域看起来也被盖了一层）
        self.setGraphicsEffect(None)

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(18, 8, 18, 8)
        self.layout.setSpacing(0)

        self.item_name = InfoPillItem("👤 姓名: --")
        self.item_age  = InfoPillItem("📅 年龄: --")
        self.item_date = InfoPillItem("🕒 日期: --")
        self.item_id   = InfoPillItem("📄 编号: 2025-A01")

        for w in (self.item_name, self.item_age, self.item_date, self.item_id):
            w.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
            w.setMinimumWidth(150)

        self._add_item(self.item_name)
        self._add_divider()
        self._add_item(self.item_age)
        self._add_divider()
        self._add_item(self.item_date)
        self._add_divider()
        self._add_item(self.item_id)

    def _add_item(self, w):
        self.layout.addWidget(w)

    def _add_divider(self):
        line = QFrame()
        line.setFixedWidth(1)
        line.setStyleSheet("background-color: rgba(255,255,255,0.30);")
        self.layout.addWidget(line)

    def set_person_info(
        self,
        name="--",
        age="--",
        report_id="--",
        location="--",
        collect_dt="--",
        gen_dt="--",
        device_ver="--",
        operator="--",
        signature_text=None
    ):
        # 只保留：姓名、年龄（原来的四个里只留这俩）
        self.tag_name.setText(f"👤 姓名: {name}")
        self.tag_age.setText(f"📅 年龄: {age}")

        # 新增项目
        self.tag_report_id.setText(f"📄 报告编号: {report_id}")
        self.tag_location.setText(f"📍 采集地点: {location}")
        self.tag_collect_dt.setText(f"🧾 采集时间:\n {collect_dt}")
        self.tag_gen_dt.setText(f"🖨️ 报告生成时间:\n {gen_dt}")
        self.tag_device_ver.setText(f"🧠 采集设备:\n {device_ver}")
        self.tag_operator.setText(f"🧑‍💼 操作者: \n{operator}")

        if signature_text:
            self.tag_signature.setText(f"审核签署：{signature_text}")

class StripedSectionHeader(QFrame):
    """
    灰色斜线表头条（用于：风险指数评估 / ERP分析 / ...）
    """
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(44)

        self.label = QLabel(text, self)
        self.label.setStyleSheet(f"""
            QLabel {{
                background: transparent;
                color: #2B2B2B;
                font-family: "{GLOBAL_FONT}";
                font-size: 20px;          /* ✅ 字号放大：你要更大就改这里 */
                font-weight: 900;
                padding-left: 18px;       /* 左边内边距，类似示例图 */
            }}
        """)
        self.label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.label.setGeometry(0, 0, self.width(), self.height())

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 1) 底色（浅灰）
        painter.fillRect(self.rect(), QColor("#F2F2F2"))

        # 2) 斜线（更浅的灰）
        pen = QPen(QColor("#E3E3E3"), 2)
        painter.setPen(pen)

        step = 14  # ✅ 斜线密度：越小越密
        h = self.height()
        w = self.width()

        # 从左下到右上画斜线
        x = -w
        while x < w * 2:
            painter.drawLine(x, h, x + h, 0)
            x += step


def create_title_label(text):
    # ✅ 现在直接返回“灰色斜线表头条”
    return StripedSectionHeader(text)

def create_card(content_widget, title_text=None):
    card = QFrame()
    card.setStyleSheet(f"""
    QFrame {{
        background-color: {CARD_COLOR};
        border-radius: 16px;
        border: 2px solid {CARD_BORDER};
    }}
    """)

    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(28)
    shadow.setColor(QColor(*SHADOW_RGBA))
    shadow.setOffset(0, 10)
    card.setGraphicsEffect(shadow)

    layout = QVBoxLayout(card)
    layout.setContentsMargins(25, 20, 25, 20)
    layout.setSpacing(10)

    if title_text:
        layout.addWidget(create_title_label(title_text))

    if isinstance(content_widget, QWidget):
        old = content_widget.styleSheet() or ""
        content_widget.setStyleSheet(old + "background: transparent; border: none;")

    layout.addWidget(content_widget)
    return card


# ==========================================
# 新增：客户版必备卡片（结论 / 行动建议 / 专业帮助 / 免责声明）
# 说明：
# - 这些卡片作为 create_card(...) 的内容区使用，因此自身不再额外绘制外框与阴影，
#   以保持与现有卡片风格一致、避免双层边框。
# - 文案遵循“筛查提示，不等同诊断”，并给出可执行建议与复测提示。
# ==========================================

class ConclusionSummaryWidget(QWidget):
    """客户版：结论卡片（筛查提示）"""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)

        self.dep_line = QLabel("抑郁风险：--（--分）")
        self.dep_line.setStyleSheet(f"font-size: 20px; font-weight: 900; color: {TEXT_COLOR_PRIMARY};")
        layout.addWidget(self.dep_line)

        self.anx_line = QLabel("焦虑风险：--（--分）")
        self.anx_line.setStyleSheet(f"font-size: 20px; font-weight: 900; color: {TEXT_COLOR_PRIMARY};")
        layout.addWidget(self.anx_line)

        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: {DIVIDER_COLOR};")
        layout.addWidget(divider)

        self.key_hint = QLabel("重点提示：--")
        self.key_hint.setWordWrap(True)
        self.key_hint.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {TEXT_COLOR_SECONDARY}; line-height: 1.5;")
        layout.addWidget(self.key_hint)

        self.small_note = QLabel("提示：本报告用于体检场景心理状态风险筛查/提示，不等同医学诊断或临床结论。")
        self.small_note.setWordWrap(True)
        self.small_note.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {TEXT_COLOR_SECONDARY}; line-height: 1.5;")
        layout.addWidget(self.small_note)

    @staticmethod
    def _level_4(score: float) -> str:
        """四档：无风险/轻度/中度/重度 (对齐仪表盘 50/65/75 阈值)。"""
        if score >= 75:
            return "重度"
        if score >= 65:
            return "中度"
        if score >= 50:
            return "轻度"
        return "无"

    @staticmethod
    def _risk_to_text(level: str) -> str:
        return {"无": "无风险", "轻度": "轻度风险", "中度": "中度风险", "重度": "重度风险"}.get(level, level)

    def set_scores(self, dep_score: float, anx_score: float, hint: str = ""):
        dep_level = self._level_4(dep_score)
        anx_level = self._level_4(anx_score)
        self.dep_line.setText(f"抑郁风险：{self._risk_to_text(dep_level)}（{dep_score:.0f}分）")
        self.anx_line.setText(f"焦虑风险：{self._risk_to_text(anx_level)}（{anx_score:.0f}分）")

        if hint:
            self.key_hint.setText(f"重点提示：{hint}")
            return

        # 获取更高风险分数对应的级别
        max_score = max(dep_score, anx_score)
        max_level = self._level_4(max_score)

        if anx_score >= dep_score:
            if max_level == "重度":
                msg = "近期压力/紧张相关信号显著偏高，可能伴随持续的焦虑感与躯体反应，建议关注压力源并考虑专业评估。"
            elif max_level == "中度":
                msg = "近期压力/紧张相关信号偏高，建议通过正念/运动等方式进行主动调节，并关注睡眠质量。"
            elif max_level == "轻度":
                msg = "近期有轻度压力信号，建议保持规律作息，通过适度运动缓解紧张感。"
            else:
                msg = "当前压力相关信号总体稳定，建议继续保持健康的生活方式。"
        else:
            if max_level == "重度":
                msg = "近期情绪低落相关信号显著偏高，建议关注兴趣动力与睡眠变化，并考虑结合专业问卷进一步了解。"
            elif max_level == "中度":
                msg = "近期情绪低落相关信号偏高，建议通过增加社交/兴趣活动进行调节，关注情绪持续时长。"
            elif max_level == "轻度":
                msg = "近期有轻度情绪波动信号，建议保持规律作息，增加户外活动或社交交流。"
            else:
                msg = "当前情绪相关信号总体稳定，建议保持积极的心理状态与社交活动。"
        self.key_hint.setText(f"重点提示：{msg}")


class ActionAdviceWidget(QWidget):
    """客户版：行动建议（≤3条，可执行，含频次/时长）。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)

        self.items = []
        for i in range(3):
            lb = QLabel(f"{i+1}. --")
            lb.setWordWrap(True)
            lb.setStyleSheet(f"font-size: 20px; font-weight: 650; color: {TEXT_COLOR_PRIMARY}; line-height: 1.4;")
            layout.addWidget(lb)
            self.items.append(lb)

        self.small_note = QLabel("建议以 2–4 周为观察窗口；如需对比趋势，尽量在相近睡眠与同一时段复测。")
        self.small_note.setWordWrap(True)
        self.small_note.setStyleSheet(f"font-size: 22px; font-weight: 600; color: {TEXT_COLOR_SECONDARY}; line-height: 1.35;")
        layout.addWidget(self.small_note)

        self.set_advice([])

    def set_advice(self, advice_list):
        advice_list = (advice_list or [])[:3]
        for i, lb in enumerate(self.items):
            if i < len(advice_list):
                lb.setText(f"{i+1}. {advice_list[i]}")
                lb.show()
            else:
                lb.hide()

    def set_by_risk(self, risk_score: float):
        """根据风险分数（取 max(抑郁, 焦虑)）生成 ≤3 条可执行建议。"""
        if risk_score >= 58:
            self.set_advice([
                "睡眠：连续7天固定上床/起床时间；睡前60分钟减少屏幕刺激（每天）",
                "运动：每周≥3次中等强度运动，每次20–30分钟（持续2–4周）",
                "压力：每天10分钟呼吸放松/正念练习，并记录压力源与情绪波动（持续2周）",
            ])
        elif risk_score >= 45:
            self.set_advice([
                "睡眠：避免熬夜；睡前30–60分钟减少刺激（每天）",
                "运动：每周2–3次快走/骑行，每次20分钟（持续2周）",
                "压力：每天5–10分钟呼吸放松或拉伸（持续2周）",
            ])
        else:
            self.set_advice([
                "睡眠：保持规律作息，尽量固定上床与起床时间（每天）",
                "运动：每周2次轻中强度运动，每次20分钟（持续2周）",
                "压力：每周1–2次放松活动（散步/冥想/兴趣活动）（持续2周）",
            ])


class ProfessionalHelpWidget(QWidget):
    """客户版：需要专业帮助的提示（触发条件清单 + 推荐科室）。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)

        title = QLabel("如出现以下情况，建议尽快寻求专业帮助：")
        title.setStyleSheet(f"font-size: 22px; font-weight: 900; color: {TEXT_COLOR_PRIMARY};")
        layout.addWidget(title)

        triggers = [
            "情绪低落或兴趣下降持续 ≥2 周",
            "明显影响工作/学习效率或日常生活",
            "人际退缩、回避社交、持续紧张不适",
            "严重失眠或躯体不适（心悸、胸闷等）持续存在",
        ]
        text = "\n".join([f"• {t}" for t in triggers])

        body = QLabel(text)
        body.setWordWrap(True)
        body.setWordWrap(True)
        body.setStyleSheet(f"font-size: 20px; font-weight: 650; color: {TEXT_COLOR_SECONDARY}; line-height: 1.45;")
        layout.addWidget(body)

        route = QLabel("建议就诊/咨询：精神科 / 心理科 / 心理咨询（可先完成简短问卷复筛，再做专业评估）")
        route.setWordWrap(True)
        route.setStyleSheet(f"font-size: 20px; font-weight: 650; color: {TEXT_COLOR_PRIMARY}; line-height: 1.4;")
        layout.addWidget(route)


class DisclaimerPrivacyWidget(QWidget):
    """客户版：风险告知与免责声明（页尾必备）。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)

        row = QWidget()
        row.setStyleSheet("background: transparent; border: none;")
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(14)

        # 左：正文
        self.body = QLabel()
        self.body.setWordWrap(True)
        self.body.setStyleSheet(
            f"font-size: 20px; font-weight: 600; color: {TEXT_COLOR_SECONDARY}; line-height: 1.45;"
        )
        self.body.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        h.addWidget(self.body, 7)

        # 右：图片（assets/9.png）
        img = QLabel()
        img.setStyleSheet("background: transparent; border: none;")
        img.setAlignment(Qt.AlignRight | Qt.AlignTop)
        img.setFixedSize(210, 160)  # 可调

        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "9.png")
        if os.path.exists(p):
            pm = QPixmap(p)
            if not pm.isNull():
                pm = pm.scaled(img.width(), img.height(),
                            Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img.setPixmap(pm)

        h.addWidget(img, 3)

        layout.addWidget(row)

        self.set_text(self.default_text())

    @staticmethod
    def default_text() -> str:
        return (
            "• 风险告知与免责声明：本报告用于体检场景的心理状态风险筛查/提示与健康管理参考，不等同于医学诊断或临床结论。\n"
            "• 复测建议：一次测量不代表长期状态，建议结合近2–4周的主观感受与行为表现综合判断；如需观察趋势，可在作息调整后同条件复测。\n"
            "• 影响因素：睡眠不足、咖啡因/酒精、药物、紧张状态、测量环境、佩戴/电极接触等可能影响结果。\n"
            "• 隐私与数据使用：数据用于本次报告生成与质量管理/产品改进（如适用），按授权范围处理并设置保存期限；如需撤回授权请联系服务方。\n"
            "• 签署说明：本报告为算法自动生成结果，未进行医师审核签署。"
        )

    def set_text(self, text: str):
        self.body.setText(text)


# ==========================================
# 3. 绘图类
# ==========================================

class RoundedBarCanvas(FigureCanvas):
    def __init__(self, parent=None, width=9, height=2.6, dpi=100):
        plt.rcParams['font.sans-serif'] = ['HeiTi', 'SimHei', 'Arial']
        plt.rcParams['axes.unicode_minus'] = False

        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='none')
        self.axes = self.fig.add_subplot(111)

        super().__init__(self.fig)
        self.setParent(parent)

        self.setMinimumHeight(260)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def plot_emotion_waves(self, neutral_list, negative_list, positive_list):
        self.axes.clear()

        self.fig.subplots_adjust(left=0.06, right=0.96, top=0.90, bottom=0.32)

        categories = ['中性', '负性', '正性']
        colors = [WAVE_COLORS['Delta'], WAVE_COLORS['Theta'], WAVE_COLORS['Alpha'],
                  WAVE_COLORS['Beta'], WAVE_COLORS['Gamma']]
        wave_names = ['δ   Delta', 'θ   Theta', 'α   Alpha', 'β   Beta', 'γ   Gamma']

        data = np.array([neutral_list, negative_list, positive_list])
        n_groups = 3
        n_bars = 5

        bar_width = 0.12
        bar_spacing = 0.02
        group_spacing = 0.40
        group_width = n_bars * bar_width + (n_bars - 1) * bar_spacing
        start_pos = 0.2

        legend_handles = []

        for group_idx in range(n_groups):
            group_start = start_pos + group_idx * (group_width + group_spacing)
            for bar_idx in range(n_bars):
                x_pos = group_start + bar_idx * (bar_width + bar_spacing)
                height_val = data[group_idx, bar_idx]

                draw_height = max(height_val, 0.5)

                rect = FancyBboxPatch(
                    (x_pos, 0), bar_width, draw_height,
                    boxstyle="round,pad=0,rounding_size=0.04",
                    edgecolor='none', facecolor=colors[bar_idx],
                    linewidth=0, alpha=0.9
                )
                self.axes.add_patch(rect)

                if group_idx == 0:
                    legend_handles.append(rect)

                if height_val > 4:
                    self.axes.text(x_pos + bar_width/2, draw_height + 1.5, f'{height_val:.0f}',
                                   ha='center', va='bottom', fontsize=7.5,
                                   color=colors[bar_idx], fontweight='bold')

        group_centers = [start_pos + i * (group_width + group_spacing) + group_width/2
                        for i in range(n_groups)]

        self.axes.set_xticks(group_centers)
        self.axes.set_xticklabels(categories, fontsize=11.5, fontweight='bold', color=TEXT_COLOR_PRIMARY)

        total_width = n_groups * (group_width + group_spacing) + start_pos
        self.axes.set_xlim(0, total_width)
        self.axes.set_ylim(0, 115)
        self.axes.set_ylabel('占比 (%)', fontsize=8.5, color=TEXT_COLOR_SECONDARY)

        self.axes.legend(legend_handles, wave_names,
                        loc='upper right',
                        ncol=1,
                        frameon=True,
                        fontsize=8,
                        edgecolor='#E1E8ED',
                        labelspacing=0.8,      # 行距变松
                        handletextpad=0.8,     # 图标和文字间距
                        borderpad=0.6          # 边框内边距
                        )

        self.style_axes()
        self.draw()

    def plot_feature_bars(self, brain_activity, emotion_bias, attention_concentration):
        self.axes.clear()

        self.fig.subplots_adjust(left=0.08, right=0.96, top=0.88, bottom=0.35)

        categories = ['大脑活跃指数', '情绪偏向指数', '注意力集中度']
        values = [brain_activity, emotion_bias, attention_concentration]
        colors = ['#3498DB', '#9B59B6', '#E67E22']

        bar_width = 0.38
        x = np.arange(len(categories))

        for i, (pos, val, color) in enumerate(zip(x, values, colors)):
            draw_val = max(val, 0.02)
            rect = FancyBboxPatch((pos - bar_width/2, 0), bar_width, draw_val,
                                  boxstyle="round,pad=0,rounding_size=0.05",
                                  edgecolor='none', facecolor=color, linewidth=0, alpha=0.9)
            self.axes.add_patch(rect)

            self.axes.text(pos, draw_val + 0.03, f"{val:.2f}", ha='center', va='bottom',
                           fontsize=9.5, color=color, fontweight='bold')

        self.axes.set_xticks(x)
        self.axes.set_xticklabels(categories, fontsize=10.5, fontweight='bold',
                                   color=TEXT_COLOR_PRIMARY)

        self.axes.set_xlim(-0.6, len(categories) - 0.4)
        self.axes.set_ylim(0, 1.30)
        self.axes.set_yticks([0, 0.5, 1.0])
        self.axes.set_ylabel('指数值', fontsize=8.5, color=TEXT_COLOR_SECONDARY)

        self.style_axes()
        self.draw()

    def style_axes(self):
        self.axes.yaxis.grid(True, linestyle='--', alpha=0.3, color='#BDC3C7')
        self.axes.set_axisbelow(True)
        self.axes.spines['top'].set_visible(False)
        self.axes.spines['right'].set_visible(False)
        self.axes.spines['left'].set_color('#BDC3C7')
        self.axes.spines['bottom'].set_color('#ECF0F1')
        self.axes.spines['bottom'].set_linewidth(1.5)

        self.axes.tick_params(axis='x', length=0)
        self.axes.tick_params(axis='y', colors=TEXT_COLOR_SECONDARY, labelsize=7.5)


# ==========================================
# 4. 仪表盘 与 阶梯进度条
# ==========================================
class InfoBubble(QFrame):
    """
    仪表盘上方的小气泡说明（旧版：InfoBubble(text)）
    ✅ 支持自动换行，避免长文被截断
    """
    def __init__(self, text, parent=None):
        super().__init__(parent)

        # ❌ 不再固定死高度（否则两行一定被裁）
        self.setMinimumHeight(44)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.92);
                border-radius: 10px;
                border: 1px solid rgba(214, 238, 241, 0.95);
            }}
            QLabel {{
                color: {TEXT_COLOR_PRIMARY};
                font-size: 16px;
                font-weight: 700;
                padding: 2px 6px;
                background: transparent;
            }}
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)

        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)                 # ✅ 关键：允许换行
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout.addWidget(label)

class ScoreGaugeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(190, 190)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.score = 0.0
        self.target_score = 0.0

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._animate_step)
        self.anim_step = 1.2

        # 角度范围（类似汽车表盘：从左下到右下，不画底部留白）
        # start_deg: 起始角（度），span_deg: 总跨度（度）
        # 这里用 240°（左下 210° 到右下 -30°）
        self.start_deg = 210.0
        self.span_deg = 240.0

    def set_score(self, score, status_text=None):
        self.target_score = float(max(0.0, min(100.0, score)))
        if self.anim_timer.isActive():
            self.anim_timer.stop()

        if abs(self.target_score - self.score) < 0.6:
            self.score = self.target_score
            self.update()
            return

        self.anim_timer.start(16)

    def _animate_step(self):
        if self.score < self.target_score:
            self.score += self.anim_step
            if self.score >= self.target_score:
                self.score = self.target_score
                self.anim_timer.stop()
        else:
            self.score -= self.anim_step
            if self.score <= self.target_score:
                self.score = self.target_score
                self.anim_timer.stop()
        self.update()

    def _color_for_value(self, v: float) -> QColor:
        # 颜色分段：与你现有风险一致
        if v >= 75:
            return QColor("#EF5350")
        if v >= 65:
            return QColor("#FFA726")
        if v >= 50:
            return QColor("#9CCC65")
        return QColor("#26A69A")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        w, h = self.width(), self.height()
        cx, cy = w / 2.0, h / 2.0

        # ====== 0) 背景透明（关键：让它能“叠”在卡片上）
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.NoBrush)

        # ====== 1) 外圈底盘（淡青白）+ 阴影层次（汽车仪表盘感觉）
        outer_r = min(w, h) * 0.48
        inner_r = outer_r * 0.78

        # 外圈阴影（用径向渐变模拟）
        shadow_grad = QRadialGradient(QPointF(cx - outer_r*0.12, cy - outer_r*0.18), outer_r*1.25)
        shadow_grad.setColorAt(0.00, QColor(255, 255, 255, 255))
        shadow_grad.setColorAt(0.55, QColor(230, 246, 246, 255))
        shadow_grad.setColorAt(1.00, QColor(170, 210, 215, 140))
        painter.setBrush(QBrush(shadow_grad))
        painter.setPen(QPen(QColor(255, 255, 255, 200), 2))
        painter.drawEllipse(QPointF(cx, cy), outer_r, outer_r)

        # 外圈边线（更像“表盘外壳”）
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(255, 255, 255, 220), 3))
        painter.drawEllipse(QPointF(cx, cy), outer_r * 0.98, outer_r * 0.98)

        # ====== 2) 放射状刻度线（外侧一圈短线）
        tick_outer = outer_r * 0.93
        tick_inner = outer_r * 0.86
        tick_count = 36  # 越大越密

        painter.setPen(QPen(QColor(255, 255, 255, 170), 2))
        for i in range(tick_count + 1):
            t = i / tick_count
            deg = self.start_deg - t * self.span_deg
            rad = np.deg2rad(deg)

            x1 = cx + tick_inner * np.cos(rad)
            y1 = cy - tick_inner * np.sin(rad)
            x2 = cx + tick_outer * np.cos(rad)
            y2 = cy - tick_outer * np.sin(rad)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        # ====== 3) 背景弧（浅灰白底弧）
        arc_r = outer_r * 0.80
        arc_rect = QRectF(cx - arc_r, cy - arc_r, arc_r * 2, arc_r * 2)
        bg_pen = QPen(QColor(255, 255, 255, 160), 12)
        bg_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(bg_pen)
        painter.drawArc(arc_rect, int(self.start_deg * 16), int(-self.span_deg * 16))

        # ====== 4) 数值弧（带高光渐变）
        v = max(0.0, min(100.0, float(self.score)))
        val_span = self.span_deg * (v / 100.0)
        main_col = self._color_for_value(v)

        # 主弧
        val_pen = QPen(main_col, 12)
        val_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(val_pen)
        painter.drawArc(arc_rect, int(self.start_deg * 16), int(-val_span * 16))

        # 高光弧（略细、半透明白，叠出“灯光”）
        hi_pen = QPen(QColor(255, 255, 255, 120), 6)
        hi_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(hi_pen)
        painter.drawArc(arc_rect, int((self.start_deg - 2) * 16), int(-(max(0.0, val_span - 6)) * 16))

        # ====== 5) 中心圆（内盘）
        painter.setPen(Qt.NoPen)
        center_grad = QRadialGradient(QPointF(cx - inner_r*0.08, cy - inner_r*0.10), inner_r*1.25)
        center_grad.setColorAt(0.00, QColor(255, 255, 255, 255))
        center_grad.setColorAt(0.65, QColor(230, 246, 246, 255))
        center_grad.setColorAt(1.00, QColor(210, 235, 238, 255))
        painter.setBrush(QBrush(center_grad))
        painter.drawEllipse(QPointF(cx, cy), inner_r, inner_r)

        # 内盘细边
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(255, 255, 255, 210), 2))
        painter.drawEllipse(QPointF(cx, cy), inner_r * 0.98, inner_r * 0.98)

        # ====== 6) 文本：数值 + “分” + “满分100分”（更松、更不挤）
        v_int = int(round(v))

        # ① 数值：减小字号 + 左上移（核心）
        painter.setPen(QColor(TEXT_COLOR_PRIMARY))
        painter.setFont(QFont(GLOBAL_FONT, 34, QFont.Black))  # 原来 36 -> 34

        num_x_shift = -inner_r * 0.10
        num_y_shift = -inner_r * 0.08

        painter.drawText(
            QRectF(num_x_shift, cy - inner_r * 0.55 + num_y_shift, w, inner_r * 0.7),
            Qt.AlignHCenter | Qt.AlignVCenter,
            f"{v_int}"
        )

        # ② “分”：跟随数字位置，稍微右下角（避免与数字重叠）
        painter.setPen(QColor(TEXT_COLOR_PRIMARY))
        painter.setFont(QFont(GLOBAL_FONT, 14, QFont.Bold))  # 原来 16 -> 14

        painter.drawText(
            QRectF(cx + inner_r * 0.45 + num_x_shift, cy - inner_r * 0.30 + num_y_shift, inner_r * 0.7, inner_r * 0.40),
            Qt.AlignLeft | Qt.AlignVCenter,
            "分"
        )

        # ③ “满分100分”：减小字号 + 往下放一点（让中间更松）
        painter.setPen(QColor(TEXT_COLOR_SECONDARY))
        painter.setFont(QFont(GLOBAL_FONT, 12, QFont.Bold))  # 原来 13 -> 12

        painter.drawText(
            QRectF(0, cy + inner_r * 0.16, w, inner_r * 0.42),  # 原来 0.10 -> 0.16（往下）
            Qt.AlignHCenter | Qt.AlignTop,
            "满分100分"
        )

class RiskLevelBar(QWidget):
    """
    ✅ 主流分段状态条
    - 4段颜色块（正常/轻度/中度/重度）
    - 每段显示“标签 + 范围”
    - 一个“当前”气泡指示当前位置
    - value = 0~100
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(210)  # 更高一点，避免文字挤压
        self.value = 0

        self.icon_paths = [
            "assets/4.png",
            "assets/3.png",
            "assets/2.png",
            "assets/1.png",
        ]

        # 颜色：和你的仪表盘颜色一致（统一风格）
        self.colors = [
            QColor("#26A69A"),  # 正常
            QColor("#9CCC65"),  # 轻度
            QColor("#FFA726"),  # 中度
            QColor("#EF5350")   # 重度
        ]
        self.labels = ["正常", "轻度", "中度", "重度"]
        self.ranges_text = ["0-49", "50-64", "65-74", "75-100"]
        self.boundaries = [0, 50, 65, 75, 100]

    def set_value(self, val):
        self.value = max(0, min(100, float(val)))
        self.update()

    def _level_index(self):
        if self.value >= 75:
            return 3
        if self.value >= 65:
            return 2
        if self.value >= 50:
            return 1
        return 0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        margin_x = 25
        gap = 14
    
        # ✅ 状态条顶部基准（用于控制整体上下位置）
        top_y = 62

        # ✅ 底边统一基准线（保证所有梯形底边在同一水平线上）
        base_line = 92

        total_w = w - 2 * margin_x - 3 * gap
        seg_w = total_w / 4

        # ✅ 每段高度：下一段左高 = 上一段右高（衔接流畅）
        # 每段 (left_height, right_height)，表示从 top_y 到顶边的高度差
        # 由于顶边是斜的，我们用 left_top_offset 和 right_top_offset 来描述顶边形状
        # 下面这种写法更直观：使用“顶边相对 top_y 的下移距离”
        # 数值越大，顶边越低（条越矮）
        # 为了“上升”，我们让顶边越来越高 => 下移距离越来越小
        left_drop  = [10, 3, -4, -11]
        right_drop = [3, -4, -11, -18]

        # ✅ 颜色、标签、范围来自你的类属性
        emojis = ["😊", "😐", "😔", "😭"]

        seg_x_ranges = []
        centers = []

        # 1) 画四段直角梯形（左右边竖直，顶边从左到右上升，底边统一）
        x = margin_x
        for i in range(4):
            ld = left_drop[i]
            rd = right_drop[i]

            # 顶边左端 y，顶边右端 y（右端更高 => y更小）
            y_tl = top_y + ld
            y_tr = top_y + rd

            # 底边统一 base_line
            y_bl = base_line
            y_br = base_line

            poly = QPolygonF([
                QPointF(x, y_bl),           # 左下（直角）
                QPointF(x, y_tl),           # 左上（竖直边）
                QPointF(x + seg_w, y_tr),   # 右上（顶边上升）
                QPointF(x + seg_w, y_br)    # 右下（直角）
            ])

            painter.setPen(Qt.NoPen)
            painter.setBrush(self.colors[i])
            painter.drawPolygon(poly)

            seg_x_ranges.append((x, x + seg_w))
            centers.append(x + seg_w / 2)

            x += seg_w + gap

        # # 2) 当前指针定位（正确逻辑：按区间映射到对应段内）
        # bounds = [(0, 49), (50, 64), (65, 74), (75, 100)]

        # v = float(self.value)

        # # 找到属于哪一段
        # seg_idx = 0
        # for i, (lo, hi) in enumerate(bounds):
        #     if lo <= v <= hi:
        #         seg_idx = i
        #         break

        # lo, hi = bounds[seg_idx]

        # # 在该段内的比例（0~1）
        # if hi == lo:
        #     frac = 0.0
        # else:
        #     frac = (v - lo) / (hi - lo)

        # #  坐标 = 段起点 + 段内比例 * 段宽
        # seg_start_x = margin_x + seg_idx * (seg_w + gap)
        # cursor_x = seg_start_x + frac * seg_w


        # # 判断当前属于哪个区间（用于切割）
        # current_idx = 0
        # for i, (sx, ex) in enumerate(seg_x_ranges):
        #     if sx <= cursor_x <= ex:
        #         current_idx = i
        #         break

        # # 3) 在当前所在区间画一条“白色竖切线”（让用户清楚看到所在区间）
        # sx, ex = seg_x_ranges[current_idx]
        # split_x = max(sx + 6, min(cursor_x, ex - 6))  # 不要贴边
        # painter.setPen(QPen(Qt.white, 4))
        # painter.drawLine(QPointF(split_x, top_y + 5), QPointF(split_x, base_line - 2))

        # # 4) 向下箭头
        # # =====================================================

        # # 指针颜色：跟随当前段（0/1/2/3）
        # pointer_color = self.colors[seg_idx]

        # line_len = 10        # 竖线长度
        # line_w = 5           # 竖线粗细
        # arrow_size = 17      # 三角大小

        # # 箭头整体位置（线的顶部 y）
        # line_top_y = top_y - 22   # 越小越靠上
        # line_bottom_y = line_top_y + line_len

        # # 1) 画竖短线
        # painter.setPen(QPen(pointer_color, line_w, Qt.SolidLine, Qt.RoundCap))
        # painter.drawLine(QPointF(cursor_x, line_top_y), QPointF(cursor_x, line_bottom_y))

        # # 2) 画向下三角
        # painter.setPen(Qt.NoPen)
        # painter.setBrush(pointer_color)

        # arrow_poly = QPolygonF([
        #     QPointF(cursor_x - arrow_size/2, line_bottom_y),        # 左上
        #     QPointF(cursor_x + arrow_size/2, line_bottom_y),        # 右上
        #     QPointF(cursor_x, line_bottom_y + arrow_size)           # 下尖
        # ])
        # painter.drawPolygon(arrow_poly)

        # 5) 标签 + 范围 + emoji（在条下方）
        label_y = base_line + 10
        for i in range(4):
            painter.setPen(QColor(TEXT_COLOR_PRIMARY))
            painter.setFont(QFont(GLOBAL_FONT, 10, QFont.Bold))
            painter.drawText(QRectF(centers[i] - seg_w / 2, label_y, seg_w, 18),
                            Qt.AlignCenter, self.labels[i])

            painter.setPen(QColor(TEXT_COLOR_SECONDARY))
            painter.setFont(QFont(GLOBAL_FONT, 8))
            painter.drawText(QRectF(centers[i] - seg_w / 2, label_y + 18, seg_w, 16),
                            Qt.AlignCenter, self.ranges_text[i])

            # ✅ emoji
            # ===== 风险等级图标（PNG）=====
            icon_size = 45   # ✅ 图标显示大小（核心调节点）

            icon_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                self.icon_paths[i]
            )

            if os.path.exists(icon_path):
                pm = QPixmap(icon_path)
                if not pm.isNull():
                    pm = pm.scaled(
                        icon_size,
                        icon_size,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )

                    icon_x = centers[i] - pm.width() / 2
                    icon_y = label_y + 36   # ✅ 控制“图标距离条形的垂直位置”

                    painter.drawPixmap(int(icon_x), int(icon_y), pm)

class ERPTripleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(220)

        plt.rcParams['font.sans-serif'] = ['HeiTi', 'SimHei']
        plt.rcParams['axes.unicode_minus'] = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.neutral_canvas = FigureCanvas(Figure(figsize=(2.8, 2), dpi=100, facecolor='none'))
        self.positive_canvas = FigureCanvas(Figure(figsize=(2.8, 2), dpi=100, facecolor='none'))
        self.negative_canvas = FigureCanvas(Figure(figsize=(2.8, 2), dpi=100, facecolor='none'))

        layout.addWidget(self.neutral_canvas, 1)
        layout.addWidget(self.positive_canvas, 1)
        layout.addWidget(self.negative_canvas, 1)

        self.neutral_data = []
        self.positive_data = []
        self.negative_data = []

    def update_data(self, neutral, positive, negative):
        self.neutral_data = neutral if neutral else []
        self.positive_data = positive if positive else []
        self.negative_data = negative if negative else []
        self.plot_all()

    def plot_all(self):
        self.plot_single(self.neutral_canvas, self.neutral_data, "中性", "#3498DB")
        self.plot_single(self.positive_canvas, self.positive_data, "正性", "#2ECC71")
        self.plot_single(self.negative_canvas, self.negative_data, "负性", "#E74C3C")

    def plot_single(self, canvas, data, title, color):
        canvas.figure.clear()
        ax = canvas.figure.add_subplot(111)

        if len(data) > 0:
            time = np.linspace(0, 6, len(data))
            ax.plot(time, data, color=color, linewidth=2, alpha=0.8)
            ax.fill_between(time, 0, data, color=color, alpha=0.15)

        ax.set_title(title, fontsize=11, fontweight='bold', color=TEXT_COLOR_PRIMARY, pad=8)
        ax.set_xlabel('时间 (s)', fontsize=9, color=TEXT_COLOR_SECONDARY)
        if title == "中性":
            ax.set_ylabel('电压 (μV)', fontsize=9, color=TEXT_COLOR_SECONDARY)

        ax.set_xlim(0, 6)
        ax.axhline(y=0, color='#BDC3C7', linestyle='--', linewidth=1, alpha=0.5)
        ax.grid(True, alpha=0.2, linestyle='--', color='#BDC3C7')

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#ECF0F1')
        ax.spines['bottom'].set_color('#ECF0F1')
        ax.tick_params(colors=TEXT_COLOR_SECONDARY, labelsize=8)

        canvas.figure.tight_layout()
        canvas.draw()

# ==========================================
# 5. 主页面
# ==========================================
class TopAvatarOverlay(QWidget):
    """
    两个卡通头像叠加层：
    - bottom 对齐到 anchor_y（通常就是第一个卡片的顶边）
    - 左右并排，gap 可调
    """
    def __init__(self, parent=None, girl_rel="assets/girl.png", boy_rel="assets/boy.png",
                 avatar_h=150, left_margin=55, gap=70):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent; border: none;")

        self.avatar_h = avatar_h
        self.left_margin = left_margin
        self.gap = gap
        self.anchor_y = None  # 由外部设置：第一个卡片顶边 y

        base = os.path.dirname(os.path.abspath(__file__))
        girl_path = os.path.join(base, girl_rel)
        boy_path  = os.path.join(base, boy_rel)

        self.girl = QLabel(self)
        self.boy  = QLabel(self)
        for lb in (self.girl, self.boy):
            lb.setStyleSheet("background: transparent; border: none;")
            lb.setAttribute(Qt.WA_TranslucentBackground, True)

        self._set_pix(self.girl, girl_path)
        self._set_pix(self.boy, boy_path)

    def _set_pix(self, label: QLabel, abs_path: str):
        if os.path.exists(abs_path):
            pm = QPixmap(abs_path)
            if not pm.isNull():
                pm = pm.scaledToHeight(self.avatar_h, Qt.SmoothTransformation)
                label.setPixmap(pm)
                label.setFixedSize(pm.size())

    def set_anchor_y(self, y: int):
        self.anchor_y = int(y)
        self._reposition()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._reposition()

    def _reposition(self):
        if self.anchor_y is None:
            return

        # bottom 对齐：top = anchor_y - avatar_h
        y = self.anchor_y - self.avatar_h

        # 左右并排（固定 left_margin + gap）
        gx = self.left_margin
        bx = gx + self.girl.width() + self.gap

        self.girl.move(gx, y)
        self.boy.move(bx, y)

class WatermarkOverlay(QWidget):
    """
    斜着重复铺满：logo + 文本（左右排列），整体透明度可调
    """
    def __init__(
        self,
        parent=None,
        text="欣理医疗",
        logo_rel_path="assets/logo.png",
        opacity=0.5,
        angle_deg=-25,
        tile_w=420,
        tile_h=260,
        logo_h=80,
        gap=14
    ):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent; border: none;")

        self.text = text
        self.opacity = float(opacity)
        self.angle_deg = float(angle_deg)

        self.tile_w = int(tile_w)
        self.tile_h = int(tile_h)

        self.logo_h = int(logo_h)
        self.gap = int(gap)

        base = os.path.dirname(os.path.abspath(__file__))
        self.logo_path = os.path.join(base, logo_rel_path)
        self.logo_pm = QPixmap(self.logo_path) if os.path.exists(self.logo_path) else QPixmap()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        painter.setOpacity(self.opacity)

        # 1) 先生成一个“组合块”：logo + 文字（左右排列）
        combo = QPixmap(self.tile_w, self.tile_h)
        combo.fill(Qt.transparent)

        p = QPainter(combo)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        x = 0
        y_center = self.tile_h // 2

        # --- text (LEFT) ---
        p.setPen(QColor(0, 0, 0, 255))

        # 字体更小：22 -> 18（你可继续调 16/17/18）
        f = QFont(GLOBAL_FONT, 16, QFont.Bold)
        p.setFont(f)

        fm = p.fontMetrics()
        text_w = fm.horizontalAdvance(self.text)
        text_h = fm.height()

        # 左侧文字起点
        x_text = 0
        p.drawText(QRectF(x_text, 0, text_w + 10, self.tile_h), Qt.AlignVCenter | Qt.AlignLeft, self.text)

        # --- logo (RIGHT) ---
        if not self.logo_pm.isNull():
            # 图片更大：在这里额外乘 1.6（同时你也可以直接在 __init__ 里把 logo_h 改大）
            logo = self.logo_pm.scaledToHeight(int(self.logo_h * 1.6), Qt.SmoothTransformation)

            # logo 放在文字右侧
            x_logo = x_text + text_w + self.gap
            p.drawPixmap(x_logo, y_center - logo.height() // 2, logo)

        p.end()

        # 2) 旋转后平铺
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.angle_deg)
        painter.translate(-self.width() / 2, -self.height() / 2)

        step_x = self.tile_w
        step_y = self.tile_h

        # 多铺一圈避免旋转后空白
        start_x = -step_x
        start_y = -step_y
        end_x = self.width() + step_x
        end_y = self.height() + step_y

        yy = start_y
        while yy < end_y:
            xx = start_x
            while xx < end_x:
                painter.drawPixmap(xx, yy-25, combo)
                xx += step_x
            yy += step_y

class MentalReportPage(QWidget):
    flow_finished = pyqtSignal(str)  # 'exported' or 'closed'

    def __init__(self, mode="client"):
        super().__init__()
        self.setWindowTitle("心理健康风险评估报告")
        self.resize(1100, 1000)
        self.setStyleSheet(f"background-color: {BG_COLOR}; font-family: '{GLOBAL_FONT}';")

        self.mode = mode

        # 允许多个实例（分页系统中，某些组件可能在不同页面重复出现）
        self.all_summary_widgets = []
        self.all_dep_widgets = []
        self.all_anx_widgets = []
        self.all_risk_bars = []
        self.all_action_widgets = []
        self.all_conclusion_labels = []
        self.all_layered_widgets = []
        self.all_erp_widgets = []
        self.all_emotion_wave_canvases = []
        self.all_feature_canvases = []
        self.all_quality_widgets = []

        self.scores_data = {'depression': 0, 'anxiety': 0}
        self.feature_values = {}
        self.emotion_wave_data = {}
        
        # 允许多个实例（分页系统中，某些组件可能在不同页面重复出现）
        self.all_summary_widgets = []
        self.all_dep_widgets = []
        self.all_anx_widgets = []
        self.all_risk_bars = []
        self.all_action_widgets = []
        self.all_conclusion_labels = []
        self.all_layered_widgets = []

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none;")

        # 按钮容器
        btn_bar = QWidget()
        btn_bar.setStyleSheet(f"background: white; border-top: 1px solid #ECF0F1;")
        bl = QHBoxLayout(btn_bar)
        bl.setContentsMargins(30, 15, 30, 15)

        self.btn_export = QPushButton("导出用户版 PDF" if self.mode == "client" else "导出专业版 PDF")
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT_COLOR}; color: white;
                padding: 12px 26px; border-radius: 8px; font-weight: bold; font-size: 14px;
            }}
            QPushButton:hover {{ background-color: #25A9A4; }}
        """)
        self.btn_export.clicked.connect(self.export_pdf)

        self.btn_export_other = QPushButton("导出专业版 PDF" if self.mode == "client" else "")
        self.btn_export_other.setCursor(Qt.PointingHandCursor)
        self.btn_export_other.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFFFFF; color: {ACCENT_COLOR};
                padding: 12px 22px; border-radius: 8px; font-weight: bold; font-size: 14px;
                border: 2px solid {ACCENT_COLOR};
            }}
            QPushButton:hover {{ background-color: rgba(43, 182, 177, 0.08); }}
        """)
        if self.mode == "client":
            self.btn_export_other.clicked.connect(lambda: self._request_professional_export())
        else:
            self.btn_export_other.hide()

        bl.addStretch()
        bl.addWidget(self.btn_export_other)
        bl.addSpacing(12)
        bl.addWidget(self.btn_export)
        
        # 组装主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.scroll_area)
        main_layout.addWidget(btn_bar)

        # 初始化页面
        self.pages = []
        self._setup_pages()

    def _setup_pages(self):
        # 根据模式决定页数
        total_pages = 2 if self.mode == "client" else 4
        
        # 报告画布容器
        self.report_container = QWidget()
        self.report_container_layout = QVBoxLayout(self.report_container)
        self.report_container_layout.setContentsMargins(0, 0, 0, 0)
        self.report_container_layout.setSpacing(20) # 预览时页面间的间距
        self.report_container_layout.setAlignment(Qt.AlignCenter)
        
        for i in range(total_pages):
            p = ReportPage(i + 1, total_pages)
            self.pages.append(p)
            self.report_container_layout.addWidget(p)
            
            # 水印层（每页一个）
            watermark = WatermarkOverlay(parent=p, opacity=0.15)
            watermark.setGeometry(0, 0, A4_WIDTH, A4_HEIGHT)
            watermark.lower()
            
        self.scroll_area.setWidget(self.report_container)
        
        # 填充内容
        self._fill_content()

    def _fill_content(self):
        # 核心：清空之前的所有实例列表，防止分页/重构导致的 stale references (C++ object deleted)
        self.all_summary_widgets.clear()
        self.all_dep_widgets.clear()
        self.all_anx_widgets.clear()
        self.all_risk_bars.clear()
        self.all_action_widgets.clear()
        self.all_conclusion_labels.clear()
        self.all_layered_widgets.clear()
        self.all_erp_widgets.clear()
        self.all_emotion_wave_canvases.clear()
        self.all_feature_canvases.clear()
        self.all_quality_widgets.clear()
        # --- Page 1 ---
        p1 = self.pages[0]
        
        # Header Overlay Stack
        header_stack = QWidget()
        header_stack.setFixedSize(A4_WIDTH, 500)
        stack_layout = QStackedLayout(header_stack)
        stack_layout.setStackingMode(QStackedLayout.StackAll)
        
        # 1. Header Background
        self.header = HeaderWidget()
        self.setup_header()
        
        # 2. Avatar
        self.avatar_overlay = TopAvatarOverlay(avatar_h=120, left_margin=55, gap=50)
        self.avatar_overlay.set_anchor_y(500 - 70)
        
        stack_layout.addWidget(self.avatar_overlay)
        stack_layout.addWidget(self.header)
        
        p1.content_layout.addWidget(header_stack)
        
        # Content on Page 1
        content_p1 = QWidget()
        content_p1_v = QVBoxLayout(content_p1)
        content_p1_v.setContentsMargins(30, -70, 30, 0) # 压住 header
        content_p1_v.setSpacing(15)
        
        sw = ConclusionSummaryWidget()
        self.all_summary_widgets.append(sw)
        content_p1_v.addWidget(create_card(CardWithSideImage(sw, "assets/5.png"), "结论卡片（筛查提示）"))
        
        aw = ActionAdviceWidget()
        self.all_action_widgets.append(aw)
        content_p1_v.addWidget(create_card(CardWithSideImage(aw, "assets/6.png"), "行动建议"))
        
        self.help_widget = ProfessionalHelpWidget()
        content_p1_v.addWidget(create_card(CardWithSideImage(self.help_widget, "assets/7.png"), "需要专业帮助的提示"))
        
        content_p1_v.addStretch(1)
        p1.content_layout.addWidget(content_p1)
        
        # --- Page 2 ---
        p2 = self.pages[1]
        content_p2 = QWidget()
        content_p2_v = QVBoxLayout(content_p2)
        content_p2_v.setContentsMargins(30, 20, 30, 20)
        content_p2_v.setSpacing(10)
        
        # Risk Index
        dw = ScoreGaugeWidget()
        aw = ScoreGaugeWidget()
        rb = RiskLevelBar()
        self.all_dep_widgets.append(dw)
        self.all_anx_widgets.append(aw)
        self.all_risk_bars.append(rb)
        
        risk_content = QVBoxLayout()
        gauge_row = QHBoxLayout()
        gauge_row.setSpacing(15)
        
        # 左侧装饰图
        test_img = QLabel()
        test_img.setFixedSize(160, 180) # 稍微减少高度以防截断
        test_img.setAlignment(Qt.AlignCenter)
        p_test = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "test.png")
        if os.path.exists(p_test):
            pm = QPixmap(p_test).scaled(test_img.width(), test_img.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            test_img.setPixmap(pm)
        gauge_row.addWidget(test_img, 2)

        def create_gauge_box(title, gauge):
            box = QFrame()
            box.setStyleSheet(f"background: rgba(255,255,255,0.85); border-radius: 18px; border: 1px solid {CARD_BORDER};")
            v = QVBoxLayout(box)
            v.setContentsMargins(5, 5, 5, 5) # 紧凑布局
            bubble = InfoBubble(f"{title}")
            v.addWidget(bubble, alignment=Qt.AlignCenter)
            v.addWidget(gauge, alignment=Qt.AlignCenter)
            return box

        gauge_row.addWidget(create_gauge_box("抑郁指数", dw), 3)
        gauge_row.addWidget(create_gauge_box("焦虑指数", aw), 3)
        
        risk_content.addLayout(gauge_row)
        risk_content.addWidget(rb)
        
        risk_container = QWidget()
        risk_container.setLayout(risk_content)
        content_p2_v.addWidget(create_card(risk_container, "风险指数评估"))
        
        # Conclusion
        cl = QLabel()
        cl.setWordWrap(True)
        cl.setStyleSheet(f"font-size: 20px; font-weight: 600; line-height: 1.5; color: {TEXT_COLOR_SECONDARY};")
        self.all_conclusion_labels.append(cl)
        content_p2_v.addWidget(create_card(CardWithSideImage(cl, "assets/8.png"), "综合评估结论"))
        
        # Disclaimer (Stay on Page 2 for user version)
        self.disclaimer_widget = DisclaimerPrivacyWidget()
        content_p2_v.addWidget(create_card(self.disclaimer_widget, "风险告知与免责声明"))
        
        # Footer Removed per user request
        
        content_p2_v.addStretch(1)
        p2.content_layout.addWidget(content_p2)
        
        if self.mode == "professional":
             # 专业版 Page 3: 技术指标 1
             p3 = self.pages[2]
             content_p3 = QWidget()
             content_p3_v = QVBoxLayout(content_p3)
             content_p3_v.setContentsMargins(30, 40, 30, 30)
             content_p3_v.setSpacing(15)
             
             erp_w = ERPTripleWidget()
             self.all_erp_widgets.append(erp_w)
             content_p3_v.addWidget(create_card(erp_w, "事件相关电位 (ERP) 分析"))
             
             ewc = RoundedBarCanvas(width=9, height=2.0)
             self.all_emotion_wave_canvases.append(ewc)
             wave_explain = ExplanationCard(
                title="个性化解释",
                body=(
                    "该模块展示不同情绪刺激条件下脑电频带分布。若负性条件下β/γ比例偏高，可能提示紧张水平提升。"
                ),
                img_rel_path="assets/doctor.png"
             )
             content_p3_v.addWidget(create_card(TwoColumnModule(ewc, wave_explain), "情绪状态脑波频带分布"))
             content_p3_v.addStretch(1)
             p3.content_layout.addWidget(content_p3)
             
             # 专业版 Page 4: 技术指标 2 + 免责
             p4 = self.pages[3]
             content_p4 = QWidget()
             content_p4_v = QVBoxLayout(content_p4)
             content_p4_v.setContentsMargins(30, 40, 30, 30)
             content_p4_v.setSpacing(15)
             
             fc = RoundedBarCanvas(width=9, height=2.0)
             self.all_feature_canvases.append(fc)
             feat_explain = ExplanationCard(
                title="个性化解释",
                body=(
                    "脑电信号提取出的大脑活跃度、情绪偏向与注意力。建议结合量表综合评估。"
                ),
                img_rel_path="assets/doctor.png"
             )
             content_p4_v.addWidget(create_card(TwoColumnModule(fc, feat_explain), "脑电特征指标分析"))
             
             # 在专业版，Page 2 的免责和 Footer 应该移到最后一页 (Page 4)
             # 所以我们需要调整 Page 2 的内容，如果是在专业版模式下。
             pass

    def setup_header(self):
        self.header = HeaderWidget()
        self.header.setStyleSheet("QLabel { background-color: transparent; }")

        hl = self.header.layout()
        hl.addSpacing(30)

        title = QLabel("心理健康风险评估报告")
        title.setStyleSheet(
            "font-size: 44px; font-weight: 900; color: #FFFFFF; "
            "letter-spacing: 2px; background: transparent;"
        )
        title.setAlignment(Qt.AlignCenter)
        hl.addWidget(title)

        sub_title = QLabel("Mental Health Risk Assessment Report")
        sub_title.setStyleSheet(
            "font-size: 13px; color: rgba(255,255,255,0.9); "
            "font-weight: 500; background: transparent;"
        )
        sub_title.setAlignment(Qt.AlignCenter)
        hl.addWidget(sub_title)

        hl.addSpacing(15)

                # ===== 信息栏：4列2行（8项）+ 底部单行（审核签署）=====
        info_container = QWidget()
        info_container.setStyleSheet("background: transparent;")
        info_v = QVBoxLayout(info_container)
        info_v.setContentsMargins(0, 0, 0, 0)
        info_v.setSpacing(10)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)

        # 只保留原来的：姓名、年龄
        self.tag_name = InfoTag("姓名: --", "👤")
        self.tag_age  = InfoTag("年龄: --", "📅")

        # 新增图片里的项目（共 7 个）
        self.tag_report_id   = InfoTag("报告编号: --", "📄")
        self.tag_location    = InfoTag("采集地点: --", "📍")
        self.tag_collect_dt  = InfoTag("采集时间:\n --", "🧾")
        self.tag_gen_dt      = InfoTag("报告生成时间:\n --", "🖨️")
        self.tag_device_ver  = InfoTag("采集设备:\n --", "🧠")
        self.tag_operator    = InfoTag("操作者:\n --", "🧑‍💼")

        # 前8项：4列2行排布（每个格子都居中）
        tags_8 = [
            self.tag_name, self.tag_age, self.tag_report_id,  self.tag_location,
            self.tag_collect_dt, self.tag_gen_dt, self.tag_device_ver, self.tag_operator
        ]

        for i, tag in enumerate(tags_8):
            r = i // 4
            c = i % 4
            grid.addWidget(tag, r, c, alignment=Qt.AlignCenter)
            tag.setMinimumWidth(220)  # ✅ 控制每列宽度（空间不够可降到 200/180）

        info_v.addLayout(grid)

        # 第9项：审核签署（单独放在下面一整行）
        self.tag_signature = QLabel()
        self.tag_signature.setWordWrap(True)
        self.tag_signature.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        signature_text = (
            "审核签署：本报告为算法自动生成结果，未进行医师审核签署"
        )
        self.tag_signature.setText(
            f'<p style="margin:0; text-indent:2em;">{signature_text}</p>'
        )
        self.tag_signature.setTextFormat(Qt.RichText)
        self.tag_signature.setStyleSheet("""
            QLabel {
                color: rgba(255,255,255,0.95);
                font-family: "HeiTi";
                font-size: 20px;
                font-weight: 600;
                background: transparent;
                padding: 2px 10px;
            }
        """)
        info_v.addWidget(self.tag_signature)

        hl.addWidget(info_container, alignment=Qt.AlignCenter)
        hl.addStretch()

    def set_person_info(
        self,
        name="--",
        age="--",
        report_id="--",
        location="--",
        collect_dt="--",
        gen_dt="--",
        device_ver="--",
        operator="--",
        signature_text=None
    ):
        # 只保留：姓名、年龄（原来的四个里只留这俩）
        self.tag_name.setText(f"👤 姓名: {name}")
        self.tag_age.setText(f"📅 年龄: {age}")

        # 新增项目
        self.tag_report_id.setText(f"📄 报告编号: {report_id}")
        self.tag_location.setText(f"📍 采集地点: {location}")
        self.tag_collect_dt.setText(f"🧾 采集时间:\n {collect_dt}")
        self.tag_gen_dt.setText(f"🖨️ 报告生成时间:\n {gen_dt}")
        self.tag_device_ver.setText(f"🧠 采集设备:\n {device_ver}")
        self.tag_operator.setText(f"🧑‍💼 操作者:\n {operator}")

        if signature_text:
            self.tag_signature.setText(f"审核签署：{signature_text}")


    def set_scores(self, s1, t1, s2, t2):
        # 更新所有实例
        for dw in self.all_dep_widgets: dw.set_score(s1, t1)
        for aw in self.all_anx_widgets: aw.set_score(s2, t2)

        # 风险条：取更高风险的一项
        risk_score = max(float(s1), float(s2))
        for rb in self.all_risk_bars: rb.set_value(risk_score)

        self.scores_data = {'depression': float(s1), 'anxiety': float(s2)}

        # 客户版置顶结论卡
        for sw in self.all_summary_widgets:
            sw.set_scores(float(s1), float(s2))

        # 行动建议
        for acw in self.all_action_widgets:
            acw.set_by_risk(risk_score)

    def set_erp_data(self, neutral, positive, negative):
        for w in self.all_erp_widgets:
            w.update_data(neutral, positive, negative)
            w.plot_all()

    def set_emotion_wave_data(self, n, neg, pos):
        self.emotion_wave_data = {'neutral': n, 'negative': neg, 'positive': pos}
        for c in self.all_emotion_wave_canvases:
            c.plot_emotion_waves(n, neg, pos)

    def set_feature_data(self, brain_activity, emotion_bias, attention_concentration):
        self.feature_values = {
            'brain_activity': brain_activity,
            'emotion_bias': emotion_bias,
            'attention_concentration': attention_concentration
        }
        for c in self.all_feature_canvases:
            c.plot_feature_bars(brain_activity, emotion_bias, attention_concentration)

    def generate_auto_conclusion(self):
        if not all([self.scores_data, self.feature_values, self.emotion_wave_data]):
            return "数据不完整。"

        dep = self.scores_data.get('depression', 0)
        anx = self.scores_data.get('anxiety', 0)
        brain = self.feature_values.get('brain_activity', 0)
        bias = self.feature_values.get('emotion_bias', 0.5)
        att = self.feature_values.get('attention_concentration', 0)

        # 计算平均分
        avg = (dep + anx) / 2

        # 4级判断逻辑
        if avg < 50:
            risk = "无风险"
            status_desc = "整体心理状态平稳，处于健康范围内。"
        elif avg < 65:
            risk = "轻度风险"
            status_desc = "存在轻微的心理压力或波动，建议增加休息，注意劳逸结合。"
        elif avg < 75:
            risk = "中度风险"
            status_desc = "存在一定的心理风险信号，建议主动进行压力调节，必要时寻求专业咨询。"
        else:
            risk = "重度风险"
            status_desc = "心理风险信号显著，强烈建议尽快寻求专业评估与支持。"

        text = f"综合评估结果显示，受测者的当前心理健康风险处于{risk}水平。抑郁指数为{dep}分，焦虑指数为{anx}分。{status_desc}"

        text += f"在脑电特征方面，大脑活跃指数为{brain:.2f}，"
        if brain > 0.7:
            text += "数值偏高，提示认知负荷较大；"
        elif brain < 0.3:
            text += "数值偏低，提示可能存在疲劳；"
        else:
            text += "处于正常区间，认知功能良好；"

        text += f"情绪偏向指数为{bias:.2f}，"
        if bias > 0.55:
            text += "显示出积极的情绪倾向；"
        elif bias < 0.45:
            text += "显示出消极的情绪倾向；"
        else:
            text += "情绪状态相对平衡；"

        text += f"注意力集中度为{att:.2f}。"
        if att > 0.6:
            text += "注意力水平表现良好。"
        else:
            text += "注意力略有分散，建议适当休息或进行注意力训练。"

        text += "综合建议保持规律作息，适度运动。"

        return text

    def set_conclusion(self, t):
        for cl in self.all_conclusion_labels:
            cl.setText(t)


    def _request_professional_export(self):
        # 客户版：用户点击“导出专业版 PDF”，交给 main.py 打开专业版并触发导出
        try:
            self.flow_finished.emit("open_professional_export")
        except Exception:
            pass
        self.close()

    def closeEvent(self, event):
        # 通知主流程：窗口被关闭
        try:
            self.flow_finished.emit("closed")
        except Exception:
            pass
        super().closeEvent(event)

    def export_pdf(self, filename=None):
        if not filename:
            filename, _ = QFileDialog.getSaveFileName(
                self, "导出报告",
                ("心理健康评估报告-用户版.pdf" if self.mode == "client" else "心理健康评估报告-专业版.pdf"), "PDF Files (*.pdf)"
                )
        if not filename:
            return

        try:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setPageSize(QPrinter.A4)
            printer.setOutputFileName(filename)
            printer.setPageMargins(0, 0, 0, 0, QPrinter.Millimeter)

            painter = QPainter(printer)
            
            # 渲染每一页
            for i, page in enumerate(self.pages):
                if i > 0:
                    printer.newPage()
                
                # 抓取页面
                pixmap = page.grab()
                
                rect = printer.pageRect()
                # 保持比例充满页面
                scaled_pixmap = pixmap.scaled(rect.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
                x = int((rect.width() - scaled_pixmap.width()) / 2)
                y = int((rect.height() - scaled_pixmap.height()) / 2)
                
                painter.drawPixmap(x, y, scaled_pixmap)

            painter.end()

            print(f"导出成功: {filename}")
            # QMessageBox.information(self, "成功", "PDF 报告导出成功！")
            # 通知主流程：已导出
            try:
                self.flow_finished.emit("exported")
            except Exception:
                pass

        except Exception as e:
            print(f"导出失败: {e}")
            if 'painter' in locals() and painter.isActive():
                painter.end()
            QMessageBox.critical(self, "导出失败", f"生成 PDF 时发生错误：{str(e)}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "watermark") and self.watermark:
            self.watermark.setGeometry(self.report_widget.rect())
            self.watermark.raise_()

if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    window = MentalReportPage()
    window.show()
    sys.exit(app.exec_())
