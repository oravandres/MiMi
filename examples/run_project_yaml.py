#!/usr/bin/env python3
"""Example script to run a project using the project.yaml structure."""

import os
import sys
from pathlib import Path
import argparse

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mimi.core.project import Project
from mimi.core.runner import ProjectRunner
from mimi.utils.logger import setup_logger


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run a MiMi project using project.yaml")
    
    parser.add_argument(
        "-p", "--project-path", 
        default=str(Path(__file__).parent.parent / "projects" / "sample" / "config"),
        help="Path to the project configuration directory (should contain project.yaml)"
    )
    
    parser.add_argument(
        "-r", "--requirements", 
        required=True,
        help="Project requirements to analyze"
    )
    
    parser.add_argument(
        "--sub-project",
        help="Run only a specific sub-project (by name)"
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true",
        default=True,
        help="Execute tasks in parallel when possible (default: True)"
    )
    
    parser.add_argument(
        "--no-parallel",
        action="store_false",
        dest="parallel",
        help="Disable parallel execution of tasks"
    )
    
    parser.add_argument(
        "--max-workers",
        type=int,
        default=3,
        help="Maximum number of parallel workers (default: 3)"
    )
    
    parser.add_argument(
        "--log-level", 
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level"
    )
    
    return parser.parse_args()


def run_project(args):
    """Run a project with the specified configuration.
    
    Args:
        args: Parsed command line arguments.
    """
    # Setup logger
    setup_logger(log_level=args.log_level)
    
    # Get the project configuration directory
    project_dir = Path(args.project_path)
    
    # Load the project
    print(f"Loading project from: {project_dir}")
    project = Project.from_config(project_dir)
    
    print(f"Project: {project.name}")
    print(f"Description: {project.description}")
    print(f"Agents: {len(project.agents)}")
    print(f"Tasks: {len(project.tasks)}")
    
    # Create a runner
    runner = ProjectRunner(
        project, 
        parallel=args.parallel, 
        max_workers=args.max_workers
    )
    
    # Filter tasks by sub-project if specified
    if args.sub_project:
        print(f"\nRunning only sub-project: {args.sub_project}")
        filtered_tasks = {}
        for task_name, task in project.tasks.items():
            # Check if the task belongs to the specified sub-project
            if getattr(task, "sub_project", None) == args.sub_project:
                filtered_tasks[task_name] = task
        
        if not filtered_tasks:
            print(f"No tasks found for sub-project: {args.sub_project}")
            return
        
        # Replace project tasks with filtered ones
        project.tasks = filtered_tasks
        print(f"Filtered to {len(project.tasks)} tasks")
    
    # Prepare input
    project_input = {
        "requirements": args.requirements,
        "project_context": {
            "name": project.name,
            "description": project.description
        }
    }
    
    # Run the project
    print(f"\nRunning project with input requirements...")
    result = runner.run(project_input)
    
    # Display results
    print("\nResults:")
    if isinstance(result, dict):
        for key, value in result.items():
            if key in ["status", "message"]:
                print(f"  {key}: {value}")
            elif key == "data" and isinstance(value, dict):
                print("  Data:")
                for sub_key, sub_value in value.items():
                    if sub_key == "summary" and isinstance(sub_value, dict):
                        print("    Summary:")
                        for summary_key, summary_value in sub_value.items():
                            print(f"      {summary_key}: {summary_value}")
    else:
        print(f"  Final result: {result}")


if __name__ == "__main__":
    args = parse_args()
    run_project(args) 