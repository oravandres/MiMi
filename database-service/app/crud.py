from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime

import models
import schemas

# Project CRUD operations
def create_project(db: Session, project: schemas.ProjectCreate) -> models.Project:
    db_project = models.Project(
        name=project.name,
        description=project.description,
        config=project.config
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def get_project(db: Session, project_id: UUID) -> Optional[models.Project]:
    return db.query(models.Project).filter(models.Project.id == project_id).first()

def get_projects(db: Session, skip: int = 0, limit: int = 100) -> List[models.Project]:
    return db.query(models.Project).offset(skip).limit(limit).all()

def update_project(db: Session, project_id: UUID, project: schemas.ProjectUpdate) -> Optional[models.Project]:
    db_project = get_project(db, project_id)
    if db_project:
        update_data = project.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_project, key, value)
        db.commit()
        db.refresh(db_project)
    return db_project

def delete_project(db: Session, project_id: UUID) -> bool:
    db_project = get_project(db, project_id)
    if db_project:
        db.delete(db_project)
        db.commit()
        return True
    return False

# Task CRUD operations
def create_task(db: Session, task: schemas.TaskCreate) -> models.Task:
    db_task = models.Task(
        name=task.name,
        description=task.description,
        agent=task.agent,
        project_id=task.project_id,
        input_key=task.input_key,
        output_key=task.output_key
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def get_task(db: Session, task_id: UUID) -> Optional[models.Task]:
    return db.query(models.Task).filter(models.Task.id == task_id).first()

def get_tasks(db: Session, project_id: Optional[UUID] = None, skip: int = 0, limit: int = 100) -> List[models.Task]:
    query = db.query(models.Task)
    if project_id:
        query = query.filter(models.Task.project_id == project_id)
    return query.offset(skip).limit(limit).all()

def update_task(db: Session, task_id: UUID, task: schemas.TaskUpdate) -> Optional[models.Task]:
    db_task = get_task(db, task_id)
    if db_task:
        update_data = task.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_task, key, value)
        db.commit()
        db.refresh(db_task)
    return db_task

def delete_task(db: Session, task_id: UUID) -> bool:
    db_task = get_task(db, task_id)
    if db_task:
        db.delete(db_task)
        db.commit()
        return True
    return False

def update_task_status(db: Session, task_id: UUID, status: str, error: Optional[str] = None) -> Optional[models.Task]:
    db_task = get_task(db, task_id)
    if not db_task:
        return None
    
    db_task.status = status
    if error:
        db_task.error = error
    
    if status == "running" and not db_task.started_at:
        db_task.started_at = datetime.utcnow()
    elif status in ["completed", "failed"]:
        db_task.completed_at = datetime.utcnow()
        if db_task.started_at:
            db_task.duration = (db_task.completed_at - db_task.started_at).total_seconds()
    
    db.commit()
    db.refresh(db_task)
    return db_task

# Task dependency operations
def create_task_dependency(db: Session, dependency: schemas.TaskDependencyCreate) -> Optional[models.TaskDependency]:
    # Check if both tasks exist
    task = get_task(db, dependency.task_id)
    depends_on_task = get_task(db, dependency.depends_on_task_id)
    
    if not task or not depends_on_task:
        return None
    
    # Create dependency
    db_dependency = models.TaskDependency(
        task_id=dependency.task_id,
        depends_on_task_id=dependency.depends_on_task_id
    )
    
    try:
        db.add(db_dependency)
        db.commit()
        db.refresh(db_dependency)
        return db_dependency
    except IntegrityError:
        db.rollback()
        return None

def delete_task_dependency(db: Session, task_id: UUID, depends_on_task_id: UUID) -> bool:
    db_dependency = db.query(models.TaskDependency).filter(
        models.TaskDependency.task_id == task_id,
        models.TaskDependency.depends_on_task_id == depends_on_task_id
    ).first()
    
    if db_dependency:
        db.delete(db_dependency)
        db.commit()
        return True
    return False

