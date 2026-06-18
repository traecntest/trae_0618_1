from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String)
    full_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Integer, default=1)
    is_admin = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)


class FormData(Base):
    __tablename__ = "form_data"
    
    id = Column(String, primary_key=True, index=True)
    form_id = Column(String, index=True)
    workflow_instance_id = Column(String, index=True, nullable=True)
    data = Column(Text)
    status = Column(String, default="draft")
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class WorkflowInstance(Base):
    __tablename__ = "workflow_instances"
    
    id = Column(String, primary_key=True, index=True)
    workflow_id = Column(String, index=True)
    status = Column(String)
    current_node_ids = Column(Text)
    context = Column(Text)
    history = Column(Text)
    started_by = Column(String, nullable=True)
    started_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)
