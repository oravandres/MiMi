"""Tests for the verification agents (AnalystAgent and FeedbackProcessorAgent)."""

import pytest
from unittest.mock import MagicMock, patch

from mimi.core.agent import AnalystAgent, FeedbackProcessorAgent


class TestAnalystAgent:
    """Tests for the AnalystAgent."""

    def test_analyst_agent_creation(self) -> None:
        """Test creating an AnalystAgent instance."""
        agent = AnalystAgent(
            name="test-analyst",
            role="analyst",
            description="A test analyst agent",
            model_name="test-model",
            system_prompt="You are a verification agent that checks mathematical calculations."
        )
        
        assert agent.name == "test-analyst"
        assert agent.role == "analyst"
        assert agent.description == "A test analyst agent"
        assert agent.model_name == "test-model"

    def test_analyst_execute_correct_addition(self) -> None:
        """Test AnalystAgent.execute() with correct addition."""
        agent = AnalystAgent(
            name="test-analyst",
            role="analyst",
            description="A test analyst agent",
            model_name="test-model",
            system_prompt="You are a verification agent that checks mathematical calculations."
        )
        
        # Input with a correct addition
        task_input = {
            "input": 100.0,
            "result1": 101.0
        }
        
        result = agent.execute(task_input)
        
        # Check that the result has the expected structure and data
        assert isinstance(result, dict)
        assert result["status"] == "success"
        assert "Calculation verified successfully" in result["message"]
        assert result["data"]["input"] == 100.0
        assert result["data"]["result1"] == 101.0
        assert result["verification_results"][0]["is_correct"] is True

    def test_analyst_execute_incorrect_addition(self) -> None:
        """Test AnalystAgent.execute() with incorrect addition."""
        agent = AnalystAgent(
            name="test-analyst",
            role="analyst",
            description="A test analyst agent",
            model_name="test-model",
            system_prompt="You are a verification agent that checks mathematical calculations."
        )
        
        # Input with an incorrect addition
        task_input = {
            "input": 100.0,
            "result3": 104.0  # Should be 103.0
        }
        
        result = agent.execute(task_input)
        
        # Check that the result has the expected structure and data
        assert isinstance(result, dict)
        assert result["status"] == "error"
        assert "expected 100.0 + 3 = 103.0, but got 104.0" in result["message"]
        assert result["data"]["input"] == 100.0
        assert result["data"]["result3"] == 104.0
        assert result["verification_results"][0]["is_correct"] is False

    def test_analyst_execute_no_result_keys(self) -> None:
        """Test AnalystAgent.execute() with no result keys."""
        agent = AnalystAgent(
            name="test-analyst",
            role="analyst",
            description="A test analyst agent",
            model_name="test-model",
            system_prompt="You are a verification agent that checks mathematical calculations."
        )
        
        # Input with no result keys
        task_input = {
            "input": 100.0,
            "something_else": "value"
        }
        
        result = agent.execute(task_input)
        
        # Check that the result has the expected structure and data
        assert isinstance(result, dict)
        assert result["status"] == "warning"
        assert "No result keys found" in result["message"]


class TestFeedbackProcessorAgent:
    """Tests for the FeedbackProcessorAgent."""

    def test_feedback_processor_agent_creation(self) -> None:
        """Test creating a FeedbackProcessorAgent instance."""
        agent = FeedbackProcessorAgent(
            name="test-feedback",
            role="feedback-processor",
            description="A test feedback processor agent",
            model_name="test-model",
            system_prompt="You are a feedback agent that processes verification results and provides helpful recommendations."
        )
        
        assert agent.name == "test-feedback"
        assert agent.role == "feedback-processor"
        assert agent.description == "A test feedback processor agent"
        assert agent.model_name == "test-model"

    def test_feedback_processor_execute_success(self) -> None:
        """Test FeedbackProcessorAgent.execute() with successful verification."""
        agent = FeedbackProcessorAgent(
            name="test-feedback",
            role="feedback-processor",
            description="A test feedback processor agent",
            model_name="test-model",
            system_prompt="You are a feedback agent that processes verification results and provides helpful recommendations."
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
        assert result["original_status"] == "success"
        assert "summary" in result
        assert "recommendations" in result
        assert "All calculations were performed correctly" in result["summary"]
        assert result["errors_found"] == 0

    def test_feedback_processor_execute_error(self) -> None:
        """Test FeedbackProcessorAgent.execute() with verification error."""
        agent = FeedbackProcessorAgent(
            name="test-feedback",
            role="feedback-processor",
            description="A test feedback processor agent",
            model_name="test-model",
            system_prompt="You are a feedback agent that processes verification results and provides helpful recommendations."
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
        assert result["original_status"] == "error"
        assert "summary" in result
        assert "recommendations" in result
        assert "error" in result["summary"].lower()
        assert result["errors_found"] > 0
        assert len(result["recommendations"]) > 0

    def test_feedback_processor_execute_no_verification_keys(self) -> None:
        """Test FeedbackProcessorAgent.execute() with no verification keys."""
        agent = FeedbackProcessorAgent(
            name="test-feedback",
            role="feedback-processor",
            description="A test feedback processor agent",
            model_name="test-model",
            system_prompt="You are a feedback agent that processes verification results and provides helpful recommendations."
        )
        
        # Input with no verification keys
        task_input = {
            "input": 100.0,
            "result1": 101.0,
        }
        
        result = agent.execute(task_input)
        
        # Check that the result has the expected structure and data
        assert isinstance(result, dict)
        assert "No verification data was provided" in result["summary"]
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0 