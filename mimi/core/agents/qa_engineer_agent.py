"""QA Engineer Agent implementation for MiMi."""

from typing import Any, Dict
import os
from datetime import datetime
from pathlib import Path
import re

from mimi.core.agents.base_agent import Agent
from mimi.utils.logger import agent_log, logger
from mimi.utils.output_manager import (
    create_output_directory,
    save_documentation,
    save_code_blocks_from_text,
    create_or_update_project_log,
    _load_current_project_dir
)


def get_project_directory(project_title: str) -> Path:
    """Get the project directory, creating it if it doesn't exist.
    
    Args:
        project_title: The title of the project.
        
    Returns:
        The path to the project directory.
    """
    # First try to load the existing project directory from state file
    loaded_dir = _load_current_project_dir()
    if loaded_dir is not None:
        return loaded_dir
    
    # If no existing directory, create a new one
    return create_output_directory(project_title)


class QAEngineerAgent(Agent):
    """Agent that tests software components and creates documentation."""
    
    def execute(self, task_input: Any) -> Any:
        """Test software components or create documentation.
        
        Args:
            task_input: A dictionary containing the integrated system or fixed system.
            
        Returns:
            A dictionary with test results or documentation.
        """
        agent_log(
            self.name,
            "execute",
            f"Testing or documenting system"
        )
        
        # Log the input type for easier debugging
        input_type = type(task_input).__name__
        logger.debug(f"QAEngineerAgent received input of type: {input_type}")
        
        # Get the project directory from the input
        project_title = "Software Project"
        project_dir_str = None
        
        # Extract project information
        if isinstance(task_input, dict):
            # Look for project_title and project_dir at the top level
            project_title = task_input.get("project_title", project_title)
            project_dir_str = task_input.get("project_dir", None)
            
            # Look for project info in nested dictionaries
            if project_dir_str is None:
                for key, value in task_input.items():
                    if isinstance(value, dict):
                        if "project_dir" in value:
                            project_dir_str = value["project_dir"]
                            logger.info(f"Found project_dir in nested key '{key}'")
                        elif "data" in value and isinstance(value["data"], dict) and "project_dir" in value["data"]:
                            project_dir_str = value["data"]["project_dir"]
                            logger.info(f"Found project_dir in nested data of '{key}'")
                        
                        # Extract project title if not already found
                        if project_title == "Software Project":
                            if "project_title" in value:
                                project_title = value["project_title"]
                            elif "data" in value and isinstance(value["data"], dict) and "project_title" in value["data"]:
                                project_title = value["data"]["project_title"]
        
            # Get the project directory
            if project_dir_str:
                project_dir = Path(project_dir_str)
                logger.info(f"Using existing project directory: {project_dir}")
            else:
                project_dir = get_project_directory(project_title)
                logger.warning(f"Project directory not provided, creating new one for {project_title}")
            
            # Extract input data in various formats
            # For QA lead role, extract from the system_under_test field or look for integration data
            if self.role == "QA Lead" or "qa-lead" in self.name.lower():
                # Look for system_under_test in task_input
                if "system_under_test" in task_input:
                    return self._test_system(task_input["system_under_test"], task_input, project_dir, project_title)
                # Look for any integrated components
                elif "integrated_components" in task_input:
                    return self._test_system(task_input["integrated_components"], task_input, project_dir, project_title)
                # Look for integrated_frontend, integrated_backend, etc.
                elif any(key.startswith("integrated_") for key in task_input.keys()):
                    # Combine all integrated components
                    integrated_components = ""
                    for key, value in task_input.items():
                        if key.startswith("integrated_"):
                            if isinstance(value, dict) and "data" in value:
                                integrated_components += f"\n\n# {key.replace('integrated_', '').upper()}\n{value['data']}\n"
                            else:
                                integrated_components += f"\n\n# {key.replace('integrated_', '').upper()}\n{value}\n"
                    return self._test_system(integrated_components, task_input, project_dir, project_title)
                # Look for deployed_system
                elif "deployed_system" in task_input:
                    return self._test_system(task_input["deployed_system"], task_input, project_dir, project_title)
            
            # Standard handling for normal QA Engineers
            # Determine the task type based on input
            if "integrated_system" in task_input:
                # Handle the case where the integrated_system is the whole dictionary
                integrated_system = task_input.get("implementation", "") or task_input.get("integrated_system", "")
                if not integrated_system:
                    # If we still don't have a meaningful value, use the whole thing
                    integrated_system = str(task_input)
                return self._test_system(integrated_system, task_input, project_dir, project_title)
            elif "fixed_system" in task_input:
                fixed_system = task_input.get("fixed_system", "")
                return self._create_documentation(fixed_system, task_input, project_dir, project_title)
            # Handle input from engineer-1 during integration task
            elif "implementation" in task_input and task_input.get("specialty", "") == "backend":
                integrated_system = task_input.get("implementation", "")
                return self._test_system(integrated_system, task_input, project_dir, project_title)
            # Handle more generic input by checking if any value looks like implementation/code
            else:
                # Look for any content that might be code or documentation
                for key, value in task_input.items():
                    if isinstance(value, str) and len(value) > 100 and ('```' in value or '<' in value or 'function' in value):
                        logger.info(f"Found potential implementation content in key '{key}'")
                        return self._test_system(value, task_input, project_dir, project_title)
                    elif isinstance(value, dict) and "data" in value and isinstance(value["data"], str) and len(value["data"]) > 100:
                        logger.info(f"Found potential implementation content in key '{key}.data'")
                        return self._test_system(value["data"], task_input, project_dir, project_title)
        
        # Default error case if we get here
        agent_log(self.name, "error", "Unrecognized input format")
        
        # Try to create a meaningful project directory for logging the error
        if not project_dir_str:
            project_dir = get_project_directory(project_title)
        
        # Log the error to the agent file
        self.log_to_agent_file(
            project_dir=project_dir,
            action_type="error",
            input_summary="Unrecognized input format",
            output_summary="Failed to parse input for QA testing",
            details={
                "input_type": str(type(task_input)),
                "agent_role": self.role,
                "model_name": self.model_name,
                "model_provider": self.model_provider
            }
        )
        
        return {
            "status": "error",
            "message": "Unrecognized input format for QA engineer agent",
            "project_title": project_title,
            "project_dir": str(project_dir)
        }
    
    def _test_system(self, integrated_system: str, full_input: Dict[str, Any], project_dir: Path, project_title: str) -> Dict[str, Any]:
        """Test the integrated system for bugs and issues.
        
        Args:
            integrated_system: The integrated system to test.
            full_input: The full task input.
            project_dir: Path to the project directory.
            project_title: Title of the project.
            
        Returns:
            Testing results and identified bugs.
        """
        agent_log(
            self.name,
            "execute",
            f"Testing integrated system for {project_title}"
        )
        
        # Construct the prompt for the model
        prompt = f"""
        # Integrated System
        {integrated_system}
        
        # Task
        Test the integrated system by:
        - Creating a comprehensive test plan covering all components
        - For each component:
          * Define test cases (including edge cases)
          * Execute tests (simulated)
          * Document any issues found
        - Categorize issues by severity (critical, high, medium, low)
        - Provide recommendations for fixing each issue
        
        Format your response as a structured test report.
        Include actual test code files where appropriate, using the format:
        ```language
        tests/component/filename.ext
        // Test code content
        ```
        """
        
        # Get model client
        client = self.get_model_client()
        
        # Generate test results using the model
        response = self.generate_text(prompt)
        
        # Save the test results document
        test_results_path = project_dir / "tests" / "test_results.md"
        test_results_path.parent.mkdir(exist_ok=True)
        with open(test_results_path, 'w') as f:
            f.write(response)
        
        # Extract and save test code from the response
        saved_test_files = save_code_blocks_from_text(project_dir, "tests", response)
        
        # Structure the output
        test_results = {
            "timestamp": datetime.now().isoformat(),
            "qa_engineer": self.name,
            "test_results": response,
            "integrated_system": integrated_system,
            "project_title": project_title,
            "project_dir": str(project_dir),
            "test_results_doc": str(test_results_path),
            "saved_test_files": [str(path) for path in saved_test_files]
        }
        
        agent_log(
            self.name,
            "execute",
            f"Successfully tested the integrated system and saved results to {test_results_path}"
        )
        
        return test_results
    
    def _create_documentation(self, fixed_system: str, full_input: Dict[str, Any], project_dir: Path, project_title: str) -> Dict[str, Any]:
        """Create documentation for the system."""
        # Extract additional context if available
        backend_components = full_input.get("backend_components", "")
        frontend_components = full_input.get("frontend_components", "")
        infrastructure_components = full_input.get("infrastructure_components", "")
        integrated_system = full_input.get("integrated_system", "")
        test_results = full_input.get("test_results", "")
        
        prompt = f"""
        # System Information
        
        ## Fixed System
        {fixed_system}
        
        ## Backend Components
        {backend_components}
        
        ## Frontend Components
        {frontend_components}
        
        ## Infrastructure Components
        {infrastructure_components}
        
        ## Integrated System
        {integrated_system}
        
        ## Test Results
        {test_results}
        
        # Task
        Create comprehensive documentation including:
        - Overview and system architecture
        - User guide (installation, configuration, usage)
        - API documentation (endpoints, request/response formats)
        - Developer guide (codebase structure, contributing guidelines)
        - Deployment instructions
        - Troubleshooting guide
        
        Format your response as a structured documentation set.
        """
        
        # Get model client
        client = self.get_model_client()
        
        # Generate documentation using the model
        response = self.generate_text(prompt)
        
        # Split the documentation into separate files for different sections
        sections = [
            ("overview", "System Overview", r"# Overview|# System Overview"),
            ("user_guide", "User Guide", r"# User Guide"),
            ("api_documentation", "API Documentation", r"# API Documentation|# API Reference"),
            ("developer_guide", "Developer Guide", r"# Developer Guide|# Development Guide"),
            ("deployment", "Deployment Guide", r"# Deployment|# Deployment Guide|# Deployment Instructions"),
            ("troubleshooting", "Troubleshooting Guide", r"# Troubleshooting|# Troubleshooting Guide")
        ]
        
        # Create a main README
        readme_content = f"# {project_title} Documentation\n\n"
        readme_content += "## Documentation Sections\n\n"
        
        saved_docs = []
        for section_id, section_name, pattern in sections:
            # Try to find the section in the response
            match = re.search(f"({pattern}.*?)(?=# |$)", response, re.DOTALL | re.IGNORECASE)
            if match:
                section_content = match.group(1).strip()
                doc_path = save_documentation(project_dir, section_id, section_content)
                saved_docs.append(str(doc_path))
                readme_content += f"- [{section_name}]({os.path.basename(doc_path)})\n"
            else:
                readme_content += f"- {section_name} (Not available)\n"
        
        # Save the full documentation
        full_doc_path = project_dir / "docs" / "full_documentation.md"
        full_doc_path.parent.mkdir(exist_ok=True)
        with open(full_doc_path, 'w') as f:
            f.write(response)
        saved_docs.append(str(full_doc_path))
        
        # Save the README
        readme_path = project_dir / "README.md"
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        saved_docs.append(str(readme_path))
        
        # Structure the output
        documentation = {
            "timestamp": datetime.now().isoformat(),
            "qa_engineer": self.name,
            "documentation": response,
            "fixed_system": fixed_system,
            "project_title": project_title,
            "project_dir": str(project_dir),
            "documentation_files": saved_docs,
            "readme_path": str(readme_path)
        }
        
        agent_log(
            self.name,
            "execute",
            f"Successfully created system documentation and saved to {project_dir / 'docs'}"
        )
        
        return documentation 