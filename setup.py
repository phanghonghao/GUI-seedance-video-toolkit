#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Script - Build Video Generator Pro with PyInstaller
打包构建脚本
"""

import os
import sys
import shutil
from pathlib import Path

def build():
    """使用PyInstaller构建exe"""
    from PyInstaller.__main__ import run

    # 项目路径
    project_dir = Path(__file__).parent
    dist_dir = project_dir / "dist"
    build_dir = project_dir / "build"

    # 清理旧的构建
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)

    # PyInstaller参数
    pyinstaller_args = [
        'main.py',
        '--name=VideoGeneratorPro',
        '--onefile',                    # 单文件exe
        '--windowed',                   # 无控制台窗口
        '--clean',                      # 清理临时文件
        '--noconfirm',                  # 覆盖输出
        '--add-data=resources;resources',  # 添加资源文件
        '--hidden-import=PyQt6',
        '--hidden-import=PyQt6.QtCore',
        '--hidden-import=PyQt6.QtGui',
        '--hidden-import=PyQt6.QtWidgets',
        '--collect-all=PyQt6',
        '--icon=resources/icons/app_icon.ico' if (project_dir / 'resources/icons/app_icon.ico').exists() else '',
    ]

    # 过滤空参数
    pyinstaller_args = [arg for arg in pyinstaller_args if arg]

    print("开始构建 Video Generator Pro...")
    print(f"项目目录: {project_dir}")
    print(f"PyInstaller 参数: {' '.join(pyinstaller_args)}")

    # 执行构建
    run(pyinstaller_args)

    print(f"\n构建完成！")
    print(f"输出文件: {dist_dir / 'VideoGeneratorPro.exe'}")

    # 复制到发布目录
    release_dir = project_dir / "release"
    release_dir.mkdir(exist_ok=True)

    exe_file = dist_dir / "VideoGeneratorPro.exe"
    if exe_file.exists():
        target = release_dir / "VideoGeneratorPro.exe"
        shutil.copy2(exe_file, target)
        print(f"已复制到发布目录: {target}")

        # 获取文件大小
        size_mb = exe_file.stat().st_size / (1024 * 1024)
        print(f"文件大小: {size_mb:.1f} MB")


def build_debug():
    """构建调试版本（带控制台）"""
    from PyInstaller.__main__ import run

    project_dir = Path(__file__).parent

    pyinstaller_args = [
        'main.py',
        '--name=VideoGeneratorPro_Debug',
        '--onefile',
        '--console',                    # 保留控制台窗口
        '--clean',
        '--noconfirm',
        '--add-data=resources;resources',
        '--hidden-import=PyQt6',
    ]

    run(pyinstaller_args)
    print(f"\n调试版本构建完成！")
    print(f"输出文件: {project_dir / 'dist' / 'VideoGeneratorPro_Debug.exe'}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="构建 Video Generator Pro")
    parser.add_argument('--debug', action='store_true', help='构建调试版本（带控制台）')

    args = parser.parse_args()

    if args.debug:
        build_debug()
    else:
        build()
