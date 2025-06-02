from typing import List, Optional
from uuid import UUID
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

import crud
import models
import schemas
from database import engine, get_db

# Create tables in the database
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MiMi Database Service",
    description="API for managing MiMi projects, tasks, and artifacts",
    version="0.1.0"
)

@app.get("/")
def read_root():
    return {"message": "MiMi Database Service API"}

# Project endpoints
@app.post("/projects/", response_model=schemas.Project, status_code=status.HTTP_201_CREATED)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    return crud.create_project(db=db, project=project)

@app.get("/projects/", response_model=List[schemas.Project])
def read_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    projects = crud.get_projects(db, skip=skip, limit=limit)
    return projects

@app.get("/projects/{project_id}", response_model=schemas.Project)
def read_project(project_id: UUID, db: Session = Depends(get_db)):
    db_project = crud.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project

@app.put("/projects/{project_id}", response_model=schemas.Project)
def update_project(project_id: UUID, project: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    db_project = crud.update_project(db, project_id=project_id, project=project)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project

@app.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: UUID, db: Session = Depends(get_db)):
    success = crud.delete_project(db, project_id=project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return None

# Task endpoints
@app.post("/tasks/", response_model=schemas.Task, status_code=status.HTTP_201_CREATED)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    # Verify that project exists
    project = crud.get_project(db, project_id=task.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return crud.create_task(db=db, task=task)

@app.get("/tasks/", response_model=List[schemas.Task])
def read_tasks(project_id: Optional[UUID] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tasks = crud.get_tasks(db, project_id=project_id, skip=skip, limit=limit)
    return tasks

@app.get("/tasks/{task_id}", response_model=schemas.Task)
def read_task(task_id: UUID, db: Session = Depends(get_db)):
    db_task = crud.get_task(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@app.put("/tasks/{task_id}", response_model=schemas.Task)
def update_task(task_id: UUID, task: schemas.TaskUpdate, db: Session = Depends(get_db)):
    db_task = crud.update_task(db, task_id=task_id, task=task)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: UUID, db: Session = Depends(get_db)):
    success = crud.delete_task(db, task_id=task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return None

@app.put("/tasks/{task_id}/status", response_model=schemas.Task)
def update_task_status(task_id: UUID, status: str, error: Optional[str] = None, db: Session = Depends(get_db)):
    valid_statuses = ["pending", "running", "completed", "failed"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    db_task = crud.update_task_status(db, task_id=task_id, status=status, error=error)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

# Task dependency endpoints
@app.post("/task-dependencies/", status_code=status.HTTP_201_CREATED)
def create_task_dependency(dependency: schemas.TaskDependencyCreate, db: Session = Depends(get_db)):
    db_dependency = crud.create_task_dependency(db, dependency=dependency)
    if db_dependency is None:
        raise HTTPException(
            status_code=400, 
            detail="Could not create dependency. Ensure both tasks exist and aren't already linked."
        )
    return {"success": True}

@app.delete("/task-dependencies/{task_id}/{depends_on_task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_dependency(task_id: UUID, depends_on_task_id: UUID, db: Session = Depends(get_db)):
    success = crud.delete_task_dependency(db, task_id=task_id, depends_on_task_id=depends_on_task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task dependency not found")
    return None

# Agent endpoints
@app.post("/agents/", response_model=schemas.Agent, status_code=status.HTTP_201_CREATED)
def create_agent(agent: schemas.AgentCreate, db: Session = Depends(get_db)):
    db_agent = crud.get_agent_by_name(db, name=agent.name)
    if db_agent:
        raise HTTPException(status_code=400, detail="Agent with this name already exists")
    return crud.create_agent(db=db, agent=agent)

@app.get("/agents/", response_model=List[schemas.Agent])
def read_agents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    agents = crud.get_agents(db, skip=skip, limit=limit)
    return agents

@app.get("/agents/{agent_id}", response_model=schemas.Agent)
def read_agent(agent_id: UUID, db: Session = Depends(get_db)):
    db_agent = crud.get_agent(db, agent_id=agent_id)
    if db_agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return db_agent

@app.put("/agents/{agent_id}", response_model=schemas.Agent)
def update_agent(agent_id: UUID, agent: schemas.AgentUpdate, db: Session = Depends(get_db)):
    db_agent = crud.update_agent(db, agent_id=agent_id, agent=agent)
    if db_agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return db_agent

@app.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent(agent_id: UUID, db: Session = Depends(get_db)):
    success = crud.delete_agent(db, agent_id=agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    return None

# Artifact endpoints
@app.post("/artifacts/", response_model=schemas.Artifact, status_code=status.HTTP_201_CREATED)
def create_artifact(artifact: schemas.ArtifactCreate, db: Session = Depends(get_db)):
    # Verify that project exists
    project = crud.get_project(db, project_id=artifact.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify task if provided
    if artifact.task_id:
        task = crud.get_task(db, task_id=artifact.task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
    
    return crud.create_artifact(db=db, artifact=artifact)

@app.get("/artifacts/", response_model=List[schemas.Artifact])
def read_artifacts(
    project_id: Optional[UUID] = None, 
    task_id: Optional[UUID] = None, 
    artifact_type: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    artifacts = crud.get_artifacts(
        db, 
        project_id=project_id, 
        task_id=task_id, 
        artifact_type=artifact_type,
        skip=skip, 
        limit=limit
    )
    return artifacts

@app.get("/artifacts/{artifact_id}", response_model=schemas.Artifact)
def read_artifact(artifact_id: UUID, db: Session = Depends(get_db)):
    db_artifact = crud.get_artifact(db, artifact_id=artifact_id)
    if db_artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return db_artifact

@app.put("/artifacts/{artifact_id}", response_model=schemas.Artifact)
def update_artifact(artifact_id: UUID, artifact: schemas.ArtifactUpdate, db: Session = Depends(get_db)):
    db_artifact = crud.update_artifact(db, artifact_id=artifact_id, artifact=artifact)
    if db_artifact is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return db_artifact

@app.delete("/artifacts/{artifact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_artifact(artifact_id: UUID, db: Session = Depends(get_db)):
    success = crud.delete_artifact(db, artifact_id=artifact_id)
    if not success:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return None

# Execution log endpoints
@app.post("/logs/", response_model=schemas.ExecutionLog, status_code=status.HTTP_201_CREATED)
def create_log(log: schemas.ExecutionLogCreate, db: Session = Depends(get_db)):
    # Verify that project exists
    project = crud.get_project(db, project_id=log.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify task if provided
    if log.task_id:
        task = crud.get_task(db, task_id=log.task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
    
    # Verify agent if provided
    if log.agent_id:
        agent = crud.get_agent(db, agent_id=log.agent_id)
        if agent is None:
            raise HTTPException(status_code=404, detail="Agent not found")
    
    return crud.create_execution_log(db=db, log=log)

@app.get("/logs/", response_model=List[schemas.ExecutionLog])
def read_logs(
    project_id: Optional[UUID] = None,
    task_id: Optional[UUID] = None,
    agent_id: Optional[UUID] = None,
    log_type: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    logs = crud.get_execution_logs(
        db, 
        project_id=project_id, 
        task_id=task_id, 
        agent_id=agent_id,
        log_type=log_type,
        skip=skip, 
        limit=limit
    )
    return logs 