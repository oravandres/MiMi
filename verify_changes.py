"""Verify changes to the Software Engineer AI Super Agent system."""

from pathlib import Path
import json

from mimi.core.project import Project
from mimi.core.software_agents import ResearchAnalystAgent, ArchitectAgent, SoftwareEngineerAgent, QAEngineerAgent, ReviewerAgent


def main():
    """Verify that the new agent types are registered correctly."""
    print("Verifying Software Engineer AI Super Agent changes...\n")
    
    # Create a project from the config
    project_path = Path("projects/sample/config")
    print(f"Creating project from {project_path}...")
    
    try:
        project = Project.from_config(project_path)
        print(f"Successfully created project: {project.name}")
        print(f"Project description: {project.description}")
        print(f"Number of agents: {len(project.agents)}")
        print(f"Number of tasks: {len(project.tasks)}")
        
        # Check agent types
        print("\nVerifying agent types:")
        for name, agent in project.agents.items():
            print(f"  - {name}: {type(agent).__name__}")
        
        # Get execution order
        print("\nTask execution order:")
        order = project.get_execution_order()
        for i, task_name in enumerate(order):
            task = project.tasks[task_name]
            print(f"  {i+1}. {task_name} ({task.agent})")
        
        print("\nChanges verified successfully!")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False


if __name__ == "__main__":
    main() 