# Agent CRUD operations
def create_agent(db: Session, agent: schemas.AgentCreate) -> models.Agent:
    db_agent = models.Agent(
        name=agent.name,
        role=agent.role,
        description=agent.description,
        model_name=agent.model_name,
        model_provider=agent.model_provider,
        model_settings=agent.model_settings,
        system_prompt=agent.system_prompt
    )
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent

def get_agent(db: Session, agent_id: UUID) -> Optional[models.Agent]:
    return db.query(models.Agent).filter(models.Agent.id == agent_id).first()

def get_agent_by_name(db: Session, name: str) -> Optional[models.Agent]:
    return db.query(models.Agent).filter(models.Agent.name == name).first()

def get_agents(db: Session, skip: int = 0, limit: int = 100) -> List[models.Agent]:
    return db.query(models.Agent).offset(skip).limit(limit).all()

def update_agent(db: Session, agent_id: UUID, agent: schemas.AgentUpdate) -> Optional[models.Agent]:
    db_agent = get_agent(db, agent_id)
    if db_agent:
        update_data = agent.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_agent, key, value)
        db.commit()
        db.refresh(db_agent)
    return db_agent

def delete_agent(db: Session, agent_id: UUID) -> bool:
    db_agent = get_agent(db, agent_id)
    if db_agent:
        db.delete(db_agent)
        db.commit()
        return True
    return False

# Artifact CRUD operations
def create_artifact(db: Session, artifact: schemas.ArtifactCreate) -> models.Artifact:
    db_artifact = models.Artifact(
        name=artifact.name,
        type=artifact.type,
        path=artifact.path,
        content=artifact.content,
        artifact_metadata=artifact.artifact_metadata,
        project_id=artifact.project_id,
        task_id=artifact.task_id
    )
    db.add(db_artifact)
    db.commit()
    db.refresh(db_artifact)
    return db_artifact

def get_artifact(db: Session, artifact_id: UUID) -> Optional[models.Artifact]:
    return db.query(models.Artifact).filter(models.Artifact.id == artifact_id).first()

def get_artifacts(
    db: Session, 
    project_id: Optional[UUID] = None, 
    task_id: Optional[UUID] = None, 
    artifact_type: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[models.Artifact]:
    query = db.query(models.Artifact)
    
    if project_id:
        query = query.filter(models.Artifact.project_id == project_id)
    if task_id:
        query = query.filter(models.Artifact.task_id == task_id)
    if artifact_type:
        query = query.filter(models.Artifact.type == artifact_type)
        
    return query.offset(skip).limit(limit).all()

def update_artifact(db: Session, artifact_id: UUID, artifact: schemas.ArtifactUpdate) -> Optional[models.Artifact]:
    db_artifact = get_artifact(db, artifact_id)
    if db_artifact:
        update_data = artifact.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_artifact, key, value)
        db.commit()
        db.refresh(db_artifact)
    return db_artifact

def delete_artifact(db: Session, artifact_id: UUID) -> bool:
    db_artifact = get_artifact(db, artifact_id)
    if db_artifact:
        db.delete(db_artifact)
        db.commit()
        return True
    return False

# Execution log operations
def create_execution_log(db: Session, log: schemas.ExecutionLogCreate) -> models.ExecutionLog:
    db_log = models.ExecutionLog(
        project_id=log.project_id,
        task_id=log.task_id,
        agent_id=log.agent_id,
        log_type=log.log_type,
        message=log.message,
        details=log.details
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def get_execution_logs(
    db: Session, 
    project_id: Optional[UUID] = None,
    task_id: Optional[UUID] = None,
    agent_id: Optional[UUID] = None,
    log_type: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[models.ExecutionLog]:
    query = db.query(models.ExecutionLog)
    
    if project_id:
        query = query.filter(models.ExecutionLog.project_id == project_id)
    if task_id:
        query = query.filter(models.ExecutionLog.task_id == task_id)
    if agent_id:
        query = query.filter(models.ExecutionLog.agent_id == agent_id)
    if log_type:
        query = query.filter(models.ExecutionLog.log_type == log_type)
        
    return query.order_by(models.ExecutionLog.timestamp.desc()).offset(skip).limit(limit).all() 