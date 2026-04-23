#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Anthropic Design Theme - QSS样式表
温暖、专业、简洁的设计风格
"""

# Anthropic 设计系统颜色
ANTHROPIC_COLORS = {
    # 主色系
    "primary": "#D97757",        # 陶土橙
    "primary_hover": "#C66A4C",
    "primary_light": "#F5E6D3",  # 柔米色

    # 强调色
    "accent": "#E8B4A0",         # 蜜桃色

    # 背景色
    "background": "#FAF7F4",     # 米白
    "surface": "#FFFFFF",        # 纯白
    "surface_variant": "#F0EBE7",

    # 文本色
    "text_primary": "#2D2926",   # 暖炭灰
    "text_secondary": "#6B6560", # 哑灰
    "text_hint": "#9A958F",

    # 边框色
    "border": "#E8E4E1",
    "border_focus": "#D97757",

    # 状态色
    "success": "#5B9E5F",
    "warning": "#D9A545",
    "error": "#D95555",
    "info": "#5B8ED9",
}

# QSS样式表
ANTHROPIC_QSS = """
/* ===== 全局样式 ===== */
* {
    font-family: "Microsoft YaHei UI", "Segoe UI", "PingFang SC", sans-serif;
    font-size: 10pt;
}

QWidget {
    background-color: #FAF7F4;
    color: #2D2926;
}

/* ===== 主窗口 ===== */
QMainWindow {
    background-color: #FAF7F4;
}

QMainWindow::separator {
    background: #E8E4E1;
    width: 1px;
    height: 1px;
}

/* ===== 对话框 ===== */
QDialog {
    background-color: #FAF7F4;
}

/* ===== 按钮 ===== */
QPushButton {
    background-color: #FFFFFF;
    color: #2D2926;
    border: 1px solid #E8E4E1;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #F5E6D3;
    border-color: #D97757;
}

QPushButton:pressed {
    background-color: #E8B4A0;
}

QPushButton:disabled {
    background-color: #F0EBE7;
    color: #9A958F;
    border-color: #E8E4E1;
}

/* 主按钮 */
QPushButton[class="primary"] {
    background-color: #D97757;
    color: #FFFFFF;
    border: none;
}

QPushButton[class="primary"]:hover {
    background-color: #C66A4C;
}

QPushButton[class="primary"]:pressed {
    background-color: #B85D42;
}

/* 危险按钮 */
QPushButton[class="danger"] {
    background-color: #D95555;
    color: #FFFFFF;
    border: none;
}

QPushButton[class="danger"]:hover {
    background-color: #C94949;
}

/* ===== 输入框 ===== */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #FFFFFF;
    color: #2D2926;
    border: 1px solid #E8E4E1;
    border-radius: 6px;
    padding: 8px;
    selection-background-color: #F5E6D3;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #D97757;
}

QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {
    background-color: #F0EBE7;
    color: #9A958F;
}

/* ===== 下拉框 ===== */
QComboBox {
    background-color: #FFFFFF;
    color: #2D2926;
    border: 1px solid #E8E4E1;
    border-radius: 6px;
    padding: 6px 12px;
    min-width: 100px;
}

QComboBox:hover {
    border-color: #D97757;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    image: url(:/icons/chevron-down.svg);
    width: 12px;
    height: 12px;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #E8E4E1;
    border-radius: 6px;
    selection-background-color: #F5E6D3;
    selection-color: #2D2926;
}

/* ===== 复选框 ===== */
QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #E8E4E1;
    border-radius: 4px;
    background-color: #FFFFFF;
}

QCheckBox::indicator:hover {
    border-color: #D97757;
}

QCheckBox::indicator:checked {
    background-color: #D97757;
    border-color: #D97757;
    image: url(:/icons/check.svg);
}

QCheckBox::indicator:checked:hover {
    background-color: #C66A4C;
}

QCheckBox::indicator:disabled {
    background-color: #F0EBE7;
    border-color: #E8E4E1;
}

/* ===== 单选按钮 ===== */
QRadioButton {
    spacing: 8px;
}

QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #E8E4E1;
    border-radius: 9px;
    background-color: #FFFFFF;
}

QRadioButton::indicator:hover {
    border-color: #D97757;
}

QRadioButton::indicator:checked {
    background-color: #FFFFFF;
    border: 6px solid #D97757;
}

QRadioButton::indicator:checked:hover {
    border-color: #C66A4C;
}

/* ===== 滑块 ===== */
QSlider::groove:horizontal {
    height: 4px;
    background-color: #E8E4E1;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    width: 16px;
    height: 16px;
    background-color: #D97757;
    border-radius: 8px;
    margin: -6px 0;
}

QSlider::handle:horizontal:hover {
    background-color: #C66A4C;
}

QSlider::sub-page:horizontal {
    background-color: #F5E6D3;
    border-radius: 2px;
}

/* ===== 进度条 ===== */
QProgressBar {
    background-color: #E8E4E1;
    border: none;
    border-radius: 3px;
    height: 8px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #D97757;
    border-radius: 3px;
}

/* ===== 分组框 ===== */
QGroupBox {
    background-color: #FFFFFF;
    color: #2D2926;
    border: 1px solid #E8E4E1;
    border-radius: 10px;
    margin-top: 12px;
    padding: 12px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    background-color: #FFFFFF;
}

