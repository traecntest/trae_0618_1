import json
from typing import Any, Dict, List, Optional
from PySide6.QtCore import Qt, Signal, QPointF, QRectF, QMimeData
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath, QDrag, QAction
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QToolBar,
    QMessageBox, QFileDialog, QInputDialog, QLineEdit,
    QListWidget, QListWidgetItem, QLabel, QFrame, QScrollArea,
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsRectItem,
    QGraphicsTextItem, QGraphicsPathItem, QMenu, QDialog, QDialogButtonBox,
    QFormLayout, QComboBox, QCheckBox, QSpinBox, QPushButton
)
from widgets import PropertyEditor
from core.models.data_model import DataModel, TableSchema, Field, Relation
from config.settings import FIELD_TYPES, RELATION_TYPES
from utils.id_generator import generate_id
from utils import to_json, from_json


class TableGraphicsItem(QGraphicsRectItem):
    table_selected = Signal(str)

    def __init__(self, table_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.table_data = table_data
        self.table_id = table_data.get("id", "")
        self.table_name = table_data.get("name", "table")
        self.fields: List[Dict[str, Any]] = table_data.get("fields", [])

        self._calculate_size()
        self._setup_appearance()
        self._setup_interaction()

    def _calculate_size(self):
        width = 200
        header_height = 40
        field_height = 28
        height = header_height + len(self.fields) * field_height + 10
        self.setRect(0, 0, width, max(height, 80))

    def _setup_appearance(self):
        self.setBrush(QBrush(QColor("#ffffff")))
        self.setPen(QPen(QColor("#1890ff"), 2))
        self.setCornerRadius(8)
        self.setAcceptHoverEvents(True)

        name_item = QGraphicsTextItem(self.table_name, self)
        name_item.setDefaultTextColor(QColor("#ffffff"))
        font = name_item.font()
        font.setBold(True)
        font.setPointSize(11)
        name_item.setFont(font)
        name_item.setPos(12, 10)

        header_rect = QGraphicsRectItem(0, 0, self.rect().width(), 40, self)
        header_rect.setBrush(QBrush(QColor("#1890ff")))
        header_rect.setPen(QPen(Qt.NoPen))
        header_rect.setZValue(-1)

        y = 45
        for i, field in enumerate(self.fields):
            field_name = field.get("name", "field")
            field_type = field.get("type", "string")
            is_pk = field.get("primary_key", False)
            is_fk = field.get("foreign_key", False)

            pk_icon = "🔑 " if is_pk else ("🔗 " if is_fk else "  ")
            field_text = f"{pk_icon}{field_name}: {field_type}"

            field_item = QGraphicsTextItem(field_text, self)
            field_item.setDefaultTextColor(QColor("#333333"))
            font = field_item.font()
            font.setPointSize(10)
            field_item.setFont(font)
            field_item.setPos(12, y)

            y += 28

    def _setup_interaction(self):
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setSelected(True)
            self.table_selected.emit(self.table_id)
        super().mousePressEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            pos = self.pos()
            self.table_data["position"]["x"] = int(pos.x())
            self.table_data["position"]["y"] = int(pos.y())
        return super().itemChange(change, value)

    def get_connection_point(self, relation_type: str) -> QPointF:
        rect = self.rect()
        if relation_type == "output":
            return self.pos() + QPointF(rect.width(), rect.height() / 2)
        else:
            return self.pos() + QPointF(0, rect.height() / 2)

    def contextMenuEvent(self, event):
        menu = QMenu()
        edit_action = QAction("编辑表", menu)
        add_field_action = QAction("添加字段", menu)
        delete_action = QAction("删除表", menu)

        edit_action.triggered.connect(lambda: self._handle_edit())
        add_field_action.triggered.connect(lambda: self._handle_add_field())
        delete_action.triggered.connect(lambda: self._handle_delete())

        menu.addAction(edit_action)
        menu.addAction(add_field_action)
        menu.addAction(delete_action)
        menu.exec_(event.screenPos())

    def _handle_edit(self):
        pass

    def _handle_add_field(self):
        pass

    def _handle_delete(self):
        if self.scene():
            self.scene().removeItem(self)


class RelationGraphicsItem(QGraphicsPathItem):
    def __init__(self, source_item: TableGraphicsItem, target_item: TableGraphicsItem, relation_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.source_item = source_item
        self.target_item = target_item
        self.relation_data = relation_data

        self.setPen(QPen(QColor("#666666"), 2))
        self.setZValue(-1)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.update_position()

    def update_position(self):
        start = self.source_item.get_connection_point("output")
        end = self.target_item.get_connection_point("input")

        path = QPainterPath()
        path.moveTo(start)

        dx = end.x() - start.x()
        ctrl_offset = min(abs(dx) / 2, 100)

        path.cubicTo(
            start.x() + ctrl_offset, start.y(),
            end.x() - ctrl_offset, end.y(),
            end.x(), end.y()
        )

        self.setPath(path)

        relation_type = self.relation_data.get("type", "one_to_many")
        type_map = {
            "one_to_one": "1:1",
            "one_to_many": "1:N",
            "many_to_many": "N:M",
        }
        label_text = type_map.get(relation_type, "")

        mid_x = (start.x() + end.x()) / 2
        mid_y = (start.y() + end.y()) / 2

        if hasattr(self, '_label_item') and self._label_item:
            self._label_item.setPlainText(label_text)
            self._label_item.setPos(mid_x - 20, mid_y - 12)
        else:
            self._label_item = QGraphicsTextItem(label_text, self)
            self._label_item.setDefaultTextColor(QColor("#1890ff"))
            font = self._label_item.font()
            font.setBold(True)
            self._label_item.setFont(font)
            self._label_item.setPos(mid_x - 20, mid_y - 12)

    def contextMenuEvent(self, event):
        menu = QMenu()
        delete_action = QAction("删除关系", menu)
        delete_action.triggered.connect(lambda: self._handle_delete())
        menu.addAction(delete_action)
        menu.exec_(event.screenPos())

    def _handle_delete(self):
        if self.scene():
            self.scene().removeItem(self)


class DataModelScene(QGraphicsScene):
    table_added = Signal(dict)
    table_deleted = Signal(str)
    relation_added = Signal(dict)
    relation_deleted = Signal(str, str)
    table_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 2000, 1500)
        self._tables: Dict[str, TableGraphicsItem] = {}
        self._relations: Dict[str, RelationGraphicsItem] = {}
        self._drawing_relation = False
        self._relation_source: Optional[TableGraphicsItem] = None
        self._temp_line = None
        self.setBackgroundBrush(QBrush(QColor("#fafafa")))

    def add_table(self, table_data: Dict[str, Any]) -> TableGraphicsItem:
        table = TableGraphicsItem(table_data)
        table.setPos(
            table_data.get("position", {}).get("x", 100),
            table_data.get("position", {}).get("y", 100)
        )
        table.table_selected.connect(self._on_table_selected)
        self.addItem(table)
        self._tables[table_data["id"]] = table
        self.table_added.emit(table_data)
        return table

    def remove_table(self, table_id: str):
        table = self._tables.pop(table_id, None)
        if table:
            relations_to_remove = []
            for rel_id, rel in self._relations.items():
                if rel.source_item == table or rel.target_item == table:
                    relations_to_remove.append(rel_id)

            for rel_id in relations_to_remove:
                self.remove_relation(rel_id)

            self.removeItem(table)
            self.table_deleted.emit(table_id)

    def add_relation(self, relation_data: Dict[str, Any], source_id: str, target_id: str) -> Optional[RelationGraphicsItem]:
        source = self._tables.get(source_id)
        target = self._tables.get(target_id)
        if not source or not target:
            return None

        relation = RelationGraphicsItem(source, target, relation_data)
        self.addItem(relation)
        self._relations[relation_data["id"]] = relation
        self.relation_added.emit(relation_data)
        return relation

    def remove_relation(self, relation_id: str):
        relation = self._relations.pop(relation_id, None)
        if relation:
            if relation.relation_data:
                self.relation_deleted.emit(
                    relation.relation_data.get("source_table", ""),
                    relation.relation_data.get("target_table", "")
                )
            self.removeItem(relation)

    def mousePressEvent(self, event):
        item = self.itemAt(event.scenePos(), self.views()[0].transform())
        if isinstance(item, TableGraphicsItem) and event.button() == Qt.RightButton:
            if not self._drawing_relation:
                self._drawing_relation = True
                self._relation_source = item
                self._temp_line = QGraphicsPathItem()
                self._temp_line.setPen(QPen(QColor("#1890ff"), 2, Qt.DashLine))
                self.addItem(self._temp_line)
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drawing_relation and self._temp_line:
            start = self._relation_source.get_connection_point("output")
            end = event.scenePos()

            path = QPainterPath()
            path.moveTo(start)
            path.lineTo(end)
            self._temp_line.setPath(path)

        for rel in self._relations.values():
            rel.update_position()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._drawing_relation and self._temp_line:
            item = self.itemAt(event.scenePos(), self.views()[0].transform())
            if isinstance(item, TableGraphicsItem) and item != self._relation_source:
                relation_data = {
                    "id": generate_id(),
                    "type": "one_to_many",
                    "source_table": self._relation_source.table_id,
                    "target_table": item.table_id,
                    "source_field": "",
                    "target_field": "",
                }
                self.add_relation(relation_data, self._relation_source.table_id, item.table_id)

            self.removeItem(self._temp_line)
            self._temp_line = None
            self._drawing_relation = False
            self._relation_source = None
            return

        super().mouseReleaseEvent(event)

    def _on_table_selected(self, table_id: str):
        self.table_clicked.emit(table_id)

    def clear_all(self):
        self.clear()
        self._tables.clear()
        self._relations.clear()
        self._drawing_relation = False
        self._relation_source = None
        self._temp_line = None

    def get_table(self, table_id: str) -> Optional[TableGraphicsItem]:
        return self._tables.get(table_id)


class DataModeler(QWidget):
    datamodel_changed = Signal(dict)
    datamodel_saved = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._datamodel: Optional[DataModel] = None
        self._selected_table: Optional[Dict[str, Any]] = None
        self._table_data: Dict[str, Dict[str, Any]] = {}
        self._setup_ui()
        self._create_new_datamodel()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._setup_toolbar()
        layout.addWidget(self._toolbar)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)

        left_panel = self._create_left_panel()
        left_panel.setFixedWidth(200)
        splitter.addWidget(left_panel)

        self._scene = DataModelScene()
        self._view = QGraphicsView(self._scene)
        self._view.setRenderHints(
            QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform
        )
        self._view.setDragMode(QGraphicsView.ScrollHandDrag)
        self._view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        splitter.addWidget(self._view)

        self._property_editor = PropertyEditor()
        self._property_editor.setFixedWidth(280)
        splitter.addWidget(self._property_editor)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)

        layout.addWidget(splitter, 1)

        self._connect_signals()

    def _create_left_panel(self) -> QWidget:
        panel = QFrame()
        panel.setStyleSheet("background-color: #ffffff; border-right: 1px solid #e0e0e0;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        title = QLabel("数据模型")
        title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 8px;")
        layout.addWidget(title)

        add_table_btn = QPushButton("➕ 添加数据表")
        add_table_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
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
        add_table_btn.clicked.connect(self._add_new_table)
        layout.addWidget(add_table_btn)

        self._table_list = QListWidget()
        self._table_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background-color: #f0f7ff;
            }
            QListWidget::item:selected {
                background-color: #e6f7ff;
                color: #1890ff;
            }
        """)
        self._table_list.itemDoubleClicked.connect(self._on_table_list_double_clicked)
        layout.addWidget(self._table_list, 1)

        hint = QLabel("提示：\n• 点击'添加数据表'创建新表\n• 右键表拖拽创建关联关系")
        hint.setStyleSheet("color: #999; font-size: 11px; padding: 8px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

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
        new_action.triggered.connect(self._create_new_datamodel)
        self._toolbar.addAction(new_action)

        save_action = QAction("保存", self)
        save_action.triggered.connect(self._save_datamodel)
        self._toolbar.addAction(save_action)

        load_action = QAction("加载", self)
        load_action.triggered.connect(self._load_datamodel)
        self._toolbar.addAction(load_action)

        self._toolbar.addSeparator()

        sql_action = QAction("生成SQL", self)
        sql_action.triggered.connect(self._generate_sql)
        self._toolbar.addAction(sql_action)

        export_action = QAction("导出JSON", self)
        export_action.triggered.connect(self._export_datamodel)
        self._toolbar.addAction(export_action)

        clear_action = QAction("清空", self)
        clear_action.triggered.connect(self._clear_canvas)
        self._toolbar.addAction(clear_action)

    def _connect_signals(self):
        self._scene.table_added.connect(self._on_table_added)
        self._scene.table_deleted.connect(self._on_table_deleted)
        self._scene.relation_added.connect(self._on_relation_added)
        self._scene.relation_deleted.connect(self._on_relation_deleted)
        self._scene.table_clicked.connect(self._on_table_clicked)
        self._property_editor.property_changed.connect(self._on_property_changed)

    def _add_new_table(self):
        name, ok = QInputDialog.getText(
            self, "新建数据表",
            "请输入表名:",
            QLineEdit.Normal,
            f"table_{len(self._table_data) + 1}"
        )
        if ok and name:
            table_data = {
                "id": generate_id(),
                "name": name,
                "description": "",
                "fields": [
                    {
                        "id": generate_id(),
                        "name": "id",
                        "type": "integer",
                        "primary_key": True,
                        "auto_increment": True,
                        "nullable": False,
                        "description": "主键",
                    }
                ],
                "position": {
                    "x": 100 + len(self._table_data) * 50,
                    "y": 100 + len(self._table_data) * 30,
                },
            }
            self._scene.add_table(table_data)

    def _on_table_list_double_clicked(self, item: QListWidgetItem):
        table_id = item.data(Qt.UserRole)
        table = self._scene.get_table(table_id)
        if table:
            self._view.centerOn(table)
            table.setSelected(True)
            self._selected_table = self._table_data.get(table_id)
            self._property_editor.set_object(self._selected_table)

    def _on_table_added(self, table_data: Dict[str, Any]):
        self._table_data[table_data["id"]] = table_data
        self._refresh_table_list()
        self._update_datamodel()

    def _on_table_deleted(self, table_id: str):
        self._table_data.pop(table_id, None)
        if self._selected_table and self._selected_table.get("id") == table_id:
            self._selected_table = None
            self._property_editor.set_object(None)
        self._refresh_table_list()
        self._update_datamodel()

    def _on_relation_added(self, relation_data: Dict[str, Any]):
        self._update_datamodel()

    def _on_relation_deleted(self, source_id: str, target_id: str):
        self._update_datamodel()

    def _on_table_clicked(self, table_id: str):
        self._selected_table = self._table_data.get(table_id)
        if self._selected_table:
            self._property_editor.set_object(self._selected_table)

    def _on_property_changed(self, obj_id: str, prop_name: str, value: Any):
        table = self._table_data.get(obj_id)
        if table:
            table[prop_name] = value
            self._update_datamodel()

    def _refresh_table_list(self):
        self._table_list.clear()
        for table_id, table_data in self._table_data.items():
            item = QListWidgetItem(f"📋 {table_data.get('name', 'table')}")
            item.setData(Qt.UserRole, table_id)
            self._table_list.addItem(item)

    def _create_new_datamodel(self):
        self._clear_canvas()
        name, ok = QInputDialog.getText(
            self, "新建数据模型",
            "请输入模型名称:",
            QLineEdit.Normal,
            f"DataModel_{len(self._table_data) + 1}"
        )
        if ok and name:
            self._datamodel = DataModel(
                name=name,
                description="",
                tables=[],
                relations=[],
            )
            self.datamodel_changed.emit(self._datamodel.model_dump())

    def _clear_canvas(self):
        self._scene.clear_all()
        self._table_data.clear()
        self._selected_table = None
        self._property_editor.set_object(None)
        self._table_list.clear()

        if self._datamodel:
            self._datamodel.tables = []
            self._datamodel.relations = []
            self.datamodel_changed.emit(self._datamodel.model_dump())

    def _update_datamodel(self):
        if self._datamodel is None:
            return

        tables = []
        for table_id, table_data in self._table_data.items():
            table = TableSchema(**table_data)
            tables.append(table)

        relations = []
        for rel_id, rel_item in self._scene._relations.items():
            if rel_item.relation_data:
                rel = Relation(**rel_item.relation_data)
                relations.append(rel)

        self._datamodel.tables = tables
        self._datamodel.relations = relations
        self.datamodel_changed.emit(self._datamodel.model_dump())

    def _save_datamodel(self):
        if self._datamodel is None:
            return

        self._update_datamodel()

        from core.storage.json_store import JsonStore
        store = JsonStore("datamodels")
        store.save(self._datamodel.id, self._datamodel.model_dump())

        self.datamodel_saved.emit(self._datamodel.model_dump())
        QMessageBox.information(self, "保存成功", f"数据模型 '{self._datamodel.name}' 已保存！")

    def _load_datamodel(self):
        from core.storage.json_store import JsonStore
        store = JsonStore("datamodels")
        model_ids = store.list_ids()

        if not model_ids:
            QMessageBox.information(self, "提示", "没有可加载的数据模型")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("选择数据模型")
        dialog.resize(300, 100)
        layout = QVBoxLayout(dialog)

        combo = QComboBox()
        for mid in model_ids:
            data = store.load(mid)
            combo.addItem(data.get("name", mid), mid)
        layout.addWidget(combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.Accepted:
            model_id = combo.currentData()
            model_data = store.load(model_id)
            if model_data:
                self._load_datamodel_data(model_data)

    def _load_datamodel_data(self, model_data: Dict[str, Any]):
        self._clear_canvas()
        self._datamodel = DataModel(**model_data)

        for table in self._datamodel.tables:
            table_data = table.model_dump()
            self._scene.add_table(table_data)
            self._table_data[table.id] = table_data

        for rel in self._datamodel.relations:
            rel_data = rel.model_dump()
            self._scene.add_relation(rel_data, rel.source_table, rel.target_table)

        self._refresh_table_list()
        self.datamodel_changed.emit(self._datamodel.model_dump())

    def _generate_sql(self):
        if self._datamodel is None or not self._table_data:
            QMessageBox.information(self, "提示", "请先添加数据表")
            return

        self._update_datamodel()

        try:
            sql = self._datamodel.generate_sql()
            dialog = QDialog(self)
            dialog.setWindowTitle("生成的 SQL")
            dialog.resize(600, 400)
            layout = QVBoxLayout(dialog)

            from PySide6.QtWidgets import QTextEdit
            sql_edit = QTextEdit()
            sql_edit.setPlainText(sql)
            sql_edit.setReadOnly(True)
            sql_edit.setStyleSheet("""
                QTextEdit {
                    font-family: Consolas, Monaco, monospace;
                    font-size: 12px;
                    padding: 8px;
                }
            """)
            layout.addWidget(sql_edit)

            buttons = QDialogButtonBox(QDialogButtonBox.Ok)
            buttons.accepted.connect(dialog.accept)
            layout.addWidget(buttons)

            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "生成失败", f"SQL 生成失败: {str(e)}")

    def _export_datamodel(self):
        if self._datamodel is None:
            return

        self._update_datamodel()

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出数据模型",
            f"{self._datamodel.name}.json",
            "JSON Files (*.json)"
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(to_json(self._datamodel.model_dump(), indent=2))
            QMessageBox.information(self, "导出成功", f"数据模型已导出到 {file_path}")

    def get_datamodel(self) -> Optional[DataModel]:
        self._update_datamodel()
        return self._datamodel

    def set_datamodel(self, datamodel: DataModel):
        self._load_datamodel_data(datamodel.model_dump())
