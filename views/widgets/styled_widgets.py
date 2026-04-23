#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Styled Widget Components
Anthropic Design System 自定义组件
"""

from PyQt6.QtWidgets import (
    QPushButton, QLabel, QFrame, QWidget,
    QVBoxLayout, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtProperty
from PyQt6.QtGui import QFont


# ===== 按钮 =====

class StyledButton(QPushButton):
    """基础样式按钮"""

    def __init__(self, text: str = "", parent: QWidget = None):
        super().__init__(text, parent)
        self.setMinimumWidth(80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class PrimaryButton(StyledButton):
    """主按钮 - 陶土橙"""

    def __init__(self, text: str = "", parent: QWidget = None):
        super().__init__(text, parent)
        self.setProperty("class", "primary")


class DangerButton(StyledButton):
    """危险按钮 - 红色"""

    def __init__(self, text: str = "", parent: QWidget = None):
        super().__init__(text, parent)
        self.setProperty("class", "danger")


# ===== 标签 =====

class HeadingLabel(QLabel):
    """标题标签"""

    def __init__(self, text: str = "", parent: QWidget = None):
        super().__init__(text, parent)
        self.setProperty("class", "heading")
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        self.setFont(font)


class SubheadingLabel(QLabel):
    """副标题标签"""

    def __init__(self, text: str = "", parent: QWidget = None):
        super().__init__(text, parent)
        self.setProperty("class", "subheading")
        font = QFont()
        font.setPointSize(12)
        font.setWeight(QFont.Weight.DemiBold)
        self.setFont(font)


class HintLabel(QLabel):
    """提示标签"""

    def __init__(self, text: str = "", parent: QWidget = None):
        super().__init__(text, parent)
        self.setProperty("class", "hint")
        font = QFont()
        font.setItalic(True)
        self.setFont(font)


# ===== 框架 =====

class CardFrame(QFrame):
    """卡片框架 - 圆角白色背景"""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setProperty("class", "card")


# ===== 容器组件 =====

class ButtonRow(QWidget):
    """按钮行容器"""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(8)

    def addButton(self, button: QPushButton, stretch: int = 0):
        """添加按钮"""
        self._layout.addWidget(button, stretch)

    def addStretch(self, stretch: int = 1):
        """添加弹性空间"""
        self._layout.addStretch(stretch)


class FormRow(QWidget):
    """表单行容器 - 标签 + 输入框"""

    def __init__(self, label_text: str = "", widget: QWidget = None, parent: QWidget = None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)

        if label_text:
            label = QLabel(label_text)
            label.setMinimumWidth(100)
            layout.addWidget(label)

        if widget:
            layout.addWidget(widget, 1)

        self._label = label if label_text else None
        self._widget = widget

    def setLabel(self, text: str):
        """设置标签文本"""
        if self._label:
            self._label.setText(text)

    def setWidget(self, widget: QWidget):
        """设置输入组件"""
        if self._widget:
            self.layout().removeWidget(self._widget)
        self._widget = widget
        self.layout().addWidget(widget, 1)


class SectionCard(CardFrame):
    """区块卡片 - 带标题的卡片"""

    def __init__(self, title: str = "", parent: QWidget = None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        if title:
            title_label = SubheadingLabel(title)
            layout.addWidget(title_label)

        self._content_layout = QVBoxLayout()
        self._content_layout.setSpacing(8)
        layout.addLayout(self._content_layout)

        layout.addStretch()

    def addWidget(self, widget: QWidget):
        """添加组件到内容区"""
        self._content_layout.addWidget(widget)

    def addLayout(self, layout):
        """添加布局到内容区"""
        self._content_layout.addLayout(layout)
