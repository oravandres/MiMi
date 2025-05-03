"""Tests for the Agent class."""

import pytest
from unittest.mock import MagicMock, patch

from mimi.core.agent import Agent


class TestAgent:
    """Tests for the base Agent class."""

    def test_agent_creation(self) -> None:
        """Test creating an Agent instance."""
        agent = Agent(
            name="test-agent",
            role="test-role",
            description="Test agent for unit tests",
            model_name="test-model",
        )
        
        assert agent.name == "test-agent"
        assert agent.role == "test-role"
        assert agent.description == "Test agent for unit tests"
        assert agent.model_name == "test-model"
        assert agent.model_provider == "ollama"  # Default value

    @patch("mimi.core.agent.get_ollama_client")
    def test_agent_initialization(self, mock_get_ollama: MagicMock) -> None:
        """Test agent initialization."""
        # Mock the Ollama client
        mock_client = MagicMock()
        mock_get_ollama.return_value = mock_client
        
        # Create and initialize the agent
        agent = Agent(
            name="test-agent",
            role="test-role",
            description="Test agent for unit tests",
            model_name="test-model",
        )
        agent.initialize()
        
        # Verify the client was created
        mock_get_ollama.assert_called_once_with(
            model_name="test-model",
            base_url="http://localhost:11434",
            temperature=0.7,
            suppress_log=True,
            stream=False
        )
        assert agent._model_client == mock_client

    @patch("mimi.core.agent.get_ollama_client")
    def test_agent_from_config(self, mock_get_ollama: MagicMock) -> None:
        """Test creating an agent from a configuration dictionary."""
        # Mock the Ollama client
        mock_client = MagicMock()
        mock_get_ollama.return_value = mock_client
        
        # Create agent from config
        config = {
            "name": "test-agent",
            "role": "test-role",
            "description": "Test agent for unit tests",
            "model_name": "test-model",
            "model_provider": "ollama",
            "model_settings": {"temperature": 0.5},
        }
        
        agent = Agent.from_config(config)
        
        # Verify the agent was created correctly
        assert agent.name == "test-agent"
        assert agent.role == "test-role"
        assert agent.description == "Test agent for unit tests"
        assert agent.model_name == "test-model"
        assert agent.model_provider == "ollama"
        assert agent.model_settings == {"temperature": 0.5}
        
        # Initialize the agent to create the client
        agent.initialize()
        
        # Verify the client was created
        mock_get_ollama.assert_called_once_with(
            model_name="test-model",
            base_url="http://localhost:11434",
            temperature=0.5,
            suppress_log=True,
            stream=False
        )

