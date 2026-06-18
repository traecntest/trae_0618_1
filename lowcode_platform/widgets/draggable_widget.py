import json
from typing import Any, Dict, Optional
from PySide6.QtCore import Qt, QMimeData, QPoint, Signal
from PySide6.QtGui import QDrag, QPainter, QColor, QPen, QBrush
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QFrame, QScrollArea,
    QGridLayout, QHBoxLayout
)
from config.settings import SUPPORTED_WIDGETS


class DraggableWidget(QFrame):
    def __init__(self, widget_type: str, widget_info: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.widget_type = widget_type
        self.widget_info = widget_info
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        icon_label = QLabel(self.widget_info.get("icon", "📝"))
        icon_label.setStyleSheet("font-size: 18px;")
        icon_label.setFixedWidth(30)
        
        name_label = QLabel(self.widget_info.get("name", self.widget_type))
        name_label.setStyleSheet("font-size: 13px;")
        
        layout.addWidget(icon_label)
        layout.addWidget(name_label, 1)
        
        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
            }
            QFrame:hover {
                background-color: #f0f7ff;
                border: 1px solid #1890ff;
            }
        """)
        self.setFixedHeight(44)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            
            data = {
                "type": self.widget_type,
                "info": self.widget_info,
            }
            mime_data.setData("application/x-form-widget", json.dumps(data).encode())
            drag.setMimeData(mime_data)
            
            pixmap = self.grab()
            drag.setPixmap(pixmap)
            drag.setHotSpot(QPoint(pixmap.width() // 2, pixmap.height() // 2))
            
            drag.exec_(Qt.CopyAction)


class WidgetPalette(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        title = QLabel("控件面板")
        title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 8px;")
        layout.addWidget(title)
        
        for widget_info in SUPPORTED_WIDGETS:
            widget = DraggableWidget(widget_info["type"], widget_info)
            layout.addWidget(widget)
        
        layout.addStretch(1)
        self.setWidget(container)


class DropCanvas(QWidget):
    field_added = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._fields = []
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet("""
            DropCanvas {
                background-color: #fafafa;
                border: 2px dashed #d9d9d9;
                border-radius: 8px;
                min-height: 400px;
            }
            DropCanvas:hover {
                border-color: #1890ff;
                background-color: #f0f7ff;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        placeholder = QLabel("拖拽控件到此处")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("color: #999; font-size: 14px;")
        layout.addWidget(placeholder)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-form-widget"):
            event.acceptProposedAction()
            self.setStyleSheet("""
                DropCanvas {
                    background-color: #e6f7ff;
                    border: 2px dashed #1890ff;
                    border-radius: 8px;
                }
            """)
    
    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            DropCanvas {
                background-color: #fafafa;
                border: 2px dashed #d9d9d9;
                border-radius: 8px;
            }
        """)
    
    def dropEvent(self, event):
        data = json.loads(event.mimeData().data("application/x-form-widget"))
        widget_type = data["type"]
        widget_info = data["info"]
        
        position = event.position()

        if self.layout().count() == 1:
            item = self.layout().itemAt(0)
            if item.widget() and item.widget().text() == "拖拽控件到此处":
                item.widget().deleteLater()

        field_widget = self._create_field_widget(widget_type, widget_info, position)
        self.layout().addWidget(field_widget)

        self._fields.append({
            "type": widget_type,
            "info": widget_info,
            "widget": field_widget,
        })

        self.field_added.emit(field_widget)

        self.setStyleSheet("""
            DropCanvas {
                background-color: #fafafa;
                border: 2px dashed #d9d9d9;
                border-radius: 8px;
            }
        """)

        event.acceptProposedAction()
    
    def _create_field_widget(self, widget_type: str, widget_info: Dict[str, Any], position):
        from designers.form_designer import FormFieldWidget
        return FormFieldWidget(widget_type, widget_info)

    def get_fields(self):
        return self._fields.copy()

    def clear(self):
        while self.layout().count() > 0:
            item = self.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._fields.clear()
        
        placeholder = QLabel("拖拽控件到此处")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("color: #999; font-size: 14px;")
        self.layout().addWidget(placeholder)
