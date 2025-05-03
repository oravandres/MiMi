"""Tests for the verification agents (AnalystAgent and FeedbackProcessorAgent)."""

import pytest
from unittest.mock import MagicMock, patch

from mimi.core.agent import AnalystAgent, FeedbackProcessorAgent


class TestAnalystAgent:
    """Tests for the AnalystAgent class."""

    def test_analyst_agent_creation(self) -> None:
        """Test creating an AnalystAgent instance."""
        agent = AnalystAgent(
            name="analyst-agent",
            role="addition-verifier",
            description="Agent that verifies additions",
            model_name="test-model",
        )
        
        assert agent.name == "analyst-agent"
        assert agent.role == "addition-verifier"
        assert agent.description == "Agent that verifies additions"
        assert agent.model_name == "test-model"

    def test_analyst_execute_correct_addition(self) -> None:
        """Test AnalystAgent.execute() with correct addition."""
        agent = AnalystAgent(
            name="analyst-agent",
            role="addition-verifier",
            description="Agent that verifies additions",
            model_name="test-model",
        )
        
        # Input with a correct addition (100 + 5 = 105)
        task_input = {
            "input": 100.0,
            "result5": 105.0,
        }
        
        result = agent.execute(task_input)
        
        # Check that the result has the expected structure and data
        assert isinstance(result, dict)
        assert result["status"] == "success"
        assert "verification_results" in result
        assert len(result["verification_results"]) == 1
        assert result["verification_results"][0]["operation"] == "100.0 + 5"
        assert result["verification_results"][0]["expected"] == 105.0
        assert result["verification_results"][0]["actual"] == 105.0
        assert result["verification_results"][0]["is_correct"] is True

    def test_analyst_execute_incorrect_addition(self) -> None:
        """Test AnalystAgent.execute() with incorrect addition."""
        agent = AnalystAgent(
            name="analyst-agent",
            role="addition-verifier",
            description="Agent that verifies additions",
            model_name="test-model",
        )
        
        # Input with an incorrect addition (100 + 3 = 104 instead of 103)
        task_input = {
            "input": 100.0,
            "result3": 104.0,
        }
        
        result = agent.execute(task_input)
        
        # Check that the result has the expected structure and data
        assert isinstance(result, dict)
        assert result["status"] == "error"
        assert "verification_results" in result
        assert len(result["verification_results"]) == 1
        assert result["verification_results"][0]["operation"] == "100.0 + 3"
        assert result["verification_results"][0]["expected"] == 103.0
        assert result["verification_results"][0]["actual"] == 104.0
        assert result["verification_results"][0]["is_correct"] is False

    def test_analyst_execute_no_result_keys(self) -> None:
        """Test AnalystAgent.execute() with no result keys."""
        agent = AnalystAgent(
            name="analyst-agent",
            role="addition-verifier",
            description="Agent that verifies additions",
            model_name="test-model",
        )
        
        # Input with no result keys
        task_input = {
            "input": 100.0,
            "other_key": "value",
        }
        
        result = agent.execute(task_input)
        
        # Check that the result has the expected structure and data
        assert isinstance(result, dict)
        assert result["status"] == "warning"
        assert "message" in result
        assert "No result keys found" in result["message"]


class TestFeedbackProcessorAgent:
    """Tests for the FeedbackProcessorAgent class."""

    def test_feedback_processor_agent_creation(self) -> None:
        """Test creating a FeedbackProcessorAgent instance."""
        agent = FeedbackProcessorAgent(
            name="feedback-agent",
            role="feedback-provider",
            description="Agent that provides feedback",
            model_name="test-model",
        )
        
        assert agent.name == "feedback-agent"
        assert agent.role == "feedback-provider"
        assert agent.description == "Agent that provides feedback"
        assert agent.model_name == "test-model"

    def test_feedback_processor_execute_success(self) -> None:
        """Test FeedbackProcessorAgent.execute() with successful verification."""
        agent = FeedbackProcessorAgent(
            name="feedback-agent",
            role="feedback-provider",
            description="Agent that provides feedback",
            model_name="test-model",
        )
        
        # Input with a successful verification
        task_input = {
            "input": 100.0,
            "result1": 101.0,
            "verified1": {
                "status": "success",
                "message": "Calculation verified successfully", 
                "verification_results": [{
                    "operation": "100.0 + 1", 
                    "expected": 101.0, 
                    "actual": 101.0, 
                    "is_correct": True
                }],
                "data": {
                    "input": 100.0,
                    "result1": 101.0
                }
            }
        }
        
        result = agent.execute(task_input)
        
        # Check that the result has the expected structure and data
        assert isinstance(result, dict)
        assert result["status"] == "success"
        assert "continue" in result
        assert result["continue"] is True

    def test_feedback_processor_execute_error(self) -> None:
        """Test FeedbackProcessorAgent.execute() with verification error."""
        agent = FeedbackProcessorAgent(
            name="feedback-agent",
            role="feedback-provider",
            description="Agent that provides feedback",
            model_name="test-model",
        )
        
        # Input with a verification error
        task_input = {
            "input": 100.0,
            "result3": 104.0,
            "verified3": {
                "status": "error",
                "message": "Calculation error: expected 100.0 + 3 = 103.0, but got 104.0",
                "verification_results": [{
                    "operation": "100.0 + 3",
                    "expected": 103.0,
                    "actual": 104.0,
                    "is_correct": False
                }],
                "data": {
                    "input": 100.0,
                    "result3": 104.0
                }
            }
        }
        
        result = agent.execute(task_input)
        
        # Check that the result has the expected structure and data
        assert isinstance(result, dict)
        assert result["status"] == "error"
        assert "continue" in result
        assert result["continue"] is False

    def test_feedback_processor_execute_no_verification_keys(self) -> None:
        """Test FeedbackProcessorAgent.execute() with no verification keys."""
        agent = FeedbackProcessorAgent(
            name="feedback-agent",
            role="feedback-provider",
            description="Agent that provides feedback",
            model_name="test-model",
        )
        
        # Input with no verification keys
        task_input = {
            "input": 100.0,
            "result1": 101.0,
        }
        
        result = agent.execute(task_input)
        
        # Check that the result has the expected structure and data
        assert isinstance(result, dict)
        assert result["status"] == "warning"
        assert "continue" in result
        assert result["continue"] is True 