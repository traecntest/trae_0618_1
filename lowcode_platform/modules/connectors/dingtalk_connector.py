import requests
from typing import Any, Dict, List, Optional
from .base_connector import BaseConnector


class DingTalkConnector(BaseConnector):
    name = "dingtalk"
    display_name = "钉钉"
    description = "钉钉连接器，支持消息推送、组织架构同步"

    def __init__(self):
        super().__init__()
        self.api_base = "https://oapi.dingtalk.com"
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[float] = None

    def connect(self, config: Dict[str, Any]) -> bool:
        try:
            self.config = config
            app_key = config.get("app_key")
            app_secret = config.get("app_secret")
            
            if not app_key or not app_secret:
                return False
            
            response = requests.get(
                f"{self.api_base}/gettoken",
                params={"appkey": app_key, "appsecret": app_secret},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("errcode") == 0:
                    self._access_token = data.get("access_token")
                    import time
                    self._token_expires_at = time.time() + data.get("expires_in", 7200)
                    self.connected = True
                    return True
            return False
        except Exception:
            return False

    def disconnect(self) -> None:
        self._access_token = None
        self._token_expires_at = None
        self.connected = False

    def _ensure_token(self) -> bool:
        if not self._access_token or not self._token_expires_at:
            return self.connect(self.config)
        
        import time
        if time.time() > self._token_expires_at - 300:
            return self.connect(self.config)
        
        return True

    def send_message(self, to: str, content: Dict[str, Any]) -> bool:
        if not self._ensure_token():
            return False
        
        try:
            msg_type = content.get("type", "text")
            message = {
                "touser": to,
                "agent_id": self.config.get("agent_id"),
                "msgtype": msg_type,
            }
            
            if msg_type == "text":
                message["text"] = {"content": content.get("content", "")}
            elif msg_type == "markdown":
                message["markdown"] = {
                    "title": content.get("title", ""),
                    "text": content.get("content", ""),
                }
            elif msg_type == "action_card":
                message["action_card"] = content.get("action_card", {})
            
            response = requests.post(
                f"{self.api_base}/topapi/message/corpconversation/asyncsend_v2",
                params={"access_token": self._access_token},
                json=message,
                timeout=10
            )
            
            data = response.json()
            return data.get("errcode") == 0
        except Exception:
            return False

    def sync_data(self, sync_type: str) -> List[Dict[str, Any]]:
        if not self._ensure_token():
            return []
        
        try:
            if sync_type == "users":
                return self._sync_users()
            elif sync_type == "departments":
                return self._sync_departments()
            elif sync_type == "org":
                return self._sync_org_structure()
            return []
        except Exception:
            return []

    def _sync_users(self) -> List[Dict[str, Any]]:
        users = []
        dept_ids = self._get_department_ids()
        
        for dept_id in dept_ids:
            try:
                response = requests.get(
                    f"{self.api_base}/topapi/user/list",
                    params={
                        "access_token": self._access_token,
                        "department_id": dept_id,
                    },
                    timeout=10
                )
                data = response.json()
                if data.get("errcode") == 0:
                    users.extend(data.get("userlist", []))
            except Exception:
                continue
        
        return users

    def _sync_departments(self) -> List[Dict[str, Any]]:
        dept_ids = self._get_department_ids()
        departments = []
        
        for dept_id in dept_ids:
            try:
                response = requests.get(
                    f"{self.api_base}/department/get",
                    params={
                        "access_token": self._access_token,
                        "id": dept_id,
                    },
                    timeout=10
                )
                data = response.json()
                if data.get("errcode") == 0:
                    departments.append(data)
            except Exception:
                continue
        
        return departments

    def _get_department_ids(self) -> List[str]:
        try:
            response = requests.get(
                f"{self.api_base}/department/list_ids",
                params={"access_token": self._access_token},
                timeout=10
            )
            data = response.json()
            if data.get("errcode") == 0:
                return data.get("id_list", [])
        except Exception:
            pass
        return ["1"]

    def _sync_org_structure(self) -> List[Dict[str, Any]]:
        departments = self._sync_departments()
        users = self._sync_users()
        return [
            {"type": "departments", "data": departments},
            {"type": "users", "data": users},
        ]

    def get_user_by_mobile(self, mobile: str) -> Optional[Dict[str, Any]]:
        if not self._ensure_token():
            return None
        
        try:
            response = requests.get(
                f"{self.api_base}/topapi/v2/user/getbymobile",
                params={"access_token": self._access_token},
                data={"mobile": mobile},
                timeout=10
            )
            data = response.json()
            if data.get("errcode") == 0:
                return data.get("result")
        except Exception:
            pass
        return None

    def create_approval_instance(self, process_code: str, form_values: List[Dict], originator_user_id: str, dept_id: str = "1") -> Optional[str]:
        if not self._ensure_token():
            return None
        
        try:
            response = requests.post(
                f"{self.api_base}/topapi/processinstance/create",
                params={"access_token": self._access_token},
                json={
                    "process_code": process_code,
                    "originator_user_id": originator_user_id,
                    "dept_id": dept_id,
                    "form_component_values": form_values,
                },
                timeout=10
            )
            data = response.json()
            if data.get("errcode") == 0:
                return data.get("process_instance_id")
        except Exception:
            pass
        return None
