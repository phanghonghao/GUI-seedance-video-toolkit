#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core Application Module
"""

from .app import VideoGeneratorApp
from .theme import get_stylesheet, get_color, ANTHROPIC_COLORS

__all__ = ["VideoGeneratorApp", "get_stylesheet", "get_color", "ANTHROPIC_COLORS"]
