import sys
import os
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("=" * 60)
print("模拟测试：检查 AppSchema 数据类型")
print("=" * 60)

from core.models.app import AppSchema, AppConfig
from core.models.form import FormSchema, FieldSchema
from core.models.workflow import WorkflowSchema, WorkflowNode, WorkflowEdge
from core.models.data_model import DataModel, TableSchema, DataField

# 1. 创建 AppSchema
print("\n1. 创建 AppSchema...")
app = AppSchema(
    config=AppConfig(
        name="测试应用",
        description="测试描述",
        version="1.0.0"
    )
)
print(f"   ✓ AppSchema 创建成功")
print(f"   forms 类型: {type(app.forms)}, 值: {app.forms}")
print(f"   workflows 类型: {type(app.workflows)}, 值: {app.workflows}")
print(f"   data_models 类型: {type(app.data_models)}, 值: {app.data_models}")

# 2. 测试 add_form
print("\n2. 测试 add_form...")
form = FormSchema(
    name="测试表单",
    description="测试",
    fields=[
        FieldSchema(name="username", label="用户名", field_type="text", required=True),
        FieldSchema(name="age", label="年龄", field_type="number"),
    ]
)
app.add_form(form)
print(f"   ✓ add_form 成功")
print(f"   forms 类型: {type(app.forms)}")
try:
    for k, v in app.forms.items():
        print(f"     form[{k}]: {v.name}")
except AttributeError as e:
    print(f"   ✗ forms.items() 失败: {e}")

# 3. 测试 add_workflow
print("\n3. 测试 add_workflow...")
workflow = WorkflowSchema(
    name="测试工作流",
    description="测试",
    nodes=[
        WorkflowNode(id="start", name="开始", node_type="start", position={"x": 100, "y": 100}),
        WorkflowNode(id="end", name="结束", node_type="end", position={"x": 300, "y": 100}),
    ],
    edges=[
        WorkflowEdge(id="e1", source="start", target="end"),
    ]
)
app.add_workflow(workflow)
print(f"   ✓ add_workflow 成功")
print(f"   workflows 类型: {type(app.workflows)}")
try:
    for k, v in app.workflows.items():
        print(f"     workflow[{k}]: {v.name}")
except AttributeError as e:
    print(f"   ✗ workflows.items() 失败: {e}")

# 4. 测试 add_data_model
print("\n4. 测试 add_data_model...")
data_model = DataModel(
    name="测试模型",
    description="测试",
    tables=[
        TableSchema(
            name="test_table",
            fields=[
                DataField(name="id", field_type="int", primary_key=True),
                DataField(name="name", field_type="string"),
            ]
        )
    ]
)
app.add_data_model(data_model)
print(f"   ✓ add_data_model 成功")
print(f"   data_models 类型: {type(app.data_models)}")
try:
    for k, v in app.data_models.items():
        print(f"     data_model[{k}]: {v.name}")
except AttributeError as e:
    print(f"   ✗ data_models.items() 失败: {e}")

# 5. 测试 model_dump 和重新加载
print("\n5. 测试 model_dump 和重新加载...")
dump_data = app.model_dump()
print(f"   dump_data['forms'] 类型: {type(dump_data.get('forms'))}")
print(f"   dump_data['workflows'] 类型: {type(dump_data.get('workflows'))}")
print(f"   dump_data['data_models'] 类型: {type(dump_data.get('data_models'))}")

app2 = AppSchema(**dump_data)
print(f"   ✓ 重新加载成功")
print(f"   app2.forms 类型: {type(app2.forms)}")
try:
    for k, v in app2.forms.items():
        print(f"     form[{k}]: {v.name}")
except AttributeError as e:
    print(f"   ✗ app2.forms.items() 失败: {e}")

# 6. 测试 to_dict
print("\n6. 测试 to_dict...")
try:
    dict_data = app.to_dict()
    print(f"   ✓ to_dict 成功")
    print(f"   forms 类型: {type(dict_data.get('forms'))}")
except AttributeError as e:
    print(f"   ✗ to_dict 失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
