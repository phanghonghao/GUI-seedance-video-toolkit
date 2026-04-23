#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
New Project Wizard
新建项目向导
"""

from PyQt6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
    QLineEdit, QTextEdit, QComboBox, QSpinBox,
    QCheckBox, QLabel, QGroupBox, QScrollArea,
    QWidget, QPushButton, QProgressBar, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys

from viewmodels.project_viewmodel import ProjectViewModel
from views.widgets.styled_widgets import (
    FormRow, SectionCard, HeadingLabel, SubheadingLabel, HintLabel
)
from views.widgets.llm_scene_worker import LLMSceneWorker

# 添加CLI模块路径用于APIConfig
_cli_path = Path(__file__).parent.parent.parent / "video-generator-cli"
if _cli_path.exists():
    sys.path.insert(0, str(_cli_path))

try:
    from api_config import APIConfig
    API_CONFIG_AVAILABLE = True
except ImportError:
    API_CONFIG_AVAILABLE = False

APPEARANCE_PRESETS = [
    "短发，穿着蓝色运动服",
    "短发，穿着白色衬衫和黑色西裤",
    "长发，穿着白色衬衫",
    "长发，穿着浅色连衣裙",
    "短发，穿着休闲T恤和牛仔裤",
    "扎马尾，穿着校服",
    "短发，穿着格子衬衫",
    "长发，穿着黑色职业装",
    "短发，穿着黑色连帽衫",
    "中长发，穿着浅色毛衣",
    "自定义",
]

PERSONALITY_PRESETS = [
    "开朗、活泼",
    "沉稳、专业",
    "温和、友善",
    "热情、有活力",
    "严肃、认真",
    "幽默、风趣",
    "温柔、体贴",
    "冷静、理性",
    "自信、果断",
    "腼腆、内向",
    "自定义",
]


class NewProjectWizard(QWizard):
    """新建项目向导"""

    def __init__(self, project_vm: ProjectViewModel, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._project_vm = project_vm
        self._project_data: Dict[str, Any] = {}
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("新建项目")
        self.setMinimumSize(700, 600)
        # 使用ClassicStyle以显示Back和Next按钮
        self.setWizardStyle(QWizard.WizardStyle.ClassicStyle)

        # 添加页面
        self._add_pages()

    def _add_pages(self):
        """添加向导页面"""
        # 1. 基本信息
        basic_page = BasicInfoPage(self)
        self.addPage(basic_page)

        # 2. 角色设定
        character_page = CharacterPage(self)
        self.addPage(character_page)

        # 3. 视频设置
        video_page = VideoSettingsPage(self)
        self.addPage(video_page)

        # 4. 场景规划
        scene_page = ScenePage(self)
        self.addPage(scene_page)

        # 5. Prompt预览与编辑（仅在智能模式时显示）
        preview_page = PromptPreviewPage(self)
        self.addPage(preview_page)

    def getProjectData(self) -> Dict[str, Any]:
        """获取项目数据"""
        return self._project_data.copy()

    def setProjectData(self, data: Dict[str, Any]):
        """设置项目数据"""
        self._project_data = data.copy()


class BasicInfoPage(QWizardPage):
    """基本信息页"""

    def __init__(self, wizard: NewProjectWizard):
        super().__init__(wizard)
        self._wizard = wizard
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self.setTitle("项目基本信息")
        self.setSubTitle("请填写项目的基本信息")

        container = QWidget()
        layout = QVBoxLayout(container)

        # 项目名称
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("例如: 智能手表产品介绍")
        self._name_edit.textChanged.connect(self._check_fields)

        name_row = FormRow("项目名称:", self._name_edit)
        layout.addWidget(name_row)

        # 项目描述
        self._desc_edit = QTextEdit()
        self._desc_edit.setPlaceholderText(
            "描述视频的主要内容、目标和受众。\n"
            "例如: 介绍智能手表的健康监测、运动追踪、消息通知等功能，"
            "适合想要了解智能手表的潜在用户。"
        )
        self._desc_edit.setMaximumHeight(100)
        self._desc_edit.textChanged.connect(self._check_fields)

        layout.addWidget(QLabel("项目描述:"))
        layout.addWidget(self._desc_edit)

        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(container)
        page_layout = QVBoxLayout(self)
        page_layout.addWidget(scroll)

    def _check_fields(self):
        """检查字段并更新完成按钮"""
        name = self._name_edit.text().strip()
        desc = self._desc_edit.toPlainText().strip()

        # 注册字段以便向导可以访问
        self.setField("project_name", name)
        self.setField("project_description", desc)

    def validatePage(self) -> bool:
        """验证页面"""
        name = self._name_edit.text().strip()
        if not name:
            return False

        desc = self._desc_edit.toPlainText().strip()
        if not desc:
            return False

        # 检查项目名是否已存在
        if self._wizard._project_vm:
            existing = self._wizard._project_vm.get_project(name)
            if existing:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "警告", f"项目 '{name}' 已存在，请使用其他名称")
                return False

        # 保存数据
        self._wizard._project_data["project_name"] = name
        self._wizard._project_data["project_description"] = desc

        return True


class CharacterPage(QWizardPage):
    """角色设定页"""

    def __init__(self, wizard: NewProjectWizard):
        super().__init__(wizard)
        self._wizard = wizard
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self.setTitle("角色设定")
        self.setSubTitle("设置视频中的主要角色（可选）")

        container = QWidget()
        layout = QVBoxLayout(container)

        # 是否有主要角色
        self._has_character_cb = QCheckBox("视频中有主要角色")
        self._has_character_cb.setChecked(True)
        self._has_character_cb.toggled.connect(self._on_character_toggled)
        layout.addWidget(self._has_character_cb)

        # 角色设置组
        self._character_group = QGroupBox("角色详情")
        character_layout = QVBoxLayout(self._character_group)

        # 年龄
        self._age_combo = QComboBox()
        self._age_combo.addItems(["儿童", "青年", "中年", "老年"])
        self._age_combo.setCurrentIndex(1)  # 默认青年

        age_row = FormRow("年龄段:", self._age_combo)
        character_layout.addWidget(age_row)

        # 性别
        self._gender_combo = QComboBox()
        self._gender_combo.addItems(["男", "女", "不限"])

        gender_row = FormRow("性别:", self._gender_combo)
        character_layout.addWidget(gender_row)

        # 外貌
        self._appearance_combo = QComboBox()
        self._appearance_combo.addItems(APPEARANCE_PRESETS)
        self._appearance_combo.currentTextChanged.connect(self._on_appearance_changed)

        appearance_row = FormRow("外貌特征:", self._appearance_combo)
        character_layout.addWidget(appearance_row)

        self._appearance_custom = QLineEdit()
        self._appearance_custom.setPlaceholderText("请输入自定义外貌特征...")
        self._appearance_custom.setVisible(False)
        character_layout.addWidget(self._appearance_custom)

        # 性格
        self._personality_combo = QComboBox()
        self._personality_combo.addItems(PERSONALITY_PRESETS)
        self._personality_combo.currentTextChanged.connect(self._on_personality_changed)

        personality_row = FormRow("性格特点:", self._personality_combo)
        character_layout.addWidget(personality_row)

        self._personality_custom = QLineEdit()
        self._personality_custom.setPlaceholderText("请输入自定义性格特点...")
        self._personality_custom.setVisible(False)
        character_layout.addWidget(self._personality_custom)

        layout.addWidget(self._character_group)

        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(container)
        page_layout = QVBoxLayout(self)
        page_layout.addWidget(scroll)

    def _on_character_toggled(self, checked: bool):
        """角色复选框变化"""
        self._character_group.setEnabled(checked)

    def _on_appearance_changed(self, text: str):
        """外貌选择变化"""
        is_custom = text == "自定义"
        self._appearance_custom.setVisible(is_custom)
        if is_custom:
            self._appearance_custom.setFocus()

    def _on_personality_changed(self, text: str):
        """性格选择变化"""
        is_custom = text == "自定义"
        self._personality_custom.setVisible(is_custom)
        if is_custom:
            self._personality_custom.setFocus()

    def initializePage(self) -> None:
        """初始化页面"""
        super().initializePage()

    def validatePage(self) -> bool:
        """验证页面"""
        has_character = self._has_character_cb.isChecked()

        # 获取外貌值
        if has_character:
            if self._appearance_combo.currentText() == "自定义":
                appearance = self._appearance_custom.text().strip()
            else:
                appearance = self._appearance_combo.currentText()

            if self._personality_combo.currentText() == "自定义":
                personality = self._personality_custom.text().strip()
            else:
                personality = self._personality_combo.currentText()
        else:
            appearance = ""
            personality = ""

        self._wizard._project_data["has_main_character"] = has_character
        self._wizard._project_data["character"] = {
            "age": self._age_combo.currentText() if has_character else "",
            "gender": self._gender_combo.currentText() if has_character else "",
            "appearance": appearance,
            "personality": personality,
        }

        return True


class VideoSettingsPage(QWizardPage):
    """视频设置页"""

    def __init__(self, wizard: NewProjectWizard):
        super().__init__(wizard)
        self._wizard = wizard
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self.setTitle("视频设置")
        self.setSubTitle("设置视频的风格和质量参数")

        container = QWidget()
        layout = QVBoxLayout(container)

        # 视频风格
        self._style_combo = QComboBox()
        self._style_combo.addItems(["写实风格", "动画风格", "信息图表", "产品展示", "蒙太奇"])

        style_row = FormRow("视频风格:", self._style_combo)
        layout.addWidget(style_row)

        # 视频比例
        self._ratio_combo = QComboBox()
        self._ratio_combo.addItems(["16:9", "9:16", "1:1", "4:3"])

        ratio_row = FormRow("视频比例:", self._ratio_combo)
        layout.addWidget(ratio_row)

        # 视频质量
        self._quality_combo = QComboBox()
        self._quality_combo.addItems(["720P", "1080P", "4K"])
        self._quality_combo.setCurrentIndex(1)  # 默认1080P

        quality_row = FormRow("视频质量:", self._quality_combo)
        layout.addWidget(quality_row)

        # 目标时长
        self._duration_spin = QSpinBox()
        self._duration_spin.setRange(1, 30)
        self._duration_spin.setValue(3)
        self._duration_spin.setSuffix(" 分钟")

        duration_row = FormRow("目标时长:", self._duration_spin)
        layout.addWidget(duration_row)

        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(container)
        page_layout = QVBoxLayout(self)
        page_layout.addWidget(scroll)

    def validatePage(self) -> bool:
        """验证页面"""
        self._wizard._project_data["video"] = {
            "style": self._style_combo.currentText(),
            "aspect_ratio": self._ratio_combo.currentText(),
            "quality": self._quality_combo.currentText(),
            "target_duration": self._duration_spin.value(),
        }

        return True


class ScenePage(QWizardPage):
    """场景规划页"""

    def __init__(self, wizard: NewProjectWizard):
        super().__init__(wizard)
        self._wizard = wizard
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self.setTitle("场景规划")
        self.setSubTitle("规划视频的场景内容")

        layout = QVBoxLayout(self)

        # 场景数量
        self._scene_count_spin = QSpinBox()
        self._scene_count_spin.setRange(1, 50)
        self._scene_count_spin.setValue(5)
        self._scene_count_spin.valueChanged.connect(self._on_count_changed)

        count_row = FormRow("场景数量:", self._scene_count_spin)
        layout.addWidget(count_row)

        # 生成方式
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("场景生成方式:"))

        self._manual_mode_rb = QCheckBox("手动输入")
        self._manual_mode_rb.toggled.connect(self._on_mode_changed)
        mode_layout.addWidget(self._manual_mode_rb)

        self._smart_mode_rb = QCheckBox("智能推荐")
        self._smart_mode_rb.setChecked(True)
        self._smart_mode_rb.toggled.connect(self._on_mode_changed)
        mode_layout.addWidget(self._smart_mode_rb)

        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        # 场景列表
        layout.addWidget(QLabel("场景描述:"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(250)

        self._scenes_widget = QWidget()
        self._scenes_layout = QVBoxLayout(self._scenes_widget)
        self._scenes_layout.setContentsMargins(0, 0, 0, 0)
        self._scenes_layout.setSpacing(8)

        scroll.setWidget(self._scenes_widget)
        layout.addWidget(scroll, 1)

        # 添加场景按钮
        add_btn_layout = QHBoxLayout()
        add_btn_layout.addStretch()

        from PyQt6.QtWidgets import QPushButton
        add_btn = QPushButton("+ 添加场景")
        add_btn.clicked.connect(self._add_scene)
        add_btn_layout.addWidget(add_btn)

        layout.addLayout(add_btn_layout)

        # 初始化场景
        self._on_count_changed()

    def _on_count_changed(self):
        """场景数量变化"""
        target_count = self._scene_count_spin.value()
        current_count = self._scenes_layout.count()

        if target_count > current_count:
            # 添加场景
            for i in range(current_count, target_count):
                self._add_scene_edit(i)
        elif target_count < current_count:
            # 移除场景
            for i in range(current_count - 1, target_count - 1, -1):
                item = self._scenes_layout.takeAt(i)
                if item.widget():
                    item.widget().deleteLater()

    def _add_scene_edit(self, index: int):
        """添加场景编辑框"""
        edit = QLineEdit()
        edit.setPlaceholderText(f"场景{index + 1}描述...")
        self._scenes_layout.addWidget(QLabel(f"场景{index + 1}:"))
        self._scenes_layout.addWidget(edit)

    def _on_mode_changed(self):
        """生成模式变化"""
        # 手动输入模式
        is_manual = self._manual_mode_rb.isChecked()

        for i in range(self._scenes_layout.count()):
            item = self._scenes_layout.itemAt(i)
            if item and item.widget():
                item.widget().setEnabled(is_manual)

    def nextId(self) -> int:
        """控制向导跳转：手动模式跳过PreviewPage，智能模式进入PreviewPage"""
        if self._manual_mode_rb.isChecked():
            # 手动模式 → 跳过PreviewPage，直接完成
            return -1
        else:
            # 智能模式 → 进入 PromptPreviewPage (默认下一页)
            return super().nextId()

    def _add_scene(self):
        """添加额外场景"""
        index = self._scenes_layout.count() // 2
        self._scene_count_spin.setValue(self._scene_count_spin.value() + 1)
        self._add_scene_edit(index)

    def validatePage(self) -> bool:
        """验证页面"""
        is_manual = self._manual_mode_rb.isChecked()
        is_smart = self._smart_mode_rb.isChecked()

        # 设置生成模式标记，供下一页使用
        if is_smart and not is_manual:
            self.setField("generation_mode", "smart")
            # 智能模式：不在此处生成场景，由下一页 PromptPreviewPage 处理
            self._wizard._project_data["generation_mode"] = "smart"
            self._wizard._project_data["scene_count"] = self._scene_count_spin.value()
            return True

        # 手动模式：收集场景
        self.setField("generation_mode", "manual")
        self._wizard._project_data["generation_mode"] = "manual"
        scenes = []

        for i in range(0, self._scenes_layout.count(), 2):
            label_item = self._scenes_layout.itemAt(i)
            edit_item = self._scenes_layout.itemAt(i + 1)

            if edit_item and edit_item.widget():
                text = edit_item.widget().text().strip()
                if text:
                    scenes.append({
                        "id": len(scenes) + 1,
                        "description": text,
                        "duration": 5,
                    })

        self._wizard._project_data["scenes"] = scenes

        return len(scenes) > 0

    def _generate_smart_scenes(self) -> List[Dict[str, Any]]:
        """生成智能场景"""
        description = self._wizard._project_data.get("project_description", "")
        count = self._scene_count_spin.value()

        # 简单的关键词匹配
        scenes = []

        if "产品" in description or "功能" in description:
            templates = [
                "开场：展示用户面临的痛点或问题",
                f"产品登场：展示产品外观和特征",
                "功能演示1：展示核心功能的使用",
                "功能演示2：展示其他实用功能",
                "用户反馈：展示使用后的满意效果",
                "应用场景：展示在不同场景下的使用",
                "总结：强调产品的优势和购买方式",
            ]
        elif "教程" in description or "教学" in description:
            templates = [
                "开场介绍：说明将要学习的内容",
                "准备工作：展示所需的工具或材料",
                "步骤1：详细演示第一步",
                "步骤2：详细演示第二步",
                "步骤3：详细演示第三步",
                "注意事项：提醒常见问题",
                "完成效果：展示最终成果",
            ]
        else:
            templates = [
                "开场介绍，展示主题或问题",
                "背景说明，介绍相关信息",
                "核心内容展示",
                "细节演示或说明",
                "效果展示或对比",
                "总结回顾",
                "行动号召或结尾",
            ]

        for i in range(count):
            if i < len(templates):
                desc = templates[i]
            else:
                desc = f"场景{i+1}内容"

            scenes.append({
                "id": i + 1,
                "description": desc,
                "duration": 5,
            })

        return scenes


class PromptPreviewPage(QWizardPage):
    """Prompt预览与编辑页 - 智能模式下显示LLM生成的场景"""

    def __init__(self, wizard: NewProjectWizard):
        super().__init__(wizard)
        self._wizard = wizard
        self._scenes: List[Dict[str, Any]] = []
        self._cached_scenes: Optional[List[Dict[str, Any]]] = None
        self._llm_thread: Optional[QThread] = None
        self._llm_worker: Optional[LLMSceneWorker] = None
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self.setTitle("AI场景预览与编辑")
        self.setSubTitle("查看AI生成的场景描述，您可以编辑调整后再提交")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        # 状态标签
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #D97706; font-weight: bold;")
        layout.addWidget(self._status_label)

        # 进度条
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)  # 不确定模式（滚动条动画）
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setFixedHeight(6)
        self._progress_bar.setVisible(False)
        layout.addWidget(self._progress_bar)

        # 场景编辑区
        scenes_card = SectionCard("AI生成的场景描述")
        scenes_scroll = QScrollArea()
        scenes_scroll.setWidgetResizable(True)
        scenes_scroll.setMinimumHeight(200)
        scenes_scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self._scenes_container = QWidget()
        self._scenes_vbox = QVBoxLayout(self._scenes_container)
        self._scenes_vbox.setContentsMargins(0, 0, 0, 0)
        self._scenes_vbox.setSpacing(8)

        scenes_scroll.setWidget(self._scenes_container)
        scenes_card.addWidget(scenes_scroll)
        layout.addWidget(scenes_card, 1)

        # Prompt预览区
        prompt_card = SectionCard("API提示词预览")
        self._prompt_preview = QTextEdit()
        self._prompt_preview.setReadOnly(True)
        self._prompt_preview.setMaximumHeight(150)
        self._prompt_preview.setStyleSheet(
            "font-family: 'Consolas', monospace; font-size: 11px; "
            "background-color: #F9F7F4;"
        )
        prompt_card.addWidget(self._prompt_preview)
        layout.addWidget(prompt_card)

        # 外层滚动区域（整个页面可滚动）
        outer_scroll = QScrollArea()
        outer_scroll.setWidgetResizable(True)
        outer_scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer_scroll.setWidget(container)
        page_layout = QVBoxLayout(self)
        page_layout.addWidget(outer_scroll)

    def initializePage(self) -> None:
        """进入页面时初始化"""
        super().initializePage()

        mode = self._wizard._project_data.get("generation_mode", "manual")

        if mode == "smart":
            if self._cached_scenes is not None:
                # 有缓存 → 直接使用，不重新调用LLM
                self._scenes = [s.copy() for s in self._cached_scenes]
                self._populate_scene_edits()
                self._update_prompt_preview()
                self._status_label.setText(f"已加载缓存场景 ({len(self._scenes)} 个)")
                self._status_label.setStyleSheet("color: #5B9E5F; font-weight: bold;")
            else:
                # 智能模式：启动LLM生成
                self._start_llm_generation()
        else:
            # 手动模式：直接显示已输入的场景
            self._fill_manual_scenes()

    def _fill_manual_scenes(self):
        """显示手动模式已有的场景"""
        scenes = self._wizard._project_data.get("scenes", [])
        self._scenes = scenes
        self._populate_scene_edits()
        self._update_prompt_preview()
        self._status_label.setText("手动模式 - 场景已就绪")
        self._status_label.setStyleSheet("color: #5B9E5F; font-weight: bold;")

    def _start_llm_generation(self):
        """启动LLM场景生成"""
        self._status_label.setText("正在调用AI生成场景，请稍候...")
        self._status_label.setStyleSheet("color: #D97706; font-weight: bold;")
        self._progress_bar.setVisible(True)

        # 清空旧的编辑框
        self._clear_scene_edits()
        self._prompt_preview.clear()

        # 获取API配置
        api_key = ""
        base_url = ""
        if API_CONFIG_AVAILABLE:
            try:
                api_config = APIConfig()
                api_key = api_config.get_api_key("智谱AI")
                base_url = api_config.get_base_url("智谱AI")
            except Exception:
                pass

        if not api_key:
            # 尝试使用默认provider
            if API_CONFIG_AVAILABLE:
                try:
                    api_config = APIConfig()
                    api_key = api_config.get_api_key()
                    base_url = api_config.get_base_url()
                except Exception:
                    pass

        if not api_key:
            self._on_llm_error("智谱AI API未配置，使用默认模板")
            return

        scene_count = self._wizard._project_data.get("scene_count", 5)
        project_data = {
            "project_name": self._wizard._project_data.get("project_name", ""),
            "project_description": self._wizard._project_data.get("project_description", ""),
            "has_main_character": self._wizard._project_data.get("has_main_character", False),
            "character": self._wizard._project_data.get("character", {}),
            "video": self._wizard._project_data.get("video", {}),
        }

        self._llm_worker = LLMSceneWorker(
            api_key=api_key,
            base_url=base_url,
            project_data=project_data,
            scene_count=scene_count,
        )
        self._llm_thread = QThread()
        self._llm_worker.moveToThread(self._llm_thread)

        self._llm_thread.started.connect(self._llm_worker.run)
        self._llm_worker.finished.connect(self._on_llm_finished)
        self._llm_worker.error.connect(self._on_llm_error)
        self._llm_worker.finished.connect(self._llm_thread.quit)
        self._llm_worker.error.connect(self._llm_thread.quit)

        self._llm_thread.start()

    def _on_llm_finished(self, scenes: list):
        """LLM生成完成"""
        self._progress_bar.setVisible(False)
        self._scenes = scenes
        self._cached_scenes = [s.copy() for s in scenes]
        self._populate_scene_edits()
        self._update_prompt_preview()
        self._status_label.setText(f"AI已生成 {len(scenes)} 个场景 - 您可以编辑调整")
        self._status_label.setStyleSheet("color: #5B9E5F; font-weight: bold;")

    def _on_llm_error(self, msg: str):
        """LLM生成失败，使用fallback"""
        self._progress_bar.setVisible(False)
        description = self._wizard._project_data.get("project_description", "")
        count = self._wizard._project_data.get("scene_count", 5)
        self._scenes = LLMSceneWorker.get_fallback_scenes(description, count)
        self._cached_scenes = [s.copy() for s in self._scenes]

        self._populate_scene_edits()
        self._update_prompt_preview()
        self._status_label.setText(
            f"AI生成失败({msg})，已使用默认模板 - 您可以编辑调整"
        )
        self._status_label.setStyleSheet("color: #D97706; font-weight: bold;")

    def _clear_scene_edits(self):
        """清空场景编辑框"""
        while self._scenes_vbox.count():
            item = self._scenes_vbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # 清理子布局中的widget
                sub = item.layout()
                while sub.count():
                    sub_item = sub.takeAt(0)
                    if sub_item.widget():
                        sub_item.widget().deleteLater()

    def _populate_scene_edits(self):
        """根据 self._scenes 填充编辑框"""
        self._clear_scene_edits()

        for scene in self._scenes:
            sid = scene.get("id", 0)
            desc = scene.get("description", "")
            shot = scene.get("shot_type", "中景")
            camera = scene.get("camera_movement", "固定")
            duration = scene.get("duration", 5)
            image_prompt = scene.get("image_prompt", "")
            video_prompt = scene.get("video_prompt", "")

            row = QHBoxLayout()
            label = QLabel(f"场景{sid}:")
            label.setFixedWidth(55)
            label.setStyleSheet("font-weight: bold;")
            row.addWidget(label)

            edit = QTextEdit()
            edit.setPlainText(desc)
            edit.setMaximumHeight(50)
            edit.setProperty("scene_id", sid)
            edit.setProperty("scene_duration", duration)
            edit.setProperty("scene_shot_type", shot)
            edit.setProperty("scene_camera", camera)
            edit.setProperty("scene_image_prompt", image_prompt)
            edit.setProperty("scene_video_prompt", video_prompt)
            row.addWidget(edit, 1)

            meta_label = QLabel(f"{shot} | {camera} | {duration}s")
            meta_label.setStyleSheet("color: #9A958F; font-size: 10px;")
            meta_label.setFixedWidth(120)
            row.addWidget(meta_label)

            self._scenes_vbox.addLayout(row)

        self._scenes_vbox.addStretch()

    def _update_prompt_preview(self):
        """更新prompt预览区"""
        lines = []
        style = self._wizard._project_data.get("video", {}).get("style", "写实风格")
        ratio = self._wizard._project_data.get("video", {}).get("aspect_ratio", "16:9")

        for scene in self._scenes:
            sid = scene.get("id", 0)
            desc = scene.get("description", "")
            image_prompt = scene.get("image_prompt", "")
            video_prompt = scene.get("video_prompt", "")

            # 如果LLM没生成prompt，用描述拼接
            if not image_prompt:
                style_text = "实景" if "写实" in style or "产品" in style else "动画"
                image_prompt = f"{desc} --ratio {ratio} --style {style_text}"
            else:
                image_prompt = f"{image_prompt} --ratio {ratio}"

            if not video_prompt:
                video_prompt = f"{desc} --ratio {ratio}"
            else:
                video_prompt = f"{video_prompt} --ratio {ratio}"

            lines.append(f"--- 场景 {sid}: {desc} ---")
            lines.append(f"  图片prompt: {image_prompt}")
            lines.append(f"  视频prompt: {video_prompt}")
            lines.append("")

        self._prompt_preview.setPlainText("\n".join(lines))

    def _collect_edited_scenes(self) -> List[Dict[str, Any]]:
        """从编辑框收集场景数据"""
        style = self._wizard._project_data.get("video", {}).get("style", "写实风格")
        ratio = self._wizard._project_data.get("video", {}).get("aspect_ratio", "16:9")

        scenes = []
        for i in range(self._scenes_vbox.count()):
            item = self._scenes_vbox.itemAt(i)
            if item and item.layout():
                row_layout = item.layout()
                # row_layout: label(0), textedit(1), meta(2)
                if row_layout.count() >= 2:
                    text_edit = row_layout.itemAt(1).widget()
                    if text_edit and isinstance(text_edit, QTextEdit):
                        desc = text_edit.toPlainText().strip()
                        if desc:
                            scene = {
                                "id": text_edit.property("scene_id") or len(scenes) + 1,
                                "description": desc,
                                "duration": text_edit.property("scene_duration") or 5,
                                "shot_type": text_edit.property("scene_shot_type") or "中景",
                                "camera_movement": text_edit.property("scene_camera") or "固定",
                            }

                            # 优先使用LLM生成的prompt，否则fallback拼接
                            llm_image = text_edit.property("scene_image_prompt") or ""
                            llm_video = text_edit.property("scene_video_prompt") or ""

                            if llm_image:
                                scene["image_prompt"] = f"{llm_image} --ratio {ratio}"
                            else:
                                style_text = "实景" if "写实" in style or "产品" in style else "动画"
                                scene["image_prompt"] = f"{desc} --ratio {ratio} --style {style_text}"

                            if llm_video:
                                scene["video_prompt"] = f"{llm_video} --ratio {ratio}"
                            else:
                                scene["video_prompt"] = f"{desc} --ratio {ratio}"

                            scenes.append(scene)

        # 重新编号
        for i, s in enumerate(scenes):
            s["id"] = i + 1

        return scenes

    def validatePage(self) -> bool:
        """验证并收集编辑后的场景数据"""
        scenes = self._collect_edited_scenes()

        if not scenes:
            return False

        self._cached_scenes = scenes
        self._wizard._project_data["scenes"] = scenes
        return True

    def cleanupPage(self) -> None:
        """离开页面时清理线程"""
        if self._llm_thread and self._llm_thread.isRunning():
            self._llm_thread.quit()
            self._llm_thread.wait(2000)
        super().cleanupPage()
