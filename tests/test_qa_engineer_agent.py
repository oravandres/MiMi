"""Tests for the QAEngineerAgent class."""

import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile
import shutil
import os

from mimi.core.agents.qa_engineer_agent import QAEngineerAgent
from mimi.core.agents.base_agent import Agent


class TestQAEngineerAgent(unittest.TestCase):
    """Tests for the QAEngineerAgent class."""

    def setUp(self):
        """Set up a temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.temp_dir) / "test_project"
        self.project_dir.mkdir(exist_ok=True)
        (self.project_dir / "tests").mkdir(exist_ok=True)
        
        # Mock the get_project_directory function to return our test directory
        self.patcher = patch("mimi.core.agents.qa_engineer_agent.get_project_directory", 
                             return_value=self.project_dir)
        self.mock_get_project_dir = self.patcher.start()
        
        # Create a mock model client
        self.mock_client = MagicMock()
        self.mock_client.generate.return_value = "Test QA results content"
        
        # Create the agent
        self.agent = QAEngineerAgent(
            name="test-qa",
            role="QA Engineer",
            description="A QA engineer agent",
            model_name="test-model",
            system_prompt="You are a QA engineer that tests software components.",
            model_provider="ollama"
        )
        
        # Patch the get_model_client method and generate_text method
        self.get_model_client_patcher = patch.object(QAEngineerAgent, 'get_model_client', return_value=self.mock_client)
        self.mock_get_model_client = self.get_model_client_patcher.start()
        
        self.generate_text_patcher = patch.object(QAEngineerAgent, 'generate_text', return_value="Test QA results content")
        self.mock_generate_text = self.generate_text_patcher.start()

    def tearDown(self):
        """Clean up temporary files."""
        self.patcher.stop()
        self.get_model_client_patcher.stop()
        self.generate_text_patcher.stop()
        shutil.rmtree(self.temp_dir)

    def test_integrated_frontend_input(self):
        """Test that QA agent handles integrated_frontend input correctly."""
        # Test input with integrated_frontend key
        input_data = {
            "integrated_frontend": "Frontend implementation with HTML, CSS, and JavaScript",
            "project_title": "Test Frontend Project",
            "project_dir": str(self.project_dir)
        }
        
        # Execute the method
        result = self.agent.execute(input_data)
        
        # Verify the result structure
        self.assertIsInstance(result, dict)
        self.assertIn("test_results", result)
        self.assertIn("qa_engineer", result)
        self.assertIn("project_title", result)
        self.assertIn("project_dir", result)
        self.assertIn("test_results_doc", result)
        
        # Verify the values
        self.assertEqual(result["test_results"], "Test QA results content")
        self.assertEqual(result["qa_engineer"], "test-qa")
        self.assertEqual(result["project_title"], "Test Frontend Project")
        
        # Verify the test results file was created
        test_results_path = self.project_dir / "tests" / "test_results.md"
        self.assertTrue(test_results_path.exists())
        
        # Verify the generate_text method was called
        self.mock_generate_text.assert_called_once()
        call_args = self.mock_generate_text.call_args[0]
        self.assertIn("Frontend implementation with HTML, CSS, and JavaScript", call_args[0])

    def test_integrated_backend_input(self):
        """Test that QA agent handles integrated_backend input correctly."""
        # Test input with integrated_backend key
        input_data = {
            "integrated_backend": "Backend implementation with APIs and services",
            "project_title": "Test Backend Project",
            "project_dir": str(self.project_dir)
        }
        
        # Execute the method
        result = self.agent.execute(input_data)
        
        # Verify the result structure
        self.assertIsInstance(result, dict)
        self.assertIn("test_results", result)
        self.assertIn("qa_engineer", result)
        self.assertIn("project_title", result)
        self.assertIn("project_dir", result)
        self.assertIn("test_results_doc", result)
        
        # Verify the values
        self.assertEqual(result["test_results"], "Test QA results content")
        self.assertEqual(result["qa_engineer"], "test-qa")
        self.assertEqual(result["project_title"], "Test Backend Project")
        
        # Verify the test results file was created
        test_results_path = self.project_dir / "tests" / "test_results.md"
        self.assertTrue(test_results_path.exists())
        
        # Verify the generate_text method was called
        self.mock_generate_text.assert_called_once()
        call_args = self.mock_generate_text.call_args[0]
        self.assertIn("Backend implementation with APIs and services", call_args[0])

    def test_integrated_system_input_legacy(self):
        """Test that QA agent still handles legacy integrated_system input."""
        # Test input with legacy integrated_system key
        input_data = {
            "integrated_system": "Legacy system implementation",
            "project_title": "Test Legacy Project",
            "project_dir": str(self.project_dir)
        }
        
        # Execute the method
        result = self.agent.execute(input_data)
        
        # Verify the result structure
        self.assertIsInstance(result, dict)
        self.assertIn("test_results", result)
        self.assertEqual(result["test_results"], "Test QA results content")
        
        # Verify the generate_text method was called
        self.mock_generate_text.assert_called_once()

    def test_fixed_system_input(self):
        """Test that QA agent handles fixed_system input for documentation."""
        # Mock the _create_documentation method
        with patch.object(self.agent, '_create_documentation') as mock_create_doc:
            mock_create_doc.return_value = {"status": "success", "documentation": "Test docs"}
            
            # Test input with fixed_system key
            input_data = {
                "fixed_system": "Fixed system implementation",
                "project_title": "Test Documentation Project",
                "project_dir": str(self.project_dir)
            }
            
            # Execute the method
            result = self.agent.execute(input_data)
            
            # Verify _create_documentation was called
            mock_create_doc.assert_called_once_with(
                "Fixed system implementation", 
                input_data, 
                self.project_dir, 
                "Test Documentation Project"
            )

    def test_unrecognized_input_format(self):
        """Test that QA agent handles unrecognized input formats gracefully."""
        # Test input with unrecognized keys
        input_data = {
            "unknown_key": "Some unknown data",
            "another_key": "More unknown data",
            "project_title": "Test Error Project",
            "project_dir": str(self.project_dir)
        }
        
        # Execute the method
        result = self.agent.execute(input_data)
        
        # Verify error response
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertEqual(result["status"], "error")
        self.assertIn("message", result)
        self.assertIn("Unrecognized input format", result["message"])
        self.assertIn("project_title", result)
        self.assertIn("project_dir", result)

    def test_game_project_detection(self):
        """Test that QA agent correctly detects game projects."""
        # Create actual game files so the test goes through the normal flow
        (self.project_dir / "index.html").write_text("<!DOCTYPE html><html></html>")
        (self.project_dir / "js").mkdir(exist_ok=True)
        (self.project_dir / "js" / "game.js").write_text("// Game logic")
        (self.project_dir / "css").mkdir(exist_ok=True)
        (self.project_dir / "css" / "styles.css").write_text("/* Game styles */")
        
        # Test input for a game project
        input_data = {
            "integrated_frontend": "Flappy Bird game implementation",
            "project_title": "Flappy Bird Game",
            "project_dir": str(self.project_dir)
        }
        
        # Execute the method
        result = self.agent.execute(input_data)
        
        # Verify the generate_text method was called with game-specific prompt
        self.mock_generate_text.assert_called_once()
        call_args = self.mock_generate_text.call_args[0]
        self.assertIn("Game Implementation Testing", call_args[0])
        self.assertIn("Flappy Bird", call_args[0])

    def test_qa_lead_role_handling(self):
        """Test that QA Lead role handles input differently."""
        # Create QA Lead agent
        qa_lead = QAEngineerAgent(
            name="qa-lead",
            role="QA Lead",
            description="A QA lead agent",
            model_name="test-model",
            system_prompt="You are a QA lead.",
            model_provider="ollama"
        )
        
        # Mock the _test_system method for QA Lead
        with patch.object(qa_lead, '_test_system') as mock_test_system:
            mock_test_system.return_value = {"status": "success", "test": "qa_lead_test"}
            
            # Test input without obvious implementation keys
            input_data = {
                "some_integration_data": "Integration data",
                "project_title": "Test QA Lead Project",
                "project_dir": str(self.project_dir)
            }
            
            # Execute the method
            result = qa_lead.execute(input_data)
            
            # Verify _test_system was called (QA Lead should handle various input formats)
            mock_test_system.assert_called_once()

    def test_missing_files_handling(self):
        """Test that QA agent handles missing essential files for game projects."""
        # Test with game project but no actual game files
        input_data = {
            "integrated_frontend": "Flappy Bird implementation",
            "project_title": "Flappy Bird Game", 
            "project_dir": str(self.project_dir)
        }
        
        # Mock the _generate_missing_files_report method
        with patch.object(self.agent, '_generate_missing_files_report') as mock_missing:
            mock_missing.return_value = {"status": "error", "missing_files": ["index.html"]}
            
            # Execute the method (game files don't exist in temp dir)
            result = self.agent.execute(input_data)
            
            # Should detect missing files and call the missing files report
            mock_missing.assert_called_once()

    def test_input_logging_and_debugging(self):
        """Test that the agent logs input types and debugging information."""
        # Test input
        input_data = {
            "integrated_frontend": "Test implementation",
            "project_title": "Test Project",
            "project_dir": str(self.project_dir)
        }
        
        # Mock logger to capture calls
        with patch("mimi.core.agents.qa_engineer_agent.logger") as mock_logger:
            # Execute the method
            result = self.agent.execute(input_data)
            
            # Verify debug logging was called
            debug_calls = [call for call in mock_logger.debug.call_args_list 
                          if "QAEngineerAgent received input of type: dict" in str(call)]
            self.assertTrue(len(debug_calls) > 0, "Should log input type for debugging")


if __name__ == '__main__':
    unittest.main() 