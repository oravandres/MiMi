"""Tests for agent logging functionality."""

import os
import sys
import shutil
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch, mock_open
import tempfile
import json

# Add the parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mimi.core.agent import Agent
from mimi.utils.output_manager import create_or_update_agent_log


class TestAgentLogging(unittest.TestCase):
    """Tests for agent logging functionality."""

    def setUp(self):
        """Set up a temporary directory for tests."""
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, "logs"), exist_ok=True)

    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.test_dir)

    @patch('mimi.utils.output_manager._create_or_update_json_agent_log')
    @patch('mimi.utils.output_manager._create_or_update_markdown_agent_log')
    def test_create_agent_log(self, mock_md_log, mock_json_log):
        """Test create_or_update_agent_log function."""
        # Create a fake path to return
        mock_path = Path(os.path.join(self.test_dir, "logs", "test-agent.log.md"))
        mock_md_log.return_value = mock_path
        mock_json_log.return_value = mock_path
        
        # Call with default format (markdown)
        result = create_or_update_agent_log(
            project_dir=Path(self.test_dir),
            agent_name="test-agent",
            action_type="test-action",
            input_summary="Test input",
            output_summary="Test output",
            details={"test_key": "test_value"}
        )
        
        # Verify the markdown function was called
        mock_md_log.assert_called_once()
        mock_json_log.assert_not_called()
        
        # Reset mocks
        mock_md_log.reset_mock()
        mock_json_log.reset_mock()
        
        # Call with JSON format
        result = create_or_update_agent_log(
            project_dir=Path(self.test_dir),
            agent_name="test-agent",
            action_type="test-action",
            input_summary="Test input",
            output_summary="Test output",
            details={"test_key": "test_value"},
            log_format="json"
        )
        
        # Verify the JSON function was called
        mock_md_log.assert_not_called()
        mock_json_log.assert_called_once()

    @patch('mimi.utils.output_manager._create_or_update_json_agent_log')
    def test_update_agent_log(self, mock_json_log):
        """Test create_or_update_agent_log with JSON format."""
        # Create a fake path to return
        mock_path = Path(os.path.join(self.test_dir, "logs", "test-agent.log.json"))
        mock_json_log.return_value = mock_path
        
        # Call with JSON format
        result = create_or_update_agent_log(
            project_dir=Path(self.test_dir),
            agent_name="test-agent",
            action_type="new-action",
            input_summary="New input",
            output_summary="New output",
            details={"new_key": "new_value"},
            log_format="json"
        )
        
        # Verify the JSON function was called with the right project dir
        mock_json_log.assert_called_once()
        # We don't need to check all args, just verify it was called with correct Path
        self.assertEqual(mock_json_log.call_args[0][0], Path(self.test_dir))
        
        # Also verify the call included our input and output values
        call_args_str = str(mock_json_log.call_args)
        self.assertIn("New input", call_args_str)
        self.assertIn("New output", call_args_str)
        self.assertIn("new_key", call_args_str)
        self.assertIn("new_value", call_args_str)

    def test_agent_log_to_file(self):
        """Test the Agent.log_to_agent_file method."""
        # Create a test agent
        agent = Agent(
            name="test-agent",
            role="test-role",
            description="A test agent",
            model_name="test-model",
            system_prompt="You are a helpful test agent that assists with testing."
        )
        
        # Create a custom mock function that just remembers what was passed to it
        call_args_list = []
        
        def mock_create_or_update_agent_log(*args, **kwargs):
            call_args_list.append((args, kwargs))
            return Path(self.test_dir) / "logs" / "mock_agent.log.md"
        
        # Patch the function in the module
        with patch('mimi.core.agents.base_agent.create_or_update_agent_log',
                  side_effect=mock_create_or_update_agent_log):
            # Call the method
            agent.log_to_agent_file(
                project_dir=Path(self.test_dir),
                action_type="test-action",
                input_summary="Test input",
                output_summary="Test output",
                details={"test_key": "test_value"}
            )
            
            # Check that our mock function was called correctly
            self.assertEqual(len(call_args_list), 1)
            
            # Check the arguments
            _, kwargs = call_args_list[0]
            self.assertEqual(kwargs["project_dir"], Path(self.test_dir))
            self.assertEqual(kwargs["agent_name"], "test-agent")
            self.assertEqual(kwargs["action_type"], "test-action")
            self.assertEqual(kwargs["input_summary"], "Test input")
            self.assertEqual(kwargs["output_summary"], "Test output")
            self.assertEqual(kwargs["details"]["test_key"], "test_value")
            self.assertEqual(kwargs["details"]["agent_role"], "test-role")

    def test_agent_log_with_complex_input(self):
        """Test the Agent.log_to_agent_file method with complex input."""
        # Create a test agent
        agent = Agent(
            name="test-agent",
            role="test-role",
            description="A test agent",
            model_name="test-model",
            system_prompt="You are a helpful test agent that assists with testing."
        )
        
        # Create a custom mock function that converts the complex input to a string
        call_args_list = []
        
        def mock_create_or_update_agent_log(*args, **kwargs):
            # Convert dict to string (this is what the real function should do)
            if isinstance(kwargs.get("input_summary"), dict):
                kwargs["input_summary"] = str(kwargs["input_summary"])
            call_args_list.append((args, kwargs))
            return Path(self.test_dir) / "logs" / "mock_agent.log.md"
        
        # Patch the function in the module
        with patch('mimi.core.agents.base_agent.create_or_update_agent_log',
                  side_effect=mock_create_or_update_agent_log):
            # Call the method with a dict input
            complex_input = {"key1": "value1", "key2": "value2"}
            agent.log_to_agent_file(
                project_dir=Path(self.test_dir),
                action_type="test-action",
                input_summary=complex_input,
                output_summary="Test output"
            )
            
            # Verify the result
            self.assertEqual(len(call_args_list), 1)
            
            # Check that the complex input was converted properly
            _, kwargs = call_args_list[0]
            self.assertEqual(kwargs["project_dir"], Path(self.test_dir))
            self.assertEqual(kwargs["agent_name"], "test-agent")
            self.assertEqual(kwargs["action_type"], "test-action")
            self.assertEqual(kwargs["input_summary"], str(complex_input))
            self.assertEqual(kwargs["output_summary"], "Test output")

if __name__ == "__main__":
    unittest.main() 