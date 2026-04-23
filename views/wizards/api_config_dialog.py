#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Configuration Dialog
API配置对话框
支持智谱AI (Zhipu) - LLM对话
支持并行科技 (Paratera) - 豆包图片/视频生成
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QPushButton, QLabel,
    QGroupBox, QScrollArea, QWidget, QMessageBox,
    QCheckBox, QSpinBox, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from typing import Optional, Dict, Any, List

from viewmodels.api_viewmodel import APIConfigViewModel
from views.widgets.styled_widgets import (
    CardFrame, HeadingLabel, SubheadingLabel, HintLabel,
    PrimaryButton, DangerButton, FormRow
)

# 尝试导入新的OpenAI客户端
try:
    from api_client import OpenAIClient, PROVIDER_CONFIGS, ProviderType
    API_CLIENT_AVAILABLE = True
except ImportError:
    API_CLIENT_AVAILABLE = False


# 提供商配置（与api_client.py保持一致）
DEFAULT_PROVIDERS = {
    "智谱AI": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4/",
        "models": ["glm-4.7", "glm-5.1", "glm-4-plus", "glm-4-flash"],
        "default_model": "glm-4.7",
        "description": "智谱AI BigModel - 主要LLM提供商，用于场景规划和对话"
    },
    "并行科技": {
        "base_url": "https://llmapi.paratera.com/v1/",
        "models": ["Doubao-Seedream-4.0", "Doubao-Seedance-1.0-Pro"],
        "default_model": "Doubao-Seedream-4.0",
        "description": "并行科技 - 豆包模型，用于图片和视频生成"
    },
    "自定义": {
        "base_url": "",
        "models": [],
        "default_model": "",
        "description": "自定义API端点，手动输入URL和模型"
    }
}


