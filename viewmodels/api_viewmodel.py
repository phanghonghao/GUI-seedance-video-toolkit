#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Configuration ViewModel
"""

from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
import json

from .base_viewmodel import BaseViewModel
import sys

# 添加CLI模块路径
_cli_path = Path(__file__).parent.parent / "video-generator-cli"
if _cli_path.exists():
    sys.path.insert(0, str(_cli_path))

try:
    from api_config import APIConfig, API_PROVIDERS
except ImportError:
    APIConfig = None
    API_PROVIDERS = {}

# 导入新的OpenAI客户端
try:
    from api_client import OpenAIClient, PROVIDER_CONFIGS, ProviderType
    API_CLIENT_AVAILABLE = True
except ImportError:
    API_CLIENT_AVAILABLE = False


class APIConfigViewModel(BaseViewModel):
    """API配置ViewModel"""

    # 配置状态信号
    configChanged = pyqtSignal()
    providerChanged = pyqtSignal()

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self._api_config: Optional[APIConfig] = None
        self._current_provider: str = ""
        self._providers: List[Dict[str, Any]] = []
        self._api_key: str = ""
        self._base_url: str = ""

        # 初始化加载配置
        self._init_config()

    def _init_config(self):
        """初始化API配置"""
        if APIConfig is None:
            self.set_error("CLI模块未加载")
            return

        try:
            self._api_config = APIConfig()
            self._load_providers()
            self._current_provider = self._api_config.config.get("current_provider", "")
        except Exception as e:
            self.set_error(f"加载API配置失败: {str(e)}")

    def _load_providers(self):
        """加载提供商列表"""
        if self._api_config is None:
            return

        try:
            providers = self._api_config.list_providers()
            self._providers = []

            for provider in providers:
                provider_info = {
                    "name": provider,
                    "is_current": provider == self._current_provider,
                    "api_key": self._mask_api_key(
                        self._api_config.config.get("providers", {}).get(provider, {}).get("api_key", "")
                    ),
                    "base_url": self._api_config.config.get("providers", {}).get(provider, {}).get("base_url", ""),
                }
                self._providers.append(provider_info)

            self.configChanged.emit()
        except Exception as e:
            self.set_error(f"加载提供商列表失败: {str(e)}")

    @staticmethod
    def _mask_api_key(api_key: str) -> str:
        """掩码API密钥"""
        if len(api_key) > 12:
            return f"{api_key[:8]}...{api_key[-4:]}"
        return "****"

    # ===== Property =====

    def providerCount(self) -> int:
        return len(self._providers)

    providerCount = pyqtProperty(int, providerCount, notify=configChanged)

    def currentProvider(self) -> str:
        return self._current_provider

    def setCurrentProvider(self, provider: str):
        if self._current_provider != provider:
            self._current_provider = provider
            if self._api_config:
                self._api_config.set_current_provider(provider)
            self.providerChanged.emit()
            self._load_providers()

    currentProvider = pyqtProperty(str, fget=currentProvider, fset=setCurrentProvider, notify=providerChanged)

    # ===== 配置状态 =====

    def isConfigured(self, provider: str = None) -> bool:
        """检查提供商是否已配置"""
        if provider is None:
            provider = self._current_provider
        return self._api_config.is_configured(provider) if self._api_config else False

    def getApiConfig(self) -> Optional[APIConfig]:
        """获取API配置对象"""
        return self._api_config

    # ===== 提供商管理 =====

    def getProviders(self) -> List[Dict[str, Any]]:
        """获取提供商列表"""
        return self._providers.copy()

    def getBuiltInProviders(self) -> List[str]:
        """获取内置提供商列表"""
        providers = list(API_PROVIDERS.keys()) if API_PROVIDERS else []

        # 如果OpenAI客户端可用，添加智谱AI
        if API_CLIENT_AVAILABLE:
            if "智谱AI" not in providers:
                providers.insert(0, "智谱AI")  # 智谱AI作为默认选项

        return providers

    def getProviderInfo(self, provider: str) -> Optional[Dict[str, Any]]:
        """获取提供商信息"""
        # 首先检查新的api_client配置
        if API_CLIENT_AVAILABLE:
            provider_type = OpenAIClient.get_provider_by_name(provider)
            config = OpenAIClient.get_provider_config(provider_type)
            if config:
                return config

        # 回退到旧的API_PROVIDERS
        if API_PROVIDERS and provider in API_PROVIDERS:
            return API_PROVIDERS[provider]
        return None

    # ===== 添加/更新提供商 =====

    def addProvider(self, provider: str, api_key: str, base_url: str = "") -> bool:
        """添加或更新提供商"""
        if self._api_config is None:
            self.set_error("API配置未初始化")
            return False

        try:
            if not api_key:
                self.set_error("API密钥不能为空")
                return False

            self._api_config.add_provider(provider, api_key, base_url)

            # 如果是第一个提供商，设为当前
            if not self._current_provider:
                self._current_provider = provider

            self._load_providers()
            self.set_success(f"提供商 '{provider}' 已添加")
            return True

        except Exception as e:
            self.set_error(f"添加提供商失败: {str(e)}")
            return False

    def removeProvider(self, provider: str) -> bool:
        """删除提供商"""
        if self._api_config is None:
            self.set_error("API配置未初始化")
            return False

        try:
            self._api_config.remove_provider(provider)
            self._load_providers()

            if self._current_provider == provider:
                self._current_provider = self._api_config.config.get("current_provider", "")
                self.providerChanged.emit()

            self.set_success(f"提供商 '{provider}' 已删除")
            return True

        except Exception as e:
            self.set_error(f"删除提供商失败: {str(e)}")
            return False

    # ===== 获取API信息 =====

    def getApiKey(self, provider: str = None) -> str:
        """获取API密钥"""
        if self._api_config is None:
            return ""
        return self._api_config.get_api_key(provider) or ""

    def getBaseUrl(self, provider: str = None) -> str:
        """获取API基础URL"""
        if self._api_config is None:
            return ""
        return self._api_config.get_base_url(provider) or ""

    def getModel(self, model_type: str, provider: str = None) -> str:
        """获取模型名称"""
        if self._api_config is None:
            return ""
        return self._api_config.get_model(model_type, provider) or ""

    # ===== 配置导出/导入 =====

    def exportConfig(self, file_path: Path) -> bool:
        """导出配置（隐藏API密钥）"""
        if self._api_config is None:
            return False

        try:
            config = self._api_config.get_config_dict()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            self.set_success(f"配置已导出到: {file_path}")
            return True
        except Exception as e:
            self.set_error(f"导出配置失败: {str(e)}")
            return False

    def importConfig(self, file_path: Path) -> bool:
        """导入配置"""
        if self._api_config is None:
            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 合并配置
            if "providers" in config:
                for provider, data in config["providers"].items():
                    # 导入的API密钥可能是掩码的，需要重新输入
                    api_key = data.get("api_key", "")
                    if "..." in api_key or api_key == "****":
                        continue  # 跳过掩码的密钥
                    self._api_config.add_provider(provider, api_key, data.get("base_url", ""))

            if "current_provider" in config:
                self._api_config.set_current_provider(config["current_provider"])
                self._current_provider = config["current_provider"]

            self._load_providers()
            self.set_success(f"配置已从 {file_path} 导入")
            return True

        except Exception as e:
            self.set_error(f"导入配置失败: {str(e)}")
            return False

    # ===== 测试连接 =====

    def testConnection(self, provider: str = None) -> bool:
        """测试API连接"""
        if self._api_config is None:
            return False

        if provider is None:
            provider = self._current_provider

        if not provider:
            self.set_error("请先选择提供商")
            return False

        if not self.isConfigured(provider):
            self.set_error(f"提供商 '{provider}' 未配置API密钥")
            return False

        # 获取配置信息
        api_key = self.getApiKey(provider)
        base_url = self.getBaseUrl(provider)

        if not api_key:
            self.set_error("API密钥为空")
            return False

        if not base_url:
            self.set_error("API URL为空")
            return False

        # 使用OpenAI SDK测试连接
        if API_CLIENT_AVAILABLE:
            return self._test_with_openai_sdk(provider, api_key, base_url)
        else:
            return self._test_with_urllib(provider, api_key, base_url)

    def _test_with_openai_sdk(self, provider: str, api_key: str, base_url: str) -> bool:
        """使用OpenAI SDK测试连接"""
        try:
            # 确保base_url包含https://
            if not base_url.startswith("http://") and not base_url.startswith("https://"):
                base_url = f"https://{base_url}"

            # 获取模型信息（使用默认模型）
            model = "glm-4.7"  # 默认模型
            if provider in API_PROVIDERS:
                models = API_PROVIDERS[provider].get("models", {})
                if models:
                    # 优先使用image模型，如果没有则使用video模型
                    model = models.get("image") or models.get("video", "glm-4.7")

            # 创建客户端并测试
            client = OpenAIClient(api_key=api_key, base_url=base_url, model=model)
            success, message = client.test_connection()

            if success:
                self.set_success(f"提供商 '{provider}' {message}")
                return True
            else:
                self.set_error(f"提供商 '{provider}' 连接失败: {message}")
                return False

        except Exception as e:
            self.set_error(f"连接测试失败: {str(e)}")
            return False

    def _test_with_urllib(self, provider: str, api_key: str, base_url: str) -> bool:
        """使用urllib测试连接（备用方案）"""
        # 确保base_url包含https://
        if not base_url.startswith("http://") and not base_url.startswith("https://"):
            base_url = f"https://{base_url}"

        # 尝试发送简单的API请求验证
        try:
            import urllib.request
            import urllib.error

            # 构建测试请求URL（使用模型列表端点）
            test_url = f"{base_url}/v1/models"

            # 创建请求
            request = urllib.request.Request(
                test_url,
                method="GET",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
            )

            # 发送请求（超时5秒）
            with urllib.request.urlopen(request, timeout=5) as response:
                if response.status == 200:
                    self.set_success(f"提供商 '{provider}' 连接测试成功")
                    return True
                else:
                    self.set_error(f"API返回错误状态: {response.status}")
                    return False

        except urllib.error.HTTPError as e:
            error_msg = f"HTTP错误: {e.code}"
            if e.code == 401:
                error_msg = "API密钥无效或未授权"
            elif e.code == 404:
                error_msg = "API端点不存在，请检查URL配置"
            self.set_error(f"连接测试失败: {error_msg}")
            return False

        except urllib.error.URLError as e:
            self.set_error(f"网络错误: {str(e.reason)}")
            return False

        except Exception as e:
            self.set_error(f"连接测试失败: {str(e)}")
            return False
