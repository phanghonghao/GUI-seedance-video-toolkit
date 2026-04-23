#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI Wrapper - 导入现有CLI业务逻辑
"""

import sys
from pathlib import Path

# 添加CLI模块路径
_cli_path = Path(__file__).parent.parent / "video-generator-cli"
if _cli_path.exists():
    sys.path.insert(0, str(_cli_path))

# 导入核心业务模块
try:
    from api_config import APIConfig, APIConfigWizard, API_PROVIDERS
    from commands.init import ProjectConfig, InitCommand
    from templates import TemplateManager, BUILTIN_TEMPLATES
    from wizard.interactive import InteractiveWizard

    # 验证导入成功
    __all__ = [
        "APIConfig",
        "APIConfigWizard",
        "API_PROVIDERS",
        "ProjectConfig",
        "InitCommand",
        "TemplateManager",
        "BUILTIN_TEMPLATES",
        "InteractiveWizard",
    ]
except ImportError as e:
    print(f"警告: 无法导入CLI模块: {e}")
    __all__ = []
