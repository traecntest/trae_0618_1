import requests
from typing import Any, Dict, List, Optional
from .base_connector import BaseConnector


class WeChatWorkConnector(BaseConnector):
    name = "wechat_work"
    display_name = "企业微信"
    description = "企业微信连接器，支持审批推送、通讯录同步"

    def __init__(self):
        super().__init__()
        self.api_base = "https://qyapi.weixin.qq.com/cgi-bin"
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[float] = None

    def connect(self, config: Dict[str, Any]) -> bool:
        try:
            self.config = config
            corp_id = config.get("corp_id")
            corp_secret = config.get("corp_secret")
            
            if not corp_id or not corp_secret:
                return False
            
            response = requests.get(
                f"{self.api_base}/gettoken",
                params={"corpid": corp_id, "corpsecret": corp_secret},
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
                "msgtype": msg_type,
                "agentid": self.config.get("agent_id"),
                "safe": content.get("safe", 0),
            }
            
            if msg_type == "text":
                message["text"] = {"content": content.get("content", "")}
            elif msg_type == "markdown":
                message["markdown"] = {"content": content.get("content", "")}
            elif msg_type == "textcard":
                message["textcard"] = {
                    "title": content.get("title", ""),
                    "description": content.get("content", ""),
                    "url": content.get("url", ""),
                }
            elif msg_type == "news":
                message["news"] = content.get("news", {})
            
            response = requests.post(
                f"{self.api_base}/message/send",
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
                    f"{self.api_base}/user/list",
                    params={
                        "access_token": self._access_token,
                        "department_id": dept_id,
                        "fetch_child": "1",
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
        try:
            response = requests.get(
                f"{self.api_base}/department/list",
                params={"access_token": self._access_token},
                timeout=10
            )
            data = response.json()
            if data.get("errcode") == 0:
                return data.get("department", [])
        except Exception:
            pass
        return []

    def _get_department_ids(self) -> List[str]:
        departments = self._sync_departments()
        return [str(dept.get("id", "")) for dept in departments]

    def _sync_org_structure(self) -> List[Dict[str, Any]]:
        departments = self._sync_departments()
        users = self._sync_users()
        return [
            {"type": "departments", "data": departments},
            {"type": "users", "data": users},
        ]

    def create_approval(self, approval_data: Dict[str, Any]) -> Optional[str]:
        if not self._ensure_token():
            return None
        
        try:
            response = requests.post(
                f"{self.api_base}/oa/applyevent",
                params={"access_token": self._access_token},
                json=approval_data,
                timeout=10
            )
            data = response.json()
            if data.get("errcode") == 0:
                return data.get("sp_no")
        except Exception:
            pass
        return None

    def get_approval_detail(self, sp_no: str) -> Optional[Dict[str, Any]]:
        if not self._ensure_token():
            return None
        
        try:
            response = requests.post(
                f"{self.api_base}/oa/getapprovaldetail",
                params={"access_token": self._access_token},
                json={"sp_no": sp_no},
                timeout=10
            )
            data = response.json()
            if data.get("errcode") == 0:
                return data.get("info")
        except Exception:
            pass
        return None

    def get_user_by_mobile(self, mobile: str) -> Optional[Dict[str, Any]]:
        if not self._ensure_token():
            return None
        
        try:
            response = requests.get(
                f"{self.api_base}/user/getuserid",
                params={"access_token": self._access_token, "mobile": mobile},
                timeout=10
            )
            data = response.json()
            if data.get("errcode") == 0:
                user_id = data.get("userid")
                return self._get_user_detail(user_id)
        except Exception:
            pass
        return None

    def _get_user_detail(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = requests.get(
                f"{self.api_base}/user/get",
                params={"access_token": self._access_token, "userid": user_id},
                timeout=10
            )
            data = response.json()
            if data.get("errcode") == 0:
                return data
        except Exception:
            pass
        return None
