import json
from typing import Any, Dict, List, Optional
from PySide6.QtCore import Qt, Signal, QMimeData, QPointF
from PySide6.QtGui import QDrag, QIcon, QColor, QBrush, QAction
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QToolBar,
    QMessageBox, QFileDialog, QInputDialog, QLineEdit,
    QListWidget, QListWidgetItem, QLabel, QFrame, QScrollArea
)
from widgets import PropertyEditor, GraphicsView, GraphicsScene
from core.models.workflow import WorkflowSchema, Node, Edge
from config.settings import WORKFLOW_NODE_TYPES
from utils.id_generator import generate_id
from utils import to_json, from_json


class NodeListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setSpacing(2)
        self.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
            }
            QListWidget::item {
                padding: 10px 12px;
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                margin-bottom: 4px;
            }
            QListWidget::item:hover {
                background-color: #f0f7ff;
                border: 1px solid #1890ff;
            }
        """)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item:
            node_info = item.data(Qt.UserRole)
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setData("application/x-workflow-node", json.dumps(node_info).encode())
            drag.setMimeData(mime_data)
            drag.exec_(Qt.CopyAction)


class NodePalette(QScrollArea):
    node_dragged = Signal(dict)

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

        title = QLabel("节点面板")
        title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 8px;")
        layout.addWidget(title)

        self._list_widget = NodeListWidget()

        for node_info in WORKFLOW_NODE_TYPES:
            item = QListWidgetItem()
            item.setText(f"{node_info.get('icon', '⚪')}  {node_info.get('name', node_info['type'])}")
            item.setData(Qt.UserRole, node_info)
            self._list_widget.addItem(item)

        layout.addWidget(self._list_widget, 1)

        hint = QLabel("提示：拖拽节点到画布\n右键节点拖拽创建连线")
        hint.setStyleSheet("color: #999; font-size: 11px; padding: 8px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.setWidget(container)


class WorkflowDesigner(QWidget):
    workflow_changed = Signal(dict)
    workflow_saved = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._workflow_schema: Optional[WorkflowSchema] = None
        self._selected_node: Optional[Dict[str, Any]] = None
        self._node_data: Dict[str, Dict[str, Any]] = {}
        self._setup_ui()
        self._create_new_workflow()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._setup_toolbar()
        layout.addWidget(self._toolbar)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)

        self._node_palette = NodePalette()
        self._node_palette.setFixedWidth(200)
        splitter.addWidget(self._node_palette)

        self._scene = GraphicsScene()
        self._view = GraphicsView(self._scene)
        splitter.addWidget(self._view)

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
        new_action.triggered.connect(self._create_new_workflow)
        self._toolbar.addAction(new_action)

        save_action = QAction("保存", self)
        save_action.triggered.connect(self._save_workflow)
        self._toolbar.addAction(save_action)

        load_action = QAction("加载", self)
        load_action.triggered.connect(self._load_workflow)
        self._toolbar.addAction(load_action)

        self._toolbar.addSeparator()

        validate_action = QAction("验证流程", self)
        validate_action.triggered.connect(self._validate_workflow)
        self._toolbar.addAction(validate_action)

        simulate_action = QAction("模拟运行", self)
        simulate_action.triggered.connect(self._simulate_workflow)
        self._toolbar.addAction(simulate_action)

        export_action = QAction("导出JSON", self)
        export_action.triggered.connect(self._export_workflow)
        self._toolbar.addAction(export_action)

        clear_action = QAction("清空", self)
        clear_action.triggered.connect(self._clear_canvas)
        self._toolbar.addAction(clear_action)

    def _connect_signals(self):
        self._scene.node_added.connect(self._on_node_added)
        self._scene.node_deleted.connect(self._on_node_deleted)
        self._scene.edge_added.connect(self._on_edge_added)
        self._scene.edge_deleted.connect(self._on_edge_deleted)
        self._scene.node_clicked.connect(self._on_node_clicked)
        self._property_editor.property_changed.connect(self._on_property_changed)

        self._view.setAcceptDrops(True)
        self._view.dragEnterEvent = self._drag_enter_event
        self._view.dragMoveEvent = self._drag_move_event
        self._view.dropEvent = self._drop_event

    def _drag_enter_event(self, event):
        if event.mimeData().hasFormat("application/x-workflow-node"):
            event.acceptProposedAction()

    def _drag_move_event(self, event):
        if event.mimeData().hasFormat("application/x-workflow-node"):
            event.acceptProposedAction()

    def _drop_event(self, event):
        if event.mimeData().hasFormat("application/x-workflow-node"):
            node_info = json.loads(event.mimeData().data("application/x-workflow-node"))
            scene_pos = self._view.mapToScene(event.position().toPoint())

            node_data = {
                "id": generate_id(),
                "type": node_info["type"],
                "name": node_info.get("name", node_info["type"]),
                "position": {
                    "x": int(scene_pos.x()),
                    "y": int(scene_pos.y()),
                },
                "size": {
                    "width": node_info.get("width", 140),
                    "height": node_info.get("height", 60),
                },
                "config": node_info.get("default_config", {}),
            }

            self._scene.add_node(node_data)
            event.acceptProposedAction()

    def _on_node_added(self, node_data: Dict[str, Any]):
        self._node_data[node_data["id"]] = node_data
        self._update_workflow_schema()

    def _on_node_deleted(self, node_id: str):
        self._node_data.pop(node_id, None)
        if self._selected_node and self._selected_node.get("id") == node_id:
            self._selected_node = None
            self._property_editor.set_object(None)
        self._update_workflow_schema()

    def _on_edge_added(self, edge_data: Dict[str, Any]):
        self._update_workflow_schema()

    def _on_edge_deleted(self, source_id: str, target_id: str):
        self._update_workflow_schema()

    def _on_node_clicked(self, node_id: str):
        self._selected_node = self._node_data.get(node_id)
        if self._selected_node:
            self._property_editor.set_object(self._selected_node)

    def _on_property_changed(self, obj_id: str, prop_name: str, value: Any):
        node = self._node_data.get(obj_id)
        if node:
            node[prop_name] = value
            if prop_name == "name":
                graphics_node = self._scene.get_node(obj_id)
                if graphics_node:
                    graphics_node.node_name = value
            self._update_workflow_schema()

    def _create_new_workflow(self):
        self._clear_canvas()
        name, ok = QInputDialog.getText(
            self, "新建工作流",
            "请输入工作流名称:",
            QLineEdit.Normal,
            f"新建工作流_{len(self._node_data) + 1}"
        )
        if ok and name:
            self._workflow_schema = WorkflowSchema(
                name=name,
                description="",
                nodes=[],
                edges=[],
            )
            self.workflow_changed.emit(self._workflow_schema.model_dump())

    def _clear_canvas(self):
        self._scene.clear_all()
        self._node_data.clear()
        self._selected_node = None
        self._property_editor.set_object(None)

        if self._workflow_schema:
            self._workflow_schema.nodes = []
            self._workflow_schema.edges = []
            self.workflow_changed.emit(self._workflow_schema.model_dump())

    def _update_workflow_schema(self):
        if self._workflow_schema is None:
            return

        nodes = []
        for node_id, node_data in self._node_data.items():
            node = Node(**node_data)
            nodes.append(node)

        edges = []
        for edge_id, edge_item in self._scene._edges.items():
            if edge_item.edge_data:
                edge = Edge(**edge_item.edge_data)
                edges.append(edge)

        self._workflow_schema.nodes = nodes
        self._workflow_schema.edges = edges
        self.workflow_changed.emit(self._workflow_schema.model_dump())

    def _save_workflow(self):
        if self._workflow_schema is None:
            return

        self._update_workflow_schema()

        from core.storage.json_store import JsonStore
        store = JsonStore("workflows")
        store.save(self._workflow_schema.id, self._workflow_schema.model_dump())

        self.workflow_saved.emit(self._workflow_schema.model_dump())
        QMessageBox.information(self, "保存成功", f"工作流 '{self._workflow_schema.name}' 已保存！")

    def _load_workflow(self):
        from core.storage.json_store import JsonStore
        store = JsonStore("workflows")
        workflow_ids = store.list_ids()

        if not workflow_ids:
            QMessageBox.information(self, "提示", "没有可加载的工作流")
            return

        from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox
        dialog = QDialog(self)
        dialog.setWindowTitle("选择工作流")
        dialog.resize(300, 100)
        layout = QVBoxLayout(dialog)

        combo = QComboBox()
        for wid in workflow_ids:
            data = store.load(wid)
            combo.addItem(data.get("name", wid), wid)
        layout.addWidget(combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.Accepted:
            workflow_id = combo.currentData()
            workflow_data = store.load(workflow_id)
            if workflow_data:
                self._load_workflow_data(workflow_data)

    def _load_workflow_data(self, workflow_data: Dict[str, Any]):
        self._clear_canvas()
        self._workflow_schema = WorkflowSchema(**workflow_data)

        for node in self._workflow_schema.nodes:
            node_data = node.model_dump()
            self._scene.add_node(node_data)
            self._node_data[node.id] = node_data

        for edge in self._workflow_schema.edges:
            edge_data = edge.model_dump()
            self._scene.add_edge(edge_data, edge.source, edge.target)

        self.workflow_changed.emit(self._workflow_schema.model_dump())

    def _validate_workflow(self):
        if self._workflow_schema is None or not self._node_data:
            QMessageBox.information(self, "提示", "请先添加流程节点")
            return

        self._update_workflow_schema()

        errors = []
        nodes = self._workflow_schema.nodes
        edges = self._workflow_schema.edges

        start_nodes = [n for n in nodes if n.type == "start"]
        end_nodes = [n for n in nodes if n.type == "end"]

        if len(start_nodes) == 0:
            errors.append("流程必须包含一个开始节点")
        if len(start_nodes) > 1:
            errors.append("流程只能包含一个开始节点")
        if len(end_nodes) == 0:
            errors.append("流程必须包含一个结束节点")

        node_ids = {n.id for n in nodes}
        for edge in edges:
            if edge.source not in node_ids:
                errors.append(f"连线源节点不存在: {edge.source}")
            if edge.target not in node_ids:
                errors.append(f"连线目标节点不存在: {edge.target}")

        if errors:
            QMessageBox.warning(self, "验证失败", "\n".join(errors))
        else:
            QMessageBox.information(self, "验证通过", "工作流验证通过！")

    def _simulate_workflow(self):
        if self._workflow_schema is None or not self._node_data:
            QMessageBox.information(self, "提示", "请先添加流程节点")
            return

        self._update_workflow_schema()

        from core.engine.workflow_engine import WorkflowEngine
        try:
            engine = WorkflowEngine(self._workflow_schema)
            instance = engine.start({})
            QMessageBox.information(self, "模拟启动", f"流程实例已启动\n实例ID: {instance.id}")
        except Exception as e:
            QMessageBox.critical(self, "模拟失败", f"启动失败: {str(e)}")

    def _export_workflow(self):
        if self._workflow_schema is None:
            return

        self._update_workflow_schema()

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出工作流",
            f"{self._workflow_schema.name}.json",
            "JSON Files (*.json)"
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(to_json(self._workflow_schema.model_dump(), indent=2))
            QMessageBox.information(self, "导出成功", f"工作流已导出到 {file_path}")

    def get_workflow_schema(self) -> Optional[WorkflowSchema]:
        self._update_workflow_schema()
        return self._workflow_schema

    def set_workflow_schema(self, workflow_schema: WorkflowSchema):
        self._load_workflow_data(workflow_schema.model_dump())
