"""Tests for agent logging functionality."""

import os
import sys
import shutil
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

# Add the parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mimi.core.agent import Agent
from mimi.utils.output_manager import create_or_update_agent_log


class TestAgentLogging(unittest.TestCase):
    """Test agent logging functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary test directory
        self.test_dir = Path("./test_project_dir")
        self.test_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove the temporary test directory
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_create_agent_log(self):
        """Test creating a new agent log file."""
        # Call the function to create a log file
        log_path = create_or_update_agent_log(
            project_dir=self.test_dir,
            agent_name="test-agent",
            action_type="test-action",
            input_summary="Test input",
            output_summary="Test output",
            details={"test_key": "test_value"}
        )
        
        # Check that the log file was created
        self.assertTrue(log_path.exists())
        
        # Read the content of the log file
        with open(log_path, 'r') as f:
            content = f.read()
        
        # Check that the log file has the expected content
        self.assertIn("# Agent Activity Log", content)
        self.assertIn("| test-agent |", content)
        self.assertIn("| test-action |", content)
        self.assertIn("| Test input |", content)
        self.assertIn("| Test output |", content)
        self.assertIn("test_key: test_value", content)
    
    def test_update_agent_log(self):
        """Test updating an existing agent log file."""
        # Create an initial log file
        log_path = create_or_update_agent_log(
            project_dir=self.test_dir,
            agent_name="test-agent",
            action_type="test-action-1",
            input_summary="Test input 1",
            output_summary="Test output 1"
        )
        
        # Update the log file
        create_or_update_agent_log(
            project_dir=self.test_dir,
            agent_name="test-agent",
            action_type="test-action-2",
            input_summary="Test input 2",
            output_summary="Test output 2"
        )
        
        # Read the content of the log file
        with open(log_path, 'r') as f:
            content = f.read()
        
        # Check that the log file contains both entries
        self.assertIn("test-action-1", content)
        self.assertIn("Test input 1", content)
        self.assertIn("Test output 1", content)
        self.assertIn("test-action-2", content)
        self.assertIn("Test input 2", content)
        self.assertIn("Test output 2", content)
    
    @patch('mimi.core.agent.create_or_update_agent_log')
    def test_agent_log_to_file(self, mock_log):
        """Test the Agent.log_to_agent_file method."""
        # Create a test agent
        agent = Agent(
            name="test-agent",
            role="tester",
            description="Test agent for logging",
            model_name="test-model",
            model_provider="test"
        )
        
        # Call the method
        agent.log_to_agent_file(
            project_dir=self.test_dir,
            action_type="test-action",
            input_summary="Test input",
            output_summary="Test output",
            details={"test_key": "test_value"}
        )
        
        # Check that create_or_update_agent_log was called with the correct arguments
        mock_log.assert_called_once_with(
            project_dir=self.test_dir,
            agent_name="test-agent",
            action_type="test-action",
            input_summary="Test input",
            output_summary="Test output",
            details={"test_key": "test_value"}
        )
    
    @patch('mimi.core.agent.create_or_update_agent_log')
    def test_agent_log_with_complex_input(self, mock_log):
        """Test the Agent.log_to_agent_file method with complex input."""
        # Create a test agent
        agent = Agent(
            name="test-agent",
            role="tester",
            description="Test agent for logging",
            model_name="test-model",
            model_provider="test"
        )
        
        # Call the method with a dict input
        complex_input = {"key1": "value1", "key2": "value2"}
        agent.log_to_agent_file(
            project_dir=self.test_dir,
            action_type="test-action",
            input_summary=complex_input,
            output_summary="Test output"
        )
        
        # The input should be converted to a string summary
        mock_log.assert_called_once()
        args = mock_log.call_args[1]
        self.assertEqual(args["project_dir"], self.test_dir)
        self.assertEqual(args["agent_name"], "test-agent")
        self.assertEqual(args["action_type"], "test-action")
        self.assertIn("Dict with keys", args["input_summary"])
        self.assertIn("key1, key2", args["input_summary"])
        self.assertEqual(args["output_summary"], "Test output")


if __name__ == "__main__":
    unittest.main() 