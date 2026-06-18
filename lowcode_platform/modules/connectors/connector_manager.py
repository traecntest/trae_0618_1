import importlib
from typing import Any, Dict, List, Optional, Type
from .base_connector import BaseConnector


class ConnectorManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.connectors: Dict[str, BaseConnector] = {}
        self._connector_classes: Dict[str, Type[BaseConnector]] = {}
        self._load_builtin_connectors()
        self._initialized = True

    def _load_builtin_connectors(self):
        from .dingtalk_connector import DingTalkConnector
        from .wechat_connector import WeChatWorkConnector
        from .feishu_connector import FeishuConnector

        self._register_connector_class("dingtalk", DingTalkConnector)
        self._register_connector_class("wechat_work", WeChatWorkConnector)
        self._register_connector_class("feishu", FeishuConnector)

    def _register_connector_class(self, name: str, connector_class: Type[BaseConnector]) -> None:
        self._connector_classes[name] = connector_class

    def register_connector_class(self, name: str, connector_class: Type[BaseConnector]) -> None:
        self._connector_classes[name] = connector_class

    def get_connector(self, name: str) -> Optional[BaseConnector]:
        if name in self.connectors:
            return self.connectors[name]
        return None

    def create_connector(self, name: str, config: Optional[Dict[str, Any]] = None) -> Optional[BaseConnector]:
        connector_class = self._connector_classes.get(name)
        if not connector_class:
            connector = connector_class()
            if config:
                connector.config = config
            self.connectors[name] = connector
            return connector
        return None

    def connect(self, name: str, config: Dict[str, Any]) -> bool:
        connector = self.get_connector(name)
        if not connector:
            connector = self.create_connector(name, config)
        if connector:
            return connector.connect(config)
        return False

    def disconnect(self, name: str) -> None:
        connector = self.get_connector(name)
        if connector:
            connector.disconnect()

    def send_message(self, connector_name: str, to: str, content: Dict[str, Any]) -> bool:
        connector = self.get_connector(connector_name)
        if connector and connector.is_connected():
            return connector.send_message(to, content)
        return False

    def sync_data(self, connector_name: str, sync_type: str) -> List[Dict[str, Any]]:
        connector = self.get_connector(connector_name)
        if connector and connector.is_connected():
            return connector.sync_data(sync_type)
        return []

    def get_available_connectors(self) -> List[Dict[str, str]]:
        return [
            {
                "name": name,
                "display_name": cls.display_name,
                "description": cls.description,
                "connected": name in self.connectors and self.connectors[name].is_connected(),
            }
            for name, cls in self._connector_classes.items()
        ]

    def load_connector_from_module(self, module_path: str, class_name: str) -> bool:
        try:
            module = importlib.import_module(module_path)
            connector_class = getattr(module, class_name)
            if issubclass(connector_class, BaseConnector):
                name = getattr(connector_class, 'name', class_name.lower().replace("connector", ""))
                self._register_connector_class(name, connector_class)
                return True
        except (ImportError, AttributeError):
            return False
        return False

    def get_all_connectors(self) -> Dict[str, BaseConnector]:
        return self.connectors.copy()

    def remove_connector(self, name: str) -> None:
        if name in self.connectors:
            self.connectors[name].disconnect()
            del self.connectors[name]

    def broadcast_message(self, to: str, content: Dict[str, Any]) -> Dict[str, bool]:
        results = {}
        for name, connector in self.connectors.items():
            if connector.is_connected():
                results[name] = connector.send_message(to, content)
        return results
