from typing import Any, Dict, List, Optional
from pydantic import Field
from .base import BaseModel


class PermissionType(str):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"


class Permission(BaseModel):
    resource: str = ""
    action: str = ""
    description: str = ""
    field_permissions: List[str] = Field(default_factory=list)
    data_filters: List[Dict[str, Any]] = Field(default_factory=list)

    @classmethod
    def create(cls, resource: str, action: str, **kwargs) -> "Permission":
        return cls(resource=resource, action=action, **kwargs)

    def to_key(self) -> str:
        return f"{self.resource}:{self.action}"


class Role(BaseModel):
    name: str = ""
    description: str = ""
    permissions: List[Permission] = Field(default_factory=list)
    is_system: bool = False

    @classmethod
    def create(cls, name: str, **kwargs) -> "Role":
        return cls(name=name, **kwargs)

    def add_permission(self, permission: Permission) -> None:
        self.permissions.append(permission)

    def remove_permission(self, permission_id: str) -> None:
        self.permissions = [p for p in self.permissions if p.id != permission_id]

    def has_permission(self, resource: str, action: str) -> bool:
        return any(
            p.resource == resource and p.action == action
            for p in self.permissions
        )

    def get_permission(self, resource: str, action: str) -> Optional[Permission]:
        for p in self.permissions:
            if p.resource == resource and p.action == action:
                return p
        return None


class User(BaseModel):
    username: str = ""
    email: str = ""
    full_name: str = ""
    role_ids: List[str] = Field(default_factory=list)
    department: Optional[str] = None
    position: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False
    extra: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def create(cls, username: str, **kwargs) -> "User":
        return cls(username=username, **kwargs)

    def add_role(self, role_id: str) -> None:
        if role_id not in self.role_ids:
            self.role_ids.append(role_id)

    def remove_role(self, role_id: str) -> None:
        self.role_ids = [r for r in self.role_ids if r != role_id]


class PermissionManager:
    def __init__(self):
        self.roles: Dict[str, Role] = {}
        self.users: Dict[str, User] = {}

    def add_role(self, role: Role) -> None:
        self.roles[role.id] = role

    def remove_role(self, role_id: str) -> None:
        if role_id in self.roles:
            del self.roles[role_id]

    def get_role(self, role_id: str) -> Optional[Role]:
        return self.roles.get(role_id)

    def add_user(self, user: User) -> None:
        self.users[user.id] = user

    def remove_user(self, user_id: str) -> None:
        if user_id in self.users:
            del self.users[user_id]

    def get_user(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)

    def get_user_roles(self, user_id: str) -> List[Role]:
        user = self.get_user(user_id)
        if not user:
            return []
        return [self.roles[rid] for rid in user.role_ids if rid in self.roles]

    def check_permission(self, user_id: str, resource: str, action: str) -> bool:
        user = self.get_user(user_id)
        if user and user.is_admin:
            return True
        
        roles = self.get_user_roles(user_id)
        for role in roles:
            if role.has_permission(resource, action):
                return True
        return False

    def get_user_permissions(self, user_id: str) -> List[Permission]:
        permissions = []
        roles = self.get_user_roles(user_id)
        for role in roles:
            permissions.extend(role.permissions)
        return permissions

    def get_data_filters(self, user_id: str, resource: str) -> List[Dict[str, Any]]:
        filters = []
        user = self.get_user(user_id)
        if user and user.is_admin:
            return filters
        
        roles = self.get_user_roles(user_id)
        for role in roles:
            permission = role.get_permission(resource, "read")
            if permission:
                filters.extend(permission.data_filters)
        return filters

    def get_field_permissions(self, user_id: str, resource: str) -> List[str]:
        fields = []
        user = self.get_user(user_id)
        if user and user.is_admin:
            return ["*"]
        
        roles = self.get_user_roles(user_id)
        for role in roles:
            permission = role.get_permission(resource, "read")
            if permission:
                fields.extend(permission.field_permissions)
        return list(set(fields))
