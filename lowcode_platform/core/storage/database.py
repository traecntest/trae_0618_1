from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime
from config.settings import DATABASE_URL
from utils import to_json, from_json

Base = declarative_base()
T = TypeVar("T")


class MetadataEntity(Base):
    __tablename__ = "metadata"
    
    id = Column(String, primary_key=True)
    entity_type = Column(String, index=True)
    name = Column(String)
    data = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    version = Column(Integer, default=1)


class WorkflowInstanceEntity(Base):
    __tablename__ = "workflow_instances"
    
    id = Column(String, primary_key=True)
    workflow_id = Column(String, index=True)
    status = Column(String)
    current_node_ids = Column(Text)
    context = Column(Text)
    history = Column(Text)
    started_by = Column(String)
    started_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime)


class FormDataEntity(Base):
    __tablename__ = "form_data"
    
    id = Column(String, primary_key=True)
    form_id = Column(String, index=True)
    workflow_instance_id = Column(String, index=True, nullable=True)
    data = Column(Text)
    status = Column(String)
    created_by = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class UserEntity(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    username = Column(String, unique=True, index=True)
    email = Column(String)
    full_name = Column(String)
    role_ids = Column(Text)
    department = Column(String)
    position = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    extra = Column(Text)
    created_at = Column(DateTime, default=datetime.now)


class RoleEntity(Base):
    __tablename__ = "roles"
    
    id = Column(String, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)
    permissions = Column(Text)
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)


class DatabaseManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.engine = create_engine(DATABASE_URL, echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self._initialized = True
    
    def get_session(self) -> Session:
        return self.SessionLocal()
    
    def save_metadata(self, entity_type: str, entity_id: str, name: str, data: dict) -> None:
        with self.get_session() as session:
            existing = session.query(MetadataEntity).filter(
                MetadataEntity.id == entity_id
            ).first()
            
            if existing:
                existing.name = name
                existing.data = to_json(data)
                existing.version += 1
            else:
                entity = MetadataEntity(
                    id=entity_id,
                    entity_type=entity_type,
                    name=name,
                    data=to_json(data)
                )
                session.add(entity)
            session.commit()
    
    def get_metadata(self, entity_id: str) -> Optional[dict]:
        with self.get_session() as session:
            entity = session.query(MetadataEntity).filter(
                MetadataEntity.id == entity_id
            ).first()
            if entity:
                return from_json(entity.data)
        return None
    
    def list_metadata(self, entity_type: Optional[str] = None) -> List[dict]:
        with self.get_session() as session:
            query = session.query(MetadataEntity)
            if entity_type:
                query = query.filter(MetadataEntity.entity_type == entity_type)
            return [
                {
                    "id": e.id,
                    "entity_type": e.entity_type,
                    "name": e.name,
                    "data": from_json(e.data),
                    "version": e.version,
                    "created_at": e.created_at,
                    "updated_at": e.updated_at
                }
                for e in query.all()
            ]
    
    def delete_metadata(self, entity_id: str) -> bool:
        with self.get_session() as session:
            entity = session.query(MetadataEntity).filter(
                MetadataEntity.id == entity_id
            ).first()
            if entity:
                session.delete(entity)
                session.commit()
                return True
        return False


class SQLiteStorage:
    def __init__(self):
        self.db = DatabaseManager()
    
    def save(self, entity_type: str, entity_id: str, name: str, data: dict) -> None:
        self.db.save_metadata(entity_type, entity_id, name, data)
    
    def get(self, entity_id: str) -> Optional[dict]:
        return self.db.get_metadata(entity_id)
    
    def list(self, entity_type: Optional[str] = None) -> List[dict]:
        return self.db.list_metadata(entity_type)
    
    def delete(self, entity_id: str) -> bool:
        return self.db.delete_metadata(entity_id)
    
    def save_workflow_instance(self, instance_data: dict) -> None:
        with self.db.get_session() as session:
            entity = WorkflowInstanceEntity(
                id=instance_data["id"],
                workflow_id=instance_data["workflow_id"],
                status=instance_data["status"],
                current_node_ids=to_json(instance_data.get("current_node_ids", [])),
                context=to_json(instance_data.get("context", {})),
                history=to_json(instance_data.get("history", [])),
                started_by=instance_data.get("started_by")
            )
            session.add(entity)
            session.commit()
    
    def update_workflow_instance(self, instance_id: str, **kwargs) -> None:
        with self.db.get_session() as session:
            instance = session.query(WorkflowInstanceEntity).filter(
                WorkflowInstanceEntity.id == instance_id
            ).first()
            if instance:
                for key, value in kwargs.items():
                    if key in ["current_node_ids", "context", "history"]:
                        value = to_json(value)
                    setattr(instance, key, value)
                session.commit()
    
    def save_form_data(self, form_data: dict) -> None:
        with self.db.get_session() as session:
            entity = FormDataEntity(
                id=form_data["id"],
                form_id=form_data["form_id"],
                workflow_instance_id=form_data.get("workflow_instance_id"),
                data=to_json(form_data.get("data", {})),
                status=form_data.get("status", "draft"),
                created_by=form_data.get("created_by")
            )
            session.add(entity)
            session.commit()
    
    def update_form_data(self, data_id: str, **kwargs) -> None:
        with self.db.get_session() as session:
            form_data = session.query(FormDataEntity).filter(
                FormDataEntity.id == data_id
            ).first()
            if form_data:
                for key, value in kwargs.items():
                    if key == "data":
                        value = to_json(value)
                    setattr(form_data, key, value)
                session.commit()
