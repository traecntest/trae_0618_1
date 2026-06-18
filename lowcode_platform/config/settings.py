import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

RESOURCES_DIR = BASE_DIR / "resources"
RESOURCES_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "lowcode.db"

JSON_STORAGE_DIR = DATA_DIR / "json"
JSON_STORAGE_DIR.mkdir(exist_ok=True)

EXPORT_DIR = DATA_DIR / "exports"
EXPORT_DIR.mkdir(exist_ok=True)

WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900

SUPPORTED_WIDGETS = [
    {"type": "text", "name": "文本框", "icon": "📝"},
    {"type": "textarea", "name": "多行文本", "icon": "📄"},
    {"type": "number", "name": "数字输入", "icon": "🔢"},
    {"type": "select", "name": "下拉选择", "icon": "📋"},
    {"type": "checkbox", "name": "复选框", "icon": "☑️"},
    {"type": "radio", "name": "单选框", "icon": "🔘"},
    {"type": "date", "name": "日期选择", "icon": "📅"},
    {"type": "datetime", "name": "日期时间", "icon": "⏰"},
    {"type": "file", "name": "附件上传", "icon": "📎"},
    {"type": "image", "name": "图片上传", "icon": "🖼️"},
    {"type": "user", "name": "人员选择", "icon": "👤"},
    {"type": "department", "name": "部门选择", "icon": "🏢"},
]

WORKFLOW_NODE_TYPES = [
    {"type": "start", "name": "开始节点", "color": "#52c41a"},
    {"type": "end", "name": "结束节点", "color": "#ff4d4f"},
    {"type": "task", "name": "审批节点", "color": "#1890ff"},
    {"type": "condition", "name": "条件分支", "color": "#faad14"},
    {"type": "parallel", "name": "并行网关", "color": "#722ed1"},
    {"type": "countersign", "name": "会签节点", "color": "#13c2c2"},
    {"type": "subprocess", "name": "子流程", "color": "#eb2f96"},
]

FIELD_TYPES = [
    {"type": "int", "name": "整数", "sql_type": "INTEGER"},
    {"type": "string", "name": "字符串", "sql_type": "VARCHAR(255)"},
    {"type": "text", "name": "长文本", "sql_type": "TEXT"},
    {"type": "float", "name": "浮点数", "sql_type": "FLOAT"},
    {"type": "boolean", "name": "布尔", "sql_type": "BOOLEAN"},
    {"type": "datetime", "name": "日期时间", "sql_type": "DATETIME"},
    {"type": "date", "name": "日期", "sql_type": "DATE"},
    {"type": "foreign_key", "name": "外键", "sql_type": "INTEGER"},
]

RELATION_TYPES = [
    {"type": "one_to_one", "name": "一对一", "label": "1:1"},
    {"type": "one_to_many", "name": "一对多", "label": "1:N"},
    {"type": "many_to_many", "name": "多对多", "label": "N:M"},
]

PAGE_COMPONENTS = [
    {"type": "container", "name": "容器", "icon": "📦"},
    {"type": "button", "name": "按钮", "icon": "🔘"},
    {"type": "table", "name": "数据表格", "icon": "📊"},
    {"type": "form", "name": "表单组件", "icon": "📝"},
    {"type": "chart", "name": "图表", "icon": "📈"},
    {"type": "card", "name": "卡片", "icon": "🃏"},
    {"type": "tabs", "name": "标签页", "icon": "📑"},
    {"type": "menu", "name": "菜单", "icon": "📜"},
]

DATABASE_URL = f"sqlite:///{DB_PATH}"
