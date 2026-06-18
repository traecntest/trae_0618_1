# 低代码应用开发平台 - 系统架构设计

## 一、系统概述

本平台是一个基于 PySide6 (Qt for Python) 开发的低代码应用开发平台，支持可视化拖拽方式快速构建企业级应用。平台采用模块化设计，集成表单设计、工作流引擎、数据建模、页面设计、权限管理等核心功能。

## 二、系统架构分层

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────┐
│                     表现层 (Presentation)               │
│  ┌──────────┬──────────┬──────────┬──────────────────┐  │
│  │ 主窗口   │ 表单设计 │ 流程设计 │  页面/数据建模   │  │
│  └──────────┴──────────┴──────────┴──────────────────┘  │
├─────────────────────────────────────────────────────────┤
│                     业务逻辑层 (Business)               │
│  ┌──────────┬──────────┬──────────┬──────────────────┐  │
│  │ 表单引擎 │ 流程引擎 │ 渲染引擎 │  权限/连接器     │  │
│  └──────────┴──────────┴──────────┴──────────────────┘  │
├─────────────────────────────────────────────────────────┤
│                     数据层 (Data)                       │
│  ┌──────────┬──────────┬──────────┬──────────────────┐  │
│  │ 模型定义 │ 存储层   │ 序列化 │  数据访问层       │  │
│  └──────────┴──────────┴──────────┴──────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 2.2 分层职责

#### 表现层 (Presentation Layer)
- **主窗口框架**: 集成所有设计器，提供统一的用户界面
- **表单设计器**: 可视化拖拽表单控件，支持属性配置
- **工作流设计器**: BPMN 风格的流程可视化编辑器
- **数据建模器**: ER 图风格的数据表设计
- **页面设计器**: 所见即所得的页面布局编辑器

#### 业务逻辑层 (Business Layer)
- **表单引擎**: 表单渲染、数据校验、事件处理
- **流程引擎**: 流程解析、节点执行、条件判断、状态流转
- **渲染引擎**: 动态 UI 生成，支持响应式布局
- **权限控制**: 角色管理、权限校验、数据隔离
- **连接器**: 第三方系统集成（钉钉、企业微信、飞书）

#### 数据层 (Data Layer)
- **模型定义**: 所有业务实体的元数据定义
- **存储层**: JSON/XML 序列化，SQLite 元数据存储
- **数据访问层**: 统一的数据访问接口

## 三、核心模块设计

### 3.1 表单设计器模块

**组件结构**:
- `FormWidget`: 表单画布，支持拖放操作
- `WidgetPalette`: 控件面板，提供可用控件列表
- `PropertyEditor`: 属性编辑器，配置控件属性
- `FormPreview`: 表单预览组件

**核心数据结构**:
```python
FormSchema = {
    "id": str,
    "name": str,
    "fields": [FieldSchema],
    "layout": LayoutConfig,
    "validators": [ValidatorRule]
}

FieldSchema = {
    "id": str,
    "type": "text" | "select" | "date" | "file" | "checkbox" | "radio",
    "label": str,
    "name": str,
    "required": bool,
    "props": dict,
    "validation": list
}
```

### 3.2 流程引擎模块

**核心组件**:
- `WorkflowDesigner`: 流程可视化编辑器
- `WorkflowEngine`: 流程运行时引擎
- `NodeExecutor`: 节点执行器
- `ConditionEvaluator`: 条件表达式求值器

**流程数据结构**:
```python
WorkflowSchema = {
    "id": str,
    "name": str,
    "nodes": [Node],
    "edges": [Edge],
    "variables": [Variable]
}

Node = {
    "id": str,
    "type": "start" | "end" | "task" | "condition" | "parallel" | "countersign",
    "name": str,
    "config": NodeConfig,
    "position": {"x": int, "y": int}
}

Edge = {
    "id": str,
    "source": str,
    "target": str,
    "condition": str
}
```

**支持的流程模式**:
- **串行流程**: 按顺序依次执行
- **条件分支**: if/else 条件判断
- **并行网关**: 多个分支同时执行
- **会签节点**: 多人审批，支持一票通过/全票通过
- **子流程**: 流程嵌套调用

### 3.3 数据建模模块

**核心组件**:
- `DataModeler`: ER 图可视化编辑器
- `TableDesigner`: 数据表设计面板
- `RelationEditor`: 关联关系编辑器

**数据模型结构**:
```python
DataModel = {
    "id": str,
    "name": str,
    "tables": [Table],
    "relations": [Relation]
}

Table = {
    "id": str,
    "name": str,
    "fields": [Field],
    "indexes": [Index],
    "position": {"x": int, "y": int}
}

Field = {
    "name": str,
    "type": "int" | "string" | "datetime" | "text" | "foreign_key",
    "nullable": bool,
    "primary_key": bool,
    "default": any
}
```

### 3.4 页面设计器模块

**核心组件**:
- `PageDesigner`: 页面可视化编辑器
- `LayoutManager`: 布局管理器
- `ComponentLibrary`: 组件库
- `ResponsivePreview`: 响应式预览

**页面数据结构**:
```python
PageSchema = {
    "id": str,
    "name": str,
    "route": str,
    "layout": Layout,
    "components": [Component],
    "responsive": ResponsiveConfig
}

Component = {
    "id": str,
    "type": "container" | "button" | "table" | "chart" | "form",
    "props": dict,
    "children": [Component],
    "bindings": DataBinding
}
```

### 3.5 权限与发布模块

**权限模型**:
- 基于 RBAC (Role-Based Access Control)
- 支持功能权限、数据权限、字段权限
- 细粒度到按钮级别的权限控制

**发布功能**:
- 一键打包为 Web 应用 (FastAPI + Vue)
- 生成 Docker 镜像
- 支持本地部署和云部署

### 3.6 连接器模块

**预置连接器**:
- 钉钉连接器: 消息推送、组织架构同步
- 企业微信连接器: 审批推送、通讯录同步
- 飞书连接器: 多维表格、消息通知

**连接器接口**:
```python
class BaseConnector:
    def connect(self, config: dict) -> bool
    def disconnect(self) -> None
    def send_message(self, to: str, content: dict) -> bool
    def sync_data(self, sync_type: str) -> dict
```

## 四、关键技术选型

| 技术领域 | 选型方案 | 说明 |
|---------|---------|------|
| UI 框架 | PySide6 | Qt for Python，跨平台桌面应用 |
| 图形视图 | QGraphicsView | 流程设计器、数据建模器的画布 |
| 数据存储 | SQLite + JSON | 元数据存储，配置持久化 |
| 流程引擎 | 自研 | 轻量级 BPMN 风格引擎 |
| 表达式引擎 | Python eval/ast | 条件表达式安全求值 |
| 序列化 | Pydantic | 数据模型验证和 JSON 序列化 |
| 模板引擎 | Jinja2 | 代码生成模板 |
| Web 发布 | FastAPI + Vue | 生成的 Web 应用技术栈 |

## 五、核心数据流转

```
表单设计 → FormSchema JSON → 流程绑定 → 流程实例 → 数据提交
     ↓                                                  ↓
数据模型 → 数据表创建 → 数据存储 ←──────────────────────┘
     ↓
页面设计 → 页面渲染 → Web 应用 → 用户交互
```
