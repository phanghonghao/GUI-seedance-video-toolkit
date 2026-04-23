#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video Generation ViewModel
"""

from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty, QThread
from typing import List, Dict, Optional, Any
from pathlib import Path
import json
from datetime import datetime
import time
import threading
import os
import shutil
import logging
import re

# 配置日志
logger = logging.getLogger(__name__)


def _clean_prompt(prompt: str) -> str:
    """清理 prompt 中的 CLI 参数（--ratio, --style 等）"""
    cleaned = re.sub(r'\s+--\w+\s+\S+', '', prompt)
    return cleaned.strip()

from .base_viewmodel import BaseViewModel
import sys

# 添加CLI模块路径
_cli_path = Path(__file__).parent.parent / "video-generator-cli"
if _cli_path.exists():
    sys.path.insert(0, str(_cli_path))

try:
    from commands.init import ProjectConfig
    from api_config import APIConfig
except ImportError:
    ProjectConfig = None
    APIConfig = None

# 尝试导入API客户端
try:
    from api_client import OpenAIClient
    API_CLIENT_AVAILABLE = True
except ImportError:
    API_CLIENT_AVAILABLE = False

# 导入剪映集成模块
try:
    from jianying_integration import JianYingIntegration, create_jianying_integration
    JIANYING_AVAILABLE = True
except ImportError:
    JIANYING_AVAILABLE = False


def get_user_download_dir() -> Path:
    """获取用户下载目录"""
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        # 使用 SHGetKnownFolderPath 获取 Downloads 文件夹
        # FOLDERID_Downloads = {374DE290-123F-4565-9164-39C4925E467B}
        SHGetKnownFolderPath = ctypes.windll.shell32.SHGetKnownFolderPath
        SHGetKnownFolderPath.argtypes = [
            ctypes.c_void_p,  # rfid: REFKNOWNFOLDERID*
            ctypes.c_uint32,  # dwFlags: DWORD
            ctypes.c_void_p,  # hToken: HANDLE
            ctypes.POINTER(ctypes.c_wchar_p)  # ppszPath: PWSTR*
        ]

        # FOLDERID_Downloads GUID
        FOLDERID_Downloads = ctypes.create_unicode_buffer(
            "{374DE290-123F-4565-9164-39C4925E467B}"
        )

        path_ptr = ctypes.c_wchar_p()
        result = SHGetKnownFolderPath(
            FOLDERID_Downloads,
            0,
            None,
            ctypes.byref(path_ptr)
        )

        if result == 0:  # S_OK
            path = Path(path_ptr.value)
            # 释放由 SHGetKnownFolderPath 分配的内存
            ctypes.windll.ole32.CoTaskMemFree(path_ptr)
            return path
        else:
            # 回退到使用用户主目录/Downloads
            home = Path.home()
            download_dir = home / "Downloads"
            return download_dir if download_dir.exists() else home
    else:
        # macOS/Linux
        home = Path.home()
        download_dir = home / "Downloads"
        return download_dir if download_dir.exists() else home


class GenerationViewModel(BaseViewModel):
    """视频生成ViewModel"""

    # 生成进度信号
    dataChanged = pyqtSignal()
    progressChanged = pyqtSignal(int, str)  # progress, message
    sceneProgressChanged = pyqtSignal(int, int, str)  # current, total, message
    generationCompleted = pyqtSignal(bool, str)  # success, message
    referenceImageGenerated = pyqtSignal(str, str)  # scene_id, image_path
    videoGenerated = pyqtSignal(str, str)  # scene_id, video_path

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self._project_name: str = ""
        self._total_scenes: int = 0
        self._current_scene: int = 0
        self._progress: int = 0
        self._status_message: str = "就绪"
        self._selected_scenes: List[int] = []
        self._generation_step: int = 0  # 0=全部, 1=参考图, 2=视频, 3=合并
        self._continue_mode: bool = False
        self._force_mode: bool = False
        self._final_output_dir: str = ""  # 最终输出目录

    # ===== Property =====

    def projectName(self) -> str:
        return self._project_name

    def setProjectName(self, name: str):
        self._project_name = name

    projectName = pyqtProperty(str, fget=projectName, fset=setProjectName, notify=dataChanged)

    def progress(self) -> int:
        return self._progress

    def setProgress(self, value: int):
        if self._progress != value:
            self._progress = value
            self.progressChanged.emit(value, self._status_message)

    progress = pyqtProperty(int, fget=progress, fset=setProgress, notify=progressChanged)

    def statusMessage(self) -> str:
        return self._status_message

    def setStatusMessage(self, message: str):
        if self._status_message != message:
            self._status_message = message
            self.progressChanged.emit(self._progress, message)

    statusMessage = pyqtProperty(str, fget=statusMessage, fset=setStatusMessage, notify=progressChanged)

    def totalScenes(self) -> int:
        return self._total_scenes

    def setTotalScenes(self, count: int):
        self._total_scenes = count

    totalScenes = pyqtProperty(int, fget=totalScenes, fset=setTotalScenes, notify=dataChanged)

    def currentScene(self) -> int:
        return self._current_scene

    currentScene = pyqtProperty(int, fget=currentScene, notify=sceneProgressChanged)

    # ===== 生成配置 =====

    def setSelectedScenes(self, scenes: List[int]):
        """设置要生成的场景列表"""
        self._selected_scenes = scenes

    def getSelectedScenes(self) -> List[int]:
        """获取要生成的场景列表"""
        return self._selected_scenes.copy()

    def setGenerationStep(self, step: int):
        """设置生成步骤
        0=全部, 1=参考图, 2=视频, 3=合并, 4=报告
        """
        self._generation_step = step

    def getGenerationStep(self) -> int:
        return self._generation_step

    def setContinueMode(self, enabled: bool):
        """设置继续模式（跳过已存在的文件）"""
        self._continue_mode = enabled

    def setForceMode(self, enabled: bool):
        """设置强制模式（覆盖已有文件）"""
        self._force_mode = enabled

    # ===== 项目验证 =====

    def validateProject(self, project_name: str = None) -> tuple[bool, str]:
        """验证项目是否可以生成"""
        if project_name is None:
            project_name = self._project_name

        if not project_name:
            return False, "请先选择项目"

        if ProjectConfig is None:
            return False, "CLI模块未加载"

        try:
            manager = ProjectConfig(project_name)
            if not manager.config_exists():
                return False, f"项目不存在: {project_name}"

            config = manager.load_config()
            scenes = config.get("scenes", [])
            if not scenes:
                return False, "项目没有场景，请先添加场景"

            return True, ""

        except Exception as e:
            return False, f"验证项目失败: {str(e)}"

    # ===== API验证 =====

    def validateAPI(self) -> tuple[bool, str]:
        """验证API配置"""
        if APIConfig is None:
            return False, "CLI模块未加载"

        try:
            api_config = APIConfig()
            if not api_config.is_configured():
                return False, "API密钥未配置，请先配置API"

            return True, ""

        except Exception as e:
            return False, f"验证API失败: {str(e)}"

    # ===== 准备生成 =====

    def prepareGeneration(self, project_name: str = None) -> Dict[str, Any]:
        """
        准备生成，返回生成配置

        Returns:
            包含生成配置的字典，或None（失败时）
        """
        if project_name is None:
            project_name = self._project_name

        # 验证项目
        valid, error = self.validateProject(project_name)
        if not valid:
            self.set_error(error)
            return None

        # 验证API
        valid, error = self.validateAPI()
        if not valid:
            self.set_error(error)
            return None

        # 加载项目配置
        try:
            manager = ProjectConfig(project_name)
            config = manager.load_config()

            scenes = config.get("scenes", [])

            # 过滤场景
            if self._selected_scenes:
                scenes = [s for s in scenes if s.get("id") in self._selected_scenes]

            if not scenes:
                self.set_error("没有有效的场景可生成")
                return None

            self._total_scenes = len(scenes)

            generation_config = {
                "project_name": project_name,
                "project_config": config,
                "scenes": scenes,
                "output_dir": manager.get_output_dir(),
                "reference_dir": manager.get_reference_dir(),
                "video_dir": manager.get_video_dir(),
                "step": self._generation_step,
                "continue_mode": self._continue_mode,
                "force_mode": self._force_mode,
            }

            return generation_config

        except Exception as e:
            self.set_error(f"准备生成失败: {str(e)}")
            return None

    # ===== 开始生成 =====

    def startGeneration(self, project_name: str = None) -> bool:
        """
        开始视频生成

        Returns:
            是否成功启动
        """
        gen_config = self.prepareGeneration(project_name)
        if gen_config is None:
            return False

        # 重置进度
        self._current_scene = 0
        self.setProgress(0)
        self.setStatusMessage("准备生成...")

        # 在后台线程执行生成
        self._generation_thread = threading.Thread(
            target=self._run_generation,
            args=(gen_config,),
            daemon=True
        )
        self._generation_thread.start()

        return True

    def _run_generation(self, config: Dict[str, Any]):
        """
        运行视频生成（在后台线程中执行）
        """
        try:
            project_name = config["project_name"]
            scenes = config["scenes"]
            api_config = APIConfig()

            # 获取API配置 - 拆分为双provider
            paratera_key = api_config.get_api_key("并行科技")
            paratera_url = api_config.get_base_url("并行科技")
            zhipu_key = api_config.get_api_key("智谱AI")
            zhipu_url = api_config.get_base_url("智谱AI")

            if not paratera_key or not paratera_url:
                self.set_error("并行科技API配置不完整")
                self.generationCompleted.emit(False, "并行科技API配置不完整，请检查API配置")
                return

            # 创建双客户端
            if API_CLIENT_AVAILABLE:
                paratera_client = OpenAIClient(
                    api_key=paratera_key,
                    base_url=paratera_url
                )
                zhipu_client = None
                if zhipu_key and zhipu_url:
                    zhipu_client = OpenAIClient(
                        api_key=zhipu_key,
                        base_url=zhipu_url,
                        model="glm-4.7"
                    )
            else:
                paratera_client = None
                zhipu_client = None

            # 步骤0: 准备生成
            self._current_scene = 0
            self.setProgress(5)
            self.setStatusMessage("准备生成环境...")
            self.sceneProgressChanged.emit(0, len(scenes), "准备生成")
            time.sleep(0.5)

            # 根据步骤决定执行哪些操作
            step = config.get("step", 0)

            # 加载视频风格配置，用于 fallback prompt
            video_style = config.get("project_config", {}).get("video", {}).get("style", "写实风格")

            # 从项目配置提取角色信息，用于增强 fallback prompt
            character = config.get("project_config", {}).get("character", {})
            char_info = ""
            if character.get("enabled"):
                parts = [p for p in [
                    character.get("age", ""),
                    character.get("gender", ""),
                ] if p]
                if parts:
                    char_info = ", " + " ".join(parts) + " person"
                if character.get("appearance"):
                    char_info += f", {character['appearance']}"
                if character.get("personality"):
                    char_info += f", {character['personality']} personality"
                logger.info(f"角色信息已加载: {char_info}")

            # 风格文本映射
            style_text = "实景" if "写实" in video_style or "产品" in video_style else "动画风格"

            # 记录 scenes 的 prompt 情况
            for scene in scenes:
                sid = scene.get("id", "?")
                has_img = bool(scene.get("image_prompt", ""))
                has_vid = bool(scene.get("video_prompt", ""))
                logger.info(f"场景{sid}: image_prompt={'✅' if has_img else '❌'}, video_prompt={'✅' if has_vid else '❌'}")

            # 步骤1: 生成参考图（如果需要）
            # 存储图片URL供视频生成步骤使用
            image_urls = {}

            if step in [0, 1]:
                self.setProgress(10)
                self.setStatusMessage("生成参考图...")
                self.sceneProgressChanged.emit(1, len(scenes) + 1, "生成参考图")

                for i, scene in enumerate(scenes):
                    scene_id = scene.get("id", i + 1)
                    scene_desc = scene.get("description", "")

                    self.setStatusMessage(f"场景{scene_id}: {scene_desc[:20]}...")
                    self.progressChanged.emit(10 + int(20 * (i + 1) / len(scenes)), f"生成场景{scene_id}参考图")

                    # 调用API生成图片
                    try:
                        if API_CLIENT_AVAILABLE:
                            # 优先使用智谱AI生成的 prompt，否则 fallback
                            raw_image_prompt = scene.get("image_prompt", "")
                            if raw_image_prompt:
                                image_prompt = _clean_prompt(raw_image_prompt)
                                logger.info(f"场景{scene_id}: 使用智谱AI生成的 image_prompt")
                                self.progressChanged.emit(0, f"场景{scene_id}: 使用AI生成Prompt生成图片")
                            else:
                                image_prompt = f"{scene_desc}{char_info}, {style_text} cinematic photography, professional lighting, 16:9, high quality"
                                logger.info(f"场景{scene_id}: 使用 fallback image_prompt (含角色信息)")
                                self.progressChanged.emit(0, f"场景{scene_id}: 使用默认Prompt生成图片")
                            self.progressChanged.emit(0, f"调用API生成场景{scene_id}图片...")
                            response = paratera_client.generate_image(
                                prompt=image_prompt,
                                model="Doubao-Seedream-3.0-T2I"
                            )

                            # 检查错误
                            if "error" in response:
                                error_msg = response.get("error", "未知错误")
                                self.progressChanged.emit(0, f"❌ 场景{scene_id}图片生成失败: {error_msg}")
                                logger.error(f"Image generation error: {error_msg}")
                                continue

                            # 创建参考图目录
                            ref_dir = Path(config.get("reference_dir", ""))
                            ref_dir.mkdir(parents=True, exist_ok=True)

                            # 保存图片
                            if response.get("images"):
                                import urllib.request
                                img_url = response["images"][0]
                                # 存储URL供视频生成使用
                                image_urls[scene_id] = img_url
                                img_path = ref_dir / f"scene_{scene_id}.png"

                                try:
                                    urllib.request.urlretrieve(img_url, img_path)
                                    self.referenceImageGenerated.emit(str(scene_id), str(img_path))
                                    self.progressChanged.emit(0, f"✅ 场景{scene_id}参考图已保存")
                                except Exception as download_err:
                                    self.progressChanged.emit(0, f"❌ 下载图片失败: {str(download_err)}")
                                    logger.error(f"Download error: {download_err}")
                            else:
                                self.progressChanged.emit(0, f"❌ 场景{scene_id}: API未返回图片")

                    except Exception as e:
                        self.progressChanged.emit(0, f"❌ 场景{scene_id}图片生成异常: {str(e)}")
                        logger.error(f"Image generation exception: {e}", exc_info=True)

                self.setProgress(30)
                self.sceneProgressChanged.emit(2, len(scenes) + 1, "参考图生成完成")

            # 步骤2: 生成视频
            if step in [0, 2]:
                self.setProgress(35)
                self.setStatusMessage("生成视频片段...")
                self.sceneProgressChanged.emit(3, len(scenes) + 1, "生成视频")

                video_dir = Path(config.get("video_dir", ""))
                video_dir.mkdir(parents=True, exist_ok=True)

                for i, scene in enumerate(scenes):
                    scene_id = scene.get("id", i + 1)
                    scene_desc = scene.get("description", "")

                    self.setStatusMessage(f"场景{scene_id}: 生成视频...")
                    self.progressChanged.emit(35 + int(40 * (i + 1) / len(scenes)), f"生成场景{scene_id}视频")

                    try:
                        if API_CLIENT_AVAILABLE:
                            raw_video_prompt = scene.get("video_prompt", "")
                            if raw_video_prompt:
                                video_prompt = _clean_prompt(raw_video_prompt)
                                logger.info(f"场景{scene_id}: 使用智谱AI生成的 video_prompt")
                            else:
                                video_prompt = f"{scene_desc}{char_info}, cinematic motion, smooth camera, 16:9, high quality video"
                                logger.info(f"场景{scene_id}: 使用 fallback video_prompt (含角色信息)")
                            content = [
                                {"type": "text", "text": video_prompt}
                            ]

                            # 如果有参考图URL，添加到content中（API需要HTTP URL）
                            if scene_id in image_urls:
                                content.append({
                                    "type": "image_url",
                                    "image_url": {"url": image_urls[scene_id]}
                                })

                            self.progressChanged.emit(0, f"调用API生成场景{scene_id}视频...")
                            response = paratera_client.generate_video(
                                content=content,
                                model="Doubao-Seedance-1.0-Pro"
                            )

                            # 检查错误
                            if "error" in response:
                                error_msg = response.get("error", "未知错误")
                                self.progressChanged.emit(0, f"❌ 场景{scene_id}视频任务创建失败: {error_msg}")
                                logger.error(f"Video generation error: {error_msg}")
                                continue

                            # 保存任务ID并轮询结果
                            task_id = response.get("task_id")
                            if task_id:
                                self.progressChanged.emit(0, f"✅ 视频任务已创建: {task_id[:8]}...")

                                # 轮询任务状态
                                max_wait = 300  # 5分钟超时
                                wait_time = 0
                                while wait_time < max_wait:
                                    time.sleep(5)
                                    wait_time += 5

                                    status_resp = paratera_client.query_video_task(task_id)

                                    # 检查状态 — API 返回 "items" 列表
                                    items = status_resp.get("items") or status_resp.get("data") or []
                                    if items:
                                        task_data = items[0]
                                        task_status = task_data.get("status", "")

                                        if task_status == "succeeded":
                                            # 下载视频 — URL 在 content.video_url
                                            video_url = (task_data.get("content") or {}).get("video_url")
                                            if video_url:
                                                import urllib.request
                                                video_path = video_dir / f"scene_{scene_id}.mp4"
                                                urllib.request.urlretrieve(video_url, video_path)
                                                self.progressChanged.emit(0, f"✅ 场景{scene_id}视频已保存")
                                                self.videoGenerated.emit(str(scene_id), str(video_path))
                                                break
                                        elif task_status == "failed":
                                            self.progressChanged.emit(0, f"❌ 场景{scene_id}视频生成失败")
                                            break
                                        elif task_status == "processing":
                                            self.progressChanged.emit(0, f"场景{scene_id}处理中... ({wait_time}s)")
                                    else:
                                        logger.warning(f"No data in status response: {status_resp}")
                            else:
                                self.progressChanged.emit(0, f"❌ 场景{scene_id}: API未返回任务ID")

                    except Exception as e:
                        self.progressChanged.emit(0, f"❌ 场景{scene_id}视频生成异常: {str(e)}")
                        logger.error(f"Video generation exception: {e}", exc_info=True)

                self.setProgress(75)
                self.sceneProgressChanged.emit(4, len(scenes) + 1, "视频生成完成")

            # 步骤3: 整理视频文件到下载文件夹
            if step in [0, 3]:
                self.setProgress(80)
                self.setStatusMessage("整理视频文件...")
                self.sceneProgressChanged.emit(5, len(scenes) + 1, "整理文件")

                video_dir = Path(config.get("video_dir", ""))

                # 获取用户下载目录
                download_dir = get_user_download_dir()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                final_output_dir = download_dir / f"VideoGenerator_{project_name}_{timestamp}"
                final_output_dir.mkdir(parents=True, exist_ok=True)

                # 列出已生成的视频
                video_files = list(video_dir.glob("scene_*.mp4"))
                self.progressChanged.emit(0, f"共生成 {len(video_files)} 个视频片段")

                # 复制视频文件到 视频/ 子目录
                video_output_dir = final_output_dir / "视频"
                video_output_dir.mkdir(exist_ok=True)
                for vf in sorted(video_files):
                    dest = video_output_dir / vf.name
                    shutil.copy2(vf, dest)
                    self.progressChanged.emit(0, f"已复制: {vf.name}")

                # 复制参考图到 图片/ 子目录
                ref_dir = Path(config.get("reference_dir", ""))
                image_output_dir = final_output_dir / "图片"
                image_output_dir.mkdir(exist_ok=True)

                ref_files = list(ref_dir.glob("scene_*.png")) + list(ref_dir.glob("scene_*.jpg"))
                for rf in sorted(ref_files):
                    dest = image_output_dir / rf.name
                    shutil.copy2(rf, dest)

                # 生成说明文件
                readme_path = final_output_dir / "使用说明.txt"
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(f"项目: {project_name}\n")
                    f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"场景数量: {len(video_files)}\n")
                    f.write(f"\n视频文件 (视频/):\n")
                    for vf in sorted(video_files):
                        f.write(f"  - {vf.name}\n")
                    f.write(f"\n参考图 (图片/): {len(ref_files)} 张\n")
                    f.write(f"\n下一步:\n")
                    f.write(f"1. 使用剪映、Premiere等视频编辑软件打开视频文件\n")
                    f.write(f"2. 按场景顺序拼接视频片段\n")
                    f.write(f"3. 添加转场效果和背景音乐\n")
                    f.write(f"4. 导出最终视频\n")

                self.progressChanged.emit(0, f"文件已保存到: {final_output_dir}")
                self.setProgress(90)
                self.sceneProgressChanged.emit(6, len(scenes) + 1, "整理完成")

                # 保存最终输出目录路径供后续使用
                self._final_output_dir = str(final_output_dir)

            # 步骤4: 生成报告
            if step in [0, 4]:
                self.setProgress(95)
                self.setStatusMessage("生成报告...")
                self.sceneProgressChanged.emit(7, len(scenes) + 1, "生成报告")

                # 报告也保存到下载目录
                download_dir = get_user_download_dir()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_dir = download_dir / f"VideoGenerator_{project_name}_{timestamp}"
                report_dir.mkdir(parents=True, exist_ok=True)

                report = {
                    "project": project_name,
                    "generated_at": datetime.now().isoformat(),
                    "scenes_count": len(scenes),
                    "step": step,
                    "status": "completed",
                    "output_directory": str(report_dir)
                }

                report_path = report_dir / "generation_report.json"
                with open(report_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)

                self._final_output_dir = str(report_dir)
                self.setProgress(100)
                self.sceneProgressChanged.emit(8, len(scenes) + 1, "报告完成")

            # 步骤5: 剪映自动化（可选）
            if step in [0, 5] and JIANYING_AVAILABLE:
                self.setProgress(100)
                self.setStatusMessage("准备剪映自动化...")
                self.sceneProgressChanged.emit(9, len(scenes) + 2, "剪映集成")

                # 收集生成的视频文件
                video_dir = Path(config.get("video_dir", ""))
                video_files = list(video_dir.glob("scene_*.mp4"))

                # 确定输出目录（使用之前保存的或创建新的）
                if hasattr(self, '_final_output_dir') and self._final_output_dir:
                    output_dir = Path(self._final_output_dir)
                else:
                    # 创建新的输出目录
                    download_dir = get_user_download_dir()
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_dir = download_dir / f"VideoGenerator_{project_name}_{timestamp}"
                    output_dir.mkdir(parents=True, exist_ok=True)
                    self._final_output_dir = str(output_dir)

                if video_files:
                    # 创建剪映集成实例
                    jy = JianYingIntegration(project_name, video_files)

                    # 检查剪映是否可用
                    available, error_msg = jy.check_jianying_available()

                    if available:
                        # 设置进度回调
                        def jy_progress(msg, prog):
                            self.progressChanged.emit(prog, f"剪映: {msg}")

                        jy.set_progress_callback(jy_progress)

                        # 执行剪映自动化
                        if jy.execute_via_skill():
                            self.progressChanged.emit(0, "剪映自动化准备完成！")
                            self.sceneProgressChanged.emit(10, len(scenes) + 2, "剪映完成")
                        else:
                            # 自动化失败，保存指令供手动执行
                            cmd_file = output_dir / "jianying_commands.txt"
                            jy.save_commands_to_file(cmd_file)
                            self.progressChanged.emit(0, f"剪映指令已保存到: {cmd_file.name}")
                    else:
                        # 配置不可用，保存指令供手动执行
                        cmd_file = output_dir / "jianying_commands.txt"
                        jy.save_commands_to_file(cmd_file)
                        self.progressChanged.emit(0, f"剪映未配置: {error_msg}，指令已保存到: {cmd_file.name}")

            # 完成
            self.setProgress(100)
            self.setStatusMessage("生成完成！")
            self.sceneProgressChanged.emit(len(scenes) + 1, len(scenes) + 1, "完成")

            # 构建完成消息，包含输出目录
            output_location = self._final_output_dir if hasattr(self, '_final_output_dir') else "下载目录"

            # 根据执行步骤添加不同的完成信息
            if step == 5 and JIANYING_AVAILABLE:
                completion_msg = f"项目 {project_name} 生成完成！\n\n文件已保存到:\n{output_location}\n\n剪映自动化指令已生成，请使用剪映编辑器导入视频并进行后续编辑。"
            else:
                completion_msg = f"项目 {project_name} 生成完成！\n\n文件已保存到:\n{output_location}"

            self.generationCompleted.emit(True, completion_msg)

        except Exception as e:
            self.set_error(f"生成失败: {str(e)}")
            self.generationCompleted.emit(False, f"生成失败: {str(e)}")
            import traceback
            traceback.print_exc()

    # ===== 导出剪映指令 =====

    def exportJianyingCommands(self, project_name: str = None, output_file: Path = None) -> bool:
        """
        导出剪映自动化指令

        Args:
            project_name: 项目名称
            output_file: 输出文件路径

        Returns:
            是否成功
        """
        if project_name is None:
            project_name = self._project_name

        valid, error = self.validateProject(project_name)
        if not valid:
            self.set_error(error)
            return False

        try:
            manager = ProjectConfig(project_name)
            config = manager.load_config()
            scenes = config.get("scenes", [])

            # 生成剪映指令
            commands = []
            commands.append(f"# 剪映自动化指令 - {project_name}")
            commands.append(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            commands.append("")

            for i, scene in enumerate(scenes):
                desc = scene.get("description", "")
                duration = scene.get("duration", 5)
                shot_type = scene.get("shot_type", "中景")
                angle = scene.get("angle", "正面")

                commands.append(f"# 场景 {i+1}: {desc}")
                commands.append(f"# 景别: {shot_type}, 角度: {angle}, 时长: {duration}秒")

                # 这里可以生成实际的剪映指令
                # commands.append(f"import_video scene_{i+1}.mp4")

                commands.append("")

            content = "\n".join(commands)

            if output_file is None:
                output_file = Path(f"jianying_{project_name}.txt")

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)

            self.set_success(f"剪映指令已导出到: {output_file}")
            return True

        except Exception as e:
            self.set_error(f"导出剪映指令失败: {str(e)}")
            return False

    # ===== 取消生成 =====

    def cancelGeneration(self):
        """取消生成"""
        self.setStatusMessage("生成已取消")
        self.setProgress(0)
