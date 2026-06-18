from typing import Any, Dict, List, Optional
from core.models.auth import User, Role, Permission, PermissionManager as BasePermissionManager
from core.storage.database import DatabaseManager, UserEntity, RoleEntity
from utils import to_json, from_json


class PermissionManager(BasePermissionManager):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self._load_from_db()

    def _load_from_db(self) -> None:
        with self.db.get_session() as session:
            for user_entity in session.query(UserEntity).all():
                user = User(
                    id=user_entity.id,
                    username=user_entity.username,
                    email=user_entity.email or "",
                    full_name=user_entity.full_name or "",
                    role_ids=from_json(user_entity.role_ids) if user_entity.role_ids else [],
                    department=user_entity.department,
                    position=user_entity.position,
                    is_active=bool(user_entity.is_active),
                    is_admin=bool(user_entity.is_admin),
                    extra=from_json(user_entity.extra) if user_entity.extra else {},
                )
                self.users[user.id] = user

            for role_entity in session.query(RoleEntity).all():
                permissions_data = from_json(role_entity.permissions) if role_entity.permissions else []
                permissions = [Permission(**p) for p in permissions_data]
                role = Role(
                    id=role_entity.id,
                    name=role_entity.name,
                    description=role_entity.description or "",
                    permissions=permissions,
                    is_system=bool(role_entity.is_system),
                )
                self.roles[role.id] = role

    def add_role(self, role: Role) -> None:
        super().add_role(role)
        with self.db.get_session() as session:
            entity = RoleEntity(
                id=role.id,
                name=role.name,
                description=role.description,
                permissions=to_json([p.to_dict() for p in role.permissions]),
                is_system=role.is_system,
            )
            session.add(entity)
            session.commit()

    def remove_role(self, role_id: str) -> None:
        super().remove_role(role_id)
        with self.db.get_session() as session:
            entity = session.query(RoleEntity).filter(RoleEntity.id == role_id).first()
            if entity:
                session.delete(entity)
                session.commit()

    def add_user(self, user: User) -> None:
        super().add_user(user)
        with self.db.get_session() as session:
            entity = UserEntity(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role_ids=to_json(user.role_ids),
                department=user.department,
                position=user.position,
                is_active=user.is_active,
                is_admin=user.is_admin,
                extra=to_json(user.extra),
            )
            session.add(entity)
            session.commit()

    def remove_user(self, user_id: str) -> None:
        super().remove_user(user_id)
        with self.db.get_session() as session:
            entity = session.query(UserEntity).filter(UserEntity.id == user_id).first()
            if entity:
                session.delete(entity)
                session.commit()

    def create_default_roles(self) -> None:
        admin_permissions = [
            Permission.create("*", "*", description="所有权限"),
        ]
        admin_role = Role.create("系统管理员", is_system=True, permissions=admin_permissions)
        self.add_role(admin_role)

        user_permissions = [
            Permission.create("form", "read"),
            Permission.create("form", "write"),
            Permission.create("workflow", "read"),
            Permission.create("workflow", "execute"),
        ]
        user_role = Role.create("普通用户", is_system=True, permissions=user_permissions)
        self.add_role(user_role)

        guest_permissions = [
            Permission.create("form", "read"),
        ]
        guest_role = Role.create("访客", is_system=True, permissions=guest_permissions)
        self.add_role(guest_role)

    def create_default_admin(self) -> User:
        admin_user = User.create(
            username="admin",
            email="admin@example.com",
            full_name="系统管理员",
            is_admin=True,
        )
        self.add_user(admin_user)
        return admin_user
