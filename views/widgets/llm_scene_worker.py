#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM Scene Worker
通过智谱AI GLM-4.7 生成场景列表的Worker线程
"""

from PyQt6.QtCore import QObject, pyqtSignal
from typing import List, Dict, Any
import json
import sys
from pathlib import Path

# 添加CLI模块路径
_cli_path = Path(__file__).parent.parent.parent.parent / "video-generator-cli"
if _cli_path.exists():
    sys.path.insert(0, str(_cli_path))

try:
    from api_client import OpenAIClient
    API_CLIENT_AVAILABLE = True
except ImportError:
    API_CLIENT_AVAILABLE = False

try:
    from api_config import APIConfig
    API_CONFIG_AVAILABLE = True
except ImportError:
    API_CONFIG_AVAILABLE = False

# 向导中硬编码的 fallback 模板
_FALLBACK_TEMPLATES = {
    "产品": [
        "开场：展示用户面临的痛点或问题",
        "产品登场：展示产品外观和特征",
        "功能演示1：展示核心功能的使用",
        "功能演示2：展示其他实用功能",
        "用户反馈：展示使用后的满意效果",
        "应用场景：展示在不同场景下的使用",
        "总结：强调产品的优势和购买方式",
    ],
    "教程": [
        "开场介绍：说明将要学习的内容",
        "准备工作：展示所需的工具或材料",
        "步骤1：详细演示第一步",
        "步骤2：详细演示第二步",
        "步骤3：详细演示第三步",
        "注意事项：提醒常见问题",
        "完成效果：展示最终成果",
    ],
    "默认": [
        "开场介绍，展示主题或问题",
        "背景说明，介绍相关信息",
        "核心内容展示",
        "细节演示或说明",
        "效果展示或对比",
        "总结回顾",
        "行动号召或结尾",
    ],
}

_SYSTEM_PROMPT = """你是一个专业的视频场景规划师兼AI绘图提示词专家。根据用户提供的项目信息，生成一个JSON数组格式的场景列表。

要求：
1. 每个场景包含以下字段：id, description, duration, shot_type, camera_movement, image_prompt, video_prompt
2. id 从1开始递增
3. duration 单位为秒，默认5秒
4. shot_type 可选值：远景、全景、中景、近景、特写
5. camera_movement 可选值：固定、推、拉、摇、移、跟
6. description：中文，简要描述该场景的内容（给人看的）
7. image_prompt：英文，给AI图片生成模型的详细视觉提示词。要求：
   - 详细描述画面构图、色彩、光影、主体、背景、氛围
   - 融入项目中的角色外貌、服装、场景风格等细节
   - 适合 16:9 横屏构图
   - 不需要加 --ratio 等参数
8. video_prompt：英文，给AI视频生成模型的提示词。要求：
   - 描述画面中的运动、镜头变化、角色动作
   - 包含 camera_movement 对应的英文镜头运动描述
   - 不需要加 --ratio 等参数