/* ===== 滚动条 ===== */
QScrollBar:vertical {
    background-color: #F0EBE7;
    width: 12px;
    border-radius: 6px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #D97757;
    min-height: 30px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #C66A4C;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background-color: #F0EBE7;
    height: 12px;
    border-radius: 6px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background-color: #D97757;
    min-width: 30px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #C66A4C;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* ===== 列表 ===== */
QListWidget {
    background-color: #FFFFFF;
    border: 1px solid #E8E4E1;
    border-radius: 6px;
    outline: none;
}

QListWidget::item {
    padding: 8px 12px;
    border-radius: 4px;
    margin: 2px;
}

QListWidget::item:hover {
    background-color: #F5E6D3;
}

QListWidget::item:selected {
    background-color: #F5E6D3;
    color: #2D2926;
}

QListWidget::item:selected:hover {
    background-color: #E8B4A0;
}

/* ===== 表格 ===== */
QTableView {
    background-color: #FFFFFF;
    border: 1px solid #E8E4E1;
    border-radius: 6px;
    gridline-color: #E8E4E1;
    outline: none;
}

QTableView::item {
    padding: 8px;
    border: none;
}

QTableView::item:selected {
    background-color: #F5E6D3;
    color: #2D2926;
}

QTableView::horizontalHeader {
    background-color: #FAF7F4;
    color: #6B6560;
    border: none;
    border-bottom: 1px solid #E8E4E1;
    padding: 8px;
    font-weight: 600;
}

QTableView::verticalHeader {
    background-color: #FAF7F4;
    border: none;
    border-right: 1px solid #E8E4E1;
    padding: 8px;
}

/* ===== 标签页 ===== */
QTabWidget::pane {
    background-color: #FFFFFF;
    border: 1px solid #E8E4E1;
    border-radius: 6px;
    top: -1px;
}

QTabBar::tab {
    background-color: #F0EBE7;
    color: #6B6560;
    border: 1px solid #E8E4E1;
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    padding: 10px 20px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #FFFFFF;
    color: #2D2926;
    border-color: #E8E4E1;
    border-bottom: 2px solid #D97757;
}

QTabBar::tab:hover:!selected {
    background-color: #F5E6D3;
}

/* ===== 工具栏 ===== */
QToolBar {
    background-color: #FFFFFF;
    border: none;
    border-bottom: 1px solid #E8E4E1;
    spacing: 4px;
    padding: 4px;
}

QToolBar::separator {
    background-color: #E8E4E1;
    width: 1px;
    margin: 4px 8px;
}

QToolButton {
    background-color: transparent;
    border: none;
    border-radius: 6px;
    padding: 6px;
}

QToolButton:hover {
    background-color: #F5E6D3;
}

QToolButton:pressed {
    background-color: #E8B4A0;
}

/* ===== 菜单 ===== */
QMenuBar {
    background-color: #FFFFFF;
    color: #2D2926;
    border-bottom: 1px solid #E8E4E1;
}

QMenuBar::item {
    padding: 8px 16px;
    border-radius: 4px;
}

QMenuBar::item:selected {
    background-color: #F5E6D3;
}

QMenu {
    background-color: #FFFFFF;
    border: 1px solid #E8E4E1;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    padding: 8px 24px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #F5E6D3;
}

QMenu::separator {
    height: 1px;
    background-color: #E8E4E1;
    margin: 4px 8px;
}

/* ===== 状态栏 ===== */
QStatusBar {
    background-color: #FFFFFF;
    color: #6B6560;
    border-top: 1px solid #E8E4E1;
}

/* ===== 消息框 ===== */
QMessageBox {
    background-color: #FFFFFF;
}

QMessageBox QPushButton {
    min-width: 80px;
    padding: 6px 16px;
}

/* ===== 标签 ===== */
QLabel {
    color: #2D2926;
    background-color: transparent;
}

QLabel[class="heading"] {
    font-size: 18pt;
    font-weight: 600;
    color: #2D2926;
}

QLabel[class="subheading"] {
    font-size: 12pt;
    font-weight: 500;
    color: #6B6560;
}

QLabel[class="hint"] {
    color: #9A958F;
    font-style: italic;
}

/* ===== 旋转框 ===== */
QSpinBox, QDoubleSpinBox {
    background-color: #FFFFFF;
    color: #2D2926;
    border: 1px solid #E8E4E1;
    border-radius: 6px;
    padding: 6px;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #D97757;
}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #F0EBE7;
    border: none;
    width: 20px;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #F5E6D3;
}

/* ===== 分割器 ===== */
QSplitter::handle {
    background-color: #E8E4E1;
}

QSplitter::handle:hover {
    background-color: #D97757;
}

/* ===== 框架 ===== */
QFrame {
    background-color: transparent;
    border: none;
}

QFrame[class="card"] {
    background-color: #FFFFFF;
    border: 1px solid #E8E4E1;
    border-radius: 10px;
    padding: 12px;
}

QFrame[class="separator"] {
    background-color: #E8E4E1;
    max-height: 1px;
    max-width: 1px;
}

/* ===== 工具提示 ===== */
QToolTip {
    background-color: #2D2926;
    color: #FFFFFF;
    border: none;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 9pt;
}
"""


def get_stylesheet() -> str:
    """获取Anthropic主题样式表"""
    return ANTHROPIC_QSS


def get_color(name: str) -> str:
    """获取指定颜色"""
    return ANTHROPIC_COLORS.get(name, "#000000")
