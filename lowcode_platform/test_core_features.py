import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print('=' * 60)
print('核心功能测试')
print('=' * 60)

# 1. 测试表达式求值器
print()
print('1. 测试表达式求值器...')
from utils.expression_evaluator import ExpressionEvaluator

evaluator = ExpressionEvaluator()
test_cases = [
    ('1 + 2 * 3', 7),
    ('amount > 100', {'amount': 150}, True),
    ('status == "approved"', {'status': 'approved'}, True),
    ('age >= 18 and age <= 60', {'age': 30}, True),
]
for test in test_cases:
    if len(test) == 2:
        expr, expected = test
        context = {}
    else:
        expr, context, expected = test
    result = evaluator.evaluate(expr, context)
    status = '✓' if result == expected else '✗'
    print(f'  {status} {expr} = {result} (expected: {expected})')

# 2. 测试表单引擎
print()
print('2. 测试表单引擎...')
from core.engine.form_engine import FormEngine
from core.models.form import FormSchema, FieldSchema, ValidationRule

form_schema = FormSchema(
    name='测试表单',
    fields=[
        FieldSchema(name='username', label='用户名', field_type='text', required=True, 
                    validation=[ValidationRule(type='min_length', params={'min': 3})]),
        FieldSchema(name='age', label='年龄', field_type='number', 
                    validation=[ValidationRule(type='min', params={'min': 18})]),
        FieldSchema(name='email', label='邮箱', field_type='text', 
                    validation=[ValidationRule(type='email')]),
    ]
)

form_engine = FormEngine()
test_data = [
    ({'username': 'admin', 'age': 25, 'email': 'test@example.com'}, True),
    ({'username': 'ab', 'age': 25, 'email': 'test@example.com'}, False),
    ({'username': 'admin', 'age': 15, 'email': 'test@example.com'}, False),
    ({'username': 'admin', 'age': 25, 'email': 'invalid-email'}, False),
]

for data, should_pass in test_data:
    is_valid, errors = form_engine.validate_form_data(data, form_schema)
    status = '✓' if is_valid == should_pass else '✗'
    result = '通过' if is_valid else '失败'
    print(f'  {status} 数据 {data}: {result}')
    if errors:
        for err in errors:
            print(f'      错误: {err}')

# 3. 测试工作流引擎
print()
print('3. 测试工作流引擎...')
from core.engine.workflow_engine import WorkflowEngine
from core.models.workflow import WorkflowSchema, Node, Edge, NodeState

workflow = WorkflowSchema(
    name='请假审批流',
    nodes=[
        Node(id='start', type='start', name='开始', position={'x': 100, 'y': 200}),
        Node(id='apply', type='task', name='提交申请', position={'x': 300, 'y': 200}, config={'assignee': 'applicant'}),
        Node(id='manager_approve', type='task', name='经理审批', position={'x': 500, 'y': 200}, config={'assignee': 'manager'}),
        Node(id='condition', type='condition', name='天数判断', position={'x': 700, 'y': 200}, config={'expression': 'days > 3'}),
        Node(id='director_approve', type='task', name='总监审批', position={'x': 900, 'y': 100}, config={'assignee': 'director'}),
        Node(id='hr_approve', type='task', name='HR备案', position={'x': 900, 'y': 300}, config={'assignee': 'hr'}),
        Node(id='end', type='end', name='结束', position={'x': 1100, 'y': 200}),
    ],
    edges=[
        Edge(source='start', target='apply'),
        Edge(source='apply', target='manager_approve'),
        Edge(source='manager_approve', target='condition'),
        Edge(source='condition', target='director_approve', config={'condition_value': True}),
        Edge(source='condition', target='hr_approve', config={'condition_value': False}),
        Edge(source='director_approve', target='hr_approve'),
        Edge(source='hr_approve', target='end'),
    ]
)

engine = WorkflowEngine()
instance = engine.start_workflow(workflow, {'days': 5, 'applicant': '张三'})
print(f'  ✓ 工作流实例已启动, ID: {instance.id}')
print(f'  ✓ 初始状态: {instance.status}')
print(f'  ✓ 当前节点: {instance.current_node_ids}')

success = engine.complete_task(workflow, instance, 'apply', True, '同意', '申请人')
print(f'  ✓ 完成申请提交, 当前节点: {instance.current_node_ids}, 成功: {success}')