返回纯JSON数组，不要包含其他文字说明。示例格式：
```json
[
  {{"id": 1, "description": "开场：展示用户面临的痛点", "duration": 5, "shot_type": "全景", "camera_movement": "推", "image_prompt": "A frustrated young man in a blue sportswear sitting at a desk, rubbing his temples, warm indoor lighting, realistic style, cinematic composition", "video_prompt": "Camera slowly pushes in on a frustrated young man at his desk, he rubs his temples, warm indoor lighting, cinematic shot"}},
  {{"id": 2, "description": "产品登场：展示智能手表外观", "duration": 5, "shot_type": "特写", "camera_movement": "固定", "image_prompt": "Close-up of a sleek smartwatch on a white surface, screen glowing with health data, soft studio lighting, product photography style, clean background", "video_prompt": "Static close-up shot of a smartwatch display turning on, health data animations appear on screen, product showcase style"}}
]
```"""


class LLMSceneWorker(QObject):
    """在后台线程中调用LLM生成场景"""

    finished = pyqtSignal(list)   # List[Dict] 场景列表
    error = pyqtSignal(str)       # 错误信息

    def __init__(self, api_key: str, base_url: str,
                 project_data: Dict[str, Any], scene_count: int):
        super().__init__()
        self._api_key = api_key
        self._base_url = base_url
        self._project_data = project_data
        self._scene_count = scene_count

    def run(self):
        """执行LLM场景生成"""
        try:
            if not API_CLIENT_AVAILABLE:
                self.error.emit("API客户端不可用")
                return

            client = OpenAIClient(
                api_key=self._api_key,
                base_url=self._base_url,
                model="glm-4.7"
            )

            # 构造用户消息
            user_msg = self._build_user_message()

            messages = [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ]

            response = client.chat_completion(messages, model="glm-4.7")

            # 解析响应 - 兼容标准OpenAI格式和智谱AI格式
            content = ""
            if isinstance(response, dict):
                # 智谱AI: content 直接在顶层
                content = response.get("content", "")
                if not content:
                    # OpenAI标准格式: choices[0].message.content
                    choices = response.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
            elif isinstance(response, str):
                content = response

            if not content:
                self.error.emit("LLM返回空内容")
                return

            scenes = self._parse_json_response(content)

            if not scenes:
                self.error.emit("无法解析LLM响应为场景列表")
                return

            # 确保 scene 数量与要求一致
            scenes = scenes[:self._scene_count]
            while len(scenes) < self._scene_count:
                idx = len(scenes) + 1
                scenes.append({
                    "id": idx,
                    "description": f"场景{idx}内容",
                    "duration": 5,
                    "shot_type": "中景",
                    "camera_movement": "固定",
                })

            # 重新编号
            for i, s in enumerate(scenes):
                s["id"] = i + 1

            self.finished.emit(scenes)

        except Exception as e:
            self.error.emit(f"LLM生成失败: {str(e)}")

    def _build_user_message(self) -> str:
        """构造发送给LLM的用户消息"""
        parts = []

        title = self._project_data.get("project_name", "")
        if title:
            parts.append(f"项目标题：{title}")

        desc = self._project_data.get("project_description", "")
        if desc:
            parts.append(f"项目描述：{desc}")

        char = self._project_data.get("character", {})
        if self._project_data.get("has_main_character") and char:
            age = char.get("age", "")
            gender = char.get("gender", "")
            appearance = char.get("appearance", "")
            personality = char.get("personality", "")
            if age or gender:
                parts.append(f"主角设定：{age}{gender}，{appearance}，性格{personality}")

        video = self._project_data.get("video", {})
        if video:
            style = video.get("style", "写实风格")
            ratio = video.get("aspect_ratio", "16:9")
            parts.append(f"视频风格：{style}，比例：{ratio}")

        parts.append(f"请生成 {self._scene_count} 个场景")
        parts.append("注意：image_prompt 和 video_prompt 必须是英文，要详细、有画面感，融入项目描述中的关键元素。")

        return "\n".join(parts)

    def _parse_json_response(self, content: str) -> List[Dict[str, Any]]:
        """解析LLM返回的JSON，处理markdown code fence"""
        text = content.strip()

        # 去除 markdown code fence
        if "```" in text:
            # 提取 ``` ... ``` 之间的内容
            start = text.find("```")
            end = text.rfind("```")
            if start != end:
                inner = text[start:end + 3]
                # 去掉 ```json 或 ``` 行
                lines = inner.split("\n")
                cleaned = []
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith("```"):
                        continue
                    cleaned.append(line)
                text = "\n".join(cleaned).strip()

        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            return []

        if isinstance(result, list):
            # 验证每个元素
            valid = []
            for item in result:
                if isinstance(item, dict) and "description" in item:
                    desc = item.get("description", "")
                    scene = {
                        "id": item.get("id", len(valid) + 1),
                        "description": desc,
                        "duration": item.get("duration", 5),
                        "shot_type": item.get("shot_type", "中景"),
                        "camera_movement": item.get("camera_movement", "固定"),
                        "image_prompt": item.get("image_prompt", ""),
                        "video_prompt": item.get("video_prompt", ""),
                    }
                    valid.append(scene)
            return valid

        return []

    @staticmethod
    def get_fallback_scenes(description: str, count: int) -> List[Dict[str, Any]]:
        """硬编码 fallback 场景列表"""
        if "产品" in description or "功能" in description:
            templates = _FALLBACK_TEMPLATES["产品"]
        elif "教程" in description or "教学" in description:
            templates = _FALLBACK_TEMPLATES["教程"]
        else:
            templates = _FALLBACK_TEMPLATES["默认"]

        scenes = []
        for i in range(count):
            if i < len(templates):
                desc = templates[i]
            else:
                desc = f"场景{i+1}内容"
            scenes.append({
                "id": i + 1,
                "description": desc,
                "duration": 5,
                "shot_type": "中景",
                "camera_movement": "固定",
            })
        return scenes
