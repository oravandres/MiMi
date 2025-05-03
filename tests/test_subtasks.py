"""Tests for the subtask functionality."""

import pytest
from unittest.mock import MagicMock, patch
import concurrent.futures

from mimi.core.agent import Agent, TaskSplitterAgent
from mimi.core.task import Task, SubTask
from mimi.core.runner import TaskRunner


class TestSubTasks:
    """Tests for the SubTask class."""

    def test_subtask_creation(self) -> None:
        """Test creating a SubTask."""
        subtask = SubTask(
            parent_task_name="test_task",
            name="subtask_1",
            description="Test subtask",
            input_data={"test": "data"},
            depends_on=[]
        )
        
        assert subtask.parent_task_name == "test_task"
        assert subtask.name == "subtask_1"
        assert subtask.description == "Test subtask"
        assert subtask.input_data == {"test": "data"}
        assert subtask.depends_on == []
        assert subtask.id is not None  # UUID should be generated
        

class TestTaskSplitterAgent:
    """Tests for the TaskSplitterAgent class."""
    
    def test_agent_creation(self) -> None:
        """Test creating a TaskSplitterAgent."""
        agent = TaskSplitterAgent(
            name="test-splitter",
            role="task-splitter",
            description="An agent that splits tasks into subtasks",
            model_name="test-model",
            system_prompt="You are a specialized agent that divides complex tasks into smaller units for parallel processing.",
            num_subtasks=3
        )
        
        assert agent.name == "test-splitter"
        assert agent.role == "task-splitter"
        assert agent.supports_subtasks is True
        assert agent.num_subtasks == 3
    
    def test_create_subtasks_with_list(self) -> None:
        """Test creating subtasks from a list input."""
        agent = TaskSplitterAgent(
            name="test-splitter",
            role="task-splitter",
            description="An agent that splits tasks into subtasks",
            model_name="test-model",
            system_prompt="You are a specialized agent that divides complex tasks into smaller units for parallel processing.",
            num_subtasks=2
        )
        
        input_data = [1, 2, 3, 4]
        subtasks = agent.create_subtasks(input_data)
        
        assert len(subtasks) == 2
        assert subtasks[0].name == "chunk_1"
        assert subtasks[1].name == "chunk_2"
        assert subtasks[0].input_data == [1, 2]  # First half
        assert subtasks[1].input_data == [3, 4]  # Second half
    
    def test_create_subtasks_with_dict(self) -> None:
        """Test creating subtasks from a dictionary input."""
        agent = TaskSplitterAgent(
            name="test-splitter",
            role="task-splitter",
            description="An agent that splits tasks into subtasks",
            model_name="test-model",
            system_prompt="You are a specialized agent that divides complex tasks into smaller units for parallel processing.",
            num_subtasks=2
        )
        
        input_data = {"a": 1, "b": 2, "c": 3, "d": 4}
        subtasks = agent.create_subtasks(input_data)
        
        assert len(subtasks) == 2
        assert subtasks[0].name.startswith("dict_chunk_")
        assert subtasks[1].name.startswith("dict_chunk_")
        
        # Each subtask should have part of the dictionary
        assert len(subtasks[0].input_data) == 2
        assert len(subtasks[1].input_data) == 2
        
        # Combined, they should have all keys
        combined_keys = set(subtasks[0].input_data.keys()) | set(subtasks[1].input_data.keys())
        assert combined_keys == {"a", "b", "c", "d"}
    
    def test_execute_subtask(self) -> None:
        """Test executing a subtask."""
        agent = TaskSplitterAgent(
            name="test-splitter",
            role="task-splitter",
            description="An agent that splits tasks into subtasks",
            model_name="test-model",
            system_prompt="You are a specialized agent that divides complex tasks into smaller units for parallel processing.",
        )
        
        # Mock the model client initialization
        agent._model_client = MagicMock()
        
        # Create a subtask
        subtask = SubTask(
            parent_task_name="test_task",
            name="chunk_1",
            description="Test subtask",
            input_data=[1, 2, 3],
            depends_on=[]
        )
        
        # Execute the subtask
        result = agent.execute_subtask(subtask)
        
        # For list chunks, the agent should add 1 to each number
        assert result == [2, 3, 4]
    
    def test_combine_subtask_results(self) -> None:
        """Test combining subtask results."""
        agent = TaskSplitterAgent(
            name="test-splitter",
            role="task-splitter",
            description="An agent that splits tasks into subtasks",
            model_name="test-model",
            system_prompt="You are a specialized agent that divides complex tasks into smaller units for parallel processing.",
        )
        
        # Create subtasks with results
        subtask1 = SubTask(
            parent_task_name="test_task",
            name="chunk_1",
            description="Test subtask 1",
            input_data=[1, 2],
            depends_on=[]
        )
        subtask1.result = [2, 3]  # Result after adding 1
        
        subtask2 = SubTask(
            parent_task_name="test_task",
            name="chunk_2",
            description="Test subtask 2",
            input_data=[3, 4],
            depends_on=[]
        )
        subtask2.result = [4, 5]  # Result after adding 1
        
        # Combine results
        original_input = [1, 2, 3, 4]
        combined_result = agent.combine_subtask_results([subtask1, subtask2], original_input)
        
        # For list results, should be a combined list
        assert combined_result == [2, 3, 4, 5]


