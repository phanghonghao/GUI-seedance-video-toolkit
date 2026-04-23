#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base ViewModel Class
"""

from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty
from typing import Any, Optional, Callable
from pathlib import Path
import json
import sys

# 添加CLI模块路径
_cli_path = Path(__file__).parent.parent / "video-generator-cli"
if _cli_path.exists():
    sys.path.insert(0, str(_cli_path))


class BaseViewModel(QObject):
    """ViewModel基类"""

    # 通用信号
    loadingChanged = pyqtSignal(bool)
    errorOccurred = pyqtSignal(str)
    successOccurred = pyqtSignal(str)
    dataChanged = pyqtSignal()

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self._loading = False
        self._error_message = ""
        self._success_message = ""

    # ===== Property =====

    def isLoading(self) -> bool:
        return self._loading

    def setLoading(self, loading: bool):
        if self._loading != loading:
            self._loading = loading
            self.loadingChanged.emit(loading)

    loading = pyqtProperty(bool, isLoading, setLoading, notify=loadingChanged)

    # ===== 错误处理 =====

    def set_error(self, message: str):
        """设置错误消息"""
        self._error_message = message
        self.errorOccurred.emit(message)

    def set_success(self, message: str):
        """设置成功消息"""
        self._success_message = message
        self.successOccurred.emit(message)

    def clear_messages(self):
        """清除所有消息"""
        self._error_message = ""
        self._success_message = ""

    # ===== 异步任务 =====

    def run_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        在后台线程运行函数

        Args:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数执行结果
        """
        from PyQt6.QtCore import QThreadPool, QRunnable

        self.setLoading(True)

        class AsyncTask(QRunnable):
            def __init__(self, vm, func, args, kwargs):
                super().__init__()
                self.vm = vm
                self.func = func
                self.args = args
                self.kwargs = kwargs
                self.result = None
                self.error = None

            def run(self):
                try:
                    self.result = self.func(*self.args, **self.kwargs)
                except Exception as e:
                    self.error = str(e)

        task = AsyncTask(self, func, args, kwargs)
        QThreadPool.globalInstance().start(task)

        # 等待任务完成（简化版，实际应使用信号）
        QThreadPool.globalInstance().waitForDone()
        self.setLoading(False)

        if task.error:
            self.set_error(task.error)
            return None

        self.dataChanged.emit()
        return task.result

    # ===== 配置管理 =====

    @staticmethod
    def get_config_dir() -> Path:
        """获取配置目录"""
        import os
        if sys.platform == "win32":
            base_dir = Path(os.environ.get("APPDATA", Path.home()))
        else:
            base_dir = Path.home() / ".config"
        config_dir = base_dir / "video-gen"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    @staticmethod
    def load_json_config(file_path: Path) -> dict:
        """加载JSON配置"""
        if not file_path.exists():
            return {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            return {}

    @staticmethod
    def save_json_config(file_path: Path, config: dict):
        """保存JSON配置"""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    @staticmethod
    def get_project_root() -> Path:
        """获取项目根目录"""
        # 从当前文件向上查找
        current = Path(__file__).parent
        for parent in [current, current.parent, current.parent.parent, current.parent.parent.parent]:
            if (parent / "config").exists():
                return parent
        return Path.cwd()
