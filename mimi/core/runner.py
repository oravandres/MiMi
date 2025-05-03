"""Runners for executing projects and tasks in MiMi."""

from typing import Any, Dict, List, Optional, Union

from mimi.core.project import Project
from mimi.core.task import Task
from mimi.utils.logger import logger, project_log, task_log


class TaskRunner:
    """Runner for executing individual tasks."""

    def __init__(self, task: Task, agent_lookup: Dict[str, Any]) -> None:
        """Initialize the task runner.
        
        Args:
            task: The task to execute.
            agent_lookup: Dictionary mapping agent names to agent objects.
        """
        self.task = task
        self.agent_lookup = agent_lookup
        task_log(
            task.name,
            "init",
            f"Task runner initialized for task '{task.name}'",
        )
        
    def run(self, input_data: Any) -> Any:
        """Execute the task with the provided input.
        
        Args:
            input_data: Input data for the task.
            
        Returns:
            The output from the task execution.
        """
        task_log(
            self.task.name,
            "run",
            f"Running task '{self.task.name}'",
            data={"input": input_data},
        )
        
        result = self.task.execute(self.agent_lookup, input_data)
        
        task_log(
            self.task.name,
            "completed",
            f"Task '{self.task.name}' completed",
            data={"result": result},
        )
        
        return result


class ProjectRunner:
    """Runner for executing entire projects."""

    def __init__(self, project: Project) -> None:
        """Initialize the project runner.
        
        Args:
            project: The project to execute.
        """
        self.project = project
        project_log(
            project.name,
            "init",
            f"Project runner initialized for project '{project.name}'",
        )
        
    def run(self, input_data: Any) -> Any:
        """Execute the project with the provided input.
        
        Tasks are executed in dependency order.
        
        Args:
            input_data: Input data for the project.
            
        Returns:
            The final result after executing all tasks.
        """
        project_log(
            self.project.name,
            "run",
            f"Running project '{self.project.name}'",
            data={"input": input_data},
        )
        
        # Get the execution order
        task_order = self.project.get_execution_order()
        project_log(
            self.project.name,
            "planning",
            f"Task execution order: {task_order}",
        )
        
        # Execute tasks in order
        result = input_data
        for task_name in task_order:
            task = self.project.tasks[task_name]
            runner = TaskRunner(task, self.project.agents)
            
            project_log(
                self.project.name,
                "execute_task",
                f"Executing task '{task_name}'",
            )
            
            result = runner.run(result)
            
            project_log(
                self.project.name,
                "task_completed",
                f"Task '{task_name}' completed",
                data={"current_result": result},
            )
        
        project_log(
            self.project.name,
            "completed",
            f"Project '{self.project.name}' completed",
            data={"final_result": result},
        )
        
        return result 