import json
from typing import Any, Dict, Optional
from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QMimeData
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath, QDrag, QAction
from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsEllipseItem,
    QGraphicsRectItem, QGraphicsTextItem, QGraphicsLineItem, QGraphicsPathItem,
    QMenu
)


class NodeGraphicsItem(QGraphicsRectItem):
    node_selected = Signal(str)
    node_moved = Signal(str, float, float)

    def __init__(self, node_data: Dict[str, Any], parent=None):
        width = node_data.get("size", {}).get("width", 140)
        height = node_data.get("size", {}).get("height", 60)
        super().__init__(0, 0, width, height, parent)

        self.node_data = node_data
        self.node_id = node_data.get("id", "")
        self.node_type = node_data.get("type", "task")
        self.node_name = node_data.get("name", "节点")

        self._setup_appearance()
        self._setup_interaction()

    def _setup_appearance(self):
        color_map = {
            "start": "#52c41a",
            "end": "#ff4d4f",
            "task": "#1890ff",
            "condition": "#faad14",
            "parallel": "#722ed1",
            "countersign": "#13c2c2",
            "subprocess": "#eb2f96",
        }

        color = QColor(color_map.get(self.node_type, "#1890ff"))
        self.setBrush(QBrush(color))
        self.setPen(QPen(QColor("#ffffff"), 2))
        self.setCornerRadius(8)
        self.setAcceptHoverEvents(True)

        text_item = QGraphicsTextItem(self.node_name, self)
        text_item.setDefaultTextColor(QColor("#ffffff"))
        text_item.setPos(10, 15)

        type_label = QGraphicsTextItem(self.node_type.upper(), self)
        type_label.setDefaultTextColor(QColor("#ffffff", 180))
        font = type_label.font()
        font.setPointSize(8)
        type_label.setFont(font)
        type_label.setPos(10, 35)

    def _setup_interaction(self):
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setSelected(True)
            self.node_selected.emit(self.node_id)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        pos = self.pos()
        self.node_moved.emit(self.node_id, pos.x(), pos.y())

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            pos = self.pos()
            self.node_data["position"]["x"] = int(pos.x())
            self.node_data["position"]["y"] = int(pos.y())
        return super().itemChange(change, value)

    def get_connection_point(self, edge_type: str) -> QPointF:
        rect = self.rect()
        if edge_type == "output":
            return self.pos() + QPointF(rect.width(), rect.height() / 2)
        else:
            return self.pos() + QPointF(0, rect.height() / 2)

    def contextMenuEvent(self, event):
        menu = QMenu()
        edit_action = QAction("编辑节点", menu)
        delete_action = QAction("删除节点", menu)

        edit_action.triggered.connect(lambda: self._handle_edit())
        delete_action.triggered.connect(lambda: self._handle_delete())

        menu.addAction(edit_action)
        menu.addAction(delete_action)
        menu.exec_(event.screenPos())

    def _handle_edit(self):
        pass

    def _handle_delete(self):
        if self.scene():
            self.scene().removeItem(self)


class EdgeGraphicsItem(QGraphicsPathItem):
    def __init__(self, source_item: NodeGraphicsItem, target_item: NodeGraphicsItem, parent=None):
        super().__init__(parent)
        self.source_item = source_item
        self.target_item = target_item
        self.edge_data: Optional[Dict[str, Any]] = None

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

    def contextMenuEvent(self, event):
        menu = QMenu()
        delete_action = QAction("删除连线", menu)
        delete_action.triggered.connect(lambda: self._handle_delete())
        menu.addAction(delete_action)
        menu.exec_(event.screenPos())

    def _handle_delete(self):
        if self.scene():
            self.scene().removeItem(self)


