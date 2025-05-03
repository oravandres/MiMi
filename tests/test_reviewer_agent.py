"""Tests for the ReviewerAgent class."""

import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile
import shutil
import os

from mimi.core.software_agents import ReviewerAgent
from mimi.core.agent import Agent


class TestReviewerAgent(unittest.TestCase):
    """Tests for the ReviewerAgent class."""

    def setUp(self):
        """Set up a temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.temp_dir) / "test_project"
        self.project_dir.mkdir(exist_ok=True)
        (self.project_dir / "docs").mkdir(exist_ok=True)
        
        # Mock the get_project_directory function to return our test directory
        self.patcher = patch("mimi.core.software_agents.get_project_directory", 
                             return_value=self.project_dir)
        self.mock_get_project_dir = self.patcher.start()
        
        # Create a mock model client
        self.mock_client = MagicMock()
        self.mock_client.generate.return_value = "Test review content"
        
        # Create the agent and patch the get_model_client method
        self.agent = ReviewerAgent(
            name="test-reviewer",
            role="Test Reviewer",
            description="A test reviewer agent for unit tests",
            model_name="test-model",
            model_provider="test-provider"
        )
        
        # Patch the get_model_client method using unittest.mock.patch
        self.get_model_client_patcher = patch.object(ReviewerAgent, 'get_model_client', return_value=self.mock_client)
        self.mock_get_model_client = self.get_model_client_patcher.start()

    def tearDown(self):
        """Clean up temporary files."""
        self.patcher.stop()
        self.get_model_client_patcher.stop()
        shutil.rmtree(self.temp_dir)

    def test_review_component_backend(self):
        """Test the _review_component method with backend focus."""
        # Set up the agent with backend role
        self.agent.role = "Backend Reviewer"
        
        # Test input with documentation
        input_data = {
            "documentation": "Test documentation content",
            "project_title": "Test Project",
            "project_dir": str(self.project_dir)
        }
        
        # Execute the method
        result = self.agent.execute(input_data)
        
        # Verify the result
        self.assertIn("backend_review", result)
        self.assertEqual(result["backend_review"], "Test review content")
        self.assertEqual(result["component_type"], "backend")
        
        # Verify the file was saved
        backend_review_path = self.project_dir / "docs" / "backend_review.md"
        self.assertTrue(backend_review_path.exists())
        with open(backend_review_path, 'r') as f:
            content = f.read()
            self.assertEqual(content, "Test review content")
        
        # Verify the model was called with the right prompts
        call_args = self.mock_client.generate.call_args[0]
        self.assertIn("Review the backend components", call_args[0])

    def test_review_component_frontend(self):
        """Test the _review_component method with frontend focus."""
        # Set up the agent with frontend role
        self.agent.role = "Frontend Reviewer"
        
        # Test input with documentation
        input_data = {
            "documentation": "Test documentation content",
            "project_title": "Test Project",
            "project_dir": str(self.project_dir)
        }
        
        # Execute the method
        result = self.agent.execute(input_data)
        
        # Verify the result
        self.assertIn("frontend_review", result)
        self.assertEqual(result["frontend_review"], "Test review content")
        self.assertEqual(result["component_type"], "frontend")
        
        # Verify the file was saved
        frontend_review_path = self.project_dir / "docs" / "frontend_review.md"
        self.assertTrue(frontend_review_path.exists())
        
        # Verify the model was called with the right prompts
        call_args = self.mock_client.generate.call_args[0]
        self.assertIn("Review the frontend components", call_args[0])

    def test_review_component_infrastructure(self):
        """Test the _review_component method with infrastructure focus."""
        # Set up the agent with infrastructure role
        self.agent.role = "Infrastructure Reviewer"
        
        # Test input with documentation
        input_data = {
            "documentation": "Test documentation content",
            "project_title": "Test Project",
            "project_dir": str(self.project_dir)
        }
        
        # Execute the method
        result = self.agent.execute(input_data)
        
        # Verify the result
        self.assertIn("infrastructure_review", result)
        self.assertEqual(result["infrastructure_review"], "Test review content")
        self.assertEqual(result["component_type"], "infrastructure")
        
        # Verify the file was saved
        infra_review_path = self.project_dir / "docs" / "infrastructure_review.md"
        self.assertTrue(infra_review_path.exists())
        
        # Verify the model was called with the right prompts
        call_args = self.mock_client.generate.call_args[0]
        self.assertIn("Review the infrastructure components", call_args[0])

    def test_consolidate_reviews(self):
        """Test the _consolidate_reviews method."""
        # Set up the agent
        self.agent.role = "Project Reviewer"
        
        # Create sample review files
        backend_review = "Backend review content"
        frontend_review = "Frontend review content"
        infrastructure_review = "Infrastructure review content"
        
        # Test input with all component reviews
        input_data = {
            "documentation": "Test documentation content",
            "project_title": "Test Project",
            "project_dir": str(self.project_dir),
            "backend_review": backend_review,
            "frontend_review": frontend_review,
            "infrastructure_review": infrastructure_review
        }
        
        # Execute the method
        result = self.agent.execute(input_data)
        
        # Verify the result
        self.assertIn("project_review", result)
        self.assertEqual(result["project_review"], "Test review content")
        self.assertIn("backend_review", result)
        self.assertEqual(result["backend_review"], backend_review)
        self.assertIn("frontend_review", result)
        self.assertEqual(result["frontend_review"], frontend_review)
        self.assertIn("infrastructure_review", result)
        self.assertEqual(result["infrastructure_review"], infrastructure_review)
        
        # Verify the file was saved
        project_review_path = self.project_dir / "docs" / "project_review.md"
        self.assertTrue(project_review_path.exists())
        
        # Verify the model was called with the right prompts
        call_args = self.mock_client.generate.call_args[0]
        self.assertIn("Consolidate these component reviews", call_args[0])
        self.assertIn(backend_review, call_args[0])
        self.assertIn(frontend_review, call_args[0])
        self.assertIn(infrastructure_review, call_args[0])

    def test_final_approval(self):
        """Test the _final_approval method."""
        # Set up the agent
        self.agent.role = "Project Reviewer"
        
        # Test input with integrated_fixes
        input_data = {
            "integrated_fixes": "Test fixes content",
            "project_title": "Test Project",
            "project_dir": str(self.project_dir)
        }
        
        # Execute the method
        result = self.agent.execute(input_data)
        
        # Verify the result
        self.assertIn("final_approval", result)
        self.assertEqual(result["final_approval"], "Test review content")
        
        # Verify the file was saved
        final_approval_path = self.project_dir / "docs" / "final_approval.md"
        self.assertTrue(final_approval_path.exists())
        
        # Verify the model was called with the right prompts
        call_args = self.mock_client.generate.call_args[0]
        self.assertIn("Conduct a final review", call_args[0])

    def test_invalid_input(self):
        """Test handling of invalid input."""
        # Set up the agent
        self.agent.role = "Project Reviewer"
        
        # Test input with no recognized keys
        input_data = {
            "unknown_key": "Test content",
            "project_title": "Test Project",
            "project_dir": str(self.project_dir)
        }
        
        # Execute the method
        result = self.agent.execute(input_data)
        
        # Verify the result indicates an error
        self.assertIn("status", result)
        self.assertEqual(result["status"], "error")
        self.assertIn("message", result)
        self.assertIn("input_keys", result)
        self.assertIn("unknown_key", result["input_keys"])


if __name__ == "__main__":
    unittest.main() 