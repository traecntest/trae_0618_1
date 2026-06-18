import requests
from typing import Any, Dict, List, Optional
from .base_connector import BaseConnector


class FeishuConnector(BaseConnector):
    name = "feishu"
    display_name = "飞书"
    description = "飞书连接器，支持多维表格、消息通知"

    def __init__(self):
        super().__init__()
        self.api_base = "https://open.feishu.cn/open-apis"
        self._tenant_access_token: Optional[str] = None
        self._token_expires_at: Optional[float] = None

    def connect(self, config: Dict[str, Any]) -> bool:
        try:
            self.config = config
            app_id = config.get("app_id")
            app_secret = config.get("app_secret")
            
            if not app_id or not app_secret:
                return False
            
            response = requests.post(
                f"{self.api_base}/auth/v3/tenant_access_token/internal",
                json={"app_id": app_id, "app_secret": app_secret},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0:
                    self._tenant_access_token = data.get("tenant_access_token")
                    import time
                    self._token_expires_at = time.time() + data.get("expire", 7200)
                    self.connected = True
                    return True
            return False
        except Exception:
            return False

    def disconnect(self) -> None:
        self._tenant_access_token = None
        self._token_expires_at = None
        self.connected = False

    def _ensure_token(self) -> bool:
        if not self._tenant_access_token or not self._token_expires_at:
            return self.connect(self.config)
        
        import time
        if time.time() > self._token_expires_at - 300:
            return self.connect(self.config)
        
        return True

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._tenant_access_token}",
            "Content-Type": "application/json; charset=utf-8",
        }

    def send_message(self, to: str, content: Dict[str, Any]) -> bool:
        if not self._ensure_token():
            return False
        
        try:
            msg_type = content.get("type", "text")
            receive_id_type = content.get("receive_id_type", "user_id")
            
            message_content = self._build_message_content(msg_type, content)
            
            response = requests.post(
                f"{self.api_base}/im/v1/messages",
                headers=self._get_headers(),
                params={"receive_id_type": receive_id_type},
                json={
                    "receive_id": to,
                    "msg_type": msg_type,
                    "content": message_content,
                },
                timeout=10
            )
            
            data = response.json()
            return data.get("code") == 0
        except Exception:
            return False

    def _build_message_content(self, msg_type: str, content: Dict[str, Any]) -> str:
        import json
        
        if msg_type == "text":
            return json.dumps({"text": content.get("content", "")})
        elif msg_type == "post":
            return json.dumps({
                "zh_cn": {
                    "title": content.get("title", ""),
                    "content": [[{"tag": "text", "text": content.get("content", "")}]]
                }
            })
        elif msg_type == "interactive":
            return json.dumps(content.get("card", {}))
        return json.dumps({"text": content.get("content", "")})

    def sync_data(self, sync_type: str) -> List[Dict[str, Any]]:
        if not self._ensure_token():
            return []
        
        try:
            if sync_type == "users":
                return self._sync_users()
            elif sync_type == "departments":
                return self._sync_departments()
            elif sync_type == "bitable":
                return self._sync_bitable(content.get("app_token", ""))
            elif sync_type == "org":
                return self._sync_org_structure()
            return []
        except Exception:
            return []

    def _sync_users(self) -> List[Dict[str, Any]]:
        users = []
        try:
            response = requests.get(
                f"{self.api_base}/contact/v3/users",
                headers=self._get_headers(),
                params={"page_size": 100},
                timeout=10
            )
            data = response.json()
            if data.get("code") == 0:
                users = data.get("data", {}).get("items", [])
        except Exception:
            pass
        return users

    def _sync_departments(self) -> List[Dict[str, Any]]:
        departments = []
        try:
            response = requests.get(
                f"{self.api_base}/contact/v3/departments",
                headers=self._get_headers(),
                params={"page_size": 100},
                timeout=10
            )
            data = response.json()
            if data.get("code") == 0:
                departments = data.get("data", {}).get("items", [])
        except Exception:
            pass
        return departments

    def _sync_org_structure(self) -> List[Dict[str, Any]]:
        departments = self._sync_departments()
        users = self._sync_users()
        return [
            {"type": "departments", "data": departments},
            {"type": "users", "data": users},
        ]

    def _sync_bitable(self, app_token: str) -> List[Dict[str, Any]]:
        tables = []
        if not app_token:
            return tables
        
        try:
            response = requests.get(
                f"{self.api_base}/bitable/v1/apps/{app_token}/tables",
                headers=self._get_headers(),
                timeout=10
            )
            data = response.json()
            if data.get("code") == 0:
                tables = data.get("data", {}).get("items", [])
        except Exception:
            pass
        return tables

    def create_bitable_record(self, app_token: str, table_id: str, fields: Dict[str, Any]) -> Optional[str]:
        if not self._ensure_token():
            return None
        
        try:
            response = requests.post(
                f"{self.api_base}/bitable/v1/apps/{app_token}/tables/{table_id}/records",
                headers=self._get_headers(),
                json={"fields": fields},
                timeout=10
            )
            data = response.json()
            if data.get("code") == 0:
                return data.get("data", {}).get("record", {}).get("record_id")
        except Exception:
            pass
        return None

    def get_bitable_records(self, app_token: str, table_id: str, view_id: str = "") -> List[Dict[str, Any]]:
        if not self._ensure_token():
            return []
        
        try:
            params = {"page_size": 100}
            if view_id:
                params["view_id"] = view_id
            
            response = requests.get(
                f"{self.api_base}/bitable/v1/apps/{app_token}/tables/{table_id}/records",
                headers=self._get_headers(),
                params=params,
                timeout=10
            )
            data = response.json()
            if data.get("code") == 0:
                return data.get("data", {}).get("items", [])
        except Exception:
            pass
        return []

    def get_user_by_mobile(self, mobile: str) -> Optional[Dict[str, Any]]:
        if not self._ensure_token():
            return None
        
        try:
            response = requests.get(
                f"{self.api_base}/contact/v3/users/batch_get_id",
                headers=self._get_headers(),
                json={"mobiles": [mobile]},
                timeout=10
            )
            data = response.json()
            if data.get("code") == 0:
                users = data.get("data", {}).get("user_list", [])
                if users:
                    return users[0]
        except Exception:
            pass
        return None

    def create_approval(self, approval_data: Dict[str, Any]) -> Optional[str]:
        if not self._ensure_token():
            return None
        
        try:
            response = requests.post(
                f"{self.api_base}/approval/v4/instances",
                headers=self._get_headers(),
                json=approval_data,
                timeout=10
            )
            data = response.json()
            if data.get("code") == 0:
                return data.get("data", {}).get("instance_code")
        except Exception:
            pass
        return None
