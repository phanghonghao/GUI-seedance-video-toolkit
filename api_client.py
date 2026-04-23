#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAI API Client Wrapper for Video Generator
支持智谱AI (Zhipu) - LLM对话
支持并行科技 (Paratera) - 豆包图片/视频生成
"""

import openai
import logging
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class ProviderType(Enum):
    """API提供商类型"""
    ZHIPU = "智谱AI"
    PARATERA = "并行科技"
    CUSTOM = "自定义"


# 提供商配置常量
PROVIDER_CONFIGS = {
    ProviderType.ZHIPU: {
        "name": "智谱AI",
        "base_url": "https://open.bigmodel.cn/api/paas/v4/",
        "models": ["glm-4.7", "glm-5.1", "glm-4-plus", "glm-4-flash"],
        "default_model": "glm-4.7",
        "description": "智谱AI BigModel - LLM对话/场景规划",
        "api_type": "openai"
    },
    ProviderType.PARATERA: {
        "name": "并行科技",
        "base_url": "https://llmapi.paratera.com/v1/",
        "models": ["Doubao-Seedream-3.0-T2I", "Doubao-Seedance-1.0-Pro"],
        "default_model": "Doubao-Seedream-3.0-T2I",
        "description": "并行科技 - 豆包图片/视频生成",
        "endpoints": {
            "image": "/images/generations",
            "video_generate": "/p001/contents/generations/tasks",
            "video_query": "/p001/contents/generations/tasks"
        },
        "api_type": "openai"
    },
    ProviderType.CUSTOM: {
        "name": "自定义",
        "base_url": "",
        "models": [],
        "default_model": "",
        "description": "自定义API端点",
        "api_type": "openai"
    }
}


class OpenAIClient:
    """OpenAI兼容API客户端

    统一接口支持多种API提供商:
    - 智谱AI (Zhipu) - LLM对话，用于场景规划
    - 并行科技 (Paratera) - 豆包图片/视频生成
    - 自定义提供商
    """

    def __init__(self, api_key: str, base_url: str, model: str = "glm-4.7"):
        """初始化客户端

        Args:
            api_key: API密钥
            base_url: API基础URL
            model: 默认模型名称
        """
        self._api_key = api_key
        self._base_url = base_url.rstrip('/') if base_url else ""
        self._model = model

        # 创建OpenAI客户端
        self._client = openai.OpenAI(
            api_key=api_key,
            base_url=self._base_url
        )

    def test_connection(self) -> Tuple[bool, str]:
        """测试API连接

        Returns:
            (success, message): 成功状态和消息
        """
        try:
            # 尝试获取模型列表
            models = self._client.models.list()
            return True, f"连接成功，可用模型数量: {len(models.data)}"
        except openai.AuthenticationError:
            return False, "认证失败: API密钥无效"
        except openai.APIConnectionError as e:
            return False, f"网络连接错误: {str(e)}"
        except openai.RateLimitError:
            return False, "速率限制: 请求过于频繁"
        except openai.APIError as e:
            return False, f"API错误: {str(e)}"
        except Exception as e:
            return False, f"连接测试失败: {str(e)}"

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """LLM对话 - 用于场景规划

        Args:
            messages: 对话消息列表，格式:
                [{"role": "user", "content": "你好"}]
            model: 模型名称（可选，默认使用初始化时的模型）
            **kwargs: 其他参数（temperature, max_tokens等）

        Returns:
            API响应字典
        """
        if model is None:
            model = self._model

        response = self._client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )

        return {
            "content": response.choices[0].message.content,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            }
        }

    def generate_image(
        self,
        prompt: str,
        model: str = "Doubao-Seedream-4.0",
        **kwargs
    ) -> Dict[str, Any]:
        """生成图片 - 使用豆包Seedream

        Args:
            prompt: 图片描述提示词
            model: 图片生成模型名称
            **kwargs: 其他参数（size, n等）

        Returns:
            API响应字典，包含图片URL
        """
        try:
            logger.debug(f"Generating image with model: {model}, prompt: {prompt[:50]}...")
            response = self._client.images.generate(
                model=model,
                prompt=prompt,
                **kwargs
            )

            # 验证响应结构
            if not response.data or len(response.data) == 0:
                logger.error("API返回空数据")
                return {"images": [], "error": "API返回空数据"}

            image_urls = [img.url for img in response.data if hasattr(img, 'url') and img.url]

            if not image_urls:
                logger.error("API响应中没有有效的图片URL")
                return {"images": [], "error": "API响应中没有有效的图片URL"}

            logger.info(f"Successfully generated {len(image_urls)} image(s)")
            return {
                "images": image_urls,
                "model": model
            }
        except openai.APIError as e:
            logger.error(f"API error: {e}")
            return {"images": [], "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"images": [], "error": str(e)}

    def generate_video(
        self,
        content: List[Dict[str, Any]],
        model: str = "Doubao-Seedance-1.0-Pro"
    ) -> Dict[str, Any]:
        """生成视频 - 使用豆包Seedance

        Args:
            content: 内容列表，格式:
                [
                    {"type": "text", "text": "提示词 --ratio 16:9"},
                    {"type": "image_url", "image_url": {"url": "图片URL"}}
                ]
            model: 视频生成模型名称

        Returns:
            API响应字典，包含任务ID
        """
        import requests

        try:
            logger.debug(f"Generating video with model: {model}")
            url = f"{self._base_url}/p001/contents/generations/tasks"
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": model,
                "content": content
            }

            logger.debug(f"POST {url}")
            response = requests.post(url, json=data, headers=headers, timeout=30)

            # 记录响应状态和内容
            logger.debug(f"Response status: {response.status_code}")

            if response.status_code != 200:
                logger.error(f"API返回错误状态码: {response.status_code}, body: {response.text}")
                return {"task_id": None, "error": f"HTTP {response.status_code}: {response.text}"}

            response.raise_for_status()
            result = response.json()

            # 验证任务ID (API返回的是id而不是task_id)
            task_id = result.get("id") or result.get("task_id") or result.get("data", {}).get("task_id") or result.get("data", {}).get("id")

            if not task_id:
                logger.error(f"API响应中没有任务ID: {result}")
                return {"task_id": None, "error": "API响应中没有任务ID"}

            logger.info(f"Video generation task created: {task_id}")
            return {"task_id": task_id}

        except requests.RequestException as e:
            logger.error(f"Network error: {e}")
            return {"task_id": None, "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"task_id": None, "error": str(e)}

    def query_video_task(self, task_id: str) -> Dict[str, Any]:
        """查询视频生成任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态信息
        """
        import requests
        import json

        url = f"{self._base_url}/p001/contents/generations/tasks"
        headers = {
            "Authorization": f"Bearer {self._api_key}"
        }
        params = {
            "filter": json.dumps({"task_ids": [task_id]})
        }

        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()

        return response.json()

    @classmethod
    def get_provider_config(cls, provider: ProviderType) -> Dict[str, Any]:
        """获取提供商配置

        Args:
            provider: 提供商类型

        Returns:
            提供商配置字典
        """
        return PROVIDER_CONFIGS.get(provider, PROVIDER_CONFIGS[ProviderType.CUSTOM])

    @classmethod
    def get_provider_by_name(cls, name: str) -> ProviderType:
        """根据名称获取提供商类型

        Args:
            name: 提供商名称

        Returns:
            ProviderType枚举
        """
        for provider_type, config in PROVIDER_CONFIGS.items():
            if config["name"] == name:
                return provider_type
        return ProviderType.CUSTOM

    @classmethod
    def list_providers(cls) -> List[str]:
        """列出所有可用提供商

        Returns:
            提供商名称列表
        """
        return [config["name"] for config in PROVIDER_CONFIGS.values()]

    @classmethod
    def get_models_for_provider(cls, provider_name: str) -> List[str]:
        """获取提供商的模型列表

        Args:
            provider_name: 提供商名称

        Returns:
            模型名称列表
        """
        provider_type = cls.get_provider_by_name(provider_name)
        config = cls.get_provider_config(provider_type)
        return config.get("models", [])

    def test_image_generation(self, prompt: str = "一只猫") -> Tuple[bool, str, Dict]:
        """测试图片生成API

        Args:
            prompt: 测试提示词

        Returns:
            (success, message, response_data)
        """
        try:
            logger.info(f"Testing image generation with prompt: {prompt}")
            result = self.generate_image(prompt=prompt, model="Doubao-Seedream-3.0-T2I")

            if "error" in result:
                return False, result.get("error", "未知错误"), result

            if result.get("images"):
                return True, f"成功生成 {len(result['images'])} 张图片", result
            else:
                return False, "API未返回图片数据", result

        except Exception as e:
            logger.error(f"Image generation test failed: {e}", exc_info=True)
            return False, str(e), {}

    def test_video_generation(self, prompt: str = "海浪拍打岸边") -> Tuple[bool, str, Dict]:
        """测试视频生成API

        Args:
            prompt: 测试提示词

        Returns:
            (success, message, response_data)
        """
        try:
            logger.info(f"Testing video generation with prompt: {prompt}")
            content = [{"type": "text", "text": prompt}]
            result = self.generate_video(content=content, model="Doubao-Seedance-1.0-Pro")

            if "error" in result:
                return False, result.get("error", "未知错误"), result

            task_id = result.get("task_id")
            if task_id:
                return True, f"成功创建视频任务: {task_id}", result
            else:
                return False, "API未返回任务ID", result

        except Exception as e:
            logger.error(f"Video generation test failed: {e}", exc_info=True)
            return False, str(e), {}


def create_client(provider_name: str, api_key: str, base_url: str = "", model: str = "") -> OpenAIClient:
    """工厂函数：创建API客户端

    Args:
        provider_name: 提供商名称（智谱AI/并行科技/自定义）
        api_key: API密钥
        base_url: API基础URL（自定义提供商需要）
        model: 模型名称（可选，使用默认值）

    Returns:
        OpenAIClient实例

    Raises:
        ValueError: 提供商名称无效或缺少必要参数
    """
    provider_type = OpenAIClient.get_provider_by_name(provider_name)
    config = OpenAIClient.get_provider_config(provider_type)

    # 确定base_url
    if not base_url:
        base_url = config.get("base_url", "")

    if not base_url and provider_type == ProviderType.CUSTOM:
        raise ValueError("自定义提供商需要指定base_url")

    # 确定model
    if not model:
        model = config.get("default_model", "glm-4.7")

    return OpenAIClient(api_key=api_key, base_url=base_url, model=model)
