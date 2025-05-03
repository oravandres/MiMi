"""Tests for the ProjectRunner and TaskRunner classes."""

import pytest
from unittest.mock import MagicMock, patch

from mimi.core.agent import Agent
from mimi.core.project import Project
from mimi.core.runner import ProjectRunner, TaskRunner
from mimi.core.task import Task


class TestTaskRunner:
    """Tests for the TaskRunner class."""

    def test_task_runner_init(self) -> None:
        """Test initializing a TaskRunner."""
        # Create mock task and agent
        mock_task = MagicMock(spec=Task)
        mock_task.name = "test-task"
        
        mock_agent = MagicMock(spec=Agent)
        agent_lookup = {"test-agent": mock_agent}
        
        # Create the runner
        runner = TaskRunner(mock_task, agent_lookup)
        
        assert runner.task == mock_task
        assert runner.agent_lookup == agent_lookup

    def test_task_runner_run(self) -> None:
        """Test running a task."""
        # Create mock task and agent
        mock_task = MagicMock(spec=Task)
        mock_task.name = "test-task"
        mock_task.execute.return_value = 42
        
        mock_agent = MagicMock(spec=Agent)
        agent_lookup = {"test-agent": mock_agent}
        
        # Create the runner
        runner = TaskRunner(mock_task, agent_lookup)
        
        # Run the task
        result = runner.run({"input": 10})
        
        # Verify the task was executed
        mock_task.execute.assert_called_once_with(agent_lookup, {"input": 10})
        assert result == 42


class TestProjectRunner:
    """Tests for the ProjectRunner class."""

    def test_project_runner_init(self) -> None:
        """Test initializing a ProjectRunner."""
        # Create mock project
        mock_project = MagicMock(spec=Project)
        mock_project.name = "test-project"
        
        # Create the runner
        runner = ProjectRunner(mock_project)
        
        assert runner.project == mock_project

    def test_project_runner_run(self) -> None:
        """Test running a project."""
        # Create mock agents
        mock_agent1 = MagicMock(spec=Agent)
        mock_agent1.name = "agent1"
        
        mock_agent2 = MagicMock(spec=Agent)
        mock_agent2.name = "agent2"
        
        # Create mock tasks
        mock_task1 = MagicMock(spec=Task)
        mock_task1.name = "task1"
        mock_task1.execute.return_value = {"input": 10, "result1": 11}
        
        mock_task2 = MagicMock(spec=Task)
        mock_task2.name = "task2"
        mock_task2.execute.return_value = {"input": 10, "result1": 11, "result2": 12}
        
        # Create mock project
        mock_project = MagicMock(spec=Project)
        mock_project.name = "test-project"
        mock_project.agents = {"agent1": mock_agent1, "agent2": mock_agent2}
        mock_project.tasks = {"task1": mock_task1, "task2": mock_task2}
        
        # Configure the project to return a specific execution order
        mock_project.get_execution_order.return_value = ["task1", "task2"]
        
        # Create the runner
        runner = ProjectRunner(mock_project)
        
        # Run the project
        result = runner.run({"input": 10})
        
        # Verify the execution order was retrieved
        mock_project.get_execution_order.assert_called_once()
        
        # Verify the final result
        assert result == {"input": 10, "result1": 11, "result2": 12}

    @patch("mimi.core.runner.TaskRunner")
    def test_project_runner_uses_task_runner(self, mock_task_runner_class: MagicMock) -> None:
        """Test that ProjectRunner creates TaskRunner instances."""
        # Create mock TaskRunner instance
        mock_task_runner = MagicMock()
        mock_task_runner.run.return_value = {"input": 10, "result": 42}
        mock_task_runner_class.return_value = mock_task_runner
        
        # Create mock task
        mock_task = MagicMock(spec=Task)
        mock_task.name = "test-task"
        
        # Create mock agents
        mock_agent = MagicMock(spec=Agent)
        
        # Create mock project with agents attribute explicitly set
        mock_project = MagicMock(spec=Project)
        mock_project.name = "test-project"
        mock_project.tasks = {"test-task": mock_task}
        mock_project.agents = {"test-agent": mock_agent}
        mock_project.get_execution_order.return_value = ["test-task"]
        
        # Create the runner
        runner = ProjectRunner(mock_project)
        
        # Run the project
        result = runner.run({"input": 10})
        
        # Verify TaskRunner was created and used
        mock_task_runner_class.assert_called_once_with(mock_task, mock_project.agents)
        mock_task_runner.run.assert_called_once_with({"input": 10})
        assert result == {"input": 10, "result": 42} 