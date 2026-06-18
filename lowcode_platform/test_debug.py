import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from main_window import MainWindow

app = QApplication(sys.argv)

try:
    window = MainWindow()
    print("✓ MainWindow 创建成功")
    
    # 模拟创建新应用后切换各设计器
    print("\n模拟操作流程:")
    
    # 1. 切换到表单设计器
    window._nav_list.setCurrentRow(0)
    print("✓ 切换到表单设计器")
    
    # 2. 切换到工作流设计器
    window._nav_list.setCurrentRow(1)
    print("✓ 切换到工作流设计器")
    
    # 3. 切换到数据建模器
    window._nav_list.setCurrentRow(2)
    print("✓ 切换到数据建模器")
    
    # 4. 切换到页面设计器
    window._nav_list.setCurrentRow(3)
    print("✓ 切换到页面设计器")
    
    # 5. 保存应用
    window._save_app()
    print("✓ 保存应用成功")
    
    # 6. 收集应用数据
    window._collect_app_data()
    print("✓ 收集应用数据成功")
    
    # 7. 检查 forms 类型
    print(f"\n应用数据检查:")
    print(f"  forms 类型: {type(window._current_app.forms)}")
    print(f"  workflows 类型: {type(window._current_app.workflows)}")
    print(f"  data_models 类型: {type(window._current_app.data_models)}")
    print(f"  pages 类型: {type(window._current_app.pages)}")
    
    # 8. 测试调用 .items()
    try:
        for k, v in window._current_app.forms.items():
            print(f"  form[{k}]: {v.name}")
    except AttributeError as e:
        print(f"  ✗ forms.items() 失败: {e}")
    
    try:
        for k, v in window._current_app.workflows.items():
            print(f"  workflow[{k}]: {v.name}")
    except AttributeError as e:
        print(f"  ✗ workflows.items() 失败: {e}")
    
    try:
        for k, v in window._current_app.data_models.items():
            print(f"  data_model[{k}]: {v.name}")
    except AttributeError as e:
        print(f"  ✗ data_models.items() 失败: {e}")
    
    print("\n✓ 所有测试通过！")
    
except Exception as e:
    import traceback
    print(f"\n✗ 发生错误: {e}")
    traceback.print_exc()
