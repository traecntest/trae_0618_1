import json
from typing import Any, Dict, List, Optional
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QDrag, QColor, QAction
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QToolBar,
    QMessageBox, QFileDialog, QInputDialog, QLineEdit,
    QListWidget, QListWidgetItem, QLabel, QFrame, QScrollArea,
    QComboBox, QDialog, QDialogButtonBox, QPushButton, QSlider,
    QGraphicsDropShadowEffect
)
from widgets import PropertyEditor
from core.models.page import PageSchema, Component, ResponsiveConfig
from config.settings import PAGE_COMPONENTS
from utils.id_generator import generate_id
from utils import to_json, from_json


class ComponentPalette(QScrollArea):
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

        title = QLabel("组件面板")
        title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 8px;")
        layout.addWidget(title)

        for comp in PAGE_COMPONENTS:
            item_widget = QFrame()
            item_widget.setStyleSheet("""
                QFrame {
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                    padding: 8px;
                }
                QFrame:hover {
                    background-color: #f0f7ff;
                    border-color: #1890ff;
                }
            """)
            item_widget.setCursor(Qt.PointingHandCursor)

            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(8, 4, 8, 4)

            icon_label = QLabel(comp.get("icon", "📦"))
            icon_label.setStyleSheet("font-size: 16px;")
            icon_label.setFixedWidth(28)

            name_label = QLabel(comp.get("name", comp["type"]))
            name_label.setStyleSheet("font-size: 13px;")

            item_layout.addWidget(icon_label)
            item_layout.addWidget(name_label, 1)

            item_widget.mousePressEvent = lambda e, c=comp: self._start_drag(e, c)

            layout.addWidget(item_widget)

        layout.addStretch(1)
        self.setWidget(container)

    def _start_drag(self, event, component_info):
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setData("application/x-page-component", json.dumps(component_info).encode())
            drag.setMimeData(mime_data)
            drag.exec_(Qt.CopyAction)