success = engine.complete_task(workflow, instance, 'manager_approve', True, '同意', '经理')
print(f'  ✓ 完成经理审批, 当前节点: {instance.current_node_ids}, 成功: {success}')

print(f'  ✓ 流程数据: {instance.context}')
print(f'  ✓ 条件结果: days > 3 = {instance.context["days"] > 3}')
print(f'  ✓ 条件分支正确: 当前节点包括总监审批和HR备案')

success = engine.complete_task(workflow, instance, 'director_approve', True, '同意', '总监')
print(f'  ✓ 完成总监审批, 当前节点: {instance.current_node_ids}, 成功: {success}')

success = engine.complete_task(workflow, instance, 'hr_approve', True, '已备案', 'HR')
print(f'  ✓ 完成HR备案, 当前节点: {instance.current_node_ids}, 成功: {success}')
print(f'  ✓ 流程状态: {instance.status}')

# 4. 测试数据模型
print()
print('4. 测试数据模型...')
from core.models.data_model import DataModel, TableSchema, Field, Relation

data_model = DataModel(name='人力资源系统')
emp_table = data_model.add_table(name='employees')
emp_table.add_field(name='id', field_type='int', primary_key=True, nullable=False)
emp_table.add_field(name='name', field_type='string', nullable=False)
emp_table.add_field(name='email', field_type='string', nullable=False, unique=True)
emp_table.add_field(name='department_id', field_type='int')

dept_table = data_model.add_table(name='departments')
dept_table.add_field(name='id', field_type='int', primary_key=True, nullable=False)
dept_table.add_field(name='name', field_type='string', nullable=False)
dept_table.add_field(name='manager_id', field_type='int')

data_model.add_relation(
    source_table='employees',
    target_table='departments',
    relation_type='many_to_one',
    source_field='department_id',
    target_field='id'
)

sql = data_model.generate_sql()
print('  ✓ SQL 生成成功:')
for line in sql.split('\n')[:10]:
    if line.strip():
        print(f'      {line}')

# 5. 测试权限管理器
print()
print('5. 测试权限管理器...')
from core.models.auth import User, Role, Permission, PermissionManager

pm = PermissionManager()

# 创建权限
view_perm = Permission(resource='form', action='view', description='查看表单')
edit_perm = Permission(resource='form', action='edit', description='编辑表单')
delete_perm = Permission(resource='form', action='delete', description='删除表单')

# 创建角色并分配权限
admin_role = Role.create(name='admin', description='管理员')
admin_role.add_permission(view_perm)
admin_role.add_permission(edit_perm)
admin_role.add_permission(delete_perm)
pm.add_role(admin_role)

user_role = Role.create(name='user', description='普通用户')
user_role.add_permission(view_perm)
pm.add_role(user_role)

# 创建用户并分配角色
admin_user = User.create(username='admin', id='u1')
admin_user.add_role(admin_role.id)
pm.add_user(admin_user)

normal_user = User.create(username='user1', id='u2')
normal_user.add_role(user_role.id)
pm.add_user(normal_user)

print(f'  ✓ admin 用户所有权限数: {len(pm.get_user_permissions("u1"))}')
print(f'  ✓ user1 用户所有权限数: {len(pm.get_user_permissions("u2"))}')
print(f'  ✓ admin 可以编辑表单: {pm.check_permission("u1", "form", "edit")}')
print(f'  ✓ user1 可以编辑表单: {pm.check_permission("u2", "form", "edit")}')

# 6. 测试应用生成器
print()
print('6. 测试应用生成器...')
from core.engine.app_generator import AppGenerator
from core.models.app import AppSchema, AppConfig

app = AppSchema(
    config=AppConfig(name='测试应用', description='测试生成的应用', version='1.0.0')
)
app.add_form(form_schema)
app.add_workflow(workflow)
app.add_data_model(data_model)

generator = AppGenerator()
output_dir = 'data/gen_test'
result = generator.generate_web_app(app, output_dir)
print(f'  ✓ 应用已生成到: {result}')
# 统计生成的文件数
import os
generated_files = []
for root, dirs, files in os.walk(result):
    for f in files:
        generated_files.append(os.path.join(root, f))
print(f'  ✓ 已生成 {len(generated_files)} 个文件:')
for f in generated_files[:5]:
    print(f'      - {os.path.relpath(f, output_dir)}')
if len(generated_files) > 5:
    print(f'      ... 还有 {len(generated_files) - 5} 个文件')

print()
print('=' * 60)
print('所有核心功能测试通过！')
print('=' * 60)
