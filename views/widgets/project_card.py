#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project Card Widget
项目卡片组件
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from typing import Dict, Any, Optional
from pathlib import Path

from .styled_widgets import CardFrame, HeadingLabel, SubheadingLabel, HintLabel, PrimaryButton


class ProjectCard(CardFrame):
    """项目卡片"""

    # 信号
    clicked = pyqtSignal(str)  # project_name
    deleted = pyqtSignal(str)  # project_name
    edited = pyqtSignal(str)   # project_name

    def __init__(self, project_info: Dict[str, Any], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._project_info = project_info
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # 项目名称
        name_label = HeadingLabel(self._project_info.get("name", "未命名项目"))
        layout.addWidget(name_label)

        # 项目描述
        description = self._project_info.get("description", "")
        if description:
            desc_label = HintLabel(description[:60] + "..." if len(description) > 60 else description)
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        # 信息行
        info_layout = QHBoxLayout()
        info_layout.setSpacing(16)

        # 场景数量
        scene_count = self._project_info.get("scene_count", 0)
        scene_label = QLabel(f"📹 {scene_count} 个场景")
        scene_label.setStyleSheet("color: #6B6560;")
        info_layout.addWidget(scene_label)

        # 视频风格
        style = self._project_info.get("video_style", "")
        if style:
            style_label = QLabel(f"🎬 {style}")
            style_label.setStyleSheet("color: #6B6560;")
            info_layout.addWidget(style_label)

        info_layout.addStretch()
        layout.addLayout(info_layout)

        # 创建时间
        created_at = self._project_info.get("created_at", "")
        if created_at:
            date_label = HintLabel(self._format_date(created_at))
            layout.addWidget(date_label)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #E8E4E1;")
        layout.addWidget(separator)

        # 按钮行
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        open_btn = QPushButton("打开项目")
        open_btn.setProperty("class", "primary")
        open_btn.clicked.connect(lambda: self.clicked.emit(self._project_info["name"]))
        button_layout.addWidget(open_btn)

        edit_btn = QPushButton("编辑")
        edit_btn.clicked.connect(lambda: self.edited.emit(self._project_info["name"]))
        button_layout.addWidget(edit_btn)

        delete_btn = QPushButton("删除")
        delete_btn.setProperty("class", "danger")
        delete_btn.clicked.connect(lambda: self._confirm_delete())
        button_layout.addWidget(delete_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # 设置鼠标样式
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _format_date(self, date_str: str) -> str:
        """格式化日期"""
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(date_str)
            return dt.strftime("%Y年%m月%d日")
        except:
            return date_str

    def _confirm_delete(self):
        """确认删除"""
        from PyQt6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除项目 '{self._project_info['name']}' 吗？\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.deleted.emit(self._project_info["name"])

    def updateInfo(self, project_info: Dict[str, Any]):
        """更新项目信息"""
        self._project_info = project_info
        # 重建UI
        layout = self.layout()
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._setup_ui()
