#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project ViewModel
"""

from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty
from typing import List, Dict, Optional, Any
from pathlib import Path
import json
from datetime import datetime

from .base_viewmodel import BaseViewModel
import sys

# 添加CLI模块路径
_cli_path = Path(__file__).parent.parent / "video-generator-cli"
if _cli_path.exists():
    sys.path.insert(0, str(_cli_path))

try:
    from commands.init import ProjectConfig
    from templates import TemplateManager
    from api_config import APIConfig
except ImportError:
    ProjectConfig = None
    TemplateManager = None
    APIConfig = None


class ProjectViewModel(BaseViewModel):
    """项目管理ViewModel"""

    # 项目列表信号
    projectListChanged = pyqtSignal()
    currentProjectChanged = pyqtSignal()

    # 项目状态信号
    projectCreated = pyqtSignal(str)  # project_name
    projectDeleted = pyqtSignal(str)  # project_name
    projectUpdated = pyqtSignal(str)  # project_name

    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self._projects: List[Dict[str, Any]] = []
        self._current_project: Optional[str] = None
        self._current_config: Dict[str, Any] = {}
        self._project_root = self.get_project_root()

        # 初始化加载项目列表
        self.refresh_project_list()

    # ===== Property =====

    def projectCount(self) -> int:
        return len(self._projects)

    projectCount = pyqtProperty(int, projectCount, notify=projectListChanged)

    # ===== 项目列表管理 =====

    def refresh_project_list(self):
        """刷新项目列表"""
        if ProjectConfig is None:
            self._projects = []
            self.projectListChanged.emit()
            return

        try:
            project_names = ProjectConfig.list_projects(self._project_root)
            self._projects = []

            for name in project_names:
                project_info = self._get_project_info(name)
                if project_info:
                    self._projects.append(project_info)

            self.projectListChanged.emit()
        except Exception as e:
            self.set_error(f"加载项目列表失败: {str(e)}")

    def _get_project_info(self, project_name: str) -> Optional[Dict[str, Any]]:
        """获取项目信息"""
        try:
            manager = ProjectConfig(project_name, self._project_root)
            if not manager.config_exists():
                return None

            config = manager.load_config()
            project_info = config.get("project", {})

            return {
                "name": project_name,
                "description": project_info.get("description", ""),
                "created_at": project_info.get("created_at", ""),
                "updated_at": project_info.get("updated_at", ""),
                "scene_count": len(config.get("scenes", [])),
                "video_style": config.get("video", {}).get("style", ""),
                "config_file": str(manager.config_file),
                "output_dir": str(manager.get_output_dir()),
                "reference_dir": str(manager.get_reference_dir()),
                "video_dir": str(manager.get_video_dir()),
            }
        except Exception as e:
            print(f"获取项目信息失败 {project_name}: {e}")
            return None

    def get_projects(self) -> List[Dict[str, Any]]:
        """获取项目列表"""
        return self._projects.copy()

    def get_project(self, project_name: str) -> Optional[Dict[str, Any]]:
        """获取指定项目信息"""
        for project in self._projects:
            if project["name"] == project_name:
                return project
        return None

    # ===== 当前项目 =====

    def setCurrentProject(self, project_name: Optional[str]):
        """设置当前项目"""
        if self._current_project != project_name:
            self._current_project = project_name
            self._load_current_config()
            self.currentProjectChanged.emit()

    def getCurrentProject(self) -> Optional[str]:
        """获取当前项目名称"""
        return self._current_project

    currentProject = pyqtProperty(
        str,
        fget=getCurrentProject,
        fset=setCurrentProject,
        notify=currentProjectChanged
    )

    def _load_current_config(self):
        """加载当前项目配置"""
        if not self._current_project:
            self._current_config = {}
            return

        try:
            manager = ProjectConfig(self._current_project, self._project_root)
            self._current_config = manager.load_config()
        except Exception as e:
            self.set_error(f"加载项目配置失败: {str(e)}")
            self._current_config = {}

    def getCurrentConfig(self) -> Dict[str, Any]:
        """获取当前项目配置"""
        return self._current_config.copy()

    # ===== 创建项目 =====

    def create_project(self, project_data: Dict[str, Any]) -> bool:
        """
        创建新项目

        Args:
            project_data: 项目数据，包含:
                - project_name: 项目名称
                - project_description: 项目描述
                - template: 模板名称（可选）
                - character: 角色设定
                - video: 视频设置
                - scenes: 场景列表
                - audio: 音频配置

        Returns:
            是否创建成功
        """
        if ProjectConfig is None:
            self.set_error("CLI模块未加载")
            return False

        try:
            project_name = project_data.get("project_name", "未命名项目")

            # 检查项目是否已存在
            manager = ProjectConfig(project_name, self._project_root)
            if manager.config_exists():
                self.set_error(f"项目 '{project_name}' 已存在")
                return False

            # 构建配置
            config = {
                "project": {
                    "name": project_name,
                    "description": project_data.get("project_description", ""),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                },
                "character": project_data.get("character", {}),
                "video": project_data.get("video", {}),
                "scenes": project_data.get("scenes", []),
                "audio": project_data.get("audio", {}),
                "paths": {
                    "output_dir": f"output/{project_name}",
                    "reference_dir": f"assets/materials/参考图/{project_name}",
                    "video_dir": f"assets/materials/seedance-videos/{project_name}"
                }
            }

            # 保存配置
            manager.save_config(config)
            manager.create_output_dirs()

            # 刷新列表
            self.refresh_project_list()

            self.set_success(f"项目 '{project_name}' 创建成功")
            self.projectCreated.emit(project_name)
            return True

        except Exception as e:
            self.set_error(f"创建项目失败: {str(e)}")
            return False

    # ===== 从模板创建项目 =====

    def create_from_template(self, template_name: str, project_name: str, description: str = "") -> bool:
        """从模板创建项目"""
        if TemplateManager is None or ProjectConfig is None:
            self.set_error("CLI模块未加载")
            return False

        try:
            template_mgr = TemplateManager()

            # 检查模板是否存在
            if template_name not in template_mgr.list_templates():
                self.set_error(f"模板不存在: {template_name}")
                return False

            # 检查项目是否已存在
            manager = ProjectConfig(project_name, self._project_root)
            if manager.config_exists():
                self.set_error(f"项目 '{project_name}' 已存在")
                return False

            # 加载模板
            template = template_mgr.get_template(template_name)

            # 更新项目信息
            template["project"]["name"] = project_name
            if description:
                template["project"]["description"] = description
            template["project"]["created_at"] = datetime.now().isoformat()
            template["project"]["updated_at"] = datetime.now().isoformat()

            # 保存配置
            manager.save_config(template)
            manager.create_output_dirs()

            # 刷新列表
            self.refresh_project_list()

            self.set_success(f"从模板 '{template_name}' 创建项目 '{project_name}' 成功")
            self.projectCreated.emit(project_name)
            return True

        except Exception as e:
            self.set_error(f"从模板创建项目失败: {str(e)}")
            return False

    # ===== 删除项目 =====

    def delete_project(self, project_name: str) -> bool:
        """删除项目"""
        try:
            manager = ProjectConfig(project_name, self._project_root)

            if not manager.config_exists():
                self.set_error(f"项目不存在: {project_name}")
                return False

            # 删除配置文件
            manager.config_file.unlink()

            # 删除输出目录（可选）
            # output_dir = manager.get_output_dir()
            # if output_dir.exists():
            #     shutil.rmtree(output_dir)

            # 刷新列表
            self.refresh_project_list()

            # 如果删除的是当前项目，清除当前项目
            if self._current_project == project_name:
                self.setCurrentProject(None)

            self.set_success(f"项目 '{project_name}' 已删除")
            self.projectDeleted.emit(project_name)
            return True

        except Exception as e:
            self.set_error(f"删除项目失败: {str(e)}")
            return False

    # ===== 更新项目 =====

    def update_project(self, project_name: str, config: Dict[str, Any]) -> bool:
        """更新项目配置"""
        try:
            manager = ProjectConfig(project_name, self._project_root)

            if not manager.config_exists():
                self.set_error(f"项目不存在: {project_name}")
                return False

            # 更新时间戳
            if "project" not in config:
                config["project"] = {}
            config["project"]["updated_at"] = datetime.now().isoformat()

            # 保存配置
            manager.save_config(config)

            # 如果是当前项目，重新加载
            if self._current_project == project_name:
                self._load_current_config()

            # 刷新列表
            self.refresh_project_list()

            self.set_success(f"项目 '{project_name}' 已更新")
            self.projectUpdated.emit(project_name)
            return True

        except Exception as e:
            self.set_error(f"更新项目失败: {str(e)}")
            return False

    # ===== 场景管理 =====

    def add_scene(self, project_name: str, scene_data: Dict[str, Any]) -> bool:
        """添加场景"""
        try:
            manager = ProjectConfig(project_name, self._project_root)
            config = manager.load_config()

            scenes = config.get("scenes", [])

            # 生成新ID
            max_id = max([s.get("id", 0) for s in scenes], default=0)
            scene_data["id"] = max_id + 1

            scenes.append(scene_data)
            config["scenes"] = scenes

            return self.update_project(project_name, config)

        except Exception as e:
            self.set_error(f"添加场景失败: {str(e)}")
            return False

    def remove_scene(self, project_name: str, scene_id: int) -> bool:
        """删除场景"""
        try:
            manager = ProjectConfig(project_name, self._project_root)
            config = manager.load_config()

            scenes = config.get("scenes", [])
            scenes = [s for s in scenes if s.get("id") != scene_id]
            config["scenes"] = scenes

            return self.update_project(project_name, config)

        except Exception as e:
            self.set_error(f"删除场景失败: {str(e)}")
            return False

    def update_scene(self, project_name: str, scene_id: int, scene_data: Dict[str, Any]) -> bool:
        """更新场景"""
        try:
            manager = ProjectConfig(project_name, self._project_root)
            config = manager.load_config()

            scenes = config.get("scenes", [])
            for i, scene in enumerate(scenes):
                if scene.get("id") == scene_id:
                    scene_data["id"] = scene_id
                    scenes[i] = scene_data
                    break

            config["scenes"] = scenes
            return self.update_project(project_name, config)

        except Exception as e:
            self.set_error(f"更新场景失败: {str(e)}")
            return False
