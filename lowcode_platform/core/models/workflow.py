from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import Field
from .base import BaseModel
from utils import generate_id


class NodeType(str, Enum):
    START = "start"
    END = "end"
    TASK = "task"
    CONDITION = "condition"
    PARALLEL = "parallel"
    COUNTERSIGN = "countersign"
    SUBPROCESS = "subprocess"


class NodeState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    REJECTED = "rejected"
    SKIPPED = "skipped"


class CountersignMode(str, Enum):
    ALL = "all"
    ANY = "any"
    PERCENTAGE = "percentage"


class NodeConfig(BaseModel):
    assignee: Optional[str] = None
    assignees: List[str] = Field(default_factory=list)
    form_id: Optional[str] = None
    conditions: List[Dict[str, Any]] = Field(default_factory=list)
    countersign_mode: CountersignMode = CountersignMode.ALL
    countersign_percentage: int = 100
    allow_delegate: bool = True
    allow_transfer: bool = True
    notify_type: str = "all"
    remarks: Optional[str] = None
    due_date: Optional[datetime] = None
    pass


class Node(BaseModel):
    type: str = "task"
    name: str = ""
    config: NodeConfig = Field(default_factory=NodeConfig)
    position: Dict[str, int] = Field(default_factory=lambda: {"x": 0, "y": 0})
    size: Dict[str, int] = Field(default_factory=lambda: {"width": 140, "height": 60})
    style: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def create(cls, node_type: str, name: str = "", x: int = 0, y: int = 0, **kwargs) -> "Node":
        return cls(
            type=node_type,
            name=name or node_type,
            position={"x": x, "y": y},
            **kwargs
        )


class Edge(BaseModel):
    source: str = ""
    target: str = ""
    condition: str = ""
    label: str = ""
    style: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def create(cls, source: str, target: str, condition: str = "", label: str = "") -> "Edge":
        return cls(source=source, target=target, condition=condition, label=label)


class Variable(BaseModel):
    name: str = ""
    var_type: str = "string"
    default_value: Any = None
    description: str = ""


class WorkflowSchema(BaseModel):
    name: str = "新建流程"
    description: str = ""
    nodes: List[Node] = Field(default_factory=list)
    edges: List[Edge] = Field(default_factory=list)
    variables: List[Variable] = Field(default_factory=list)
    events: Dict[str, str] = Field(default_factory=dict)
    version: str = "1.0"

    def add_node(self, node_type: str, **kwargs) -> Node:
        node = Node.create(node_type, **kwargs)
        self.nodes.append(node)
        return node

    def remove_node(self, node_id: str) -> None:
        self.nodes = [n for n in self.nodes if n.id != node_id]
        self.edges = [e for e in self.edges if e.source != node_id and e.target != node_id]

    def add_edge(self, source: str, target: str, **kwargs) -> Edge:
        edge = Edge.create(source, target, **kwargs)
        self.edges.append(edge)
        return edge

    def remove_edge(self, edge_id: str) -> None:
        self.edges = [e for e in self.edges if e.id != edge_id]

    def get_node(self, node_id: str) -> Optional[Node]:
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_start_node(self) -> Optional[Node]:
        for node in self.nodes:
            if node.type == "start":
                return node
        return None

    def get_next_nodes(self, node_id: str, context: Optional[Dict[str, Any]] = None) -> List[Node]:
        from utils import safe_eval
        result = []
        context = context or {}
        
        for edge in self.edges:
            if edge.source == node_id:
                if edge.condition:
                    try:
                        if safe_eval(edge.condition, context):
                            target_node = self.get_node(edge.target)
                            if target_node:
                                result.append(target_node)
                    except:
                        pass
                else:
                    target_node = self.get_node(edge.target)
                    if target_node:
                        result.append(target_node)
        return result


class WorkflowInstance(BaseModel):
    workflow_id: str = ""
    status: str = "running"
    current_node_ids: List[str] = Field(default_factory=list)
    completed_node_ids: List[str] = Field(default_factory=list)
    node_states: Dict[str, str] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    history: List[Dict[str, Any]] = Field(default_factory=list)
    started_by: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def set_node_state(self, node_id: str, state: str) -> None:
        self.node_states[node_id] = state
        if state == "completed" and node_id not in self.completed_node_ids:
            self.completed_node_ids.append(node_id)

    def add_history(self, action: str, **kwargs) -> None:
        entry = {
            "action": action,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        self.history.append(entry)
