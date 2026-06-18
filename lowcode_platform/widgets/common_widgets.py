from typing import Any, Callable, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QPushButton, QLabel, QFrame, QHBoxLayout, QVBoxLayout,
    QWidget, QSizePolicy, QComboBox, QLineEdit, QTextEdit,
    QSpinBox, QDoubleSpinBox, QCheckBox, QRadioButton,
    QSlider, QProgressBar, QToolButton, QMenu
)


class PrimaryButton(QPushButton):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
            QPushButton:pressed {
                background-color: #096dd9;
            }
            QPushButton:disabled {
                background-color: #d9d9d9;
                color: #bfbfbf;
            }
        """)


class SecondaryButton(QPushButton):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                border-color: #1890ff;
                color: #1890ff;
            }
            QPushButton:pressed {
                background-color: #f0f7ff;
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #bfbfbf;
                border-color: #e8e8e8;
            }
        """)


class DangerButton(QPushButton):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                background-color: #ff4d4f;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #ff7875;
            }
            QPushButton:pressed {
                background-color: #d9363e;
            }
            QPushButton:disabled {
                background-color: #ffccc7;
                color: #ff7875;
            }
        """)


class SuccessButton(QPushButton):
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                background-color: #52c41a;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #73d13d;
            }
            QPushButton:pressed {
                background-color: #389e0d;
            }
            QPushButton:disabled {
                background-color: #b7eb8f;
                color: #52c41a;
            }
        """)


class Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e8e8e8;
                border-radius: 8px;
            }
        """)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 16, 16, 16)
        self._layout.setSpacing(8)

    def add_widget(self, widget: QWidget):
        self._layout.addWidget(widget)

    def set_title(self, title: str):
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self._layout.insertWidget(0, title_label)


class Badge(QLabel):
    def __init__(self, text: str = "", color: str = "#1890ff", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 11px;
            }}
        """)
        self.setAlignment(Qt.AlignCenter)


class Tag(QLabel):
    def __init__(self, text: str = "", color: str = "blue", parent=None):
        color_map = {
            "blue": "#1890ff",
            "green": "#52c41a",
            "red": "#ff4d4f",
            "orange": "#faad14",
            "purple": "#722ed1",
            "cyan": "#13c2c2",
        }
        bg_color = color_map.get(color, color)
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color}20;
                color: {bg_color};
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 12px;
                border: 1px solid {bg_color}40;
            }}
        """)


class Divider(QFrame):
    def __init__(self, orientation: Qt.Orientation = Qt.Horizontal, parent=None):
        super().__init__(parent)
        if orientation == Qt.Horizontal:
            self.setFrameShape(QFrame.HLine)
            self.setFixedHeight(1)
        else:
            self.setFrameShape(QFrame.VLine)
            self.setFixedWidth(1)
        self.setStyleSheet("background-color: #e8e8e8;")


class EmptyState(QWidget):
    def __init__(self, icon: str = "📭", title: str = "暂无数据", description: str = "", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; color: #333;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        if description:
            desc_label = QLabel(description)
            desc_label.setStyleSheet("font-size: 13px; color: #999;")
            desc_label.setAlignment(Qt.AlignCenter)
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)


class LoadingSpinner(QWidget):
    def __init__(self, size: int = 24, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._angle = 0
        self._timer = None

    def start(self):
        if self._timer is None:
            self._timer = self.startTimer(50)

    def stop(self):
        if self._timer is not None:
            self.killTimer(self._timer)
            self._timer = None

    def timerEvent(self, event):
        self._angle = (self._angle + 30) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QColor("#1890ff")
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawArc(
            4, 4,
            self.width() - 8, self.height() - 8,
            self._angle * 16, 270 * 16
        )


__all__ = [
    "PrimaryButton",
    "SecondaryButton",
    "DangerButton",
    "SuccessButton",
    "Card",
    "Badge",
    "Tag",
    "Divider",
    "EmptyState",
    "LoadingSpinner",
]