class GraphicsScene(QGraphicsScene):
    node_added = Signal(dict)
    node_deleted = Signal(str)
    edge_added = Signal(dict)
    edge_deleted = Signal(str, str)
    node_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 2000, 1500)
        self._nodes: Dict[str, NodeGraphicsItem] = {}
        self._edges: Dict[str, EdgeGraphicsItem] = {}
        self._drawing_edge = False
        self._edge_source: Optional[NodeGraphicsItem] = None
        self._temp_line: Optional[QGraphicsLineItem] = None
        self._setup_background()

    def _setup_background(self):
        self.setBackgroundBrush(QBrush(QColor("#fafafa")))

    def add_node(self, node_data: Dict[str, Any]) -> NodeGraphicsItem:
        node = NodeGraphicsItem(node_data)
        node.setPos(
            node_data.get("position", {}).get("x", 100),
            node_data.get("position", {}).get("y", 100)
        )
        node.node_selected.connect(self._on_node_selected)
        node.node_moved.connect(self._on_node_moved)
        self.addItem(node)
        self._nodes[node_data["id"]] = node
        self.node_added.emit(node_data)
        return node

    def remove_node(self, node_id: str):
        node = self._nodes.pop(node_id, None)
        if node:
            edges_to_remove = []
            for edge_id, edge in self._edges.items():
                if edge.source_item == node or edge.target_item == node:
                    edges_to_remove.append(edge_id)

            for edge_id in edges_to_remove:
                self.remove_edge(edge_id)

            self.removeItem(node)
            self.node_deleted.emit(node_id)

    def add_edge(self, edge_data: Dict[str, Any], source_id: str, target_id: str) -> Optional[EdgeGraphicsItem]:
        source = self._nodes.get(source_id)
        target = self._nodes.get(target_id)
        if not source or not target:
            return None

        edge = EdgeGraphicsItem(source, target)
        edge.edge_data = edge_data
        self.addItem(edge)
        self._edges[edge_data["id"]] = edge
        self.edge_added.emit(edge_data)
        return edge

    def remove_edge(self, edge_id: str):
        edge = self._edges.pop(edge_id, None)
        if edge:
            if edge.edge_data:
                self.edge_deleted.emit(
                    edge.edge_data.get("source", ""),
                    edge.edge_data.get("target", "")
                )
            self.removeItem(edge)

    def mousePressEvent(self, event):
        item = self.itemAt(event.scenePos(), self.views()[0].transform())
        if isinstance(item, NodeGraphicsItem) and event.button() == Qt.RightButton:
            if not self._drawing_edge:
                self._drawing_edge = True
                self._edge_source = item
                self._temp_line = QGraphicsLineItem()
                self._temp_line.setPen(QPen(QColor("#1890ff"), 2, Qt.DashLine))
                self.addItem(self._temp_line)
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drawing_edge and self._temp_line:
            start = self._edge_source.get_connection_point("output")
            end = event.scenePos()
            self._temp_line.setLine(start.x(), start.y(), end.x(), end.y())

        for edge in self._edges.values():
            edge.update_position()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._drawing_edge and self._temp_line:
            item = self.itemAt(event.scenePos(), self.views()[0].transform())
            if isinstance(item, NodeGraphicsItem) and item != self._edge_source:
                edge_data = {
                    "id": f"edge_{id(self)}_{len(self._edges)}",
                    "source": self._edge_source.node_id,
                    "target": item.node_id,
                    "condition": "",
                }
                self.add_edge(edge_data, self._edge_source.node_id, item.node_id)

            self.removeItem(self._temp_line)
            self._temp_line = None
            self._drawing_edge = False
            self._edge_source = None
            return

        super().mouseReleaseEvent(event)

    def _on_node_selected(self, node_id: str):
        self.node_clicked.emit(node_id)

    def _on_node_moved(self, node_id: str, x: float, y: float):
        for edge in self._edges.values():
            edge.update_position()

    def clear_all(self):
        self.clear()
        self._nodes.clear()
        self._edges.clear()
        self._drawing_edge = False
        self._edge_source = None
        self._temp_line = None

    def get_node(self, node_id: str) -> Optional[NodeGraphicsItem]:
        return self._nodes.get(node_id)


class GraphicsView(QGraphicsView):
    def __init__(self, scene: GraphicsScene, parent=None):
        super().__init__(scene, parent)
        self._setup_view()

    def _setup_view(self):
        self.setRenderHints(
            QPainter.Antialiasing |
            QPainter.TextAntialiasing |
            QPainter.SmoothPixmapTransform
        )
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setStyleSheet("""
            QGraphicsView {
                background-color: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
        """)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            zoom_factor = 1.15
            if event.angleDelta().y() < 0:
                zoom_factor = 0.85
            self.scale(zoom_factor, zoom_factor)
        else:
            super().wheelEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            for item in self.scene().selectedItems():
                if isinstance(item, NodeGraphicsItem):
                    self.scene().remove_node(item.node_id)
                elif isinstance(item, EdgeGraphicsItem):
                    if item.edge_data:
                        self.scene().remove_edge(item.edge_data["id"])
        else:
            super().keyPressEvent(event)
