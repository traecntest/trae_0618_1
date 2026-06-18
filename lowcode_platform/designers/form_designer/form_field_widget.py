from typing import Any, Dict, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QDateEdit, QCheckBox, QPushButton, QFrame,
    QTextEdit, QSpinBox, QFileDialog, QMessageBox
)
from PySide6.QtCore import QDate
from utils.id_generator import generate_id


class FormFieldWidget(QFrame):
    field_selected = Signal(str)
    field_deleted = Signal(str)

    def __init__(self, widget_type: str, widget_info: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.widget_type = widget_type
        self.widget_info = widget_info
        self.field_id = generate_id()
        self.field_name = f"field_{self.field_id[:8]}"
        self.field_label = widget_info.get("name", widget_type)
        self.required = False
        self.default_value = ""
        self.placeholder = ""
        self.options: list = []
        self.validation_rules: list = []

        self._is_selected = False
        self._setup_ui()
        self._setup_interaction()

    def _setup_ui(self):
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
            }
            QFrame:hover {
                border-color: #1890ff;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        self.label_widget = QLabel(f"{self.field_label} *" if self.required else self.field_label)
        self.label_widget.setStyleSheet("font-size: 13px; font-weight: 500; color: #333;")
        header_layout.addWidget(self.label_widget, 1)

        self.delete_btn = QPushButton("×")
        self.delete_btn.setFixedSize(24, 24)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #999;
                font-size: 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #fff1f0;
                color: #ff4d4f;
            }
        """)
        self.delete_btn.clicked.connect(self._on_delete)
        header_layout.addWidget(self.delete_btn)

        layout.addLayout(header_layout)

        self.input_widget = self._create_input_widget()
        layout.addWidget(self.input_widget)

    def _create_input_widget(self) -> QWidget:
        widget_map = {
            "text": self._create_text_input,
            "textarea": self._create_textarea,
            "number": self._create_number_input,
            "select": self._create_select,
            "checkbox": self._create_checkbox,
            "radio": self._create_radio,
            "date": self._create_date,
            "datetime": self._create_datetime,
            "file": self._create_file_upload,
            "image": self._create_image_upload,
        }

        creator = widget_map.get(self.widget_type, self._create_text_input)
        return creator()

    def _create_text_input(self) -> QWidget:
        widget = QLineEdit()
        widget.setPlaceholderText(self.placeholder or f"请输入{self.field_label}")
        widget.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #1890ff;
            }
        """)
        return widget

    def _create_textarea(self) -> QWidget:
        widget = QTextEdit()
        widget.setPlaceholderText(self.placeholder or f"请输入{self.field_label}")
        widget.setFixedHeight(80)
        widget.setStyleSheet("""
            QTextEdit {
                padding: 8px 12px;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                font-size: 13px;
            }
            QTextEdit:focus {
                border-color: #1890ff;
            }
        """)
        return widget

    def _create_number_input(self) -> QWidget:
        widget = QSpinBox()
        widget.setRange(-1000000, 1000000)
        widget.setStyleSheet("""
            QSpinBox {
                padding: 6px 12px;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                font-size: 13px;
            }
            QSpinBox:focus {
                border-color: #1890ff;
            }
        """)
        return widget

    def _create_select(self) -> QWidget:
        widget = QComboBox()
        widget.addItem(f"请选择{self.field_label}", "")
        for opt in self.options:
            if isinstance(opt, dict):
                widget.addItem(opt.get("label", ""), opt.get("value", ""))
            else:
                widget.addItem(str(opt), str(opt))
        widget.setStyleSheet("""
            QComboBox {
                padding: 6px 12px;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                font-size: 13px;
            }
            QComboBox:focus {
                border-color: #1890ff;
            }
        """)
        return widget

    def _create_checkbox(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        if self.options:
            for opt in self.options:
                cb = QCheckBox(opt.get("label", str(opt)) if isinstance(opt, dict) else str(opt))
                layout.addWidget(cb)
        else:
            cb = QCheckBox(self.field_label)
            layout.addWidget(cb)

        return container

    def _create_radio(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        for opt in self.options:
            from PySide6.QtWidgets import QRadioButton
            rb = QRadioButton(opt.get("label", str(opt)) if isinstance(opt, dict) else str(opt))
            layout.addWidget(rb)

        if not self.options:
            from PySide6.QtWidgets import QRadioButton
            rb = QRadioButton(self.field_label)
            layout.addWidget(rb)

        return container

    def _create_date(self) -> QWidget:
        widget = QDateEdit()
        widget.setCalendarPopup(True)
        widget.setDate(QDate.currentDate())
        widget.setDisplayFormat("yyyy-MM-dd")
        widget.setStyleSheet("""
            QDateEdit {
                padding: 6px 12px;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                font-size: 13px;
            }
            QDateEdit:focus {
                border-color: #1890ff;
            }
        """)
        return widget

    def _create_datetime(self) -> QWidget:
        from PySide6.QtWidgets import QDateTimeEdit
        from PySide6.QtCore import QDateTime
        widget = QDateTimeEdit()
        widget.setCalendarPopup(True)
        widget.setDateTime(QDateTime.currentDateTime())
        widget.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        widget.setStyleSheet("""
            QDateTimeEdit {
                padding: 6px 12px;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                font-size: 13px;
            }
            QDateTimeEdit:focus {
                border-color: #1890ff;
            }
        """)
        return widget

    def _create_file_upload(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.file_label = QLineEdit()
        self.file_label.setPlaceholderText("未选择文件")
        self.file_label.setReadOnly(True)
        self.file_label.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                font-size: 13px;
            }
        """)

        browse_btn = QPushButton("选择文件")
        browse_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
        """)
        browse_btn.clicked.connect(self._on_browse_file)

        layout.addWidget(self.file_label, 1)
        layout.addWidget(browse_btn)

        return container

    def _create_image_upload(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = QLineEdit()
        self.image_label.setPlaceholderText("未选择图片")
        self.image_label.setReadOnly(True)
        self.image_label.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                font-size: 13px;
            }
        """)

        browse_btn = QPushButton("选择图片")
        browse_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
        """)
        browse_btn.clicked.connect(self._on_browse_image)

        layout.addWidget(self.image_label, 1)
        layout.addWidget(browse_btn)

        return container

    def _on_browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", "所有文件 (*.*)")
        if file_path:
            self.file_label.setText(file_path)

    def _on_browse_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "图片文件 (*.png *.jpg *.jpeg *.gif)")
        if file_path:
            self.image_label.setText(file_path)

    def _setup_interaction(self):
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_selected = True
            self._update_selected_style()
            self.field_selected.emit(self.field_id)
        super().mousePressEvent(event)

    def _update_selected_style(self):
        if self._is_selected:
            self.setStyleSheet("""
                QFrame {
                    background-color: #e6f7ff;
                    border: 2px solid #1890ff;
                    border-radius: 6px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                }
                QFrame:hover {
                    border-color: #1890ff;
                }
            """)

    def set_selected(self, selected: bool):
        self._is_selected = selected
        self._update_selected_style()

    def _on_delete(self):
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除字段 '{self.field_label}' 吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.field_deleted.emit(self.field_id)

    def update_field(self, **kwargs):
        if "name" in kwargs:
            self.field_label = kwargs["name"]
            self.label_widget.setText(f"{self.field_label} *" if self.required else self.field_label)
        if "required" in kwargs:
            self.required = kwargs["required"]
            self.label_widget.setText(f"{self.field_label} *" if self.required else self.field_label)
        if "placeholder" in kwargs:
            self.placeholder = kwargs["placeholder"]
            if isinstance(self.input_widget, QLineEdit):
                self.input_widget.setPlaceholderText(self.placeholder or f"请输入{self.field_label}")
        if "options" in kwargs:
            self.options = kwargs["options"]
            if isinstance(self.input_widget, QComboBox):
                self.input_widget.clear()
                self.input_widget.addItem(f"请选择{self.field_label}", "")
                for opt in self.options:
                    if isinstance(opt, dict):
                        self.input_widget.addItem(opt.get("label", ""), opt.get("value", ""))
                    else:
                        self.input_widget.addItem(str(opt), str(opt))

    def get_editable_properties(self) -> Dict[str, Dict[str, Any]]:
        return {
            "field_name": {
                "type": "string",
                "label": "字段名称",
                "value": self.field_name,
            },
            "field_label": {
                "type": "string",
                "label": "显示标签",
                "value": self.field_label,
            },
            "placeholder": {
                "type": "string",
                "label": "占位提示",
                "value": self.placeholder,
            },
            "required": {
                "type": "bool",
                "label": "是否必填",
                "value": self.required,
            },
            "default_value": {
                "type": "string",
                "label": "默认值",
                "value": self.default_value,
            },
            "widget_type": {
                "type": "select",
                "label": "控件类型",
                "value": self.widget_type,
                "options": [
                    ("text", "文本框"),
                    ("textarea", "多行文本"),
                    ("number", "数字"),
                    ("select", "下拉选择"),
                    ("checkbox", "复选框"),
                    ("radio", "单选框"),
                    ("date", "日期"),
                    ("datetime", "日期时间"),
                    ("file", "文件上传"),
                    ("image", "图片上传"),
                ],
            },
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.field_id,
            "type": self.widget_type,
            "name": self.field_name,
            "label": self.field_label,
            "required": self.required,
            "placeholder": self.placeholder,
            "default_value": self.default_value,
            "options": self.options,
            "validation_rules": self.validation_rules,
        }
