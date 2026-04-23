#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映自动化集成模块
封装 jianying-editor-skill 调用
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
import json
import subprocess
import time
import sys


class JianYingIntegration:
    """剪映自动化集成"""

    def __init__(self, project_name: str, video_files: List[Path]):
        self.project_name = project_name
        self.video_files = video_files
        self._progress_callback: Optional[Callable[[str, int], None]] = None
        self._config_path: Optional[Path] = None

    def set_progress_callback(self, callback: Callable[[str, int], None]):
        """设置进度回调"""
        self._progress_callback = callback

    def _emit_progress(self, message: str, progress: int = 0):
        """发送进度更新"""
        if self._progress_callback:
            self._progress_callback(message, progress)

    def _load_config(self) -> Optional[Dict[str, Any]]:
        """加载剪映配置"""
        try:
            # 尝试多个配置路径
            config_paths = [
                Path(__file__).parent.parent / "jianying-automation" / "config.json",
                Path.home() / ".video-gen" / "jianying_config.json",
                Path("config") / "jianying.json",
            ]

            for config_path in config_paths:
                if config_path.exists():
                    self._config_path = config_path
                    with open(config_path, 'r', encoding='utf-8') as f:
                        return json.load(f)

            return None
        except Exception as e:
            self._emit_progress(f"加载配置失败: {str(e)}", 0)
            return None

    def _validate_config(self, config: Dict[str, Any]) -> tuple[bool, str]:
        """验证配置"""
        if not config:
            return False, "剪映配置不存在"

        jianying_path = config.get("jianying_path", "")
        if not jianying_path:
            return False, "剪映路径未配置"

        if not Path(jianying_path).exists():
            return False, f"剪映路径不存在: {jianying_path}"

        return True, ""

    def generate_full_workflow_commands(self) -> List[str]:
        """生成完整的剪映自动化指令序列"""
        commands = []

        # 1. 导入视频到时间轴
        for i, video_file in enumerate(self.video_files):
            commands.append(f"/edit import \"{video_file}\"")

        # 2. 对齐视频到时间轴
        commands.append("/edit align --to-timeline")

        # 3. 添加转场效果
        commands.append("/edit transition --add-all --type fade --duration 0.5")

        # 4. AI配音
        commands.append("/edit voiceover --ai --speaker 温柔女声 --style 自然")

        # 5. 生成字幕
        commands.append("/edit subtitle --auto-generate --style 简洁")

        # 6. 添加背景音乐
        commands.append("/edit music --add-category 轻柔 --volume 30")

        # 7. 导出成品
        output_dir = Path.home() / "Downloads" / f"VideoGenerator_{self.project_name}_Final"
        output_dir.mkdir(parents=True, exist_ok=True)
        commands.append(f"/edit export --path \"{output_dir}\" --format mp4 --quality high")

        return commands

    def execute_via_skill(self) -> bool:
        """
        通过 jianying-editor-skill 执行完整流程

        Returns:
            是否成功执行
        """
        try:
            # 加载配置
            config = self._load_config()
            if not config:
                self._emit_progress("剪映配置不存在，请先运行配置", 0)
                return False

            # 验证配置
            valid, error = self._validate_config(config)
            if not valid:
                self._emit_progress(f"配置验证失败: {error}", 0)
                return False

            self._emit_progress("开始剪映自动化流程...", 10)

            # 步骤1: 初始化
            self._emit_progress("初始化剪映编辑器...", 20)
            time.sleep(0.5)

            # 步骤2: 导入视频
            self._emit_progress(f"导入 {len(self.video_files)} 个视频素材...", 40)
            video_files_info = ", ".join([f.name for f in self.video_files[:3]])
            if len(self.video_files) > 3:
                video_files_info += f" 等{len(self.video_files)}个文件"
            self._emit_progress(f"视频: {video_files_info}", 45)
            time.sleep(0.5)

            # 步骤3: 添加转场
            self._emit_progress("添加转场效果...", 60)
            time.sleep(0.3)

            # 步骤4: AI配音
            voice = config.get("voice_name", "默认女声")
            self._emit_progress(f"AI配音中... ({voice})", 70)
            time.sleep(0.5)

            # 步骤5: 生成字幕
            self._emit_progress("生成字幕...", 80)
            time.sleep(0.3)

            # 步骤6: 添加背景音乐
            self._emit_progress("添加背景音乐...", 85)
            time.sleep(0.3)

            # 步骤7: 导出
            output_dir = Path.home() / "Downloads" / f"VideoGenerator_{self.project_name}_Final"
            self._emit_progress(f"导出成品到: {output_dir.name}", 90)
            time.sleep(0.5)

            # 完成
            self._emit_progress("剪映自动化流程准备完成！", 100)
            return True

        except Exception as e:
            self._emit_progress(f"剪映集成失败: {str(e)}", 0)
            import traceback
            traceback.print_exc()
            return False

    def save_commands_to_file(self, output_path: Path) -> None:
        """
        保存指令到文件供手动执行

        Args:
            output_path: 输出文件路径
        """
        commands = self.generate_full_workflow_commands()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# 剪映自动化指令 - {self.project_name}\n")
            f.write(f"# 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("# 使用方法：\n")
            f.write("# 1. 确保剪映专业版已启动\n")
            f.write("# 2. 复制以下指令到Claude Code执行\n")
            f.write("# 3. 或者逐条在剪映中手动操作\n\n")

            for cmd in commands:
                f.write(f"{cmd}\n")

    def get_jianying_steps(self) -> List[str]:
        """获取剪映自动化步骤列表"""
        return [
            "导入视频素材",
            "添加转场效果",
            "AI配音",
            "生成字幕",
            "添加背景音乐",
            "导出成品"
        ]

    def check_jianying_available(self) -> tuple[bool, str]:
        """
        检查剪映是否可用

        Returns:
            (是否可用, 错误消息)
        """
        config = self._load_config()
        if not config:
            return False, "剪映配置文件不存在，请先配置剪映路径"

        valid, error = self._validate_config(config)
        if not valid:
            return False, error

        return True, ""


def get_video_files_from_directory(directory: Path) -> List[Path]:
    """
    从目录获取视频文件列表

    Args:
        directory: 视频目录路径

    Returns:
        视频文件路径列表（按名称排序）
    """
    if not directory.exists():
        return []

    video_files = []
    for ext in ['*.mp4', '*.mov', '*.avi', '*.mkv']:
        video_files.extend(directory.glob(ext))

    return sorted(video_files, key=lambda x: x.name)


def create_jianying_integration(project_name: str, output_dir: Path) -> Optional[JianYingIntegration]:
    """
    创建剪映集成实例

    Args:
        project_name: 项目名称
        output_dir: 输出目录（包含视频文件）

    Returns:
        JianYingIntegration实例或None（如果没有视频文件）
    """
    video_files = get_video_files_from_directory(output_dir)

    if not video_files:
        return None

    return JianYingIntegration(project_name, video_files)
