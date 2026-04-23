#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video Generator Pro - Main Entry Point
主程序入口
"""

import sys
import os
from pathlib import Path

# 添加项目路径到sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from core.app import VideoGeneratorApp
from views.main_window import MainWindow


def main():
    """主函数"""
    # Qt6自动支持高DPI缩放

    # 创建应用
    app = VideoGeneratorApp(sys.argv)

    # 创建并显示主窗口
    window = MainWindow()
    window.show()

    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
