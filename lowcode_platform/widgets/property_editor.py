from typing import Any, Dict, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QCheckBox, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit,
    QFrame, QScrollArea, QFormLayout, QPushButton, QColorDialog
)
from PySide6.QtGui import QColor


class PropertyEditor(QScrollArea):
    property_changed = Signal(str, str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_object: Optional[Any] = None
        self._editors: Dict[str, QWidget] = {}
        self._setup_ui()

    def _setup_ui(self):
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)

        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(4)

        self._title_label = QLabel("属性编辑")
        self._title_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 8px;")
        self._layout.addWidget(self._title_label)

        self._form_layout = QFormLayout()
        self._form_layout.setSpacing(8)
        self._form_layout.setContentsMargins(8, 8, 8, 8)
        self._layout.addLayout(self._form_layout)

        self._layout.addStretch(1)
        self.setWidget(self._container)

    def set_object(self, obj: Optional[Any]):
        self._current_object = obj
        self._clear_editors()

        if obj is None:
            self._title_label.setText("属性编辑")
            return

        self._title_label.setText(f"属性: {getattr(obj, 'name', '未命名')}")
        self._build_editors(obj)

    def _clear_editors(self):
        while self._form_layout.rowCount() > 0:
            self._form_layout.removeRow(0)
        self._editors.clear()

    def _build_editors(self, obj: Any):
        if hasattr(obj, "get_editable_properties"):
            properties = obj.get_editable_properties()
        else:
            properties = self._auto_discover_properties(obj)

        for prop_name, prop_info in properties.items():
            self._add_property_editor(prop_name, prop_info, obj)

    def _auto_discover_properties(self, obj: Any) -> Dict[str, Dict[str, Any]]:
        properties = {}
        exclude = {"id", "created_at", "updated_at", "fields", "children", "permissions"}

        for attr_name in dir(obj):
            if attr_name.startswith("_") or attr_name in exclude:
                continue

            attr_value = getattr(obj, attr_name, None)
            if callable(attr_value):
                continue

            if isinstance(attr_value, str):
                properties[attr_name] = {"type": "string", "label": attr_name, "value": attr_value}
            elif isinstance(attr_value, bool):
                properties[attr_name] = {"type": "bool", "label": attr_name, "value": attr_value}
            elif isinstance(attr_value, int):
                properties[attr_name] = {"type": "int", "label": attr_name, "value": attr_value}
            elif isinstance(attr_value, float):
                properties[attr_name] = {"type": "float", "label": attr_name, "value": attr_value}
            elif isinstance(attr_value, dict):
                properties[attr_name] = {"type": "dict", "label": attr_name, "value": attr_value}

        return properties

    def _add_property_editor(self, prop_name: str, prop_info: Dict[str, Any], obj: Any):
        prop_type = prop_info.get("type", "string")
        label = prop_info.get("label", prop_name)
        value = prop_info.get("value", getattr(obj, prop_name, ""))

        editor = None

        if prop_type == "string":
            editor = QLineEdit(str(value))
            editor.textChanged.connect(
                lambda val, name=prop_name: self._on_property_changed(name, val)
            )
        elif prop_type == "text":
            editor = QTextEdit(str(value))
            editor.setFixedHeight(80)
            editor.textChanged.connect(
                lambda name=prop_name: self._on_property_changed(name, editor.toPlainText())
            )
        elif prop_type == "bool":
            editor = QCheckBox()
            editor.setChecked(bool(value))
            editor.stateChanged.connect(
                lambda state, name=prop_name: self._on_property_changed(name, state == Qt.Checked)
            )
        elif prop_type == "int":
            editor = QSpinBox()
            editor.setRange(-1000000, 1000000)
            editor.setValue(int(value or 0))
            editor.valueChanged.connect(
                lambda val, name=prop_name: self._on_property_changed(name, val)
            )
        elif prop_type == "float":
            editor = QDoubleSpinBox()
            editor.setRange(-1000000.0, 1000000.0)
            editor.setDecimals(2)
            editor.setValue(float(value or 0.0))
            editor.valueChanged.connect(
                lambda val, name=prop_name: self._on_property_changed(name, val)
            )
        elif prop_type == "select":
            editor = QComboBox()
            options = prop_info.get("options", [])
            for opt in options:
                if isinstance(opt, tuple):
                    editor.addItem(opt[1], opt[0])
                else:
                    editor.addItem(str(opt), opt)
            idx = editor.findData(value)
            if idx >= 0:
                editor.setCurrentIndex(idx)
            editor.currentIndexChanged.connect(
                lambda idx, name=prop_name: self._on_property_changed(name, editor.itemData(idx))
            )
        elif prop_type == "color":
            editor = QPushButton()
            editor.setStyleSheet(f"background-color: {value or '#ffffff'};")
            editor.clicked.connect(
                lambda checked, name=prop_name, btn=editor: self._pick_color(name, btn)
            )
        elif prop_type == "dict":
            editor = QPushButton("编辑 JSON")
            editor.clicked.connect(
                lambda checked, name=prop_name: self._edit_json(name, value)
            )

        if editor:
            self._editors[prop_name] = editor
            label_widget = QLabel(label)
            label_widget.setStyleSheet("color: #666;")
            self._form_layout.addRow(label_widget, editor)

    def _on_property_changed(self, prop_name: str, value: Any):
        if self._current_object is not None:
            if hasattr(self._current_object, "update"):
                self._current_object.update(**{prop_name: value})
            else:
                setattr(self._current_object, prop_name, value)

            self.property_changed.emit(
                getattr(self._current_object, "id", ""),
                prop_name,
                value
            )

    def _pick_color(self, prop_name: str, button: QPushButton):
        current_color = button.styleSheet().split(":")[-1].strip("; ")
        color = QColorDialog.getColor(QColor(current_color), self, "选择颜色")
        if color.isValid():
            color_str = color.name()
            button.setStyleSheet(f"background-color: {color_str};")
            self._on_property_changed(prop_name, color_str)

    def _edit_json(self, prop_name: str, value: Any):
        from utils import to_json
        dialog = QWidget()
        dialog.setWindowTitle("编辑 JSON")
        dialog.resize(400, 300)
        layout = QVBoxLayout(dialog)
        editor = QTextEdit(to_json(value or {}))
        layout.addWidget(editor)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        btn_layout.addStretch(1)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        ok_btn.clicked.connect(dialog.accept if hasattr(dialog, 'accept') else dialog.close)
        cancel_btn.clicked.connect(dialog.close if hasattr(dialog, 'close') else dialog.hide)

        if dialog.exec() if hasattr(dialog, 'exec') else True:
            try:
                from utils import from_json
                data = from_json(editor.toPlainText())
                self._on_property_changed(prop_name, data)
            except Exception as e:
                pass

    def update_value(self, prop_name: str, value: Any):
        editor = self._editors.get(prop_name)
        if editor:
            if isinstance(editor, QLineEdit):
                editor.setText(str(value))
            elif isinstance(editor, QCheckBox):
                editor.setChecked(bool(value))
            elif isinstance(editor, QSpinBox):
                editor.setValue(int(value))
            elif isinstance(editor, QDoubleSpinBox):
                editor.setValue(float(value))
