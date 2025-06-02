import uuid
import os
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Float, UniqueConstraint, Table, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from database import Base, metadata, USE_SQLITE

# Use appropriate column types based on database
JSONB_TYPE = JSON if USE_SQLITE else JSONB

# SQLite doesn't support UUID directly, so we'll use a helper function
def get_uuid_column():
    if USE_SQLITE:
        return Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    else:
        return Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

# Adjust table_args based on database
def get_table_args(schema_name="mimi"):
    if USE_SQLITE:
        return {}
    else:
        return {"schema": schema_name}

class Project(Base):
    __tablename__ = "projects"
    __table_args__ = get_table_args()
    
    id = get_uuid_column()
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    config = Column(JSONB_TYPE)
    status = Column(String(50), default="pending")
    
    # Relationships
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="project", cascade="all, delete-orphan")
    execution_logs = relationship("ExecutionLog", back_populates="project", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = get_table_args()
    
    id = get_uuid_column()
    project_id = Column(String(36) if USE_SQLITE else UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    agent = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    input_key = Column(JSONB_TYPE)
    output_key = Column(String(255))
    status = Column(String(50), default="pending")
    error = Column(Text)
    duration = Column(Float)
    
    # Relationships
    project = relationship("Project", back_populates="tasks")
    artifacts = relationship("Artifact", back_populates="task", cascade="all, delete-orphan")
    execution_logs = relationship("ExecutionLog", back_populates="task", cascade="all, delete-orphan")
    # Task dependencies
    depends_on = relationship(
        "Task",
        secondary="task_dependencies",
        primaryjoin="Task.id==TaskDependency.task_id",
        secondaryjoin="Task.id==TaskDependency.depends_on_task_id",
        backref="dependent_tasks"
    )

class TaskDependency(Base):
    __tablename__ = "task_dependencies"
    __table_args__ = (
        UniqueConstraint("task_id", "depends_on_task_id", name="uq_task_dependency"),
        get_table_args()
    )
    
    id = get_uuid_column()
    task_id = Column(String(36) if USE_SQLITE else UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    depends_on_task_id = Column(String(36) if USE_SQLITE else UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class Agent(Base):
    __tablename__ = "agents"
    __table_args__ = get_table_args()
    
    id = get_uuid_column()
    name = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    description = Column(Text)
    model_name = Column(String(255), nullable=False)
    model_provider = Column(String(255), nullable=False)
    model_settings = Column(JSONB_TYPE)
    system_prompt = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    execution_logs = relationship("ExecutionLog", back_populates="agent", cascade="all, delete-orphan")

class Artifact(Base):
    __tablename__ = "artifacts"
    __table_args__ = get_table_args()
    
    id = get_uuid_column()
    project_id = Column(String(36) if USE_SQLITE else UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(String(36) if USE_SQLITE else UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"))
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    path = Column(Text)
    content = Column(Text)
    metadata = Column(JSONB_TYPE)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="artifacts")
    task = relationship("Task", back_populates="artifacts")

class ExecutionLog(Base):
    __tablename__ = "execution_logs"
    __table_args__ = get_table_args()
    
    id = get_uuid_column()
    project_id = Column(String(36) if USE_SQLITE else UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(String(36) if USE_SQLITE else UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"))
    agent_id = Column(String(36) if USE_SQLITE else UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"))
    log_type = Column(String(50), nullable=False)
    message = Column(Text)
    details = Column(JSONB_TYPE)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="execution_logs")
    task = relationship("Task", back_populates="execution_logs")
    agent = relationship("Agent", back_populates="execution_logs") 