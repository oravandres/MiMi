#!/usr/bin/env python3
"""Demo script for Rich-based visualizations in MiMi."""

import sys
import time
from pathlib import Path

# Add parent directory to path so we can import mimi
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table

from mimi.utils.logger import print_intro, setup_logger, console
from mimi.utils.logger import agent_log, task_log, project_log

# Initialize the console
console = Console()

def simulate_workflow():
    """Simulate a MiMi workflow with rich visualizations."""
    # Print the intro
    print_intro()
    
    # Show project initialization
    project_log("Rich Demo Project", "init", "Project runner initialized for project 'Rich Demo Project' (parallel=True, max_workers=4)")
    
    # Show agent initialization
    for agent_name, role, model in [
        ("frontend-analyst", "Frontend Requirements Analyst", "qwen3:latest"),
        ("frontend-architect", "Frontend Architect", "deepseek-r1:latest"),
        ("ui-designer", "UI/UX Designer", "qwen3:latest"),
        ("frontend-developer", "Frontend Developer", "deepseek-r1:latest"),
    ]:
        agent_log(agent_name, "info", f"Initialized agent '{agent_name}' with role '{role}' using ollama model: {model}")
        time.sleep(0.5)
    
    # Show project planning
    project_log("Rich Demo Project", "planning", "Executing batch of 2 tasks: ['frontend-requirements-analysis', 'backend-requirements-analysis']")
    
    # Simulate task execution with progress
    simulate_task("frontend-requirements-analysis", "frontend-analyst", 3)
    simulate_task("backend-requirements-analysis", "backend-analyst", 2)
    
    # Show project completion
    project_log("Rich Demo Project", "completed", "All tasks completed successfully")
    
    # Show project stats (create a fake result dictionary)
    result = {
        "input": "Create a flappy bird game in html and javascript",
        "frontend_specs": {"status": "completed", "duration": 3.2},
        "backend_specs": {"status": "completed", "duration": 2.1},
        "data_models": {"status": "completed", "duration": 1.5},
        "api_design": {"status": "completed", "duration": 2.8},
    }
    
    # Create a mock Project and args object for result summary
    class MockProject:
        def __init__(self):
            self.agents = {
                "frontend-analyst": MockAgent("Frontend Requirements Analyst", "ollama", "qwen3"),
                "backend-analyst": MockAgent("Backend Requirements Analyst", "ollama", "qwen3"),
                "frontend-architect": MockAgent("Frontend Architect", "ollama", "deepseek-r1"),
                "backend-architect": MockAgent("Backend Architect", "ollama", "qwen3"),
            }
            self.tasks = {
                "frontend-requirements-analysis": MockTask("frontend-analyst", []),
                "backend-requirements-analysis": MockTask("backend-analyst", []),
                "frontend-architecture-design": MockTask("frontend-architect", ["frontend-requirements-analysis"]),
                "api-design": MockTask("backend-architect", ["backend-requirements-analysis"]),
            }
        
        def get_execution_order(self):
            return [
                "frontend-requirements-analysis",
                "backend-requirements-analysis",
                "frontend-architecture-design",
                "api-design",
            ]
    
    class MockAgent:
        def __init__(self, role, provider, model_name):
            self.role = role
            self.model_provider = provider
            self.model_name = model_name
    
    class MockTask:
        def __init__(self, agent, depends_on):
            self.agent = agent
            self.depends_on = depends_on
    
    class MockArgs:
        def __init__(self):
            self.parallel = True
            self.max_workers = 4
    
    # Print the result summary
    from mimi.utils.logger import print_result_summary
    print_result_summary(result, MockProject(), MockArgs())


def simulate_task(task_name, agent_name, duration):
    """Simulate a task execution with progress."""
    # Task started
    task_log(task_name, "started", f"Runner executing task with agent '{agent_name}'", data={"agent": agent_name})
    time.sleep(0.2)
    task_log(task_name, "started", f"Executing task with agent '{agent_name}'", data={"agent": agent_name})
    time.sleep(0.2)
    
    # Task processing
    task_log(
        task_name, 
        "processing", 
        "Cleaning input data for verification/feedback agent", 
        data={"agent": agent_name}
    )
    time.sleep(0.2)
    agent_log(agent_name, "execute", f"Analyzing software requirements")
    
    # Show progress with Rich's progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[bold]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task(f"[cyan]Processing task '{task_name}'...", total=100)
        
        for i in range(101):
            time.sleep(duration / 100)  # Spread over the duration
            progress.update(task, completed=i)
    
    # Task completed
    agent_log(agent_name, "completed", "Analysis completed successfully")
    
    # Task description for completion messages
    task_description = f"Analyze {task_name.split('-')[0]} requirements"
    
    task_log(
        task_name, 
        "completed", 
        "Stored result in output key", 
        data={
            "agent": agent_name, 
            "output_key": f"{task_name.split('-')[0]}_specs",
            "description": task_description
        }
    )
    
    task_log(
        task_name, 
        "completed", 
        f"Task '{task_name}' completed", 
        data={
            "agent": agent_name,
            "description": task_description
        }
    )
    
    # Project task completed
    project_log("Rich Demo Project", "task_completed", f"Task '{task_name}' completed", {"duration": duration})


if __name__ == "__main__":
    # Setup logger with Rich enabled
    setup_logger(log_level="INFO", use_rich=True)
    
    # Run the demo
    simulate_workflow() 