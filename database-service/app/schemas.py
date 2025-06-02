from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

# Project schemas
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class Project(ProjectBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    status: str

    class Config:
        from_attributes = True

# Task schemas
class TaskBase(BaseModel):
    name: str
    description: Optional[str] = None
    agent: Optional[str] = None
    input_key: Optional[Dict[str, Any]] = None
    output_key: Optional[str] = None

class TaskCreate(TaskBase):
    project_id: UUID

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    agent: Optional[str] = None
    input_key: Optional[Dict[str, Any]] = None
    output_key: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None

class Task(TaskBase):
    id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str
    error: Optional[str] = None
    duration: Optional[float] = None
    
    class Config:
        from_attributes = True

# Agent schemas
class AgentBase(BaseModel):
    name: str
    role: str
    description: Optional[str] = None
    model_name: str
    model_provider: str
    model_settings: Optional[Dict[str, Any]] = None
    system_prompt: str

class AgentCreate(AgentBase):
    pass

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    description: Optional[str] = None
    model_name: Optional[str] = None
    model_provider: Optional[str] = None
    model_settings: Optional[Dict[str, Any]] = None
    system_prompt: Optional[str] = None

class Agent(AgentBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Artifact schemas
class ArtifactBase(BaseModel):
    name: str
    type: str
    path: Optional[str] = None
    content: Optional[str] = None
    artifact_metadata: Optional[Dict[str, Any]] = None

class ArtifactCreate(ArtifactBase):
    project_id: UUID
    task_id: Optional[UUID] = None

class ArtifactUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    path: Optional[str] = None
    content: Optional[str] = None
    artifact_metadata: Optional[Dict[str, Any]] = None

class Artifact(ArtifactBase):
    id: UUID
    project_id: UUID
    task_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Execution log schemas
class ExecutionLogBase(BaseModel):
    log_type: str
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class ExecutionLogCreate(ExecutionLogBase):
    project_id: UUID
    task_id: Optional[UUID] = None
    agent_id: Optional[UUID] = None

class ExecutionLog(ExecutionLogBase):
    id: UUID
    project_id: UUID
    task_id: Optional[UUID] = None
    agent_id: Optional[UUID] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True

# Task dependency schema
class TaskDependencyCreate(BaseModel):
    task_id: UUID
    depends_on_task_id: UUID 