class TestTaskWithSubtasks:
    """Tests for tasks that use subtasks."""

    def test_task_with_subtasks(self) -> None:
        """Test a task that creates and executes subtasks."""
        # Create a mock agent that supports subtasks
        mock_agent = MagicMock(spec=TaskSplitterAgent)
        mock_agent.name = "test-splitter"
        mock_agent.supports_subtasks = True
        
        # Create a task
        task = Task(
            name="test_task",
            description="Test task",
            agent="test-splitter",
            parallel_subtasks=True
        )
        
        # Setup mock agent's create_subtasks method
        subtask1 = SubTask(
            parent_task_name="test_task",
            name="subtask_1",
            description="Test subtask 1",
            input_data={"part": 1},
            depends_on=[]
        )
        
        subtask2 = SubTask(
            parent_task_name="test_task",
            name="subtask_2",
            description="Test subtask 2",
            input_data={"part": 2},
            depends_on=[]
        )
        
        mock_agent.create_subtasks.return_value = [subtask1, subtask2]
        
        # Mock the agent's execute_subtask and combine_subtask_results methods
        def execute_subtask(subtask):
            if subtask.name == "subtask_1":
                return {"part": 1, "processed": True}
            else:
                return {"part": 2, "processed": True}
                
        mock_agent.execute_subtask.side_effect = execute_subtask
        mock_agent.combine_subtask_results.return_value = {"combined": True, "parts": [1, 2]}
        
        # Execute the task
        agent_lookup = {"test-splitter": mock_agent}
        
        # Create the task runner
        runner = TaskRunner(task, agent_lookup)
        
        # Mock the _execute_subtasks method to avoid parallel execution in tests
        with patch.object(TaskRunner, '_execute_subtasks') as mock_execute_subtasks:
            mock_execute_subtasks.return_value = {"combined": True, "parts": [1, 2]}
            
            # Run the task
            result = runner.run({"input": "test"})
            
            # Verify create_subtasks was called
            mock_agent.create_subtasks.assert_called_once()
            
            # Verify _execute_subtasks was called
            mock_execute_subtasks.assert_called_once()
            
            # Check the result
            assert result == {"combined": True, "parts": [1, 2]}


