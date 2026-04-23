#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video Generator Pro - Application Core
"""

import sys
import os
from pathlib import Path

# 设置Windows控制台UTF-8输出
if sys.platform == "win32":
    try:
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())
        os.environ['PYTHONIOENCODING'] = 'utf-8'
    except:
        pass

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QTranslator, QLocale
from PyQt6.QtGui import QFont, QIcon

from .theme import get_stylesheet


class VideoGeneratorApp(QApplication):
    """主应用程序类"""

    def __init__(self, argv):
        super().__init__(argv)

        # 设置应用属性
        self.setApplicationName("Video Generator Pro")
        self.setApplicationVersion("1.0.0")
        self.setOrganizationName("VideoGenerator")

        # Qt6自动支持高DPI缩放，无需手动设置

        # 设置默认字体
        font = QFont("Microsoft YaHei UI", 10)
        self.setFont(font)

        # 应用样式表
        self.setStyleSheet(get_stylesheet())

        # 设置异常处理
        sys.excepthook = self._handle_exception

        # 启动时静默检查API配置
        self._api_needs_config = self._check_api_on_startup()

    def _check_api_on_startup(self) -> bool:
        """
        启动时静默检查API配置
        返回True表示需要配置，False表示已配置
        """
        try:
            # 添加CLI模块路径
            cli_path = Path(__file__).parent.parent.parent / "video-generator-cli"
            if cli_path.exists():
                import sys
                if str(cli_path) not in sys.path:
                    sys.path.insert(0, str(cli_path))

            from api_config import APIConfig
            api_config = APIConfig()
            return not api_config.is_configured()
        except Exception:
            # 如果检查失败，假定需要配置
            return True

    def isApiNeedsConfig(self) -> bool:
        """获取API配置状态"""
        return getattr(self, '_api_needs_config', True)

    def _handle_exception(self, exc_type, exc_value, exc_traceback):
        """全局异常处理"""
        import traceback

        error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

        QMessageBox.critical(
            None,
            "程序错误",
            f"发生未捕获的异常:\n\n{exc_value}\n\n详细错误信息已记录。",
            QMessageBox.StandardButton.Ok
        )

        # 记录到文件
        error_log = Path.home() / ".video-gen" / "error.log"
        error_log.parent.mkdir(parents=True, exist_ok=True)
        with open(error_log, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Time: {Path(__file__).stat().st_mtime}\n")
            f.write(error_msg)

    @staticmethod
    def get_resource_path(relative_path: str) -> Path:
        """获取资源文件路径"""
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller打包后的路径
            return Path(sys._MEIPASS) / "resources" / relative_path
        else:
            # 开发环境路径
            return Path(__file__).parent.parent / "resources" / relative_path
