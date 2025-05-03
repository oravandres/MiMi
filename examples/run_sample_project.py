#!/usr/bin/env python3
"""Example script to run the sample project."""

import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mimi.core.project import Project
from mimi.core.runner import ProjectRunner
from mimi.utils.logger import setup_logger


def run_sample_project(input_value: float = 5.0) -> None:
    """Run the sample number adder project.
    
    Args:
        input_value: The input number to process.
    """
    # Setup logger with more detailed output
    setup_logger(log_level="DEBUG")
    
    # Get the project directory
    project_dir = Path(__file__).parent.parent / "projects" / "sample" / "config"
    
    # Load the project
    print(f"Loading project from: {project_dir}")
    project = Project.from_config(project_dir)
    
    # Create a runner
    runner = ProjectRunner(project)
    
    # Run the project
    print(f"\nRunning project with input: {input_value}")
    result = runner.run({"input": input_value})
    
    # Display results
    print("\nResults:")
    if isinstance(result, dict):
        for key, value in result.items():
            if key.startswith("result"):
                print(f"  {key}: {value}")
    else:
        print(f"  Final result: {result}")


if __name__ == "__main__":
    # Get input value from command line if provided
    input_value = 5.0
    if len(sys.argv) > 1:
        try:
            input_value = float(sys.argv[1])
        except ValueError:
            print(f"Invalid input: {sys.argv[1]}, using default value of 5.0")
    
    run_sample_project(input_value) 