class TestParallelSubtaskExecution:
    """Tests for parallel execution of subtasks."""

    def test_execute_subtasks_parallel(self) -> None:
        """Test executing subtasks in parallel."""
        # Create a mock agent
        mock_agent = MagicMock(spec=TaskSplitterAgent)
        mock_agent.name = "test-splitter"
        
        # Create a task
        task = Task(
            name="test_task",
            description="Test task",
            agent="test-splitter",
            parallel_subtasks=True
        )
        
        # Create subtasks
        subtask1 = SubTask(
            parent_task_name="test_task",
            name="subtask_1",
            description="Test subtask 1",
            input_data={"part": 1},
            depends_on=[]
        )
        
        subtask2 = SubTask(
            parent_task_name="test_task",
            name="subtask_2",
            description="Test subtask 2",
            input_data={"part": 2},
            depends_on=[]
        )
        
        # Add the subtasks to the task
        task.subtasks = {subtask1.id: subtask1, subtask2.id: subtask2}
        
        # Mock the agent's execute_subtask method
        def execute_subtask(subtask):
            # Attach a result to the subtask
            if subtask.name == "subtask_1":
                return {"part": 1, "processed": True}
            else:
                return {"part": 2, "processed": True}
                
        mock_agent.execute_subtask.side_effect = execute_subtask
        
        # Mock the agent's combine_subtask_results method
        mock_agent.combine_subtask_results.return_value = {"combined": True, "parts": [1, 2]}
        
        # Create the task runner
        agent_lookup = {"test-splitter": mock_agent}
        runner = TaskRunner(task, agent_lookup)
        
        # Execute the subtasks (no need to mock ThreadPoolExecutor for this test)
        parent_result = {"original": "input"}
        result = runner._execute_subtasks(parent_result)
        
        # Verify execute_subtask was called for both subtasks
        assert mock_agent.execute_subtask.call_count == 2
        
        # Verify combine_subtask_results was called
        mock_agent.combine_subtask_results.assert_called_once()
        
        # Check the result
        assert result == {"combined": True, "parts": [1, 2]}
        
    def test_execute_subtasks_with_dependencies(self) -> None:
        """Test executing subtasks with dependencies."""
        # Create a mock agent
        mock_agent = MagicMock(spec=TaskSplitterAgent)
        mock_agent.name = "test-splitter"
        
        # Create a task
        task = Task(
            name="test_task",
            description="Test task",
            agent="test-splitter",
            parallel_subtasks=True
        )
        
        # Create subtasks with dependencies
        subtask1 = SubTask(
            parent_task_name="test_task",
            name="subtask_1",
            description="Test subtask 1",
            input_data={"part": 1},
            depends_on=[]  # No dependencies
        )
        
        subtask2 = SubTask(
            parent_task_name="test_task",
            name="subtask_2",
            description="Test subtask 2",
            input_data={"part": 2},
            depends_on=[subtask1.id]  # Depends on subtask1
        )
        
        subtask3 = SubTask(
            parent_task_name="test_task",
            name="subtask_3",
            description="Test subtask 3",
            input_data={"part": 3},
            depends_on=[subtask2.id]  # Depends on subtask2
        )
        
        # Add the subtasks to the task
        task.subtasks = {
            subtask1.id: subtask1, 
            subtask2.id: subtask2,
            subtask3.id: subtask3
        }
        
        # Mock the agent's execute_subtask method
        def execute_subtask(subtask):
            # Different result based on subtask
            if subtask.name == "subtask_1":
                return {"part": 1, "processed": True}
            elif subtask.name == "subtask_2":
                return {"part": 2, "processed": True}
            else:
                return {"part": 3, "processed": True}
                
        mock_agent.execute_subtask.side_effect = execute_subtask
        
        # Mock the agent's combine_subtask_results method
        mock_agent.combine_subtask_results.return_value = {"combined": True, "parts": [1, 2, 3]}
        
        # Create the task runner
        agent_lookup = {"test-splitter": mock_agent}
        runner = TaskRunner(task, agent_lookup)
        
        # Execute the subtasks
        parent_result = {"original": "input"}
        result = runner._execute_subtasks(parent_result)
        
        # Verify execute_subtask was called for all subtasks
        assert mock_agent.execute_subtask.call_count == 3
        
        # Verify combine_subtask_results was called
        mock_agent.combine_subtask_results.assert_called_once()
        
        # Check the result
        assert result == {"combined": True, "parts": [1, 2, 3]} 