class APIConfigDialog(QDialog):
    """API配置对话框"""

    def __init__(self, api_vm: APIConfigViewModel, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._api_vm = api_vm
        self._provider_models: Dict[str, List[str]] = DEFAULT_PROVIDERS
        self._setup_ui()
        self._load_providers()

    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("API配置管理")
        self.setMinimumSize(650, 550)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 标题
        title = HeadingLabel("API配置管理")
        layout.addWidget(title)

        # 提示
        hint = HintLabel("配置您的API密钥以使用视频生成功能。配置将保存在本地，不会上传到任何服务器。")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # 添加新提供商区域
        add_section = self._create_add_provider_section()
        layout.addWidget(add_section)

        # 已配置的提供商列表
        list_section = self._create_providers_list_section()
        layout.addWidget(list_section, 1)

        # 关闭按钮
        close_layout = QHBoxLayout()
        close_layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        close_layout.addWidget(close_btn)

        layout.addLayout(close_layout)

    def _create_add_provider_section(self) -> CardFrame:
        """创建添加提供商区域"""
        section = CardFrame()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 标题
        layout.addWidget(SubheadingLabel("添加新提供商"))

        # 提供商选择
        provider_layout = QHBoxLayout()
        provider_layout.addWidget(QLabel("提供商:"))

        self._provider_combo = QComboBox()
        self._provider_combo.addItems(list(DEFAULT_PROVIDERS.keys()))
        self._provider_combo.currentTextChanged.connect(self._on_provider_changed)
        provider_layout.addWidget(self._provider_combo, 1)

        layout.addLayout(provider_layout)

        # 提供商描述
        self._description_label = HintLabel(DEFAULT_PROVIDERS["智谱AI"]["description"])
        self._description_label.setWordWrap(True)
        self._description_label.setStyleSheet("color: #6B6560; padding: 4px 8px; background: #F5E6D3; border-radius: 4px;")
        layout.addWidget(self._description_label)

        # 模型选择
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("模型:"))

        self._model_combo = QComboBox()
        self._model_combo.addItems(DEFAULT_PROVIDERS["智谱AI"]["models"])
        self._model_combo.setCurrentText(DEFAULT_PROVIDERS["智谱AI"]["default_model"])
        model_layout.addWidget(self._model_combo, 1)

        layout.addLayout(model_layout)

        # API密钥
        self._api_key_edit = QLineEdit()
        self._api_key_edit.setPlaceholderText("输入API密钥")
        self._api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)

        key_row = FormRow("API密钥:", self._api_key_edit)
        layout.addWidget(key_row)

        # 显示/隐藏密钥
        self._show_key_cb = QCheckBox("显示密钥")
        self._show_key_cb.toggled.connect(self._on_show_key_toggled)
        layout.addWidget(self._show_key_cb)

        # API URL（只读，显示当前配置）
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("API URL:"))

        self._url_label = QLabel(DEFAULT_PROVIDERS["智谱AI"]["base_url"])
        self._url_label.setStyleSheet("color: #6B6560; font-family: monospace;")
        url_layout.addWidget(self._url_label, 1)

        layout.addLayout(url_layout)

        # 自定义URL输入（仅自定义提供商显示）
        self._custom_url_edit = QLineEdit()
        self._custom_url_edit.setPlaceholderText("输入自定义API URL，例如: https://api.example.com/v1/")
        self._custom_url_row = FormRow("自定义URL:", self._custom_url_edit)
        self._custom_url_row.setVisible(False)
        layout.addWidget(self._custom_url_row)

        # 按钮行
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        test_btn = QPushButton("测试连接")
        test_btn.clicked.connect(self._test_connection)
        button_layout.addWidget(test_btn)

        add_btn = PrimaryButton("保存配置")
        add_btn.clicked.connect(self._add_provider)
        button_layout.addWidget(add_btn)

        layout.addLayout(button_layout)

        return section

    def _create_providers_list_section(self) -> CardFrame:
        """创建已配置提供商列表区域"""
        section = CardFrame()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        layout.addWidget(SubheadingLabel("已配置的提供商"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(200)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._providers_widget = QWidget()
        self._providers_layout = QVBoxLayout(self._providers_widget)
        self._providers_layout.setContentsMargins(0, 0, 0, 0)
        self._providers_layout.setSpacing(8)

        scroll.setWidget(self._providers_widget)
        layout.addWidget(scroll)

        return section

    def _on_provider_changed(self, provider: str):
        """提供商选择变化"""
        config = DEFAULT_PROVIDERS.get(provider, DEFAULT_PROVIDERS["自定义"])

        # 更新描述
        self._description_label.setText(config["description"])

        # 更新模型列表
        self._model_combo.clear()
        models = config.get("models", [])
        if models:
            self._model_combo.addItems(models)
            default_model = config.get("default_model", models[0])
            self._model_combo.setCurrentText(default_model)

        # 更新URL显示
        base_url = config.get("base_url", "")
        self._url_label.setText(base_url)

        # 显示/隐藏自定义URL输入
        is_custom = provider == "自定义"
        self._custom_url_row.setVisible(is_custom)
        self._url_label.setVisible(not is_custom)

    def _on_show_key_toggled(self, checked: bool):
        """显示/隐藏密钥"""
        if checked:
            self._api_key_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self._api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)

    def _load_providers(self):
        """加载已配置的提供商"""
        # 清除现有列表
        while self._providers_layout.count():
            item = self._providers_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 添加提供商
        for provider in self._api_vm.getProviders():
            card = self._create_provider_card(provider)
            self._providers_layout.addWidget(card)

        self._providers_layout.addStretch()

    def _create_provider_card(self, provider_info: dict) -> CardFrame:
        """创建提供商卡片"""
        card = CardFrame()

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # 名称和状态
        header = QHBoxLayout()
        name = provider_info.get("name", "")
        is_current = provider_info.get("is_current", False)

        name_label = SubheadingLabel(name)
        header.addWidget(name_label)

        header.addStretch()

        if is_current:
            current_badge = QLabel("✓ 当前")
            current_badge.setStyleSheet("color: #5B9E5F; font-weight: bold;")
            header.addWidget(current_badge)

        layout.addLayout(header)

        # API密钥（掩码）
        api_key = provider_info.get("api_key", "")
        key_label = HintLabel(f"密钥: {api_key}")
        layout.addWidget(key_label)

        # 基础URL
        base_url = provider_info.get("base_url", "")
        if base_url:
            url_label = HintLabel(f"URL: {base_url}")
            layout.addWidget(url_label)

        # 按钮行
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        if not is_current:
            set_current_btn = QPushButton("设为当前")
            set_current_btn.clicked.connect(lambda: self._set_current(name))
            button_layout.addWidget(set_current_btn)

        delete_btn = DangerButton("删除")
        delete_btn.clicked.connect(lambda: self._delete_provider(name))
        button_layout.addWidget(delete_btn)

        layout.addLayout(button_layout)

        return card

    def _add_provider(self):
        """添加提供商"""
        provider = self._provider_combo.currentText()
        api_key = self._api_key_edit.text().strip()

        # 获取base_url
        if provider == "自定义":
            base_url = self._custom_url_edit.text().strip()
        else:
            base_url = DEFAULT_PROVIDERS.get(provider, {}).get("base_url", "")

        if not api_key:
            QMessageBox.warning(self, "警告", "请输入API密钥")
            return

        if not base_url and provider == "自定义":
            QMessageBox.warning(self, "警告", "请输入API URL")
            return

        if self._api_vm.addProvider(provider, api_key, base_url):
            # 清空输入
            self._api_key_edit.clear()

            # 如果是第一个提供商，设为当前
            if self._api_vm.providerCount == 1:
                self._api_vm.setCurrentProvider(provider)

            self._load_providers()
            QMessageBox.information(self, "成功", f"提供商 '{provider}' 配置已保存")

    def _delete_provider(self, name: str):
        """删除提供商"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除提供商 '{name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self._api_vm.removeProvider(name):
                self._load_providers()

    def _set_current(self, name: str):
        """设为当前提供商"""
        self._api_vm.setCurrentProvider(name)
        self._load_providers()

    def _test_connection(self):
        """测试连接"""
        provider = self._provider_combo.currentText()
        api_key = self._api_key_edit.text().strip()

        # 获取base_url
        if provider == "自定义":
            base_url = self._custom_url_edit.text().strip()
        else:
            base_url = DEFAULT_PROVIDERS.get(provider, {}).get("base_url", "")

        if not api_key:
            QMessageBox.warning(self, "警告", "请输入API密钥")
            return

        if not base_url:
            QMessageBox.warning(self, "警告", "请输入API URL")
            return

        # 使用OpenAI SDK测试（如果可用）
        if API_CLIENT_AVAILABLE:
            self._test_with_openai_sdk(provider, api_key, base_url)
        else:
            self._test_with_vm(provider, api_key, base_url)

    def _test_with_openai_sdk(self, provider: str, api_key: str, base_url: str):
        """使用OpenAI SDK测试连接"""
        try:
            model = self._model_combo.currentText()

            # 创建客户端并测试
            client = OpenAIClient(api_key=api_key, base_url=base_url, model=model)
            success, message = client.test_connection()

            if success:
                QMessageBox.information(
                    self,
                    "测试结果",
                    f"✓ 连接测试成功\n\n提供商: {provider}\n模型: {model}\n\n{message}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "测试结果",
                    f"✗ 连接测试失败\n\n提供商: {provider}\n\n错误: {message}"
                )
        except Exception as e:
            QMessageBox.warning(
                self,
                "测试结果",
                f"✗ 连接测试失败\n\n提供商: {provider}\n\n错误: {str(e)}"
            )

    def _test_with_vm(self, provider: str, api_key: str, base_url: str):
        """使用ViewModel测试连接（备用）"""
        # 临时添加提供商进行测试
        original_providers = self._api_vm._api_config.config.get("providers", {}).copy()

        self._api_vm._api_config.config["providers"] = self._api_vm._api_config.config.get("providers", {})
        self._api_vm._api_config.config["providers"][provider] = {
            "api_key": api_key,
            "base_url": base_url
        }

        # 使用ViewModel的测试方法
        if self._api_vm.testConnection(provider):
            QMessageBox.information(
                self,
                "测试结果",
                f"✓ 连接测试成功\n\n提供商: {provider}\nURL: {base_url}"
            )
        else:
            error_msg = self._api_vm._error_message if hasattr(self._api_vm, '_error_message') else "未知错误"
            QMessageBox.warning(
                self,
                "测试结果",
                f"✗ 连接测试失败\n\n提供商: {provider}\n\n{error_msg}"
            )

        # 恢复原配置
        self._api_vm._api_config.config["providers"] = original_providers
