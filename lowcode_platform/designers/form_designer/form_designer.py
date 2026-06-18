from typing import Any, Dict, List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QToolBar,
    QMessageBox, QFileDialog, QInputDialog, QLineEdit
)
from widgets import WidgetPalette, DropCanvas, PropertyEditor
from core.models.form import FormSchema, FieldSchema, LayoutConfig
from utils.id_generator import generate_id
from utils import to_json, from_json


class FormDesigner(QWidget):
    form_changed = Signal(dict)
    form_saved = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._form_schema: Optional[FormSchema] = None
        self._selected_field: Optional[Any] = None
        self._field_widgets: Dict[str, Any] = {}
        self._setup_ui()
        self._create_new_form()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._setup_toolbar()
        layout.addWidget(self._toolbar)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)

        self._widget_palette = WidgetPalette()
        self._widget_palette.setFixedWidth(200)
        splitter.addWidget(self._widget_palette)

        self._drop_canvas = DropCanvas()
        splitter.addWidget(self._drop_canvas)

        self._property_editor = PropertyEditor()
        self._property_editor.setFixedWidth(280)
        splitter.addWidget(self._property_editor)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)

        layout.addWidget(splitter, 1)

        self._connect_signals()

    def _setup_toolbar(self):
        self._toolbar = QToolBar()
        self._toolbar.setMovable(False)
        self._toolbar.setStyleSheet("""
            QToolBar {
                background-color: #ffffff;
                border-bottom: 1px solid #e0e0e0;
                padding: 4px;
                spacing: 4px;
            }
            QToolButton {
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 13px;
            }
            QToolButton:hover {
                background-color: #f0f7ff;
            }
        """)

        new_action = QAction("新建", self)
        new_action.triggered.connect(self._create_new_form)
        self._toolbar.addAction(new_action)

        save_action = QAction("保存", self)
        save_action.triggered.connect(self._save_form)
        self._toolbar.addAction(save_action)

        load_action = QAction("加载", self)
        load_action.triggered.connect(self._load_form)
        self._toolbar.addAction(load_action)

        self._toolbar.addSeparator()

        preview_action = QAction("预览", self)
        preview_action.triggered.connect(self._preview_form)
        self._toolbar.addAction(preview_action)

        export_action = QAction("导出JSON", self)
        export_action.triggered.connect(self._export_form)
        self._toolbar.addAction(export_action)

        clear_action = QAction("清空", self)
        clear_action.triggered.connect(self._clear_canvas)
        self._toolbar.addAction(clear_action)

    def _connect_signals(self):
        self._drop_canvas.field_added.connect(self._on_field_added)
        self._property_editor.property_changed.connect(self._on_property_changed)

    def _on_field_added(self, child):
        if hasattr(child, "field_selected"):
            child.field_selected.connect(self._on_field_selected)
            child.field_deleted.connect(self._on_field_deleted)
            self._field_widgets[child.field_id] = child
            self._update_form_schema()

    def _on_field_selected(self, field_id: str):
        for fid, widget in self._field_widgets.items():
            widget.set_selected(fid == field_id)

        self._selected_field = self._field_widgets.get(field_id)
        self._property_editor.set_object(self._selected_field)

    def _on_field_deleted(self, field_id: str):
        widget = self._field_widgets.pop(field_id, None)
        if widget:
            widget.deleteLater()
            self._selected_field = None
            self._property_editor.set_object(None)
            self._update_form_schema()

    def _on_property_changed(self, obj_id: str, prop_name: str, value: Any):
        field = self._field_widgets.get(obj_id)
        if field:
            field.update_field(**{prop_name: value})
            self._update_form_schema()

    def _create_new_form(self):
        self._clear_canvas()
        name, ok = QInputDialog.getText(
            self, "新建表单",
            "请输入表单名称:",
            QLineEdit.Normal,
            f"新建表单_{len(self._field_widgets) + 1}"
        )
        if ok and name:
            self._form_schema = FormSchema(
                name=name,
                description="",
                fields=[],
                layout=LayoutConfig(type="vertical")
            )
            self.form_changed.emit(self._form_schema.model_dump())

    def _clear_canvas(self):
        for widget in self._field_widgets.values():
            widget.deleteLater()
        self._field_widgets.clear()
        self._selected_field = None
        self._property_editor.set_object(None)

        if self._form_schema:
            self._form_schema.fields = []
            self.form_changed.emit(self._form_schema.model_dump())

    def _update_form_schema(self):
        if self._form_schema is None:
            return

        fields = []
        for field_id, widget in self._field_widgets.items():
            field_data = widget.to_dict()
            field_schema = FieldSchema(**field_data)
            fields.append(field_schema)

        self._form_schema.fields = fields
        self.form_changed.emit(self._form_schema.model_dump())

    def _save_form(self):
        if self._form_schema is None:
            return

        self._update_form_schema()

        from core.storage.json_store import JsonStore
        store = JsonStore("forms")
        store.save(self._form_schema.id, self._form_schema.model_dump())

        self.form_saved.emit(self._form_schema.model_dump())
        QMessageBox.information(self, "保存成功", f"表单 '{self._form_schema.name}' 已保存！")

    def _load_form(self):
        from core.storage.json_store import JsonStore
        store = JsonStore("forms")
        form_ids = store.list_ids()

        if not form_ids:
            QMessageBox.information(self, "提示", "没有可加载的表单")
            return

        from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox
        dialog = QDialog(self)
        dialog.setWindowTitle("选择表单")
        dialog.resize(300, 100)
        layout = QVBoxLayout(dialog)

        combo = QComboBox()
        for fid in form_ids:
            data = store.load(fid)
            combo.addItem(data.get("name", fid), fid)
        layout.addWidget(combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.Accepted:
            form_id = combo.currentData()
            form_data = store.load(form_id)
            if form_data:
                self._load_form_data(form_data)

    def _load_form_data(self, form_data: Dict[str, Any]):
        self._clear_canvas()
        self._form_schema = FormSchema(**form_data)

        for field in self._form_schema.fields:
            widget_info = {"name": field.label, "type": field.type}
            widget = self._drop_canvas._create_field_widget(field.type, widget_info, None)
            widget.field_id = field.id
            widget.field_name = field.name
            widget.field_label = field.label
            widget.required = field.required
            widget.placeholder = field.placeholder
            widget.default_value = field.default_value
            widget.options = field.options if hasattr(field, 'options') else []

            widget.update_field(
                name=field.label,
                required=field.required,
                placeholder=field.placeholder,
                options=field.options if hasattr(field, 'options') else []
            )

            widget.field_selected.connect(self._on_field_selected)
            widget.field_deleted.connect(self._on_field_deleted)

            self._drop_canvas.layout().addWidget(widget)
            self._field_widgets[field.id] = widget

        self.form_changed.emit(self._form_schema.model_dump())

    def _preview_form(self):
        if self._form_schema is None or not self._field_widgets:
            QMessageBox.information(self, "提示", "请先添加表单字段")
            return

        dialog = QWidget(self, Qt.Window)
        dialog.setWindowTitle("表单预览")
        dialog.resize(500, 600)
        dialog.setStyleSheet("background-color: #ffffff;")

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLineEdit(self._form_schema.name)
        title.setReadOnly(True)
        title.setStyleSheet("""
            QLineEdit {
                font-size: 18px;
                font-weight: bold;
                border: none;
                padding: 0;
                background: transparent;
            }
        """)
        layout.addWidget(title)

        if self._form_schema.description:
            desc = QLineEdit(self._form_schema.description)
            desc.setReadOnly(True)
            desc.setStyleSheet("color: #666; border: none; padding: 0; background: transparent;")
            layout.addWidget(desc)

        layout.addSpacing(8)

        for widget in self._field_widgets.values():
            preview_widget = self._create_preview_field(widget)
            layout.addWidget(preview_widget)

        layout.addStretch(1)

        from PySide6.QtWidgets import QPushButton
        btn_layout = QHBoxLayout()
        submit_btn = QPushButton("提交")
        submit_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 32px;
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
        """)
        submit_btn.clicked.connect(dialog.close)
        btn_layout.addStretch(1)
        btn_layout.addWidget(submit_btn)
        layout.addLayout(btn_layout)

        dialog.show()

    def _create_preview_field(self, widget: Any) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        label_text = f"{widget.field_label} *" if widget.required else widget.field_label
        label = QLabel(label_text)
        label.setStyleSheet("font-size: 14px; font-weight: 500; color: #333;")
        layout.addWidget(label)

        input_widget = self._create_preview_input(widget)
        layout.addWidget(input_widget)

        return container

    def _create_preview_input(self, widget: Any) -> QWidget:
        if widget.widget_type == "text":
            input_w = QLineEdit()
            input_w.setPlaceholderText(widget.placeholder or f"请输入{widget.field_label}")
        elif widget.widget_type == "textarea":
            input_w = QLineEdit()
            input_w.setPlaceholderText(widget.placeholder or f"请输入{widget.field_label}")
        elif widget.widget_type == "number":
            from PySide6.QtWidgets import QSpinBox
            input_w = QSpinBox()
            input_w.setRange(-1000000, 1000000)
        elif widget.widget_type == "select":
            input_w = QLineEdit()
            input_w.setPlaceholderText(f"请选择{widget.field_label}")
        elif widget.widget_type == "checkbox":
            input_w = QCheckBox()
            input_w.setText(widget.field_label)
        elif widget.widget_type == "date":
            from PySide6.QtWidgets import QDateEdit
            input_w = QDateEdit()
            input_w.setCalendarPopup(True)
            input_w.setDisplayFormat("yyyy-MM-dd")
        elif widget.widget_type == "datetime":
            from PySide6.QtWidgets import QDateTimeEdit
            input_w = QDateTimeEdit()
            input_w.setCalendarPopup(True)
            input_w.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        elif widget.widget_type in ["file", "image"]:
            input_w = QLineEdit()
            input_w.setPlaceholderText("点击上传")
            input_w.setReadOnly(True)
        else:
            input_w = QLineEdit()
            input_w.setPlaceholderText(widget.placeholder or f"请输入{widget.field_label}")

        input_w.setStyleSheet("""
            QLineEdit, QSpinBox, QDateEdit, QDateTimeEdit {
                padding: 8px 12px;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus, QSpinBox:focus, QDateEdit:focus, QDateTimeEdit:focus {
                border-color: #1890ff;
            }
        """)
        return input_w

    def _export_form(self):
        if self._form_schema is None:
            return

        self._update_form_schema()

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出表单",
            f"{self._form_schema.name}.json",
            "JSON Files (*.json)"
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(to_json(self._form_schema.model_dump(), indent=2))
            QMessageBox.information(self, "导出成功", f"表单已导出到 {file_path}")

    def get_form_schema(self) -> Optional[FormSchema]:
        self._update_form_schema()
        return self._form_schema

    def set_form_schema(self, form_schema: FormSchema):
        self._load_form_data(form_schema.model_dump())
