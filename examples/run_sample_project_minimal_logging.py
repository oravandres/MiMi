#!/usr/bin/env python3
"""Run the sample project with minimal logging.

This script runs the sample project with reduced logging, showing only 
essential log entries (started, execute, completed) to reduce verbosity.
"""

import sys
from pathlib import Path

# Add the root directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mimi.core.project import Project, ProjectRunner
from mimi.utils.logger import update_allowed_log_types


def main():
    """Run the sample project with a given input value."""
    # Parse input value from command line
    if len(sys.argv) < 2:
        print("Usage: python run_sample_project_minimal_logging.py <input_value>")
        print("Example: python run_sample_project_minimal_logging.py 100")
        sys.exit(1)
        
    try:
        input_value = float(sys.argv[1])
    except ValueError:
        print(f"Error: '{sys.argv[1]}' is not a valid number")
        sys.exit(1)
    
    # Configure even more minimal logging - just show agent execute statements
    # Uncomment different settings to control verbosity
    
    # Most minimal - only show agent execution
    update_allowed_log_types(["execute"])
    
    # Basic - show task start/complete and agent execution
    # update_allowed_log_types(["started", "execute", "completed"])
    
    # More detailed - include feedback messages
    # update_allowed_log_types(["started", "execute", "completed", "feedback"])
    
    # Load the project from config
    project_config_path = Path(__file__).parent.parent / "projects" / "sample" / "config"
    project = Project.from_config_dir(project_config_path)
    
    # Create a project runner and run the project
    runner = ProjectRunner(project)
    
    print(f"\nRunning project with input: {input_value}")
    result = runner.run({"input": input_value})
    
    print("\nProject completed! Final result:")
    print(f"Input: {input_value}")
    
    # Display the result keys
    result_keys = sorted([k for k in result if k.startswith("result")])
    for key in result_keys:
        print(f"{key}: {result[key]}")
    
    # Display verification status
    verified_keys = sorted([k for k in result if k.startswith("verified")])
    for key in verified_keys:
        if isinstance(result[key], dict):
            status = result[key].get("status", "unknown")
            message = result[key].get("message", "No message")
            print(f"{key}: {status} - {message}")
    
    # Display feedback messages
    feedback_keys = sorted([k for k in result if k.startswith("feedback")])
    for key in feedback_keys:
        if isinstance(result[key], dict):
            status = result[key].get("status", "unknown")
            message = result[key].get("message", "No message")
            continue_flag = "Continue" if result[key].get("continue", False) else "Stop"
            print(f"{key}: {status} - {continue_flag} - {message}")
    
    print("\nFinal state contains these keys:")
    print(", ".join(sorted(result.keys())))


if __name__ == "__main__":
    main() 