"""Tests for the logging fix to handle complex data structures with curly braces."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys

# Add the parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mimi.core.task import Task
from mimi.utils.logger import logger


class TestLoggingFix:
    """Tests for the logging fix that handles complex data structures."""

    def test_complex_nested_data_logging(self) -> None:
        """Test that logging works with complex nested data containing curly braces."""
        # Create test data that was causing the original KeyError
        complex_data = {
            'input': {
                'input': 'Create javascript and html app of flappy bird, that I could run in easily',
                'project_dir': Path('Software/20250602_215231_Advanced_Software_Engineering_Project')
            },
            'other_data': {
                'nested': {'key': 'value'},
                'list': [1, 2, 3]
            }
        }
        
        # Create a task
        task = Task(
            name="test-task",
            description="A test task for logging",
            agent="test-agent",
        )
        
        # Create a mock agent
        mock_agent = MagicMock()
        mock_agent.execute.return_value = "success"
        mock_agent.__class__.__name__ = "TestAgent"  # Not AnalystAgent to avoid cleaning
        
        # This should not raise a KeyError anymore
        try:
            result = task.execute({"test-agent": mock_agent}, complex_data)
            # If we get here, the fix worked
            assert result == "success"
        except KeyError as e:
            pytest.fail(f"Logging should not raise KeyError with complex data: {e}")

    def test_task_logging_with_single_quotes_in_data(self) -> None:
        """Test that task logging handles data with single quotes."""
        complex_data = {
            "message": "This is a 'quoted' string",
            "nested": {
                "data": "More 'quotes' here"
            }
        }
        
        task = Task(
            name="quote-test-task",
            description="Test task with quoted data",
            agent="test-agent",
        )
        
        mock_agent = MagicMock()
        mock_agent.execute.return_value = "handled quotes"
        mock_agent.__class__.__name__ = "TestAgent"
        
        # This should work without errors
        result = task.execute({"test-agent": mock_agent}, complex_data)
        assert result == "handled quotes"

    def test_task_logging_with_curly_braces_in_strings(self) -> None:
        """Test that task logging handles strings containing curly braces."""
        complex_data = {
            "code": "function test() { return {key: 'value'}; }",
            "template": "Hello {name}, welcome to {place}!",
            "json_string": '{"key": "value", "number": 123}'
        }
        
        task = Task(
            name="braces-test-task",
            description="Test task with braces in data",
            agent="test-agent",
        )
        
        mock_agent = MagicMock()
        mock_agent.execute.return_value = "handled braces"
        mock_agent.__class__.__name__ = "TestAgent"
        
        # This should work without KeyError
        result = task.execute({"test-agent": mock_agent}, complex_data)
        assert result == "handled braces"

    def test_task_logging_with_empty_and_none_data(self) -> None:
        """Test that task logging handles edge cases like empty dicts and None."""
        test_cases = [
            {},  # Empty dict
            None,  # None
            {"empty_nested": {}},  # Nested empty dict
            {"none_value": None},  # None value
        ]
        
        for i, test_data in enumerate(test_cases):
            task = Task(
                name=f"edge-case-task-{i}",
                description=f"Test task for edge case {i}",
                agent="test-agent",
            )
            
            mock_agent = MagicMock()
            mock_agent.execute.return_value = f"handled case {i}"
            mock_agent.__class__.__name__ = "TestAgent"
            
            # Should handle all edge cases without error
            result = task.execute({"test-agent": mock_agent}, test_data)
            assert result == f"handled case {i}"

    def test_input_key_extraction_with_complex_data(self) -> None:
        """Test that input_key extraction works with complex data."""
        complex_data = {
            'target_key': {
                'input': 'This is the target data with {braces}',
                'metadata': {'created': '2024-01-01'}
            },
            'other_key': {
                'different': 'data'
            }
        }
        
        task = Task(
            name="extraction-test-task",
            description="Test task for input key extraction",
            agent="test-agent",
            input_key="target_key"
        )
        
        mock_agent = MagicMock()
        mock_agent.execute.return_value = "extracted successfully"
        mock_agent.__class__.__name__ = "TestAgent"
        
        result = task.execute({"test-agent": mock_agent}, complex_data)
        
        # Verify the agent was called with the extracted data
        expected_input = {
            'input': 'This is the target data with {braces}',
            'metadata': {'created': '2024-01-01'}
        }
        mock_agent.execute.assert_called_once_with(expected_input)
        assert result == "extracted successfully"

    def test_output_key_storage_with_complex_data(self) -> None:
        """Test that output_key storage works when input contains complex data."""
        complex_input = {
            'original_data': {
                'message': 'Data with {braces} and "quotes"',
                'numbers': [1, 2, 3]
            }
        }
        
        task = Task(
            name="storage-test-task",
            description="Test task for output key storage",
            agent="test-agent",
            output_key="processed_result"
        )
        
        mock_agent = MagicMock()
        mock_agent.execute.return_value = {"processed": True, "count": 42}
        mock_agent.__class__.__name__ = "TestAgent"
        
        result = task.execute({"test-agent": mock_agent}, complex_input)
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert "processed_result" in result
        assert result["processed_result"] == {"processed": True, "count": 42}
        assert result["original_data"] == complex_input["original_data"]  # Original preserved

    @patch('mimi.core.task.logger')
    def test_debug_logging_escapes_braces(self, mock_logger) -> None:
        """Test that the debug logging properly escapes curly braces."""
        problematic_data = {
            'input': {
                'input': 'Text with {braces} and more {formatting}',
                'project_dir': Path('/test/path')
            }
        }
        
        task = Task(
            name="debug-test-task",
            description="Test task for debug logging",
            agent="test-agent",
        )
        
        mock_agent = MagicMock()
        mock_agent.execute.return_value = "success"
        mock_agent.__class__.__name__ = "TestAgent"
        
        # Execute the task
        task.execute({"test-agent": mock_agent}, problematic_data)
        
        # Verify that logger.debug was called
        assert mock_logger.debug.called
        
        # Get the first call to logger.debug
        debug_call = mock_logger.debug.call_args_list[0]
        debug_message = debug_call[0][0]  # First positional argument
        
        # Verify that the message contains escaped braces
        assert "{{" in debug_message and "}}" in debug_message
        # Verify that the braces inside the data are properly double-escaped
        assert "{{braces}}" in debug_message  # Should be escaped as {{braces}}
        assert "{{formatting}}" in debug_message  # Should be escaped as {{formatting}} 