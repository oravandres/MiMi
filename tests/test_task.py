"""Tests for the Task class."""

import pytest
from unittest.mock import MagicMock

from mimi.core.task import Task


class TestTask:
    """Tests for the Task class."""

    def test_task_creation(self) -> None:
        """Test creating a Task instance."""
        task = Task(
            name="test-task",
            description="A test task",
            agent="test-agent",
        )
        
        assert task.name == "test-task"
        assert task.description == "A test task"
        assert task.agent == "test-agent"
        assert task.input_key is None
        assert task.output_key is None
        assert task.depends_on == []

    def test_task_with_keys(self) -> None:
        """Test Task with input and output keys."""
        task = Task(
            name="test-task",
            description="A test task",
            agent="test-agent",
            input_key="test_input",
            output_key="test_output",
        )
        
        assert task.input_key == "test_input"
        assert task.output_key == "test_output"

    def test_task_with_dependencies(self) -> None:
        """Test Task with dependencies."""
        task = Task(
            name="test-task",
            description="A test task",
            agent="test-agent",
            depends_on=["task1", "task2"],
        )
        
        assert task.depends_on == ["task1", "task2"]

    def test_task_execute_agent_not_found(self) -> None:
        """Test task execution when agent is not found."""
        task = Task(
            name="test-task",
            description="A test task",
            agent="missing-agent",
        )
        
        with pytest.raises(ValueError):
            task.execute({}, {"input": 42})

    def test_task_execute_basic(self) -> None:
        """Test basic task execution."""
        task = Task(
            name="test-task",
            description="A test task",
            agent="test-agent",
        )
        
        # Create a mock agent
        mock_agent = MagicMock()
        mock_agent.execute.return_value = 42
        
        # Execute the task
        result = task.execute({"test-agent": mock_agent}, {"input": 10})
        
        # Verify the agent was called
        mock_agent.execute.assert_called_once_with({"input": 10})
        assert result == 42

    def test_task_execute_with_input_key(self) -> None:
        """Test task execution with input_key."""
        task = Task(
            name="test-task",
            description="A test task",
            agent="test-agent",
            input_key="value",
        )
        
        # Create a mock agent
        mock_agent = MagicMock()
        mock_agent.execute.return_value = 42
        
        # Execute the task
        result = task.execute(
            {"test-agent": mock_agent}, 
            {"value": 10, "other": "data"}
        )
        
        # Verify the agent was called with the right input
        mock_agent.execute.assert_called_once_with(10)
        assert result == 42

    def test_task_execute_with_output_key(self) -> None:
        """Test task execution with output_key."""
        task = Task(
            name="test-task",
            description="A test task",
            agent="test-agent",
            output_key="result",
        )
        
        # Create a mock agent
        mock_agent = MagicMock()
        mock_agent.execute.return_value = 42
        
        # Execute the task
        result = task.execute(
            {"test-agent": mock_agent}, 
            {"input": 10}
        )
        
        # Verify the result is stored under the output key
        assert isinstance(result, dict)
        assert result["result"] == 42
        assert result["input"] == 10  # Original input preserved

    def test_task_execute_with_both_keys(self) -> None:
        """Test task execution with both input_key and output_key."""
        task = Task(
            name="test-task",
            description="A test task",
            agent="test-agent",
            input_key="value",
            output_key="result",
        )
        
        # Create a mock agent
        mock_agent = MagicMock()
        mock_agent.execute.return_value = 42
        
        # Execute the task
        result = task.execute(
            {"test-agent": mock_agent}, 
            {"value": 10, "other": "data"}
        )
        
        # Verify the agent was called with the right input
        mock_agent.execute.assert_called_once_with(10)
        
        # Verify the result is stored under the output key
        assert isinstance(result, dict)
        assert result["result"] == 42
        assert result["value"] == 10  # Original input preserved
        assert result["other"] == "data"  # Other data preserved

    def test_task_from_config(self) -> None:
        """Test creating a task from a configuration dictionary."""
        config = {
            "name": "test-task",
            "description": "A test task",
            "agent": "test-agent",
            "input_key": "input",
            "output_key": "output",
            "depends_on": ["task1"],
        }
        
        task = Task.from_config(config)
        
        assert task.name == "test-task"
        assert task.description == "A test task"
        assert task.agent == "test-agent"
        assert task.input_key == "input"
        assert task.output_key == "output"
        assert task.depends_on == ["task1"] 