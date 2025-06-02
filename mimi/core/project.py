"""Project and configuration handling for MiMi."""

import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

# Add vendor directory to path to find pydantic
vendor_path = Path(__file__).parent.parent / "vendor"
if vendor_path.exists() and str(vendor_path) not in sys.path:
    sys.path.append(str(vendor_path))

from pydantic import BaseModel, Field, ConfigDict

from mimi.core.agents import (
    Agent, 
    AnalystAgent, 
    ArchitectAgent,
    SoftwareEngineerAgent,
    QAEngineerAgent,
    ReviewerAgent,
    DeveloperAgent,
    SecurityEngineerAgent,
    UIDesignerAgent,
    TechnicalWriterAgent
)
from mimi.core.task import Task
from mimi.utils.config import load_project_config
from mimi.utils.logger import logger, project_log
from mimi.utils.output_manager import create_or_update_project_log


class Project(BaseModel):
    """A project that orchestrates agents and tasks."""

    name: str = Field(..., description="Name of the project")
    description: str = Field(
        ..., description="Description of what the project does"
    )
    agents: Dict[str, Agent] = Field(
        default_factory=dict, description="Dictionary of agent name to agent object"
    )
    tasks: Dict[str, Task] = Field(
        default_factory=dict, description="Dictionary of task name to task object"
    )
    
    # Pydantic v2 configuration
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def initialize(self) -> None:
        """Initialize the project and all its agents."""
        project_log(
            self.name, 
            "initialize", 
            f"Initializing project with {len(self.agents)} agents and {len(self.tasks)} tasks"
        )
        
        for agent_name, agent in self.agents.items():
            agent.initialize()

    def validate_task_dependencies(self) -> None:
        """Validate that all task dependencies exist and there are no cycles.
        
        Raises:
            ValueError: If there are missing dependencies or circular dependencies.
        """
        # Check that all dependencies exist
        all_task_names = set(self.tasks.keys())
        
        for task_name, task in self.tasks.items():
            missing_deps = set(task.depends_on) - all_task_names
            if missing_deps:
                error_msg = f"Task '{task_name}' depends on non-existent tasks: {missing_deps}"
                project_log(self.name, "error", error_msg)
                raise ValueError(error_msg)
        
        # Check for circular dependencies
        visited: Dict[str, bool] = {}
        temp: Dict[str, bool] = {}
        
        def has_cycle(task_name: str) -> bool:
            if task_name in temp:
                # Already in the recursion stack, so we have a cycle
                return True
            if task_name in visited:
                # Already processed this node, no cycle here
                return False
                
            # Mark as being processed
            temp[task_name] = True
            
            # Check all dependencies
            for dep in self.tasks[task_name].depends_on:
                if has_cycle(dep):
                    return True
                    
            # Remove from 'being processed'
            temp.pop(task_name)
            # Mark as processed
            visited[task_name] = True
            
            return False
        
        for task_name in self.tasks:
            if has_cycle(task_name):
                error_msg = f"Circular dependency detected involving task '{task_name}'"
                project_log(self.name, "error", error_msg)
                raise ValueError(error_msg)

    def get_execution_order(self) -> List[str]:
        """Get an ordered list of task names based on dependencies.
        
        Returns:
            A list of task names in execution order.
        """
        self.validate_task_dependencies()
        
        # Topological sort
        visited: Set[str] = set()
        result: List[str] = []
        
        def visit(task_name: str) -> None:
            if task_name in visited:
                return
                
            visited.add(task_name)
            
            for dep in self.tasks[task_name].depends_on:
                visit(dep)
                
            result.append(task_name)
        
        for task_name in self.tasks:
            visit(task_name)
            
        return result

    def update_project_log(self, agent_name: str, event_type: str, description: str, details: Dict[str, Any]) -> None:
        """Update the project log with agent outputs.
        
        Args:
            agent_name: Name of the agent
            event_type: Type of event (e.g., "code-implementation", "ui-design")
            description: Description of the action
            details: Details about the action
        """
        if agent_name in self.agents:
            agent = self.agents[agent_name]
            try:
                # Try to get project_dir from details
                project_dir = details.get("project_dir", None)
                if project_dir:
                    # Create or update the project log
                    create_or_update_project_log(
                        project_dir=project_dir,
                        event_type=event_type,
                        agent_name=agent_name,
                        description=description,
                        details=details
                    )
                    logger.info(f"Updated project log for agent '{agent_name}': {event_type}")
            except Exception as e:
                logger.error(f"Error updating project log for agent '{agent_name}': {str(e)}")

    @classmethod
    def from_config(cls, config_dir: Union[str, Path]) -> "Project":
        """Create a project from a configuration directory.
        
        Args:
            config_dir: Directory containing configuration files.
            
        Returns:
            An initialized Project instance.
        """
        config = load_project_config(config_dir)
        
        # Extract project metadata
        project_config = config.get("project", {})
        agents_config = config.get("agents", {})
        tasks_config = config.get("tasks", {})
        
        project_name = project_config.get("project_name", "MiMi Project")
        project_desc = project_config.get(
            "project_description", "A multi-agent project"
        )
        
        # Create the project
        project = cls(
            name=project_name,
            description=project_desc,
            agents={},
            tasks={},
        )
        
        # Create agents
        for agent_config in agents_config.get("agents", []):
            agent_name = agent_config.get("name", "")
            agent_type = agent_config.get("type", "default")
            
            if agent_type.lower() == "analyst":
                # Special case for analyst agents
                agent = AnalystAgent.from_config(agent_config)
            elif agent_type.lower() == "architect":
                agent = ArchitectAgent.from_config(agent_config)
            elif agent_type.lower() == "software_engineer" or agent_type.lower() == "developer":
                agent = SoftwareEngineerAgent.from_config(agent_config)
            elif agent_type.lower() == "qa_engineer" or agent_type.lower() == "qa":
                agent = QAEngineerAgent.from_config(agent_config)
            elif agent_type.lower() == "reviewer":
                agent = ReviewerAgent.from_config(agent_config)
            elif agent_type.lower() == "writer" or agent_type.lower() == "technical_writer":
                # Map writer type to agent
                agent = TechnicalWriterAgent.from_config(agent_config)
            elif agent_type.lower() == "designer" or agent_type.lower() == "ui_designer":
                # Map designer type to agent
                agent = UIDesignerAgent.from_config(agent_config)
            elif agent_type.lower() == "security_engineer" or agent_type.lower() == "security":
                # Map security engineer type to agent
                agent = SecurityEngineerAgent.from_config(agent_config)
            elif agent_type.lower() == "engineer":
                # Map general engineer type to agent
                agent = DeveloperAgent.from_config(agent_config)
            else:
                # Default agent type
                agent = Agent.from_config(agent_config)
                
            project.agents[agent_name] = agent
            
        # Create tasks
        for task_config in tasks_config.get("tasks", []):
            task_name = task_config.get("name", "")
            task = Task.from_config(task_config)
            project.tasks[task_name] = task
            
        # Log sub-project information if available
        if "sub_projects" in project_config:
            sub_projects = project_config.get("sub_projects", [])
            project_log(
                project_name,
                "initialize",
                f"Project contains {len(sub_projects)} sub-projects"
            )
            
        # Validate task dependencies but don't initialize agents yet
        # The main.py will call initialize() separately
        project.validate_task_dependencies()
        
        return project 