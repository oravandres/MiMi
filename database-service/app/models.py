import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Float, UniqueConstraint, Table
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from database import Base, db_metadata

class Project(Base):
    __tablename__ = "projects"
    __table_args__ = {"schema": "mimi"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    config = Column(JSONB)
    status = Column(String(50), default="pending")
    
    # Relationships
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="project", cascade="all, delete-orphan")
    execution_logs = relationship("ExecutionLog", back_populates="project", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = {"schema": "mimi"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("mimi.projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    agent = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    input_key = Column(JSONB)
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
        secondary="mimi.task_dependencies",
        primaryjoin="Task.id==TaskDependency.task_id",
        secondaryjoin="Task.id==TaskDependency.depends_on_task_id",
        backref="dependent_tasks"
    )

class TaskDependency(Base):
    __tablename__ = "task_dependencies"
    __table_args__ = (
        UniqueConstraint("task_id", "depends_on_task_id", name="uq_task_dependency"),
        {"schema": "mimi"}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("mimi.tasks.id", ondelete="CASCADE"), nullable=False)
    depends_on_task_id = Column(UUID(as_uuid=True), ForeignKey("mimi.tasks.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class Agent(Base):
    __tablename__ = "agents"
    __table_args__ = {"schema": "mimi"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    description = Column(Text)
    model_name = Column(String(255), nullable=False)
    model_provider = Column(String(255), nullable=False)
    model_settings = Column(JSONB)
    system_prompt = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    execution_logs = relationship("ExecutionLog", back_populates="agent", cascade="all, delete-orphan")

class Artifact(Base):
    __tablename__ = "artifacts"
    __table_args__ = {"schema": "mimi"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("mimi.projects.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey("mimi.tasks.id", ondelete="SET NULL"))
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    path = Column(Text)
    content = Column(Text)
    artifact_metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="artifacts")
    task = relationship("Task", back_populates="artifacts")

class ExecutionLog(Base):
    __tablename__ = "execution_logs"
    __table_args__ = {"schema": "mimi"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("mimi.projects.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey("mimi.tasks.id", ondelete="CASCADE"))
    agent_id = Column(UUID(as_uuid=True), ForeignKey("mimi.agents.id", ondelete="SET NULL"))
    log_type = Column(String(50), nullable=False)
    message = Column(Text)
    details = Column(JSONB)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="execution_logs")
    task = relationship("Task", back_populates="execution_logs")
    agent = relationship("Agent", back_populates="execution_logs") 