#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Image Gallery Widget
参考图预览画廊 - 水平滚动展示缩略图 + 视频卡片
"""

import os
import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QFrame, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QScrollArea, QSizePolicy, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtGui import QPixmap

from .styled_widgets import CardFrame, SubheadingLabel, StyledButton

# Try importing PyQt6 Multimedia for video playback
try:
    from PyQt6.QtMultimedia import QMediaPlayer
    from PyQt6.QtMultimediaWidgets import QVideoWidget
    MULTIMEDIA_AVAILABLE = True
except ImportError:
    MULTIMEDIA_AVAILABLE = False


class VideoCard(QWidget):
    """视频缩略图卡片 - 鼠标 hover 时播放视频"""

    THUMB_W = 160
    THUMB_H = 90

    def __init__(self, video_path: str, label: str = "", parent=None):
        super().__init__(parent)
        self._video_path = video_path
        self._player = None
        self._video_widget = None
        self._cover_label = None
        self._init_ui(label)

    def _init_ui(self, label: str):
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(4)

        if MULTIMEDIA_AVAILABLE:
            self._setup_player_ui()
        else:
            self._setup_fallback_ui()

        name_label = QLabel(label or Path(self._video_path).stem)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("color: #6B6560; font-size: 10px;")
        name_label.setFixedWidth(self.THUMB_W)
        name_label.setText("🎬 " + name_label.text())
        vbox.addWidget(name_label)

    def _setup_player_ui(self):
        """使用 QMediaPlayer + QVideoWidget 播放视频"""
        self._video_widget = QVideoWidget()
        self._video_widget.setFixedSize(self.THUMB_W, self.THUMB_H)
        self._video_widget.setStyleSheet(
            "background-color: #1a1a2e; border-radius: 6px;"
        )

        self._player = QMediaPlayer(self)
        self._player.setVideoOutput(self._video_widget)
        self._player.setSource(QUrl.fromLocalFile(self._video_path))
        self._player.setLoops(QMediaPlayer.Loops.Infinite)

        # Show first frame then pause
        self._player.play()
        self._player.pause()

        self.layout().addWidget(self._video_widget)

    def _setup_fallback_ui(self):
        """Fallback: 显示视频文件图标 + 文件名"""
        self._cover_label = QLabel("🎬")
        self._cover_label.setFixedSize(self.THUMB_W, self.THUMB_H)
        self._cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cover_label.setStyleSheet(
            "background-color: #1a1a2e; border-radius: 6px; "
            "color: #E8E2DA; font-size: 24px;"
        )
        self._cover_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.layout().addWidget(self._cover_label)

    def enterEvent(self, event):
        if self._player:
            self._player.play()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._player:
            self._player.pause()
            self._player.setPosition(0)
        super().leaveEvent(event)

    def cleanup(self):
        """释放播放器资源"""
        if self._player:
            self._player.stop()
            self._player.setVideoOutput(None)
            self._player.deleteLater()
            self._player = None


class ImageGalleryWidget(CardFrame):
    """参考图预览画廊 - 水平滚动展示缩略图 + 视频"""

    imageClicked = pyqtSignal(str)  # image_path

    THUMB_W = 160
    THUMB_H = 90

    def __init__(self, parent=None):
        super().__init__(parent)

        self._image_count = 0
        self._video_count = 0
        self._last_image_dir = ""
        self._last_video_dir = ""

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(8)

        # 标题行
        header = QHBoxLayout()
        self._title_label = SubheadingLabel("媒体预览")
        header.addWidget(self._title_label)
        self._count_label = QLabel("")
        self._count_label.setStyleSheet("color: #9A958F;")
        header.addWidget(self._count_label)
        header.addStretch()

        # 打开文件夹按钮（图片 / 视频）
        self._open_image_folder_btn = StyledButton("打开图片文件夹")
        self._open_image_folder_btn.setFixedHeight(28)
        self._open_image_folder_btn.setStyleSheet(
            self._open_image_folder_btn.styleSheet() + """
            QPushButton { font-size: 11px; padding: 2px 10px; }
            """
        )
        self._open_image_folder_btn.clicked.connect(self._open_image_folder)
        self._open_image_folder_btn.setVisible(False)
        header.addWidget(self._open_image_folder_btn)

        self._open_video_folder_btn = StyledButton("打开视频文件夹")
        self._open_video_folder_btn.setFixedHeight(28)
        self._open_video_folder_btn.setStyleSheet(
            self._open_video_folder_btn.styleSheet() + """
            QPushButton { font-size: 11px; padding: 2px 10px; }
            """
        )
        self._open_video_folder_btn.clicked.connect(self._open_video_folder)
        self._open_video_folder_btn.setVisible(False)
        header.addWidget(self._open_video_folder_btn)

        outer.addLayout(header)

        # 水平滚动区域
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )
        self._scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._scroll.setFixedHeight(140)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._container = QWidget()
        self._hlayout = QHBoxLayout(self._container)
        self._hlayout.setContentsMargins(0, 0, 0, 0)
        self._hlayout.setSpacing(12)
        self._hlayout.addStretch()

        self._scroll.setWidget(self._container)
        outer.addWidget(self._scroll)

    # ---- public API ----

    def addImage(self, image_path: str, label: str = ""):
        """添加一张缩略图"""
        self._image_count += 1
        self._last_image_dir = str(Path(image_path).parent)

        card = QWidget()
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(4)

        img_label = QLabel()
        img_label.setFixedSize(self.THUMB_W, self.THUMB_H)
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_label.setStyleSheet(
            "background-color: #F0ECE6; border-radius: 6px;"
        )

        pm = QPixmap(image_path)
        if not pm.isNull():
            scaled = pm.scaled(
                self.THUMB_W, self.THUMB_H,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            # 居中裁剪
            x = max(0, (scaled.width() - self.THUMB_W) // 2)
            y = max(0, (scaled.height() - self.THUMB_H) // 2)
            cropped = scaled.copy(x, y, self.THUMB_W, self.THUMB_H)
            img_label.setPixmap(cropped)
        else:
            img_label.setText("加载失败")

        img_label.setCursor(Qt.CursorShape.PointingHandCursor)
        img_label.mousePressEvent = (
            lambda e, p=image_path: self.imageClicked.emit(p)
        )

        name_label = QLabel(label or Path(image_path).stem)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("color: #6B6560; font-size: 10px;")
        name_label.setFixedWidth(self.THUMB_W)

        vbox.addWidget(img_label)
        vbox.addWidget(name_label)

        # insert before the trailing stretch
        self._hlayout.insertWidget(self._hlayout.count() - 1, card)
        self._update_count()

    def addVideo(self, video_path: str, label: str = ""):
        """添加一个视频卡片"""
        self._video_count += 1
        self._last_video_dir = str(Path(video_path).parent)

        card = VideoCard(video_path, label)
        # insert before the trailing stretch
        self._hlayout.insertWidget(self._hlayout.count() - 1, card)
        self._update_count()

    def clearImages(self):
        """清除所有卡片（图片和视频）"""
        # Cleanup video players first
        for i in range(self._hlayout.count()):
            item = self._hlayout.itemAt(i)
            if item and item.widget():
                w = item.widget()
                if isinstance(w, VideoCard):
                    w.cleanup()

        while self._hlayout.count() > 1:  # keep trailing stretch
            item = self._hlayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._image_count = 0
        self._video_count = 0
        self._last_image_dir = ""
        self._last_video_dir = ""
        self._update_count()

    def setImageCount(self, total: int):
        """显示占位框（图片生成前）"""
        self.clearImages()
        for i in range(total):
            card = QWidget()
            vbox = QVBoxLayout(card)
            vbox.setContentsMargins(0, 0, 0, 0)
            vbox.setSpacing(4)

            placeholder = QLabel(f"场景 {i+1}")
            placeholder.setFixedSize(self.THUMB_W, self.THUMB_H)
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet(
                "background-color: #F0ECE6; border-radius: 6px; "
                "color: #B5B0AA; font-size: 11px;"
            )
            vbox.addWidget(placeholder)

            name = QLabel(f"场景 {i+1}")
            name.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name.setStyleSheet("color: #9A958F; font-size: 10px;")
            name.setFixedWidth(self.THUMB_W)
            vbox.addWidget(name)

            self._hlayout.insertWidget(self._hlayout.count() - 1, card)

    # ---- internal ----

    def _update_count(self):
        parts = []
        if self._image_count > 0:
            parts.append(f"{self._image_count} 张图片")
        if self._video_count > 0:
            parts.append(f"{self._video_count} 个视频")
        text = "、".join(parts)
        self._count_label.setText(f"({text})" if text else "")
        self._open_image_folder_btn.setVisible(bool(self._last_image_dir))
        self._open_video_folder_btn.setVisible(bool(self._last_video_dir))

    def _open_image_folder(self):
        """打开图片所在文件夹"""
        self._open_dir(self._last_image_dir)

    def _open_video_folder(self):
        """打开视频所在文件夹"""
        self._open_dir(self._last_video_dir)

    @staticmethod
    def _open_dir(folder: str):
        """打开文件夹"""
        if not folder or not os.path.isdir(folder):
            return
        if sys.platform == "win32":
            os.startfile(folder)
        elif sys.platform == "darwin":
            os.system(f'open "{folder}"')
        else:
            os.system(f'xdg-open "{folder}"')