class PageCanvas(QScrollArea):
    component_added = Signal(object)
    component_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._components: List[Dict[str, Any]] = []
        self._selected_component_id: Optional[str] = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setAcceptDrops(True)

        self._canvas_widget = QFrame()
        self._canvas_widget.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
            }
        """)

        self._canvas_layout = QVBoxLayout(self._canvas_widget)
        self._canvas_layout.setContentsMargins(24, 24, 24, 24)
        self._canvas_layout.setSpacing(16)

        self._canvas_layout.addStretch(1)
        self.setWidget(self._canvas_widget)

    def set_device_size(self, device_type: str):
        size_map = {
            "desktop": {"width": 1200, "name": "桌面端"},
            "tablet": {"width": 768, "name": "平板"},
            "mobile": {"width": 375, "name": "移动端"},
        }
        size = size_map.get(device_type, size_map["desktop"])
        self._canvas_widget.setMinimumWidth(size["width"])
        self._canvas_widget.setMaximumWidth(size["width"])

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-page-component"):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-page-component"):
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-page-component"):
            component_info = json.loads(event.mimeData().data("application/x-page-component"))
            component_data = {
                "id": generate_id(),
                "type": component_info["type"],
                "name": component_info.get("name", component_info["type"]),
                "config": component_info.get("default_config", {}),
                "responsive": {
                    "xs": {"span": 24},
                    "sm": {"span": 24},
                    "md": {"span": 12},
                    "lg": {"span": 8},
                    "xl": {"span": 6},
                },
                "children": [],
            }

            component_widget = self._create_component_widget(component_data)
            insert_pos = self._canvas_layout.count() - 1
            self._canvas_layout.insertWidget(insert_pos, component_widget)

            self._components.append(component_data)
            self.component_added.emit(component_data)
            event.acceptProposedAction()

    def _create_component_widget(self, component_data: Dict[str, Any]) -> QFrame:
        widget = QFrame()
        widget.setProperty("component_id", component_data["id"])
        widget.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 2px solid transparent;
                border-radius: 8px;
                padding: 16px;
            }
            QFrame:hover {
                border-color: #91d5ff;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        widget.setGraphicsEffect(shadow)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        component_type = component_data["type"]
        content = self._render_component_preview(component_type, component_data.get("config", {}))
        layout.addWidget(content)

        widget.mousePressEvent = lambda e, cid=component_data["id"]: self._on_component_clicked(e, cid)

        return widget

    def _render_component_preview(self, component_type: str, config: Dict[str, Any]) -> QWidget:
        container = QFrame()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        type_label = QLabel(f"[{component_type}] {config.get('title', '组件')}")
        type_label.setStyleSheet("font-size: 12px; color: #1890ff; font-weight: bold;")
        layout.addWidget(type_label)

        if component_type == "navbar":
            nav = QFrame()
            nav.setStyleSheet("background-color: #001529; min-height: 48px; border-radius: 4px;")
            nav_layout = QHBoxLayout(nav)
            nav_layout.setContentsMargins(16, 0, 16, 0)

            logo = QLabel(config.get("logo", "LOGO"))
            logo.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")
            nav_layout.addWidget(logo)
            nav_layout.addStretch(1)

            for item in config.get("menu_items", ["首页", "关于", "联系"]):
                menu_item = QLabel(item)
                menu_item.setStyleSheet("color: rgba(255,255,255,0.75); padding: 0 8px;")
                nav_layout.addWidget(menu_item)

            layout.addWidget(nav)

        elif component_type == "hero":
            hero = QFrame()
            hero.setStyleSheet("background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 180px; border-radius: 8px;")
            hero_layout = QVBoxLayout(hero)
            hero_layout.setContentsMargins(40, 40, 40, 40)

            title = QLabel(config.get("title", "欢迎使用"))
            title.setStyleSheet("color: white; font-size: 28px; font-weight: bold;")
            hero_layout.addWidget(title)

            subtitle = QLabel(config.get("subtitle", "这是一个副标题"))
            subtitle.setStyleSheet("color: rgba(255,255,255,0.85); font-size: 14px;")
            hero_layout.addWidget(subtitle)

            hero_layout.addSpacing(16)

            btn_layout = QHBoxLayout()
            btn = QPushButton(config.get("button_text", "立即开始"))
            btn.setStyleSheet("""
                QPushButton {
                    padding: 8px 24px;
                    background-color: #52c41a;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 14px;
                }
            """)
            btn_layout.addWidget(btn)
            btn_layout.addStretch(1)
            hero_layout.addLayout(btn_layout)

            layout.addWidget(hero)

        elif component_type == "card":
            card = QFrame()
            card.setStyleSheet("background-color: #fafafa; border: 1px solid #e8e8e8; border-radius: 8px;")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 16, 16, 16)

            card_title = QLabel(config.get("title", "卡片标题"))
            card_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
            card_layout.addWidget(card_title)

            card_desc = QLabel(config.get("description", "这是卡片的描述内容"))
            card_desc.setStyleSheet("font-size: 13px; color: #666;")
            card_desc.setWordWrap(True)
            card_layout.addWidget(card_desc)

            layout.addWidget(card)

        elif component_type == "button":
            btn = QPushButton(config.get("text", "按钮"))
            btn_type = config.get("type", "primary")
            btn_style = {
                "primary": "background-color: #1890ff; color: white;",
                "success": "background-color: #52c41a; color: white;",
                "warning": "background-color: #faad14; color: white;",
                "danger": "background-color: #ff4d4f; color: white;",
                "default": "background-color: #ffffff; color: #333; border: 1px solid #d9d9d9;",
            }
            btn.setStyleSheet(f"""
                QPushButton {{
                    padding: 8px 24px;
                    {btn_style.get(btn_type, btn_style["primary"])}
                    border: none;
                    border-radius: 4px;
                    font-size: 14px;
                }}
            """)
            layout.addWidget(btn)

        elif component_type == "form":
            form_preview = QLabel("📋 表单组件 - 可绑定已设计的表单")
            form_preview.setStyleSheet("font-size: 14px; color: #666; padding: 20px;")
            form_preview.setAlignment(Qt.AlignCenter)
            layout.addWidget(form_preview)

        elif component_type == "table":
            table_preview = QLabel("📊 表格组件 - 可绑定数据表")
            table_preview.setStyleSheet("font-size: 14px; color: #666; padding: 20px;")
            table_preview.setAlignment(Qt.AlignCenter)
            layout.addWidget(table_preview)

        elif component_type == "list":
            for i in range(3):
                item = QFrame()
                item.setStyleSheet("background-color: #f5f5f5; border-radius: 4px; padding: 12px;")
                item_layout = QHBoxLayout(item)

                icon = QLabel("📄")
                icon.setFixedWidth(24)
                item_layout.addWidget(icon)

                text = QLabel(f"列表项 {i + 1}")
                text.setStyleSheet("font-size: 13px;")
                item_layout.addWidget(text, 1)

                layout.addWidget(item)

        else:
            preview = QLabel(f"📦 {component_type} 组件")
            preview.setStyleSheet("font-size: 14px; color: #666; padding: 20px;")
            preview.setAlignment(Qt.AlignCenter)
            layout.addWidget(preview)

        return container

    def _on_component_clicked(self, event, component_id: str):
        if event.button() == Qt.LeftButton:
            for i in range(self._canvas_layout.count()):
                item = self._canvas_layout.itemAt(i)
                if item.widget():
                    widget = item.widget()
                    if widget.property("component_id") == component_id:
                        widget.setStyleSheet("""
                            QFrame {
                                background-color: #e6f7ff;
                                border: 2px solid #1890ff;
                                border-radius: 8px;
                                padding: 16px;
                            }
                        """)
                    else:
                        widget.setStyleSheet("""
                            QFrame {
                                background-color: #ffffff;
                                border: 2px solid transparent;
                                border-radius: 8px;
                                padding: 16px;
                            }
                            QFrame:hover {
                                border-color: #91d5ff;
                            }
                        """)

            self._selected_component_id = component_id
            self.component_selected.emit(component_id)

    def get_components(self) -> List[Dict[str, Any]]:
        return self._components.copy()

    def get_component(self, component_id: str) -> Optional[Dict[str, Any]]:
        for comp in self._components:
            if comp["id"] == component_id:
                return comp
        return None

    def clear(self):
        while self._canvas_layout.count() > 0:
            item = self._canvas_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._components.clear()
        self._selected_component_id = None
        self._canvas_layout.addStretch(1)


class PageDesigner(QWidget):
    page_changed = Signal(dict)
    page_saved = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._page_schema: Optional[PageSchema] = None
        self._selected_component: Optional[Dict[str, Any]] = None
        self._current_device: str = "desktop"
        self._setup_ui()
        self._create_new_page()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._setup_toolbar()
        layout.addWidget(self._toolbar)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)

        self._component_palette = ComponentPalette()
        self._component_palette.setFixedWidth(200)
        splitter.addWidget(self._component_palette)

        center_panel = self._create_center_panel()
        splitter.addWidget(center_panel)

        self._property_editor = PropertyEditor()
        self._property_editor.setFixedWidth(280)
        splitter.addWidget(self._property_editor)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)

        layout.addWidget(splitter, 1)

        self._connect_signals()

    def _create_center_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        device_bar = QFrame()
        device_bar.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e0e0e0;")
        device_layout = QHBoxLayout(device_bar)
        device_layout.setContentsMargins(16, 8, 16, 8)
        device_layout.setSpacing(8)

        device_label = QLabel("设备预览：")
        device_label.setStyleSheet("font-size: 13px; color: #666;")
        device_layout.addWidget(device_label)

        self._device_combo = QComboBox()
        self._device_combo.addItems([
            "🖥️ 桌面端 (1200px)",
            "📱 平板 (768px)",
            "📲 移动端 (375px)",
        ])
        self._device_combo.currentIndexChanged.connect(self._on_device_changed)
        self._device_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 12px;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                font-size: 13px;
            }
        """)
        device_layout.addWidget(self._device_combo)

        device_layout.addStretch(1)

        zoom_label = QLabel("缩放：")
        zoom_label.setStyleSheet("font-size: 13px; color: #666;")
        device_layout.addWidget(zoom_label)

        self._zoom_slider = QSlider(Qt.Horizontal)
        self._zoom_slider.setRange(50, 150)
        self._zoom_slider.setValue(100)
        self._zoom_slider.setFixedWidth(100)
        self._zoom_slider.valueChanged.connect(self._on_zoom_changed)
        device_layout.addWidget(self._zoom_slider)

        self._zoom_value = QLabel("100%")
        self._zoom_value.setStyleSheet("font-size: 13px; color: #666;")
        device_layout.addWidget(self._zoom_value)

        layout.addWidget(device_bar)

        self._canvas = PageCanvas()
        layout.addWidget(self._canvas, 1)

        return panel

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
        new_action.triggered.connect(self._create_new_page)
        self._toolbar.addAction(new_action)

        save_action = QAction("保存", self)
        save_action.triggered.connect(self._save_page)
        self._toolbar.addAction(save_action)

        load_action = QAction("加载", self)
        load_action.triggered.connect(self._load_page)
        self._toolbar.addAction(load_action)

        self._toolbar.addSeparator()

        preview_action = QAction("预览", self)
        preview_action.triggered.connect(self._preview_page)
        self._toolbar.addAction(preview_action)

        generate_action = QAction("生成代码", self)
        generate_action.triggered.connect(self._generate_code)
        self._toolbar.addAction(generate_action)

        export_action = QAction("导出JSON", self)
        export_action.triggered.connect(self._export_page)
        self._toolbar.addAction(export_action)

        clear_action = QAction("清空", self)
        clear_action.triggered.connect(self._clear_canvas)
        self._toolbar.addAction(clear_action)

    def _connect_signals(self):
        self._canvas.component_added.connect(self._on_component_added)
        self._canvas.component_selected.connect(self._on_component_selected)
        self._property_editor.property_changed.connect(self._on_property_changed)

    def _on_device_changed(self, index: int):
        device_map = {0: "desktop", 1: "tablet", 2: "mobile"}
        self._current_device = device_map.get(index, "desktop")
        self._canvas.set_device_size(self._current_device)

    def _on_zoom_changed(self, value: int):
        self._zoom_value.setText(f"{value}%")

    def _on_component_added(self, component_data: Dict[str, Any]):
        self._update_page_schema()

    def _on_component_selected(self, component_id: str):
        self._selected_component = self._canvas.get_component(component_id)
        if self._selected_component:
            self._property_editor.set_object(self._selected_component)

    def _on_property_changed(self, obj_id: str, prop_name: str, value: Any):
        comp = self._canvas.get_component(obj_id)
        if comp:
            if prop_name in comp:
                comp[prop_name] = value
            else:
                comp.setdefault("config", {})
                comp["config"][prop_name] = value
            self._update_page_schema()

    def _create_new_page(self):
        self._clear_canvas()
        name, ok = QInputDialog.getText(
            self, "新建页面",
            "请输入页面名称:",
            QLineEdit.Normal,
            f"Page_{len(self._canvas.get_components()) + 1}"
        )
        if ok and name:
            self._page_schema = PageSchema(
                name=name,
                description="",
                route=f"/{name.lower().replace(' ', '_')}",
                components=[],
                responsive=ResponsiveConfig(breakpoints={
                    "xs": 0, "sm": 576, "md": 768, "lg": 992, "xl": 1200
                }),
            )
            self.page_changed.emit(self._page_schema.model_dump())

    def _clear_canvas(self):
        self._canvas.clear()
        self._selected_component = None
        self._property_editor.set_object(None)

        if self._page_schema:
            self._page_schema.components = []
            self.page_changed.emit(self._page_schema.model_dump())

    def _update_page_schema(self):
        if self._page_schema is None:
            return

        components = []
        for comp_data in self._canvas.get_components():
            comp = Component(**comp_data)
            components.append(comp)

        self._page_schema.components = components
        self.page_changed.emit(self._page_schema.model_dump())

    def _save_page(self):
        if self._page_schema is None:
            return

        self._update_page_schema()

        from core.storage.json_store import JsonStore
        store = JsonStore("pages")
        store.save(self._page_schema.id, self._page_schema.model_dump())

        self.page_saved.emit(self._page_schema.model_dump())
        QMessageBox.information(self, "保存成功", f"页面 '{self._page_schema.name}' 已保存！")

    def _load_page(self):
        from core.storage.json_store import JsonStore
        store = JsonStore("pages")
        page_ids = store.list_ids()

        if not page_ids:
            QMessageBox.information(self, "提示", "没有可加载的页面")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("选择页面")
        dialog.resize(300, 100)
        layout = QVBoxLayout(dialog)

        combo = QComboBox()
        for pid in page_ids:
            data = store.load(pid)
            combo.addItem(data.get("name", pid), pid)
        layout.addWidget(combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.Accepted:
            page_id = combo.currentData()
            page_data = store.load(page_id)
            if page_data:
                self._load_page_data(page_data)

    def _load_page_data(self, page_data: Dict[str, Any]):
        self._clear_canvas()
        self._page_schema = PageSchema(**page_data)

        for comp in self._page_schema.components:
            comp_data = comp.model_dump()
            component_widget = self._canvas._create_component_widget(comp_data)
            insert_pos = self._canvas._canvas_layout.count() - 1
            self._canvas._canvas_layout.insertWidget(insert_pos, component_widget)
            self._canvas._components.append(comp_data)

        self.page_changed.emit(self._page_schema.model_dump())

    def _preview_page(self):
        if self._page_schema is None or not self._canvas.get_components():
            QMessageBox.information(self, "提示", "请先添加页面组件")
            return

        self._update_page_schema()

        from PySide6.QtWidgets import QMainWindow
        preview = QMainWindow(self, Qt.Window)
        preview.setWindowTitle(f"预览: {self._page_schema.name}")
        preview.resize(1000, 700)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QFrame()
        content.setStyleSheet("background-color: #ffffff;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)

        for comp_data in self._canvas.get_components():
            preview_widget = self._canvas._create_component_widget(comp_data)
            content_layout.addWidget(preview_widget)

        content_layout.addStretch(1)
        scroll.setWidget(content)
        preview.setCentralWidget(scroll)

        preview.show()

    def _generate_code(self):
        if self._page_schema is None:
            return

        self._update_page_schema()

        try:
            from core.engine.app_generator import AppGenerator
            generator = AppGenerator()
            vue_code = generator.generate_single_page(self._page_schema)

            dialog = QDialog(self)
            dialog.setWindowTitle("生成的 Vue 代码")
            dialog.resize(800, 500)
            layout = QVBoxLayout(dialog)

            from PySide6.QtWidgets import QTextEdit
            code_edit = QTextEdit()
            code_edit.setPlainText(vue_code)
            code_edit.setReadOnly(True)
            code_edit.setStyleSheet("""
                QTextEdit {
                    font-family: Consolas, Monaco, monospace;
                    font-size: 12px;
                    padding: 8px;
                }
            """)
            layout.addWidget(code_edit)

            buttons = QDialogButtonBox(QDialogButtonBox.Ok)
            buttons.accepted.connect(dialog.accept)
            layout.addWidget(buttons)

            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "生成失败", f"代码生成失败: {str(e)}")

    def _export_page(self):
        if self._page_schema is None:
            return

        self._update_page_schema()

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出页面",
            f"{self._page_schema.name}.json",
            "JSON Files (*.json)"
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(to_json(self._page_schema.model_dump(), indent=2))
            QMessageBox.information(self, "导出成功", f"页面已导出到 {file_path}")

    def get_page_schema(self) -> Optional[PageSchema]:
        self._update_page_schema()
        return self._page_schema

    def set_page_schema(self, page_schema: PageSchema):
        self._load_page_data(page_schema.model_dump())
