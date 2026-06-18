import sys
import os
from typing import Optional
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QAction, QKeySequence
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QStackedWidget, QLabel, QFrame,
    QToolBar, QStatusBar, QMessageBox, QFileDialog, QInputDialog,
    QComboBox, QDialog, QDialogButtonBox, QVBoxLayout as QVBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QLineEdit
)
from designers.form_designer import FormDesigner
from designers.workflow_designer import WorkflowDesigner
from designers.data_modeler import DataModeler
from designers.page_designer import PageDesigner
from modules.deployment.app_publisher import AppPublisher
from modules.auth.permission_manager import PermissionManager
from modules.connectors.connector_manager import ConnectorManager
from core.models.app import AppSchema, AppConfig
from utils.id_generator import generate_id
from utils import to_json, from_json


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._current_app: Optional[AppSchema] = None
        self._app_publisher = AppPublisher()
        self._permission_manager = PermissionManager()
        self._connector_manager = ConnectorManager()
        self._setup_ui()
        self._create_new_app()

    def _setup_ui(self):
        self.setWindowTitle("低代码应用开发平台")
        self.resize(1400, 900)
        self.setMinimumSize(1024, 768)

        self._setup_menu()
        self._setup_toolbar()
        self._setup_central_widget()
        self._setup_statusbar()

        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f2f5;
            }
            QMenuBar {
                background-color: #ffffff;
                border-bottom: 1px solid #e0e0e0;
                padding: 4px 0;
            }
            QMenuBar::item {
                padding: 6px 12px;
                border-radius: 4px;
            }
            QMenuBar::item:hover {
                background-color: #f0f7ff;
            }
        """)

    def _setup_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("文件(&F)")

        new_action = QAction("新建应用", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self._create_new_app)
        file_menu.addAction(new_action)

        open_action = QAction("打开应用", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self._open_app)
        file_menu.addAction(open_action)

        save_action = QAction("保存应用", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self._save_app)
        file_menu.addAction(save_action)

        save_as_action = QAction("另存为...", self)
        save_as_action.triggered.connect(self._save_app_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        import_action = QAction("导入应用包", self)
        import_action.triggered.connect(self._import_app)
        file_menu.addAction(import_action)

        export_action = QAction("导出应用包", self)
        export_action.triggered.connect(self._export_app)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        edit_menu = menubar.addMenu("编辑(&E)")

        undo_action = QAction("撤销", self)
        undo_action.setShortcut(QKeySequence.Undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("重做", self)
        redo_action.setShortcut(QKeySequence.Redo)
        edit_menu.addAction(redo_action)

        publish_menu = menubar.addMenu("发布(&P)")

        publish_local_action = QAction("发布到本地", self)
        publish_local_action.triggered.connect(lambda: self._publish_app("local"))
        publish_menu.addAction(publish_local_action)

        publish_docker_action = QAction("发布 Docker 镜像", self)
        publish_docker_action.triggered.connect(lambda: self._publish_app("docker"))
        publish_menu.addAction(publish_docker_action)

        preview_action = QAction("预览应用", self)
        preview_action.setShortcut("F5")
        preview_action.triggered.connect(self._preview_app)
        publish_menu.addAction(preview_action)

        tools_menu = menubar.addMenu("工具(&T)")

        permission_action = QAction("权限管理", self)
        permission_action.triggered.connect(self._manage_permissions)
        tools_menu.addAction(permission_action)

        connector_action = QAction("连接器配置", self)
        connector_action.triggered.connect(self._manage_connectors)
        tools_menu.addAction(connector_action)

        help_menu = menubar.addMenu("帮助(&H)")

        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_toolbar(self):
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(18, 18))
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #ffffff;
                border-bottom: 1px solid #e0e0e0;
                padding: 4px 8px;
                spacing: 4px;
            }
            QToolButton {
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 13px;
            }
            QToolButton:hover {
                background-color: #f0f7ff;
            }
        """)

        new_app_action = QAction("📝 新建应用", self)
        new_app_action.triggered.connect(self._create_new_app)
        toolbar.addAction(new_app_action)

        save_app_action = QAction("💾 保存", self)
        save_app_action.triggered.connect(self._save_app)
        toolbar.addAction(save_app_action)

        toolbar.addSeparator()

        publish_action = QAction("🚀 一键发布", self)
        publish_action.triggered.connect(lambda: self._publish_app("local"))
        toolbar.addAction(publish_action)

        preview_action = QAction("👁️ 预览", self)
        preview_action.triggered.connect(self._preview_app)
        toolbar.addAction(preview_action)

        toolbar.addSeparator()

        self._app_name_label = QLineEdit()
        self._app_name_label.setPlaceholderText("应用名称")
        self._app_name_label.setFixedWidth(200)
        self._app_name_label.setStyleSheet("""
            QLineEdit {
                padding: 6px 12px;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QLineEdit:focus {
                border-color: #1890ff;
            }
        """)
        self._app_name_label.editingFinished.connect(self._on_app_name_changed)
        toolbar.addWidget(self._app_name_label)

        toolbar.addWidget(QLabel("  "))

        self._app_desc_label = QLineEdit()
        self._app_desc_label.setPlaceholderText("应用描述")
        self._app_desc_label.setFixedWidth(300)
        self._app_desc_label.setStyleSheet("""
            QLineEdit {
                padding: 6px 12px;
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #1890ff;
            }
        """)
        self._app_desc_label.editingFinished.connect(self._on_app_desc_changed)
        toolbar.addWidget(self._app_desc_label)

        self.addToolBar(toolbar)

    def _setup_central_widget(self):
        central_widget = QWidget()
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)

        self._nav_panel = self._create_navigation_panel()
        self._nav_panel.setFixedWidth(180)
        splitter.addWidget(self._nav_panel)

        self._content_stack = QStackedWidget()
        self._content_stack.setStyleSheet("background-color: #ffffff;")
        splitter.addWidget(self._content_stack)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)
        self.setCentralWidget(central_widget)

        self._setup_designers()

    def _create_navigation_panel(self) -> QWidget:
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #001529;
            }
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        logo = QLabel("🏗️ 低代码平台")
        logo.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 20px 16px;
                background-color: #002140;
            }
        """)
        layout.addWidget(logo)

        self._nav_list = QListWidget()
        self._nav_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                padding: 8px 0;
            }
            QListWidget::item {
                padding: 12px 20px;
                color: rgba(255, 255, 255, 0.75);
                font-size: 14px;
                border: none;
            }
            QListWidget::item:hover {
                background-color: rgba(255, 255, 255, 0.08);
                color: white;
            }
            QListWidget::item:selected {
                background-color: #1890ff;
                color: white;
            }
        """)
        self._nav_list.setSpacing(2)

        nav_items = [
            ("📋 表单设计", 0),
            ("🔄 流程设计", 1),
            ("🗄️ 数据模型", 2),
            ("📱 页面设计", 3),
            ("👥 权限管理", 4),
            ("🔌 连接器", 5),
        ]

        for text, index in nav_items:
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, index)
            self._nav_list.addItem(item)

        self._nav_list.currentRowChanged.connect(self._on_nav_changed)
        layout.addWidget(self._nav_list, 1)

        return panel

    def _setup_designers(self):
        self._form_designer = FormDesigner()
        self._content_stack.addWidget(self._form_designer)

        self._workflow_designer = WorkflowDesigner()
        self._content_stack.addWidget(self._workflow_designer)

        self._data_modeler = DataModeler()
        self._content_stack.addWidget(self._data_modeler)

        self._page_designer = PageDesigner()
        self._content_stack.addWidget(self._page_designer)

        self._permission_panel = self._create_permission_panel()
        self._content_stack.addWidget(self._permission_panel)

        self._connector_panel = self._create_connector_panel()
        self._content_stack.addWidget(self._connector_panel)

        self._nav_list.setCurrentRow(0)

    def _create_permission_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("👥 权限管理")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        desc = QLabel("管理应用的角色、用户和权限配置")
        desc.setStyleSheet("font-size: 14px; color: #666;")
        layout.addWidget(desc)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        add_role_btn = QPushButton("➕ 添加角色")
        add_role_btn.setStyleSheet(self._get_button_style("primary"))
        add_role_btn.clicked.connect(self._add_role)
        toolbar.addWidget(add_role_btn)

        add_user_btn = QPushButton("👤 添加用户")
        add_user_btn.setStyleSheet(self._get_button_style("default"))
        add_user_btn.clicked.connect(self._add_user)
        toolbar.addWidget(add_user_btn)

        toolbar.addStretch(1)

        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setStyleSheet(self._get_button_style("default"))
        refresh_btn.clicked.connect(self._refresh_permissions)
        toolbar.addWidget(refresh_btn)

        layout.addLayout(toolbar)

        self._role_table = QTableWidget()
        self._role_table.setColumnCount(4)
        self._role_table.setHorizontalHeaderLabels(["角色名称", "描述", "权限数量", "操作"])
        self._role_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._role_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #fafafa;
                padding: 12px;
                border: none;
                border-bottom: 1px solid #e0e0e0;
                font-weight: bold;
            }
        """)
        layout.addWidget(self._role_table, 1)

        return panel

    def _create_connector_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("🔌 连接器配置")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        desc = QLabel("配置第三方系统连接器（钉钉、企业微信、飞书等）")
        desc.setStyleSheet("font-size: 14px; color: #666;")
        layout.addWidget(desc)

        connectors = [
            ("钉钉", "💬", "dingtalk", "企业级智能移动办公平台"),
            ("企业微信", "💼", "wechat", "企业通讯与办公工具"),
            ("飞书", "✈️", "feishu", "新一代协作与管理平台"),
        ]

        for name, icon, ctype, desc_text in connectors:
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 16px;
                }
                QFrame:hover {
                    border-color: #1890ff;
                }
            """)
            card_layout = QHBoxLayout(card)
            card_layout.setSpacing(16)

            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 32px;")
            icon_label.setFixedWidth(48)
            card_layout.addWidget(icon_label)

            info_layout = QVBoxLayout()
            info_layout.setSpacing(4)

            name_label = QLabel(name)
            name_label.setStyleSheet("font-size: 16px; font-weight: bold;")
            info_layout.addWidget(name_label)

            desc_label = QLabel(desc_text)
            desc_label.setStyleSheet("font-size: 13px; color: #666;")
            info_layout.addWidget(desc_label)

            card_layout.addLayout(info_layout, 1)

            config_btn = QPushButton("配置")
            config_btn.setStyleSheet(self._get_button_style("primary"))
            config_btn.setFixedWidth(80)
            config_btn.clicked.connect(lambda c=ctype: self._configure_connector(c))
            card_layout.addWidget(config_btn)

            layout.addWidget(card)

        layout.addStretch(1)
        return panel

    def _get_button_style(self, button_type: str) -> str:
        styles = {
            "primary": """
                QPushButton {
                    padding: 8px 20px;
                    background-color: #1890ff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #40a9ff;
                }
            """,
            "default": """
                QPushButton {
                    padding: 8px 20px;
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #d9d9d9;
                    border-radius: 4px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    border-color: #1890ff;
                    color: #1890ff;
                }
            """,
        }
        return styles.get(button_type, styles["default"])

    def _setup_statusbar(self):
        statusbar = QStatusBar()
        statusbar.setStyleSheet("""
            QStatusBar {
                background-color: #ffffff;
                border-top: 1px solid #e0e0e0;
                padding: 4px 16px;
            }
        """)
        self.setStatusBar(statusbar)

        self._status_label = QLabel("就绪")
        statusbar.addWidget(self._status_label)

        self._version_label = QLabel("v1.0.0")
        self._version_label.setStyleSheet("color: #999;")
        statusbar.addPermanentWidget(self._version_label)

    def _on_nav_changed(self, index: int):
        self._content_stack.setCurrentIndex(index)

    def _on_app_name_changed(self):
        if self._current_app:
            self._current_app.config.name = self._app_name_label.text()
            self._update_status("应用名称已更新")

    def _on_app_desc_changed(self):
        if self._current_app:
            self._current_app.config.description = self._app_desc_label.text()
            self._update_status("应用描述已更新")

    def _create_new_app(self):
        name, ok = QInputDialog.getText(
            self, "新建应用",
            "请输入应用名称:",
            QLineEdit.Normal,
            "我的应用"
        )
        if ok and name:
            self._current_app = AppSchema(
                config=AppConfig(
                    name=name,
                    description="",
                    version="1.0.0",
                ),
            )
            self._app_name_label.setText(name)
            self._app_desc_label.setText("")
            self._clear_all_designers()
            self._update_status(f"已创建应用: {name}")

    def _clear_all_designers(self):
        if hasattr(self, '_form_designer'):
            self._form_designer._clear_canvas()
        if hasattr(self, '_workflow_designer'):
            self._workflow_designer._clear_canvas()
        if hasattr(self, '_data_modeler'):
            self._data_modeler._clear_canvas()
        if hasattr(self, '_page_designer'):
            self._page_designer._clear_canvas()

    def _save_app(self):
        if not self._current_app:
            QMessageBox.warning(self, "提示", "请先创建应用")
            return

        self._collect_app_data()

        from core.storage.json_store import JsonStore
        store = JsonStore("apps")
        store.save(self._current_app.id, self._current_app.model_dump())

        self._update_status(f"应用已保存: {self._current_app.config.name}")
        QMessageBox.information(self, "保存成功", f"应用 '{self._current_app.config.name}' 已保存！")

    def _save_app_as(self):
        if not self._current_app:
            QMessageBox.warning(self, "提示", "请先创建应用")
            return

        name, ok = QInputDialog.getText(
            self, "另存为",
            "请输入新的应用名称:",
            QLineEdit.Normal,
            self._current_app.config.name + "_copy"
        )
        if ok and name:
            self._collect_app_data()
            self._current_app.id = generate_id()
            self._current_app.config.name = name
            self._app_name_label.setText(name)

            from core.storage.json_store import JsonStore
            store = JsonStore("apps")
            store.save(self._current_app.id, self._current_app.model_dump())

            self._update_status(f"应用已另存为: {name}")
            QMessageBox.information(self, "保存成功", f"应用已另存为 '{name}'！")

    def _open_app(self):
        from core.storage.json_store import JsonStore
        store = JsonStore("apps")
        app_ids = store.list_ids()

        if not app_ids:
            QMessageBox.information(self, "提示", "没有可加载的应用")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("选择应用")
        dialog.resize(400, 300)
        layout = QVBox(dialog)

        list_widget = QListWidget()
        for aid in app_ids:
            data = store.load(aid)
            item = QListWidgetItem(f"📱 {data.get('name', aid)}")
            item.setData(Qt.UserRole, aid)
            list_widget.addItem(item)
        layout.addWidget(list_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.Accepted and list_widget.currentItem():
            app_id = list_widget.currentItem().data(Qt.UserRole)
            app_data = store.load(app_id)
            if app_data:
                self._load_app_data(app_data)

    def _load_app_data(self, app_data: dict):
        self._current_app = AppSchema(**app_data)
        self._app_name_label.setText(self._current_app.config.name)
        self._app_desc_label.setText(self._current_app.config.description)

        self._clear_all_designers()

        if self._current_app.forms and hasattr(self, '_form_designer'):
            form = self._current_app.forms[0]
            self._form_designer.set_form_schema(form)

        if self._current_app.workflows and hasattr(self, '_workflow_designer'):
            workflow = self._current_app.workflows[0]
            self._workflow_designer.set_workflow_schema(workflow)

        if self._current_app.data_models and hasattr(self, '_data_modeler'):
            datamodel = self._current_app.data_models[0]
            self._data_modeler.set_datamodel(datamodel)

        if self._current_app.pages and hasattr(self, '_page_designer'):
            page = self._current_app.pages[0]
            self._page_designer.set_page_schema(page)

        self._update_status(f"已加载应用: {self._current_app.config.name}")

    def _collect_app_data(self):
        if not self._current_app:
            return

        if hasattr(self, '_form_designer'):
            form_schema = self._form_designer.get_form_schema()
            if form_schema:
                self._current_app.add_form(form_schema)

        if hasattr(self, '_workflow_designer'):
            workflow_schema = self._workflow_designer.get_workflow_schema()
            if workflow_schema:
                self._current_app.add_workflow(workflow_schema)

        if hasattr(self, '_data_modeler'):
            datamodel = self._data_modeler.get_datamodel()
            if datamodel:
                self._current_app.add_data_model(datamodel)

        if hasattr(self, '_page_designer'):
            page_schema = self._page_designer.get_page_schema()
            if page_schema:
                self._current_app.add_page(page_schema)

    def _publish_app(self, deploy_type: str = "local"):
        if not self._current_app:
            QMessageBox.warning(self, "提示", "请先创建应用")
            return

        self._save_app()
        self._collect_app_data()

        reply = QMessageBox.question(
            self, "确认发布",
            f"确定要发布应用 '{self._current_app.config.name}' 吗？\n发布类型: {deploy_type}",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            self._update_status("正在发布应用...")
            result = self._app_publisher.publish_app(
                self._current_app,
                deploy_type=deploy_type
            )

            if result["success"]:
                self._update_status(f"应用发布成功: {result.get('output_path', '')}")
                QMessageBox.information(
                    self, "发布成功",
                    f"应用 '{self._current_app.config.name}' 发布成功！\n\n"
                    f"输出路径: {result.get('output_path', '')}\n"
                    f"访问地址: {result.get('url', 'http://localhost:8000')}"
                )
            else:
                QMessageBox.critical(
                    self, "发布失败",
                    f"应用发布失败: {result.get('error', '未知错误')}"
                )
        except Exception as e:
            QMessageBox.critical(self, "发布失败", f"发布过程中发生错误: {str(e)}")
        finally:
            self._update_status("就绪")

    def _preview_app(self):
        if not self._current_app:
            QMessageBox.warning(self, "提示", "请先创建应用")
            return

        self._collect_app_data()

        try:
            self._update_status("正在启动预览...")
            self._app_publisher.start_preview(self._current_app)
            self._update_status("预览服务已启动")

            QMessageBox.information(
                self, "预览已启动",
                "应用预览已启动！\n\n"
                "访问地址: http://localhost:8000\n"
                "在浏览器中打开以上地址查看效果"
            )
        except Exception as e:
            QMessageBox.critical(self, "预览失败", f"启动预览失败: {str(e)}")

    def _import_app(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入应用包",
            "",
            "应用包 (*.zip *.json)"
        )
        if file_path:
            try:
                result = self._app_publisher.import_app_package(file_path)
                if result["success"]:
                    self._load_app_data(result["app_data"])
                    QMessageBox.information(self, "导入成功", "应用包导入成功！")
                else:
                    QMessageBox.critical(self, "导入失败", f"导入失败: {result.get('error', '未知错误')}")
            except Exception as e:
                QMessageBox.critical(self, "导入失败", f"导入过程中发生错误: {str(e)}")

    def _export_app(self):
        if not self._current_app:
            QMessageBox.warning(self, "提示", "请先创建应用")
            return

        self._save_app()
        self._collect_app_data()

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出应用包",
            f"{self._current_app.config.name}.zip",
            "应用包 (*.zip)"
        )
        if file_path:
            try:
                result = self._app_publisher.export_app_package(self._current_app, file_path)
                if result["success"]:
                    QMessageBox.information(self, "导出成功", f"应用包已导出到: {file_path}")
                else:
                    QMessageBox.critical(self, "导出失败", f"导出失败: {result.get('error', '未知错误')}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出过程中发生错误: {str(e)}")

    def _manage_permissions(self):
        self._nav_list.setCurrentRow(4)
        self._refresh_permissions()

    def _manage_connectors(self):
        self._nav_list.setCurrentRow(5)

    def _add_role(self):
        name, ok = QInputDialog.getText(self, "添加角色", "请输入角色名称:")
        if ok and name:
            self._permission_manager.create_role(name, f"{name}角色")
            self._refresh_permissions()

    def _add_user(self):
        name, ok = QInputDialog.getText(self, "添加用户", "请输入用户名:")
        if ok and name:
            self._permission_manager.create_user(name, f"{name}@example.com")
            self._refresh_permissions()

    def _refresh_permissions(self):
        roles = self._permission_manager.list_roles()
        self._role_table.setRowCount(len(roles))

        for i, role in enumerate(roles):
            self._role_table.setItem(i, 0, QTableWidgetItem(role.name))
            self._role_table.setItem(i, 1, QTableWidgetItem(role.description or ""))
            self._role_table.setItem(i, 2, QTableWidgetItem(str(len(role.permissions))))

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(0, 0, 0, 0)

            edit_btn = QPushButton("编辑")
            edit_btn.setStyleSheet(self._get_button_style("default"))
            edit_btn.setFixedWidth(60)
            btn_layout.addWidget(edit_btn)

            delete_btn = QPushButton("删除")
            delete_btn.setStyleSheet(self._get_button_style("default"))
            delete_btn.setFixedWidth(60)
            btn_layout.addWidget(delete_btn)

            self._role_table.setCellWidget(i, 3, btn_widget)

    def _configure_connector(self, connector_type: str):
        connectors = {
            "dingtalk": "钉钉",
            "wechat": "企业微信",
            "feishu": "飞书",
        }

        connector_name = connectors.get(connector_type, connector_type)

        dialog = QDialog(self)
        dialog.setWindowTitle(f"配置{connector_name}连接器")
        dialog.resize(400, 300)
        layout = QFormLayout(dialog)

        app_key = QLineEdit()
        app_key.setPlaceholderText(f"请输入{connector_name} AppKey")
        layout.addRow("AppKey:", app_key)

        app_secret = QLineEdit()
        app_secret.setPlaceholderText(f"请输入{connector_name} AppSecret")
        app_secret.setEchoMode(QLineEdit.Password)
        layout.addRow("AppSecret:", app_secret)

        agent_id = QLineEdit()
        agent_id.setPlaceholderText("请输入 Agent ID (可选)")
        layout.addRow("Agent ID:", agent_id)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply)
        buttons.button(QDialogButtonBox.Apply).setText("测试连接")
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        buttons.button(QDialogButtonBox.Apply).clicked.connect(
            lambda: self._test_connector(connector_type, app_key.text(), app_secret.text())
        )
        layout.addRow(buttons)

        if dialog.exec() == QDialog.Accepted:
            config = {
                "app_key": app_key.text(),
                "app_secret": app_secret.text(),
                "agent_id": agent_id.text(),
            }
            self._connector_manager.register_connector(connector_type, config)
            QMessageBox.information(self, "配置成功", f"{connector_name}连接器配置已保存！")

    def _test_connector(self, connector_type: str, app_key: str, app_secret: str):
        try:
            if connector_type == "dingtalk":
                from modules.connectors.dingtalk_connector import DingTalkConnector
                connector = DingTalkConnector({"app_key": app_key, "app_secret": app_secret})
            elif connector_type == "wechat":
                from modules.connectors.wechat_connector import WeChatConnector
                connector = WeChatConnector({"app_key": app_key, "app_secret": app_secret})
            elif connector_type == "feishu":
                from modules.connectors.feishu_connector import FeishuConnector
                connector = FeishuConnector({"app_key": app_key, "app_secret": app_secret})
            else:
                QMessageBox.warning(self, "测试失败", "未知的连接器类型")
                return

            result = connector.test_connection()
            if result.get("success"):
                QMessageBox.information(self, "连接成功", "连接测试成功！")
            else:
                QMessageBox.warning(self, "连接失败", f"连接测试失败: {result.get('error', '未知错误')}")
        except Exception as e:
            QMessageBox.warning(self, "连接失败", f"连接测试失败: {str(e)}")

    def _show_about(self):
        QMessageBox.about(
            self, "关于",
            "🏗️ 低代码应用开发平台\n\n"
            "版本: 1.0.0\n"
            "基于 PySide6 开发\n\n"
            "功能特性:\n"
            "• 可视化表单设计器\n"
            "• 工作流引擎\n"
            "• 数据建模\n"
            "• 页面设计器\n"
            "• 一键发布 Web 应用\n"
            "• 角色权限控制\n"
            "• 第三方连接器\n\n"
            "© 2024 LowCode Platform"
        )

    def _update_status(self, message: str):
        self._status_label.setText(message)

    def closeEvent(self, event):
        if self._current_app:
            reply = QMessageBox.question(
                self, "退出",
                "是否保存当前应用？",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if reply == QMessageBox.Yes:
                self._save_app()
                event.accept()
            elif reply == QMessageBox.Cancel:
                event.ignore()
            else:
                event.accept()
        else:
            event.accept()
