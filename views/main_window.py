#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main Window
主窗口
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QPushButton, QLabel, QStatusBar,
    QMessageBox, QFileDialog, QMenu, QComboBox, QFrame,
    QScrollArea, QTextBrowser, QCheckBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings
from PyQt6.QtGui import QAction, QIcon, QCursor
from typing import Optional
from pathlib import Path

import sys

# 添加CLI模块路径
_cli_path = Path(__file__).parent.parent.parent / "video-generator-cli"
if _cli_path.exists():
    sys.path.insert(0, str(_cli_path))

try:
    from api_config import APIConfig
except ImportError:
    APIConfig = None

from viewmodels.project_viewmodel import ProjectViewModel
from viewmodels.api_viewmodel import APIConfigViewModel
from viewmodels.generation_viewmodel import GenerationViewModel

from views.widgets import *
from views.widgets.progress_panel import ProgressPanel
from views.widgets.image_gallery import ImageGalleryWidget
from views.wizards.new_project_wizard import NewProjectWizard
from views.wizards.api_config_dialog import APIConfigDialog


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self._setup_viewmodels()
        self._setup_ui()
        self._connect_signals()
        self._load_settings()

        # ViewModel 初始化时 UI 尚未就绪，此处刷新一次
        self._project_vm.refresh_project_list()

    def _setup_viewmodels(self):
        """设置ViewModels"""
        self._project_vm = ProjectViewModel(self)
        self._api_vm = APIConfigViewModel(self)
        self._generation_vm = GenerationViewModel(self)

    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("Video Generator Pro")
        self.setMinimumSize(1000, 700)

        # 创建中央组件
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 顶部欢迎区
        welcome_widget = self._create_welcome_widget()
        layout.addWidget(welcome_widget)

        # 导航按钮区
        nav_widget = self._create_navigation_widget()
        layout.addWidget(nav_widget)

        # 内容区域
        self._stack = QStackedWidget()
        layout.addWidget(self._stack, 1)

        # 添加页面
        self._add_pages()

        # 状态栏
        self._create_status_bar()

    def _create_welcome_widget(self) -> QWidget:
        """创建欢迎区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 主标题
        title = HeadingLabel("Video Generator Pro")
        layout.addWidget(title)

        # 副标题
        subtitle = QLabel("智能视频生成工具 - 从创意到成品，一键生成专业视频")
        subtitle.setStyleSheet("color: #6B6560; font-size: 11pt;")
        layout.addWidget(subtitle)

        return widget

    def _create_navigation_widget(self) -> QWidget:
        """创建导航区域"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 导航按钮
        buttons = [
            ("📋", "新建项目", "new_project"),
            ("📂", "项目列表", "project_list"),
            ("⚙️", "API配置", "api_config"),
            ("🎬", "视频生成", "generation"),
            ("📖", "帮助", "help"),
        ]

        for icon, text, page_id in buttons:
            btn = QPushButton(f"{icon} {text}")
            btn.setProperty("nav_id", page_id)
            btn.setMinimumHeight(50)
            btn.setMinimumWidth(120)
            btn.clicked.connect(lambda checked, pid=page_id: self._navigate_to(pid))
            layout.addWidget(btn)

        layout.addStretch()

        return widget

    def _add_pages(self):
        """添加页面"""
        # 欢迎页（空页面）
        welcome_page = QWidget()
        welcome_layout = QVBoxLayout(welcome_page)
        welcome_layout.addStretch()

        welcome_label = QLabel("请选择上方功能开始使用")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_label.setStyleSheet("color: #9A958F; font-size: 14pt;")
        welcome_layout.addWidget(welcome_label)

        welcome_layout.addStretch()
        self._stack.addWidget(welcome_page)
        self._welcome_page_idx = self._stack.count() - 1

        # 项目列表页
        self._project_list_page = self._create_project_list_page()
        self._stack.addWidget(self._project_list_page)
        self._project_list_page_idx = self._stack.count() - 1

        # API配置页
        self._api_config_page = self._create_api_config_page()
        self._stack.addWidget(self._api_config_page)
        self._api_config_page_idx = self._stack.count() - 1

        # 视频生成页
        self._generation_page = self._create_generation_page()
        self._stack.addWidget(self._generation_page)
        self._generation_page_idx = self._stack.count() - 1

        # 帮助页
        help_page = self._create_help_page()
        self._stack.addWidget(help_page)
        self._help_page_idx = self._stack.count() - 1

    def _create_project_list_page(self) -> QWidget:
        """创建项目列表页"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标题行
        title_layout = QHBoxLayout()
        title_layout.addWidget(HeadingLabel("我的项目"))

        title_layout.addStretch()

        new_btn = PrimaryButton("新建项目")
        new_btn.clicked.connect(self._new_project)
        title_layout.addWidget(new_btn)

        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self._refresh_projects)
        title_layout.addWidget(refresh_btn)

        layout.addLayout(title_layout)

        # 项目列表（滚动区域）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._project_list_widget = QWidget()
        self._project_list_layout = QVBoxLayout(self._project_list_widget)
        self._project_list_layout.setSpacing(12)
        self._project_list_layout.addStretch()

        scroll.setWidget(self._project_list_widget)
        layout.addWidget(scroll, 1)

        return page

    def _create_api_config_page(self) -> QWidget:
        """创建API配置页"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标题行
        title_layout = QHBoxLayout()
        title_layout.addWidget(HeadingLabel("API配置"))

        title_layout.addStretch()

        add_btn = PrimaryButton("添加提供商")
        add_btn.clicked.connect(self._add_provider)
        title_layout.addWidget(add_btn)

        layout.addLayout(title_layout)

        # 提示信息
        hint = HintLabel("配置您的API密钥以使用视频生成功能。配置将保存在本地，不会上传到任何服务器。")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        return page

    def _create_generation_page(self) -> QWidget:
        """创建视频生成页"""
        page = QWidget()
        outer_layout = QVBoxLayout(page)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 标题行
        title_layout = QHBoxLayout()
        title_layout.addWidget(HeadingLabel("视频生成"))
        layout.addLayout(title_layout)

        # 主内容区域 - 使用水平布局分为左右两部分
        main_content = QHBoxLayout()
        main_content.setSpacing(12)

        # 左侧：配置和控制区域
        config_panel = CardFrame()
        config_layout = QVBoxLayout(config_panel)
        config_layout.setContentsMargins(16, 16, 16, 16)
        config_layout.setSpacing(12)

        config_layout.addWidget(SubheadingLabel("生成配置"))

        # 项目选择
        self._project_combo = QComboBox()
        self._project_combo.setMinimumWidth(200)
        row = FormRow("选择项目:", self._project_combo)
        config_layout.addWidget(row)

        # 生成选项
        options_layout = QVBoxLayout()
        options_layout.setSpacing(8)

        self._continue_mode_cb = QCheckBox("继续模式（跳过已生成）")
        self._continue_mode_cb.setChecked(True)
        options_layout.addWidget(self._continue_mode_cb)

        self._force_mode_cb = QCheckBox("强制模式（覆盖已有文件）")
        options_layout.addWidget(self._force_mode_cb)

        config_layout.addLayout(options_layout)

        # 生成步骤选择
        step_layout = QVBoxLayout()
        step_layout.setSpacing(4)
        step_layout.addWidget(QLabel("生成步骤:"))

        self._step_combo = QComboBox()
        self._step_combo.addItems([
            "全部生成（参考图+视频+合并）",
            "仅生成参考图",
            "仅生成视频",
            "仅合并视频",
            "导出剪映指令",
            "剪映自动化"
        ])
        step_layout.addWidget(self._step_combo)
        config_layout.addLayout(step_layout)

        config_layout.addStretch()

        # 开始生成按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # 添加测试API按钮
        self._test_api_btn = QPushButton("🔍 测试API")
        self._test_api_btn.clicked.connect(self._test_api_connection)
        button_layout.addWidget(self._test_api_btn)

        self._start_generate_btn = PrimaryButton("开始生成")
        self._start_generate_btn.clicked.connect(self._start_generation)
        button_layout.addWidget(self._start_generate_btn)

        config_layout.addLayout(button_layout)

        main_content.addWidget(config_panel, 1)

        # 右侧：进度面板
        self._progress_panel = ProgressPanel()
        self._progress_panel.setVisible(False)  # 初始隐藏
        main_content.addWidget(self._progress_panel, 2)

        layout.addLayout(main_content, 1)

        # 参考图预览画廊
        self._image_gallery = ImageGalleryWidget()
        self._image_gallery.setVisible(False)
        layout.addWidget(self._image_gallery)

        scroll.setWidget(container)
        outer_layout.addWidget(scroll)
        return page

    def _create_help_page(self) -> QWidget:
        """创建帮助页"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        title = HeadingLabel("帮助与文档")
        layout.addWidget(title)

        browser = QTextBrowser()
        browser.setHtml("""
        <h2>Video Generator Pro 使用指南</h2>

        <h3>快速开始</h3>
        <ol>
            <li>配置API密钥：点击"API配置"，添加您的API提供商</li>
            <li>创建项目：点击"新建项目"，按照向导填写项目信息</li>
            <li>生成视频：点击"视频生成"，选择项目并开始生成</li>
        </ol>

        <h3>功能说明</h3>
        <ul>
            <li><b>新建项目</b>：创建新的视频项目，配置角色、场景、视频风格等</li>
            <li><b>项目列表</b>：查看和管理所有已创建的项目</li>
            <li><b>API配置</b>：管理API密钥和提供商设置</li>
            <li><b>视频生成</b>：启动视频生成任务并查看进度</li>
        </ul>

        <h3>常见问题</h3>
        <p><b>Q: 支持哪些API提供商？</b><br>
        A: 目前支持并行科技、OpenAI，以及自定义兼容OpenAI API的提供商。</p>

        <p><b>Q: 生成的视频保存在哪里？</b><br>
        A: 视频保存在项目目录的output文件夹中。</p>

        <h3>技术支持</h3>
        <p>如遇问题，请联系技术支持或查看项目文档。</p>
        """)
        layout.addWidget(browser, 1)

        return page

    def _create_status_bar(self):
        """创建状态栏"""
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)

        # API状态指示器（可点击）
        self._api_status_label = QLabel()
        self._api_status_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._update_api_status()
        self._status_bar.addPermanentWidget(self._api_status_label)

    def _update_api_status(self):
        """更新API状态显示（增强版）"""
        if self._api_vm.isConfigured():
            provider = self._api_vm.currentProvider
            self._api_status_label.setText(f"✅ API: {provider}")
            self._api_status_label.setStyleSheet(
                "color: #5B9E5F; "
                "padding: 2px 8px; "
                "border-radius: 4px;"
            )
            # 已配置时不处理点击
            self._api_status_label.mousePressEvent = lambda e: None
        else:
            self._api_status_label.setText("⚠️ API未配置 - 点击配置")
            self._api_status_label.setStyleSheet(
                "color: #D9A545; "
                "padding: 2px 8px; "
                "border-radius: 4px; "
                "background-color: #FEF7E0;"
            )
            # 添加点击事件
            self._api_status_label.mousePressEvent = self._on_api_status_clicked

    def _on_api_status_clicked(self, event):
        """点击API状态跳转到配置页"""
        self._navigate_to("api_config")

    def _connect_signals(self):
        """连接信号"""
        self._project_vm.projectListChanged.connect(self._on_project_list_changed)
        self._project_vm.errorOccurred.connect(self._on_error)
        self._project_vm.successOccurred.connect(self._on_success)

        self._api_vm.configChanged.connect(self._on_api_config_changed)
        self._api_vm.errorOccurred.connect(self._on_error)
        self._api_vm.successOccurred.connect(self._on_success)

        # 连接生成ViewModel信号到进度面板
        self._generation_vm.progressChanged.connect(self._on_progress_changed)
        self._generation_vm.sceneProgressChanged.connect(self._on_scene_progress_changed)
        self._generation_vm.generationCompleted.connect(self._on_generation_completed)
        self._generation_vm.referenceImageGenerated.connect(self._on_reference_image_generated)
        self._generation_vm.videoGenerated.connect(self._on_video_generated)

        # 连接进度面板信号
        self._progress_panel.cancelled.connect(self._cancel_generation)
        self._progress_panel.paused.connect(self._pause_generation)
        self._progress_panel.resumed.connect(self._resume_generation)

    def _navigate_to(self, page_id: str):
        """导航到指定页面"""
        page_map = {
            "new_project": (self._project_list_page_idx, self._new_project),
            "project_list": self._project_list_page_idx,
            "api_config": self._api_config_page_idx,
            "generation": (self._generation_page_idx, self._refresh_generation_page),
            "help": self._help_page_idx,
        }

        if page_id in page_map:
            page_idx = page_map[page_id]
            if isinstance(page_idx, tuple):
                page_idx, callback = page_idx
                if callback:
                    callback()
            self._stack.setCurrentIndex(page_idx)

    # ===== 项目操作 =====

    def _new_project(self):
        """新建项目"""
        wizard = NewProjectWizard(self._project_vm, self)
        if wizard.exec() == NewProjectWizard.DialogCode.Accepted:
            project_data = wizard.getProjectData()
            if self._project_vm.create_project(project_data):
                self._navigate_to("project_list")

    def _refresh_projects(self):
        """刷新项目列表"""
        self._project_vm.refresh_project_list()

    def _on_project_list_changed(self):
        """项目列表变化"""
        # 清除现有项目卡片
        while self._project_list_layout.count():
            item = self._project_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 添加项目卡片
        for project in self._project_vm.get_projects():
            card = ProjectCard(project)
            card.clicked.connect(self._open_project)
            card.deleted.connect(self._delete_project)
            card.edited.connect(self._edit_project)
            self._project_list_layout.insertWidget(
                self._project_list_layout.count() - 1, card
            )

        # 更新项目下拉框
        if hasattr(self, '_project_combo'):
            current = self._project_combo.currentText()
            self._project_combo.clear()
            for project in self._project_vm.get_projects():
                self._project_combo.addItem(project['name'])
            # 恢复之前的选择
            index = self._project_combo.findText(current)
            if index >= 0:
                self._project_combo.setCurrentIndex(index)

    def _open_project(self, project_name: str):
        """打开项目"""
        self._project_vm.setCurrentProject(project_name)
        # 同步 combo box 选择到当前项目
        index = self._project_combo.findText(project_name)
        if index >= 0:
            self._project_combo.setCurrentIndex(index)
        self._navigate_to("generation")

    def _delete_project(self, project_name: str):
        """删除项目"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除项目 '{project_name}' 吗？\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._project_vm.delete_project(project_name)

    def _edit_project(self, project_name: str):
        """编辑项目"""
        # TODO: 实现编辑功能
        QMessageBox.information(self, "提示", "编辑功能即将推出")

    # ===== API配置操作 =====

    def _add_provider(self):
        """添加提供商"""
        dialog = APIConfigDialog(self._api_vm, self)
        dialog.exec()

    def _on_api_config_changed(self):
        """API配置变化"""
        self._update_api_status()

    # ===== 生成操作 =====

    def _refresh_generation_page(self):
        """刷新视频生成页面的项目列表"""
        # 保存当前选择
        current = self._project_combo.currentText()

        # 清空并重新加载项目
        self._project_combo.clear()
        projects = self._project_vm.get_projects()
        for project in projects:
            self._project_combo.addItem(project['name'])

        # 恢复之前的选择（如果还存在）
        index = self._project_combo.findText(current)
        if index >= 0:
            self._project_combo.setCurrentIndex(index)
        elif projects:
            self._project_combo.setCurrentIndex(0)

    def _start_generation(self):
        """开始视频生成"""
        project_name = self._project_combo.currentText()
        if not project_name:
            QMessageBox.warning(self, "警告", "请先选择项目")
            return

        # 验证项目
        valid, error = self._generation_vm.validateProject(project_name)
        if not valid:
            QMessageBox.warning(self, "警告", error)
            return

        # 验证API
        valid, error = self._generation_vm.validateAPI()
        if not valid:
            reply = QMessageBox.question(
                self,
                "API未配置",
                f"{error}\n是否前往配置API？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._navigate_to("api_config")
            return

        # 设置生成选项
        step_index = self._step_combo.currentIndex()
        self._generation_vm.setGenerationStep(step_index)
        self._generation_vm.setContinueMode(self._continue_mode_cb.isChecked())
        self._generation_vm.setForceMode(self._force_mode_cb.isChecked())

        # 显示并重置进度面板
        self._progress_panel.setVisible(True)
        self._progress_panel.reset()
        self._progress_panel.setSteps([
            "准备生成配置",
            "生成参考图",
            "生成视频片段",
            "合并视频",
            "完成"
        ])
        self._progress_panel.addLog(f"开始生成任务: {project_name}", "info")

        # 重置参考图画廊
        self._image_gallery.clearImages()
        self._image_gallery.setVisible(True)

        # 禁用开始按钮
        self._start_generate_btn.setEnabled(False)

        # 启动生成
        self._generation_vm.startGeneration(project_name)

    def _test_api_connection(self):
        """测试API连接"""
        from api_client import OpenAIClient

        try:
            if APIConfig is None:
                QMessageBox.warning(self, "配置错误", "CLI模块未加载")
                return

            api_config = APIConfig()
            api_key = api_config.get_api_key()
            base_url = api_config.get_base_url()

            if not api_key or not base_url:
                QMessageBox.warning(self, "配置错误", "请先配置API密钥")
                return

            # 显示测试中提示
            test_btn = self._test_api_btn
            original_text = test_btn.text()
            test_btn.setText("测试中...")
            test_btn.setEnabled(False)
            QApplication.processEvents()

            client = OpenAIClient(api_key=api_key, base_url=base_url)

            # 测试连接
            success, message = client.test_connection()
            if not success:
                QMessageBox.critical(self, "连接失败", f"API连接失败:\n{message}")
                test_btn.setText(original_text)
                test_btn.setEnabled(True)
                return

            # 测试图片生成
            success, msg, result = client.test_image_generation("测试图片")
            if success:
                img_result = "✅ 图片生成: 通过"
            else:
                img_result = f"❌ 图片生成: 失败\n{msg}"

            # 测试视频生成
            success, msg, result = client.test_video_generation("测试视频")
            if success:
                video_result = "✅ 视频生成: 通过"
            else:
                video_result = f"❌ 视频生成: 失败\n{msg}"

            # 恢复按钮
            test_btn.setText(original_text)
            test_btn.setEnabled(True)

            # 显示结果
            all_pass = "✅" in img_result and "✅" in video_result
            if all_pass:
                QMessageBox.information(
                    self,
                    "API测试结果",
                    "✅ 全部测试通过\n\n连接测试: 通过\n图片生成: 通过\n视频生成: 通过"
                )
            else:
                QMessageBox.warning(
                    self,
                    "API测试结果",
                    f"连接测试: ✅ 通过\n\n{img_result}\n\n{video_result}"
                )

        except Exception as e:
            self._test_api_btn.setText(original_text)
            self._test_api_btn.setEnabled(True)
            QMessageBox.critical(self, "测试失败", f"测试过程中发生错误:\n{str(e)}")

    def _cancel_generation(self):
        """取消生成"""
        self._generation_vm.cancelGeneration()
        self._progress_panel.addLog("生成已取消", "warning")
        self._progress_panel.setCompleted(False, "用户取消")
        self._start_generate_btn.setEnabled(True)

    def _pause_generation(self):
        """暂停生成"""
        self._progress_panel.addLog("生成暂停", "warning")
        # TODO: 实现暂停逻辑

    def _resume_generation(self):
        """继续生成"""
        self._progress_panel.addLog("生成继续", "info")
        # TODO: 实现继续逻辑

    def _on_progress_changed(self, progress: int, message: str):
        """进度变化"""
        self._progress_panel.setProgress(progress, message)
        if message:
            self._progress_panel.addLog(message, "info")

    def _on_scene_progress_changed(self, current: int, total: int, message: str):
        """场景进度变化"""
        step_msg = f"{message} ({current}/{total})" if message else f"步骤 {current}/{total}"
        self._progress_panel.setStatusMessage(step_msg)

        # 更新步骤显示 (最多5个步骤)
        step_index = min(current - 1, 4)
        self._progress_panel.setCurrentStep(step_index)

        # 完成之前的步骤
        for i in range(step_index):
            self._progress_panel.completeStep(i)

        # 添加日志
        if message:
            self._progress_panel.addLog(message, "info")

    def _on_generation_completed(self, success: bool, message: str):
        """生成完成"""
        self._progress_panel.setCompleted(success, message)
        self._start_generate_btn.setEnabled(True)

        if success:
            QMessageBox.information(self, "完成", f"视频生成完成！\n\n{message}")
        else:
            QMessageBox.warning(self, "失败", f"视频生成失败\n\n{message}")

    def _on_reference_image_generated(self, scene_id: str, image_path: str):
        """参考图生成完成"""
        self._image_gallery.setVisible(True)
        self._image_gallery.addImage(image_path, f"场景 {scene_id}")

    def _on_video_generated(self, scene_id: str, video_path: str):
        """视频生成完成"""
        self._image_gallery.setVisible(True)
        self._image_gallery.addVideo(video_path, f"场景 {scene_id}")

    # ===== 通用处理 =====

    def _on_error(self, message: str):
        """处理错误"""
        QMessageBox.critical(self, "错误", message)

    def _on_success(self, message: str):
        """处理成功"""
        QMessageBox.information(self, "成功", message)

    def _load_settings(self):
        """加载设置"""
        settings = QSettings("VideoGenerator", "VideoGeneratorPro")

        # 恢复窗口大小和位置
        size = settings.value("window_size")
        if size:
            self.resize(size)

        position = settings.value("window_position")
        if position:
            self.move(position)

    def closeEvent(self, event):
        """关闭事件"""
        # 保存设置
        settings = QSettings("VideoGenerator", "VideoGeneratorPro")
        settings.setValue("window_size", self.size())
        settings.setValue("window_position", self.pos())

        event.accept()
