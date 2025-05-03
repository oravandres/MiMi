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

from mimi.core.agent import Agent, AnalystAgent, FeedbackProcessorAgent
from mimi.core.software_agents import ResearchAnalystAgent, ArchitectAgent, SoftwareEngineerAgent, QAEngineerAgent, ReviewerAgent
from mimi.core.task import Task
from mimi.utils.config import load_project_config
from mimi.utils.logger import logger, project_log


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
        agents_config = config["agents"]
        tasks_config = config["tasks"]
        
        project_name = agents_config.get("project_name", "MiMi Project")
        project_desc = agents_config.get(
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
            elif agent_type.lower() == "feedback_processor":
                # Special case for feedback processor agents
                agent = FeedbackProcessorAgent.from_config(agent_config)
            # New agent types for Software Engineer AI Super Agent
            elif agent_type.lower() == "research_analyst":
                agent = ResearchAnalystAgent.from_config(agent_config)
            elif agent_type.lower() == "architect":
                agent = ArchitectAgent.from_config(agent_config)
            elif agent_type.lower() == "software_engineer":
                agent = SoftwareEngineerAgent.from_config(agent_config)
            elif agent_type.lower() == "qa_engineer":
                agent = QAEngineerAgent.from_config(agent_config)
            elif agent_type.lower() == "reviewer":
                agent = ReviewerAgent.from_config(agent_config)
            else:
                # Default agent type
                agent = Agent.from_config(agent_config)
                
            project.agents[agent_name] = agent
            
        # Create tasks
        for task_config in tasks_config.get("tasks", []):
            task_name = task_config.get("name", "")
            task = Task.from_config(task_config)
            project.tasks[task_name] = task
            
        # Validate task dependencies but don't initialize agents yet
        # The main.py will call initialize() separately
        project.validate_task_dependencies()
        
        return project 