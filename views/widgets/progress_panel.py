#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Progress Panel Widget
进度面板组件
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QTextEdit, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import List, Tuple

from .styled_widgets import CardFrame, HeadingLabel, SubheadingLabel


class ProgressPanel(CardFrame):
    """进度面板"""

    # 信号
    cancelled = pyqtSignal()
    paused = pyqtSignal()
    resumed = pyqtSignal()

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._steps: List[Tuple[str, bool]] = []  # (step_name, completed)
        self._current_step = 0
        self._is_paused = False
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 标题
        title_label = HeadingLabel("生成进度")
        layout.addWidget(title_label)

        # 总体进度
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(4)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        progress_layout.addWidget(self._progress_bar)

        self._status_label = QLabel("准备中...")
        self._status_label.setStyleSheet("color: #6B6560;")
        progress_layout.addWidget(self._status_label)

        layout.addLayout(progress_layout)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #E8E4E1;")
        layout.addWidget(separator)

        # 步骤列表
        layout.addWidget(QLabel("生成步骤:"))
        self._steps_widget = QWidget()
        self._steps_layout = QVBoxLayout(self._steps_widget)
        self._steps_layout.setContentsMargins(0, 0, 0, 0)
        self._steps_layout.setSpacing(4)
        layout.addWidget(self._steps_widget)

        layout.addStretch()

        # 日志区域
        layout.addWidget(QLabel("详细日志:"))
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setMaximumHeight(150)
        self._log_text.setStyleSheet("""
            QTextEdit {
                background-color: #FAF7F4;
                border: 1px solid #E8E4E1;
                border-radius: 6px;
                padding: 8px;
                font-family: "Consolas", "Microsoft YaHei UI", monospace;
                font-size: 9pt;
            }
        """)
        layout.addWidget(self._log_text)

        # 按钮行
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        self._pause_btn = QPushButton("暂停")
        self._pause_btn.clicked.connect(self._toggle_pause)
        button_layout.addWidget(self._pause_btn)

        self._cancel_btn = QPushButton("取消")
        self._cancel_btn.setProperty("class", "danger")
        self._cancel_btn.clicked.connect(self.cancelled.emit)
        button_layout.addWidget(self._cancel_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

    def setSteps(self, steps: List[str]):
        """设置步骤列表（支持剪映扩展）"""
        self._steps = [(step, False) for step in steps]
        self._current_step = 0

        # 如果是完整生成（5个标准步骤），添加剪映步骤
        if len(steps) == 5:  # 标准的5个步骤
            jianying_steps = [
                "导入视频素材",
                "添加转场效果",
                "AI配音",
                "生成字幕",
                "添加背景音乐",
                "导出成品"
            ]
            for jy_step in jianying_steps:
                self._steps.append((jy_step, False))

        self._update_steps_ui()

    def _update_steps_ui(self):
        """更新步骤UI"""
        # 清除现有步骤
        while self._steps_layout.count():
            item = self._steps_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 添加步骤
        for i, (step_name, completed) in enumerate(self._steps):
            step_widget = QWidget()
            step_layout = QHBoxLayout(step_widget)
            step_layout.setContentsMargins(0, 4, 0, 4)

            # 状态图标
            if i < self._current_step:
                icon = "✅"
                color = "#5B9E5F"
            elif i == self._current_step:
                icon = "⏳"
                color = "#D97757"
            else:
                icon = "⏸️"
                color = "#9A958F"

            icon_label = QLabel(icon)
            icon_label.setFixedWidth(30)
            step_layout.addWidget(icon_label)

            # 步骤名称
            name_label = QLabel(step_name)
            name_label.setStyleSheet(f"color: {color};")
            step_layout.addWidget(name_label)

            step_layout.addStretch()

            self._steps_layout.addWidget(step_widget)

    def setCurrentStep(self, step_index: int, step_name: str = ""):
        """设置当前步骤"""
        self._current_step = step_index
        if step_index < len(self._steps):
            if step_name:
                self._steps[step_index] = (step_name, False)
        self._update_steps_ui()

    def completeStep(self, step_index: int):
        """完成步骤"""
        if 0 <= step_index < len(self._steps):
            name, _ = self._steps[step_index]
            self._steps[step_index] = (name, True)
        self._update_steps_ui()

    def setProgress(self, value: int, message: str = ""):
        """设置进度"""
        self._progress_bar.setValue(value)
        if message:
            self._status_label.setText(message)

    def setStatusMessage(self, message: str):
        """设置状态消息"""
        self._status_label.setText(message)

    def addLog(self, message: str, level: str = "info"):
        """添加日志"""
        color_map = {
            "info": "#2D2926",
            "success": "#5B9E5F",
            "warning": "#D9A545",
            "error": "#D95555",
        }
        color = color_map.get(level, "#2D2926")

        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")

        html = f'<span style="color: #9A958F;">[{timestamp}]</span> <span style="color: {color};">{message}</span>'
        self._log_text.append(html)

    def clearLog(self):
        """清除日志"""
        self._log_text.clear()

    def _toggle_pause(self):
        """切换暂停状态"""
        self._is_paused = not self._is_paused
        if self._is_paused:
            self._pause_btn.setText("继续")
            self.paused.emit()
            self.addLog("生成已暂停", "warning")
        else:
            self._pause_btn.setText("暂停")
            self.resumed.emit()
            self.addLog("生成已继续", "info")

    def setCompleted(self, success: bool, message: str = ""):
        """设置完成状态"""
        if success:
            self.setProgress(100, "完成！")
            self._pause_btn.setEnabled(False)
            self._cancel_btn.setEnabled(False)
            self.addLog(message or "生成完成！", "success")
        else:
            self._status_label.setText(f"失败: {message}")
            self.addLog(f"生成失败: {message}", "error")

    def reset(self):
        """重置面板"""
        self._progress_bar.setValue(0)
        self._status_label.setText("准备中...")
        self._current_step = 0
        self._is_paused = False
        self._pause_btn.setText("暂停")
        self._pause_btn.setEnabled(True)
        self._cancel_btn.setEnabled(True)
        self.clearLog()
        self._steps = []
        self._update_steps_ui()
