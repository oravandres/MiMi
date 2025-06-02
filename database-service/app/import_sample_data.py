#!/usr/bin/env python3
"""Import sample data from MiMi YAML files into the database."""

import os
import sys
import yaml
import uuid
from datetime import datetime
from pathlib import Path

# Add parent directory to path to find MiMi modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session

import models
import schemas
import crud
from database import SessionLocal, engine

# Initialize the database
models.Base.metadata.create_all(bind=engine)

def import_project_yaml(yaml_path: str, db: Session) -> dict:
    """Import a MiMi project from a YAML file into the database."""
    print(f"Importing project from {yaml_path}...")
    
    # Load the YAML file
    with open(yaml_path, 'r') as f:
        project_config = yaml.safe_load(f)
    
    # Create the project
    project_create = schemas.ProjectCreate(
        name=project_config.get('project_name', 'Imported Project'),
        description=project_config.get('project_description', ''),
        config=project_config
    )
    db_project = crud.create_project(db=db, project=project_create)
    print(f"Created project: {db_project.name} (ID: {db_project.id})")
    
    # Store agent mappings (name -> id)
    agent_map = {}
    
    # Create agents
    if 'agents' in project_config:
        for agent_config in project_config['agents']:
            model_settings = {}
            if 'model_settings' in agent_config:
                model_settings = agent_config['model_settings']
                
            agent_create = schemas.AgentCreate(
                name=agent_config['name'],
                role=agent_config['role'],
                description=agent_config.get('description', ''),
                model_name=agent_config.get('model_name', 'unknown'),
                model_provider=agent_config.get('model_provider', 'ollama'),
                model_settings=model_settings,
                system_prompt=agent_config.get('system_prompt', '')
            )
            
            try:
                db_agent = crud.create_agent(db=db, agent=agent_create)
                agent_map[db_agent.name] = db_agent.id
                print(f"Created agent: {db_agent.name} (ID: {db_agent.id})")
            except Exception as e:
                print(f"Error creating agent {agent_config['name']}: {str(e)}")
    
    # Store task mappings (name -> id)
    task_map = {}
    task_dependencies = []
    
    # Process tasks
    if 'sub_projects' in project_config:
        for subproject in project_config['sub_projects']:
            if 'tasks' in subproject:
                for task_config in subproject['tasks']:
                    # Convert input_key to a dictionary
                    input_key_data = {}
                    if 'input_key' in task_config:
                        if isinstance(task_config['input_key'], list):
                            input_key_data = {"input_sources": task_config['input_key']}
                        else:
                            input_key_data = {"input_source": task_config['input_key']}
                    
                    # Create the task
                    task_create = schemas.TaskCreate(
                        name=task_config['name'],
                        description=task_config.get('description', ''),
                        agent=task_config.get('agent', ''),
                        input_key=input_key_data,
                        output_key=task_config.get('output_key', ''),
                        project_id=db_project.id
                    )
                    
                    try:
                        db_task = crud.create_task(db=db, task=task_create)
                        task_map[db_task.name] = db_task.id
                        print(f"Created task: {db_task.name} (ID: {db_task.id})")
                        
                        # Store dependencies to create after all tasks are created
                        if 'depends_on' in task_config and task_config['depends_on']:
                            for dependency in task_config['depends_on']:
                                task_dependencies.append((db_task.name, dependency))
                    except Exception as e:
                        print(f"Error creating task {task_config['name']}: {str(e)}")
    
    # Create task dependencies
    for task_name, dependency_name in task_dependencies:
        if task_name in task_map and dependency_name in task_map:
            try:
                dependency_create = schemas.TaskDependencyCreate(
                    task_id=task_map[task_name],
                    depends_on_task_id=task_map[dependency_name]
                )
                crud.create_task_dependency(db=db, dependency=dependency_create)
                print(f"Created dependency: {task_name} depends on {dependency_name}")
            except Exception as e:
                print(f"Error creating dependency {task_name} -> {dependency_name}: {str(e)}")
        else:
            print(f"Warning: Could not create dependency {task_name} -> {dependency_name}, task not found")
    
    # Create a log entry for the import
    log_create = schemas.ExecutionLogCreate(
        project_id=db_project.id,
        log_type="import",
        message=f"Imported project from {yaml_path}",
        details={
            "source": yaml_path,
            "import_time": datetime.utcnow().isoformat(),
            "task_count": len(task_map),
            "agent_count": len(agent_map)
        }
    )
    crud.create_execution_log(db=db, log=log_create)
    
    return {
        "project_id": str(db_project.id),
        "task_count": len(task_map),
        "agent_count": len(agent_map),
        "dependency_count": len(task_dependencies)
    }

def import_all_projects(base_dir: str = None) -> None:
    """Import all project YAML files found in the given directory."""
    if base_dir is None:
        # Default to project directory in MiMi repo
        base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "projects")
    
    project_paths = []
    
    # Find all project.yaml files
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file == "project.yaml":
                project_paths.append(os.path.join(root, file))
    
    print(f"Found {len(project_paths)} project files to import")
    
    # Import each project
    result = []
    with SessionLocal() as db:
        for project_path in project_paths:
            try:
                project_data = import_project_yaml(project_path, db)
                result.append(project_data)
                print(f"Successfully imported {project_path}")
            except Exception as e:
                print(f"Error importing {project_path}: {str(e)}")
    
    print(f"Imported {len(result)} projects")
    return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        import_project_yaml(sys.argv[1], SessionLocal())
    else:
        import_all_projects() 