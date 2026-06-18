from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseConnector(ABC):
    name: str = "base"
    display_name: str = "基础连接器"
    description: str = "连接器基类"

    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.connected: bool = False

    @abstractmethod
    def connect(self, config: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass

    @abstractmethod
    def send_message(self, to: str, content: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def sync_data(self, sync_type: str) -> List[Dict[str, Any]]:
        pass

    def is_connected(self) -> bool:
        return self.connected

    def get_config(self) -> Dict[str, Any]:
        return self.config.copy()

    def test_connection(self) -> bool:
        try:
            return self.connect(self.config)
        except Exception:
            return False
        finally:
            self.disconnect()

    def get_webhook_url(self) -> Optional[str]:
        return self.config.get("webhook_url")

    def get_access_token(self) -> Optional[str]:
        return self.config.get("access_token")
