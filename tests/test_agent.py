"""Tests for the Agent class."""

import pytest
from unittest.mock import MagicMock, patch

from mimi.core.agent import Agent


class TestAgent:
    """Tests for the Agent class."""

    def test_agent_creation(self) -> None:
        """Test creating an Agent instance."""
        agent = Agent(
            name="test-agent",
            role="test-role",
            description="A test agent",
            model_name="test-model",
            system_prompt="You are a helpful test agent that assists with testing."
        )
        
        assert agent.name == "test-agent"
        assert agent.role == "test-role"
        assert agent.description == "A test agent"
        assert agent.model_name == "test-model"
        assert agent.model_provider == "ollama"
        assert agent.system_prompt == "You are a helpful test agent that assists with testing."

    def test_agent_initialization(self) -> None:
        """Test initializing an Agent with a mock model client."""
        # Create a mock Ollama client
        mock_client = MagicMock()
        
        # Patch the get_ollama_client function to return our mock
        with patch("mimi.core.agents.base_agent.get_ollama_client", return_value=mock_client):
            # Create the agent
            agent = Agent(
                name="test-agent",
                role="test-role",
                description="A test agent",
                model_name="test-model",
                system_prompt="You are a helpful test agent that assists with testing."
            )
            
            # Initialize the agent
            agent.initialize()
            
            # Check that the model client was initialized
            assert agent._model_client == mock_client

    def test_agent_from_config(self) -> None:
        """Test creating an Agent from a configuration dictionary."""
        config = {
            "name": "test-agent",
            "role": "test-role",
            "description": "A test agent",
            "model_name": "test-model",
            "model_config": {"temperature": 0.5},
            "system_prompt": "You are a helpful test agent that assists with testing."
        }
        
        agent = Agent.from_config(config)
        
        assert agent.name == "test-agent"
        assert agent.role == "test-role"
        assert agent.description == "A test agent"
        assert agent.model_name == "test-model"
        assert agent.model_settings == {"temperature": 0.5}
        assert agent.system_prompt == "You are a helpful test agent that assists with testing."

