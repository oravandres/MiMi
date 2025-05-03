#!/usr/bin/env python3
"""Test script for agent logging functionality."""

import sys
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from mimi.core.agent import Agent
from mimi.utils.logger import setup_logger
from mimi.utils.output_manager import create_output_directory, create_or_update_agent_log, create_or_update_project_log


def main():
    """Run a simple test of the agent logging functionality."""
    # Setup logging
    setup_logger(log_level="DEBUG")
    
    # Create a test project directory
    project_title = "AgentLogTest"
    project_dir = create_output_directory(project_title)
    print(f"Created project directory: {project_dir}")
    
    # Create a test agent
    agent = Agent(
        name="test-agent",
        role="Test Agent",
        description="A test agent for logging",
        model_name="test-model",
        model_provider="test"
    )
    
    # Log some actions
    print("Logging agent actions...")
    
    # Test project log
    create_or_update_project_log(
        project_dir=project_dir,
        event_type="test-event",
        agent_name="test-agent",
        description="Testing project logging",
        details={"test_key": "test_value"}
    )
    
    # Test agent log
    agent.log_to_agent_file(
        project_dir=project_dir,
        action_type="test-action",
        input_summary="Test input data with some content",
        output_summary="Test output with results",
        details={
            "action_id": "test-123",
            "duration": "1.5s",
            "status": "success"
        }
    )
    
    # Test complex input/output
    complex_input = {
        "project_requirements": "Build a web application",
        "user_preferences": {
            "theme": "dark",
            "language": "en-US"
        },
        "constraints": ["time", "budget", "resources"]
    }
    
    complex_output = {
        "implementation": "Generated code and components",
        "files_created": 12,
        "completion_status": "success",
        "metrics": {
            "lines_of_code": 1200,
            "components": 8,
            "files": 15
        }
    }
    
    agent.log_to_agent_file(
        project_dir=project_dir,
        action_type="complex-test",
        input_summary=complex_input,
        output_summary=complex_output,
        details={"test_type": "complex data"}
    )
    
    # Log final status
    project_log_path = project_dir / "project.log.md"
    agent_log_path = project_dir / "agent.log.md"
    
    print(f"\nTest complete!")
    print(f"Project log file: {project_log_path}")
    print(f"Agent log file: {agent_log_path}")
    
    # Display log content
    if project_log_path.exists():
        print("\nProject Log Content:")
        print("-" * 50)
        with open(project_log_path, 'r') as f:
            print(f.read())
    
    if agent_log_path.exists():
        print("\nAgent Log Content:")
        print("-" * 50)
        with open(agent_log_path, 'r') as f:
            print(f.read())


if __name__ == "__main__":
    main() 