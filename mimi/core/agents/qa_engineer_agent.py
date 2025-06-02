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
    create_or_update_project_log
)


def get_project_directory(project_title: str) -> Path:
    """Get the project directory, creating it if it doesn't exist.
    
    Args:
        project_title: The title of the project.
        
    Returns:
        The path to the project directory.
    """
    # Get caller info for debugging
    import traceback
    stack = traceback.extract_stack()
    caller = stack[-2]  # Get caller info
    logger.debug(f"PROJECT DIR DEBUG: get_project_directory({project_title}) called from {caller.filename}:{caller.lineno}")
    
    # Create a path to the project directory using the output manager
    # This will either create a new directory or find an existing one with the same title
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
                # Log the full input data structure for debugging
                logger.debug(f"QA Lead received input keys: {task_input.keys() if isinstance(task_input, dict) else 'Not a dict'}")
                
                # Look for system_under_test in task_input
                if isinstance(task_input, dict) and "system_under_test" in task_input:
                    return self._test_system(task_input["system_under_test"], task_input, project_dir, project_title)
                # Look for any integrated components
                elif isinstance(task_input, dict) and "integrated_components" in task_input:
                    return self._test_system(task_input["integrated_components"], task_input, project_dir, project_title)
                # Look for implementation field which is commonly used
                elif isinstance(task_input, dict) and "implementation" in task_input:
                    return self._test_system(task_input["implementation"], task_input, project_dir, project_title)
                # Look for data field which might contain the implementation
                elif isinstance(task_input, dict) and "data" in task_input and isinstance(task_input["data"], str):
                    return self._test_system(task_input["data"], task_input, project_dir, project_title)
                # Look for backend_implementation field
                elif isinstance(task_input, dict) and "backend_implementation" in task_input:
                    return self._test_system(task_input["backend_implementation"], task_input, project_dir, project_title)
                # If task_input itself is a string, use it as the implementation
                elif isinstance(task_input, str) and len(task_input) > 100:
                    return self._test_system(task_input, {"input": task_input}, project_dir, project_title)
                # If nothing obvious found, test the entire project directory
                else:
                    # Create a simple representation of the project to test
                    system_to_test = f"Project directory: {project_dir}\n"
                    
                    # Try to find and add index.html content
                    index_path = project_dir / "index.html"
                    if index_path.exists():
                        try:
                            with open(index_path, 'r') as f:
                                index_content = f.read()
                                system_to_test += f"\n# index.html\n{index_content}\n"
                        except Exception as e:
                            logger.error(f"Error reading index.html: {str(e)}")
                    
                    # Try to find and add game.js content
                    game_js_path = project_dir / "js" / "game.js"
                    if game_js_path.exists():
                        try:
                            with open(game_js_path, 'r') as f:
                                js_content = f.read()
                                system_to_test += f"\n# js/game.js\n{js_content}\n"
                        except Exception as e:
                            logger.error(f"Error reading game.js: {str(e)}")
                    
                    # Try to find and add styles.css content
                    css_path = project_dir / "css" / "styles.css"
                    if css_path.exists():
                        try:
                            with open(css_path, 'r') as f:
                                css_content = f.read()
                                system_to_test += f"\n# css/styles.css\n{css_content}\n"
                        except Exception as e:
                            logger.error(f"Error reading styles.css: {str(e)}")
                    
                    logger.info(f"QA Lead testing project directory: {project_dir}")
                    return self._test_system(system_to_test, task_input, project_dir, project_title)
            
            # Standard handling for normal QA Engineers
            # Determine the task type based on input
            if "integrated_system" in task_input:
                # Handle the case where the integrated_system is the whole dictionary
                integrated_system = task_input.get("implementation", "") or task_input.get("integrated_system", "")
                if not integrated_system:
                    # If we still don't have a meaningful value, use the whole thing
                    integrated_system = str(task_input)
                return self._test_system(integrated_system, task_input, project_dir, project_title)
            elif "integrated_frontend" in task_input:
                # Handle frontend QA testing specifically
                integrated_frontend = task_input.get("integrated_frontend", "")
                agent_log(self.name, "execute", f"Testing integrated frontend for {project_title}")
                return self._test_system(integrated_frontend, task_input, project_dir, project_title)
            elif "integrated_backend" in task_input:
                # Handle backend QA testing specifically
                integrated_backend = task_input.get("integrated_backend", "")
                agent_log(self.name, "execute", f"Testing integrated backend for {project_title}")
                return self._test_system(integrated_backend, task_input, project_dir, project_title)
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
        
        # Provide better debugging information
        input_keys = list(task_input.keys()) if isinstance(task_input, dict) else "Not a dict"
        logger.error(f"QA Agent {self.name} failed to parse input. Available keys: {input_keys}")
        
        # Log the error to the agent file
        self.log_to_agent_file(
            project_dir=project_dir,
            action_type="error",
            input_summary="Unrecognized input format",
            output_summary="Failed to parse input for QA testing",
            details={
                "input_type": str(type(task_input)),
                "input_keys": input_keys,
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
        
        # Check if this is a game implementation
        is_game = False
        if "game" in project_title.lower() or "flappy" in project_title.lower() or "flappy" in integrated_system.lower():
            is_game = True
            
        # First, check for specific files that should exist based on project type
        missing_files = []
        
        if is_game:
            # For game projects, check essential files
            essential_files = [
                (project_dir / "index.html", "Main HTML file"),
                (project_dir / "js" / "game.js", "Main game JavaScript"),
                (project_dir / "css" / "styles.css", "Game CSS styles")
            ]
            
            for file_path, description in essential_files:
                if not file_path.exists():
                    missing_files.append(f"{description} ({file_path}) is missing")
                    
            # If critical files are missing, create a specialized test report
            if missing_files:
                logger.warning(f"Found {len(missing_files)} missing files in game implementation")
                test_results = self._generate_missing_files_report(missing_files, project_dir, project_title)
                return test_results
                
        # Construct the main testing prompt based on project type        
        if is_game:
            prompt = f"""
            # Game Implementation Testing
            
            ## Project: {project_title}
            
            ## Test this HTML5 game implementation for bugs and issues:
            {integrated_system}
            
            # Task
            As a QA Engineer, thoroughly test this game implementation by:
            
            1. Checking all required files exist:
               - index.html (must exist at project root)
               - game.js (must handle game logic)
               - styles.css (must style the game elements)
            
            2. Reviewing the implementation for common issues:
               - Missing event handlers
               - Incomplete game logic (collisions, scoring, game over)
               - Incorrect file references
               - Missing or incomplete HTML structure
               - CSS problems or errors
               - Incomplete JavaScript game functionality
            
            3. Specifically for Flappy Bird game:
               - Bird physics implementation
               - Pipe generation and movement
               - Collision detection
               - Scoring mechanism
               - Game over handling
               - Game restart functionality
               - Visual style and aesthetics
            
            ## Format your response as a detailed test report including:
            1. Executive summary (overall assessment)
            2. Detailed findings for each component
            3. Issues categorized by component and severity
            4. Specific fix recommendations for each issue
            5. Suggested improvements
            
            Include actual test code files where appropriate to validate functionality.
            """
        else:
            # Default prompt for non-game implementations
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
        
        # For game projects, create a simple validation test
        if is_game:
            self._create_game_validation_test(project_dir)
        
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
    
    def _generate_missing_files_report(self, missing_files: list, project_dir: Path, project_title: str) -> Dict[str, Any]:
        """Generate a test report specifically for missing essential files.
        
        Args:
            missing_files: List of missing files with descriptions
            project_dir: Project directory path
            project_title: Project title
            
        Returns:
            Dictionary with test results
        """
        # Create a structured report focused on the missing files
        report = f"""# Critical Implementation Issues: Missing Files
        
## Project: {project_title}

## Executive Summary
The implementation is **incomplete** with critical files missing. The game cannot function without these core components.

## Missing Essential Files
{chr(10).join(f"- {file}" for file in missing_files)}

## Recommendations
The implementation needs to be redone with the following structure:

1. `index.html` - Main HTML file at project root:
   - Should include proper DOCTYPE and HTML structure
   - Should link to CSS and JS files correctly
   - Should define the game container (canvas or div elements)

2. `js/game.js` - Main game logic:
   - Game initialization
   - Event handlers for user input
   - Game loop implementation
   - Collision detection
   - Scoring mechanism
   - Game state management

3. `css/styles.css` - Game styling:
   - Game container styling
   - Game element visual properties
   - Responsiveness for different screen sizes

## Required Action
The implementation needs to be completely redone to include all necessary files with proper structure.
"""

        # Save the test results document
        test_results_path = project_dir / "tests" / "test_results.md"
        test_results_path.parent.mkdir(exist_ok=True)
        with open(test_results_path, 'w') as f:
            f.write(report)
            
        # Structure the output
        test_results = {
            "timestamp": datetime.now().isoformat(),
            "qa_engineer": self.name,
            "test_results": report,
            "status": "error",
            "message": "Critical implementation issues: Missing essential files",
            "project_title": project_title,
            "project_dir": str(project_dir),
            "test_results_doc": str(test_results_path),
            "missing_files": missing_files
        }
        
        return test_results
        
    def _create_game_validation_test(self, project_dir: Path) -> None:
        """Create a simple validation test for HTML5 games.
        
        Args:
            project_dir: Project directory path
        """
        validation_js = """// game_validation.test.js
// Simple validation test for HTML5 game implementation

function validateGameImplementation() {
    // Check for essential files
    const files = {
        html: fileExists('index.html'),
        js: fileExists('js/game.js'),
        css: fileExists('css/styles.css')
    };
    
    console.log('File validation:', files);
    
    // Check HTML content
    const htmlContent = readFile('index.html');
    const htmlValidation = {
        hasDoctype: htmlContent.includes('<!DOCTYPE html>'),
        hasCanvas: htmlContent.includes('<canvas') || 
                   (htmlContent.includes('<div') && htmlContent.includes('id="game"')),
        hasScriptLink: htmlContent.includes('src="js/game.js"'),
        hasCssLink: htmlContent.includes('href="css/styles.css"')
    };
    
    console.log('HTML validation:', htmlValidation);
    
    // Check JS content
    const jsContent = readFile('js/game.js');
    const jsValidation = {
        hasEventListeners: jsContent.includes('addEventListener'),
        hasGameLoop: jsContent.includes('requestAnimationFrame') || 
                     jsContent.includes('setInterval'),
        hasCollisionDetection: jsContent.includes('collision') ||
                               jsContent.includes('hit') || 
                               jsContent.includes('intersect'),
        hasScoreTracking: jsContent.includes('score')
    };
    
    console.log('JavaScript validation:', jsValidation);
    
    // Check CSS content
    const cssContent = readFile('css/styles.css');
    const cssValidation = {
        hasBodyStyles: cssContent.includes('body {'),
        hasGameContainerStyles: cssContent.includes('#game') || 
                               cssContent.includes('.game') ||
                               cssContent.includes('canvas')
    };
    
    console.log('CSS validation:', cssValidation);
    
    // Overall validation
    const overallValidation = {
        filesComplete: Object.values(files).every(Boolean),
        htmlComplete: Object.values(htmlValidation).every(Boolean),
        jsComplete: Object.values(jsValidation).every(Boolean),
        cssComplete: Object.values(cssValidation).every(Boolean)
    };
    
    console.log('Overall validation:', overallValidation);
    
    // Helper functions (mocked for simulation)
    function fileExists(path) {
        // In a real test, this would check if the file exists
        console.log(`Checking if ${path} exists`);
        return true; // Mocked result
    }
    
    function readFile(path) {
        // In a real test, this would read file contents
        console.log(`Reading ${path}`);
        return "Mocked file content"; // Mocked result
    }
}

// Execute validation
validateGameImplementation();
"""

        # Save validation test
        validation_path = project_dir / "tests" / "game_validation.test.js"
        validation_path.parent.mkdir(exist_ok=True)
        with open(validation_path, 'w') as f:
            f.write(validation_js)
            
        logger.info(f"Created game validation test at {validation_path}")
    
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