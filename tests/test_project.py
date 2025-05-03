"""Tests for the Project class."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from mimi.core.agent import Agent
from mimi.core.project import Project
from mimi.core.task import Task


class TestProject:
    """Tests for the Project class."""

    def test_project_creation(self) -> None:
        """Test creating a Project instance."""
        project = Project(
            name="test-project",
            description="A test project",
        )
        
        assert project.name == "test-project"
        assert project.description == "A test project"
        assert project.agents == {}
        assert project.tasks == {}

    def test_project_with_agents_and_tasks(self) -> None:
        """Test Project with agents and tasks."""
        # Create mock agents
        agent1 = MagicMock(spec=Agent)
        agent1.name = "agent1"
        
        agent2 = MagicMock(spec=Agent)
        agent2.name = "agent2"
        
        # Create mock tasks
        task1 = MagicMock(spec=Task)
        task1.name = "task1"
        task1.depends_on = []
        
        task2 = MagicMock(spec=Task)
        task2.name = "task2"
        task2.depends_on = ["task1"]
        
        # Create the project
        project = Project(
            name="test-project",
            description="A test project",
            agents={"agent1": agent1, "agent2": agent2},
            tasks={"task1": task1, "task2": task2},
        )
        
        assert len(project.agents) == 2
        assert project.agents["agent1"] == agent1
        assert project.agents["agent2"] == agent2
        
        assert len(project.tasks) == 2
        assert project.tasks["task1"] == task1
        assert project.tasks["task2"] == task2

    def test_project_initialize(self) -> None:
        """Test project initialization."""
        # Create mock agents
        agent1 = MagicMock(spec=Agent)
        agent1.name = "agent1"
        
        agent2 = MagicMock(spec=Agent)
        agent2.name = "agent2"
        
        # Create the project
        project = Project(
            name="test-project",
            description="A test project",
            agents={"agent1": agent1, "agent2": agent2},
        )
        
        # Initialize the project
        project.initialize()
        
        # Verify the agents were initialized
        agent1.initialize.assert_called_once()
        agent2.initialize.assert_called_once()

    def test_validate_task_dependencies_valid(self) -> None:
        """Test validating task dependencies with valid dependencies."""
        # Create mock tasks
        task1 = MagicMock(spec=Task)
        task1.name = "task1"
        task1.depends_on = []
        
        task2 = MagicMock(spec=Task)
        task2.name = "task2"
        task2.depends_on = ["task1"]
        
        task3 = MagicMock(spec=Task)
        task3.name = "task3"
        task3.depends_on = ["task1", "task2"]
        
        # Create the project
        project = Project(
            name="test-project",
            description="A test project",
            tasks={"task1": task1, "task2": task2, "task3": task3},
        )
        
        # Validate dependencies - should not raise any errors
        project.validate_task_dependencies()

    def test_validate_task_dependencies_missing(self) -> None:
        """Test validating task dependencies with missing dependencies."""
        # Create mock tasks
        task1 = MagicMock(spec=Task)
        task1.name = "task1"
        task1.depends_on = []
        
        task2 = MagicMock(spec=Task)
        task2.name = "task2"
        task2.depends_on = ["missing-task"]
        
        # Create the project
        project = Project(
            name="test-project",
            description="A test project",
            tasks={"task1": task1, "task2": task2},
        )
        
        # Validate dependencies - should raise ValueError
        with pytest.raises(ValueError):
            project.validate_task_dependencies()

    def test_validate_task_dependencies_circular(self) -> None:
        """Test validating task dependencies with circular dependencies."""
        # Create mock tasks with circular dependencies
        task1 = MagicMock(spec=Task)
        task1.name = "task1"
        task1.depends_on = ["task3"]
        
        task2 = MagicMock(spec=Task)
        task2.name = "task2"
        task2.depends_on = ["task1"]
        
        task3 = MagicMock(spec=Task)
        task3.name = "task3"
        task3.depends_on = ["task2"]
        
        # Create the project
        project = Project(
            name="test-project",
            description="A test project",
            tasks={"task1": task1, "task2": task2, "task3": task3},
        )
        
        # Validate dependencies - should raise ValueError
        with pytest.raises(ValueError):
            project.validate_task_dependencies()

    def test_get_execution_order(self) -> None:
        """Test getting the execution order for tasks."""
        # Create real Task instances (not mocks) for proper dependency checking
        task1 = Task(
            name="task1",
            description="Task 1",
            agent="agent1",
            depends_on=[],
        )
        
        task2 = Task(
            name="task2",
            description="Task 2",
            agent="agent2",
            depends_on=["task1"],
        )
        
        task3 = Task(
            name="task3",
            description="Task 3",
            agent="agent3",
            depends_on=["task2"],
        )
        
        # Create the project
        project = Project(
            name="test-project",
            description="A test project",
            tasks={"task1": task1, "task2": task2, "task3": task3},
        )
        
        # Get execution order
        order = project.get_execution_order()
        
        # Verify the order is correct
        assert order == ["task1", "task2", "task3"]

    @patch("mimi.core.project.load_project_config")
    @patch("mimi.core.project.Agent.from_config")
    @patch("mimi.core.project.NumberAdderAgent.from_config")
    @patch("mimi.core.project.AnalystAgent.from_config")
    @patch("mimi.core.project.ResearchAnalystAgent.from_config")
    @patch("mimi.core.project.ArchitectAgent.from_config")
    @patch("mimi.core.project.SoftwareEngineerAgent.from_config")
    @patch("mimi.core.project.QAEngineerAgent.from_config")
    @patch("mimi.core.project.ReviewerAgent.from_config")
    @patch("mimi.core.project.Task.from_config")
    def test_from_config(
        self,
        mock_task_from_config: MagicMock,
        mock_reviewer_from_config: MagicMock,
        mock_qa_from_config: MagicMock,
        mock_engineer_from_config: MagicMock,
        mock_architect_from_config: MagicMock,
        mock_analyst_from_config: MagicMock,
        mock_number_adder_from_config: MagicMock,
        mock_analyst_agent_from_config: MagicMock,
        mock_agent_from_config: MagicMock,
        mock_load_config: MagicMock,
    ) -> None:
        """Test creating a Project from a configuration directory."""
        # Mock the config loading
        mock_load_config.return_value = {
            "agents": {
                "project_name": "Test Project",
                "project_description": "A test project",
                "agents": [
                    {"name": "agent1", "type": "default"},
                    {"name": "agent2", "type": "number_adder"},
                    {"name": "agent3", "type": "analyst"},
                    {"name": "agent4", "type": "research_analyst"},
                    {"name": "agent5", "type": "architect"},
                    {"name": "agent6", "type": "software_engineer"},
                    {"name": "agent7", "type": "qa_engineer"},
                    {"name": "agent8", "type": "reviewer"},
                ],
            },
            "tasks": {
                "tasks": [
                    {"name": "task1"},
                    {"name": "task2"},
                ],
            },
        }
        
        # Mock the agent creation
        mock_agent1 = MagicMock()
        mock_agent2 = MagicMock()
        mock_agent3 = MagicMock()
        mock_agent4 = MagicMock()
        mock_agent5 = MagicMock()
        mock_agent6 = MagicMock()
        mock_agent7 = MagicMock()
        mock_agent8 = MagicMock()
        
        mock_agent_from_config.return_value = mock_agent1
        mock_number_adder_from_config.return_value = mock_agent2
        mock_analyst_agent_from_config.return_value = mock_agent3
        mock_analyst_from_config.return_value = mock_agent4
        mock_architect_from_config.return_value = mock_agent5
        mock_engineer_from_config.return_value = mock_agent6
        mock_qa_from_config.return_value = mock_agent7
        mock_reviewer_from_config.return_value = mock_agent8
        
        # Mock the task creation
        mock_task1 = MagicMock()
        mock_task2 = MagicMock()
        mock_task_from_config.side_effect = [mock_task1, mock_task2]
        
        # Call the method
        project = Project.from_config("fake_dir")
        
        # Verify the project was created with the right name and description
        assert project.name == "Test Project"
        assert project.description == "A test project"
        
        # Verify the agents were created correctly
        assert len(project.agents) == 8
        assert project.agents["agent1"] == mock_agent1
        assert project.agents["agent2"] == mock_agent2
        assert project.agents["agent3"] == mock_agent3
        assert project.agents["agent4"] == mock_agent4
        assert project.agents["agent5"] == mock_agent5
        assert project.agents["agent6"] == mock_agent6
        assert project.agents["agent7"] == mock_agent7
        assert project.agents["agent8"] == mock_agent8
        
        # Verify the tasks were created correctly
        assert len(project.tasks) == 2
        assert project.tasks["task1"] == mock_task1
        assert project.tasks["task2"] == mock_task2 