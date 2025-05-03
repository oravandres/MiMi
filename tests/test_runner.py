"""Tests for the ProjectRunner and TaskRunner classes."""

import pytest
from unittest.mock import MagicMock, patch
import concurrent.futures

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
        mock_task.agent = "test-agent"
        mock_task.output_key = "result"  # Need to set this property
        mock_task.execute.return_value = {"result": 42}
        
        mock_agent = MagicMock(spec=Agent)
        agent_lookup = {"test-agent": mock_agent}
        
        # Create the runner
        runner = TaskRunner(mock_task, agent_lookup)
        
        # Run the task
        result = runner.run({"input": 10})
        
        # Verify the task was executed
        mock_task.execute.assert_called_once_with(agent_lookup, {"input": 10})
        assert result == {"result": 42}


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
        assert runner.results == {}

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
        mock_task1.agent = "agent1"
        mock_task1.depends_on = []
        mock_task1.input_key = ""
        mock_task1.output_key = "result1"
        mock_task1.execute.return_value = {"input": 10, "result1": 11}
        
        mock_task2 = MagicMock(spec=Task)
        mock_task2.name = "task2"
        mock_task2.agent = "agent2"
        mock_task2.depends_on = ["task1"]
        mock_task2.input_key = "result1"
        mock_task2.output_key = "result2"
        mock_task2.execute.return_value = {"result1": 11, "result2": 22}
        
        # Create mock project
        mock_project = MagicMock(spec=Project)
        mock_project.name = "test-project"
        mock_project.agents = {"agent1": mock_agent1, "agent2": mock_agent2}
        mock_project.tasks = {"task1": mock_task1, "task2": mock_task2}
        mock_project.get_execution_order.return_value = ["task1", "task2"]
        
        # Create the runner
        runner = ProjectRunner(mock_project)
        
        # Run the project
        input_data = {"input": 10}
        result = runner.run(input_data)
        
        # Verify the tasks were executed and have expected results
        # The result will have task names as keys and nested dictionaries as values
        assert "task1" in result
        assert "task2" in result
        assert "result1" in result["task1"]
        assert "result2" in result["task2"]
        assert result["task1"]["result1"] == 11
        assert result["task2"]["result2"] == 22
        
        # Check the results dictionary has durations
        assert "task1" in runner.results
        assert "task2" in runner.results
        assert "duration" in runner.results["task1"]
        assert "duration" in runner.results["task2"]

    def test_project_runner_uses_task_runner(self) -> None:
        """Test that ProjectRunner uses TaskRunner."""
        # Create mock task and agent
        mock_task = MagicMock(spec=Task)
        mock_task.name = "test-task"
        mock_task.agent = "test-agent"
        mock_task.depends_on = []
        mock_task.input_key = ""
        mock_task.output_key = "result"
        
        mock_agent = MagicMock(spec=Agent)
        mock_agent.name = "test-agent"
        
        # Create mock project
        mock_project = MagicMock(spec=Project)
        mock_project.name = "test-project"
        mock_project.agents = {"test-agent": mock_agent}
        mock_project.tasks = {"test-task": mock_task}
        mock_project.get_execution_order.return_value = ["test-task"]
        
        # Mock TaskRunner
        with patch("mimi.core.runner.TaskRunner") as mock_task_runner_class:
            mock_task_runner = MagicMock()
            mock_task_runner.run.return_value = {"result": 42}
            mock_task_runner_class.return_value = mock_task_runner
            
            # Create and run the project runner
            runner = ProjectRunner(mock_project)
            result = runner.run({"input": 10})
            
            # Verify TaskRunner was used
            mock_task_runner_class.assert_called_once_with(mock_task, {"test-agent": mock_agent})
            
            # The project runner will wrap the input in a dict with the input key
            mock_task_runner.run.assert_called_once()
            call_args = mock_task_runner.run.call_args[0][0]
            assert "input" in call_args

    def test_parallel_execution(self) -> None:
        """Test parallel execution of tasks."""
        # Create mock tasks with parallel execution potential
        mock_task1 = MagicMock(spec=Task)
        mock_task1.name = "task1"
        mock_task1.agent = "agent1"
        mock_task1.depends_on = []
        mock_task1.input_key = ""
        mock_task1.output_key = "result1"
        mock_task1.execute.return_value = {"result1": 11}
        
        # These tasks both depend only on task1, so can run in parallel
        mock_task2 = MagicMock(spec=Task)
        mock_task2.name = "task2"
        mock_task2.agent = "agent2"
        mock_task2.depends_on = ["task1"]
        mock_task2.input_key = "result1"
        mock_task2.output_key = "result2"
        mock_task2.execute.return_value = {"result1": 11, "result2": 22}
        
        mock_task3 = MagicMock(spec=Task)
        mock_task3.name = "task3"
        mock_task3.agent = "agent3"
        mock_task3.depends_on = ["task1"]
        mock_task3.input_key = "result1"
        mock_task3.output_key = "result3"
        mock_task3.execute.return_value = {"result1": 11, "result3": 33}
        
        # This task depends on both task2 and task3, so must wait for them
        mock_task4 = MagicMock(spec=Task)
        mock_task4.name = "task4"
        mock_task4.agent = "agent4"
        mock_task4.depends_on = ["task2", "task3"]
        mock_task4.input_key = ""
        mock_task4.output_key = "result4"
        mock_task4.execute.return_value = {"result2": 22, "result3": 33, "result4": 44}
        
        # Create mock agents
        mock_agents = {}
        for i in range(1, 5):
            agent_name = f"agent{i}"
            mock_agent = MagicMock(spec=Agent)
            mock_agent.name = agent_name
            mock_agents[agent_name] = mock_agent
        
        # Create mock project
        mock_project = MagicMock(spec=Project)
        mock_project.name = "test-project"
        mock_project.agents = mock_agents
        mock_project.tasks = {
            "task1": mock_task1,
            "task2": mock_task2, 
            "task3": mock_task3,
            "task4": mock_task4
        }
        
        # Return all tasks (order doesn't matter since we'll group by dependencies)
        mock_project.get_execution_order.return_value = ["task1", "task2", "task3", "task4"]
        
        # Instead of trying to mock ThreadPoolExecutor directly, we'll patch
        # the runner's own _run_task method and check that it's called correctly
        with patch.object(ProjectRunner, '_run_task') as mock_run_task:
            # Set up return values for each task
            task1_result = {"data": {"result1": 11}, "duration": 1.0, "task": "task1", "output_key": "result1"}
            task2_result = {"data": {"result1": 11, "result2": 22}, "duration": 1.0, "task": "task2", "output_key": "result2"}
            task3_result = {"data": {"result1": 11, "result3": 33}, "duration": 1.0, "task": "task3", "output_key": "result3"}
            task4_result = {"data": {"result2": 22, "result3": 33, "result4": 44}, "duration": 1.0, "task": "task4", "output_key": "result4"}
            
            # Use side_effect to return different values based on the task name
            def side_effect(task_name, _):
                if task_name == "task1":
                    runner.results[task_name] = task1_result
                    return task1_result
                elif task_name == "task2":
                    runner.results[task_name] = task2_result
                    return task2_result
                elif task_name == "task3":
                    runner.results[task_name] = task3_result
                    return task3_result
                elif task_name == "task4":
                    runner.results[task_name] = task4_result
                    return task4_result
            
            mock_run_task.side_effect = side_effect
            
            # Create and run the project runner with parallel execution
            runner = ProjectRunner(mock_project, parallel=True, max_workers=2)
            result = runner.run({"input": 10})
            
            # Verify all tasks were executed
            assert mock_run_task.call_count == 4
            
            # Check which tasks were called
            task_names = [call[0][0] for call in mock_run_task.call_args_list]
            assert set(task_names) == {"task1", "task2", "task3", "task4"}
            
            # Verify task1 was called first (it has no dependencies)
            assert task_names[0] == "task1"
            
            # The result should contain task outputs
            assert "input" in result
            assert "task1" in result
            assert "task2" in result
            assert "task3" in result
            assert "task4" in result 