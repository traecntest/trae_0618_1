# 关键技术实现要点

## 一、核心技术实现

### 1.1 可视化拖拽实现

**技术方案**: 使用 Qt 的 Drag and Drop 机制 + MIME 数据传递

```python
# 拖拽源实现
class DraggableWidget(QWidget):
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setData("application/x-widget", 
                            json.dumps({"type": self.widget_type}).encode())
            drag.setMimeData(mime_data)
            drag.exec_(Qt.CopyAction)

# 拖拽目标实现
class DropCanvas(QWidget):
    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-widget"):
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        data = json.loads(event.mimeData().data("application/x-widget"))
        self.create_widget(data["type"], event.position())
```

### 1.2 流程引擎实现

**核心算法**: 基于图的广度优先搜索 (BFS) + 状态机

```python
class WorkflowEngine:
    def __init__(self, workflow_schema):
        self.schema = workflow_schema
        self.node_states = {}  # node_id -> state
        
    def start_instance(self, data: dict) -> str:
        instance_id = self._create_instance(data)
        start_node = self._find_start_node()
        self._execute_node(start_node, instance_id, data)
        return instance_id
        
    def _execute_node(self, node, instance_id, data):
        # 1. 执行节点逻辑
        result = self._node_executor.execute(node, data)
        
        # 2. 更新节点状态
        self.node_states[node["id"]] = "completed"
        
        # 3. 查找下一个节点
        next_nodes = self._find_next_nodes(node, data)
        
        # 4. 并行/串行执行后续节点
        for next_node in next_nodes:
            if self._can_execute(next_node):
                self._execute_node(next_node, instance_id, data)
```

### 1.3 条件表达式求值

**安全求值方案**: 使用 ast 模块解析表达式，白名单机制

```python
import ast
import operator

SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Compare: lambda left, ops, comparators: all(
        _compare(left, op, comp) for op, comp in zip(ops, comparators)
    ),
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.And: operator.and_,
    ast.Or: operator.or_,
    ast.Not: operator.not_,
}

def safe_eval(expression: str, context: dict) -> bool:
    tree = ast.parse(expression, mode="eval")
    return _eval_node(tree.body, context)
```

### 1.4 数据模型与数据库映射

**ORM 动态生成**: 根据数据模型动态创建 SQLAlchemy 模型

```python
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

def create_dynamic_model(table_schema: dict):
    attrs = {
        "__tablename__": table_schema["name"],
        "id": Column(Integer, primary_key=True, autoincrement=True),
    }
    
    for field in table_schema["fields"]:
        col_type = _map_type(field["type"])
        attrs[field["name"]] = Column(
            col_type,
            nullable=field.get("nullable", True),
            default=field.get("default")
        )
    
    return type(table_schema["name"], (Base,), attrs)
```

### 1.5 响应式布局实现

**断点系统**: 基于 Bootstrap 的响应式断点

```python
class ResponsiveLayout:
    BREAKPOINTS = {
        "xs": 0,
        "sm": 576,
        "md": 768,
        "lg": 992,
        "xl": 1200
    }
    
    def get_layout(self, width: int) -> dict:
        for bp in reversed(self.BREAKPOINTS):
            if width >= self.BREAKPOINTS[bp]:
                return self.layouts.get(bp, self.layouts["xs"])
        return self.layouts["xs"]
```

### 1.6 权限控制实现

**RBAC 模型 + 数据权限过滤器**:

```python
class PermissionManager:
    def check_permission(self, user_id: str, resource: str, action: str) -> bool:
        user_roles = self._get_user_roles(user_id)
        for role in user_roles:
            if self._role_has_permission(role, resource, action):
                return True
        return False
        
    def filter_data(self, user_id: str, query):
        user_roles = self._get_user_roles(user_id)
        data_filters = []
        for role in user_roles:
            data_filters.extend(self._get_role_data_filters(role))
        return self._apply_filters(query, data_filters)
```

### 1.7 连接器插件系统

**插件架构 + 抽象基类**:

```python
from abc import ABC, abstractmethod
from importlib import import_module

class BaseConnector(ABC):
    @abstractmethod
    def connect(self, config: dict) -> bool: pass
    
    @abstractmethod
    def send_message(self, to: str, content: dict) -> bool: pass

class ConnectorManager:
    def __init__(self):
        self.connectors = {}
        
    def load_connector(self, name: str):
        module = import_module(f".{name}", __package__)
        connector_cls = getattr(module, f"{name.capitalize()}Connector")
        self.connectors[name] = connector_cls()
```

### 1.8 代码生成与发布

**Jinja2 模板 + 文件系统操作**:

```python
from jinja2 import Environment, FileSystemLoader
import os
import shutil

class AppGenerator:
    def __init__(self, template_dir: str):
        self.env = Environment(loader=FileSystemLoader(template_dir))
        
    def generate_web_app(self, app_schema: dict, output_dir: str):
        # 1. 生成后端代码 (FastAPI)
        self._generate_backend(app_schema, output_dir)
        
        # 2. 生成前端代码 (Vue)
        self._generate_frontend(app_schema, output_dir)
        
        # 3. 生成 Dockerfile
        self._generate_dockerfile(app_schema, output_dir)
        
        # 4. 生成 requirements.txt
        self._generate_requirements(app_schema, output_dir)
```

## 二、性能优化要点

### 2.1 图形视图性能
- 使用 `QGraphicsItem` 的缓存机制 `setCacheMode(DeviceCoordinateCache)`
- 懒加载大型场景中的图元
- 使用 `BspTreeIndex` 优化碰撞检测

### 2.2 数据序列化性能
- 使用 `orjson` 替代标准 `json` 模块提升序列化速度
- 大对象分块序列化
- 增量更新机制

### 2.3 流程执行性能
- 异步执行耗时节点
- 流程实例状态缓存
- 节点执行结果复用

## 三、安全要点

### 3.1 表达式注入防护
- 使用 AST 解析而不是直接 eval
- 函数调用白名单
- 执行超时限制

### 3.2 数据安全
- SQL 注入防护 (使用 ORM 参数化查询)
- XSS 防护 (HTML 转义)
- 敏感数据加密存储

### 3.3 权限安全
- 最小权限原则
- 权限校验必须在服务端执行
- 操作日志审计
