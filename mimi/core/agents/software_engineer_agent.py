"""Software Engineer Agent implementation for MiMi."""

from typing import Any, Dict, List, Optional, Union
import json
import os
from datetime import datetime
from pathlib import Path
import re
import sys

from pydantic import Field

from mimi.core.agents.base_agent import Agent
from mimi.utils.logger import agent_log, logger
from mimi.utils.output_manager import (
    create_output_directory,
    process_implementation_output,
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


class SoftwareEngineerAgent(Agent):
    """Agent that implements software components according to the architecture plan."""
    
    specialty: str = Field("backend", description="Engineer's specialty (backend, frontend, or infrastructure)")
    
    def execute(self, task_input: Any) -> Any:
        """Execute a software engineering task.
        
        Args:
            task_input: The input to the task.
            
        Returns:
            The output from the task.
        """
        agent_log(self.name, "execute", f"Executing task")
        
        # Check if this is a dict with nested input
        if isinstance(task_input, dict) and "input" in task_input and isinstance(task_input["input"], dict):
            # Debug the nested input structure
            logger.debug(f"SoftwareEngineerAgent received nested input with keys: {list(task_input.keys())}")
            logger.debug(f"Inner input has keys: {list(task_input['input'].keys())}")
            
            # Check if project_dir exists at either level
            if "project_dir" in task_input:
                logger.debug(f"PROJECT DEBUG: Found project_dir at top level: {task_input['project_dir']}")
            elif "project_dir" in task_input["input"]:
                logger.debug(f"PROJECT DEBUG: Found project_dir in nested input: {task_input['input']['project_dir']}")
            else:
                logger.debug(f"PROJECT DEBUG: No project_dir found at any level in input")
                
            # Extract the true input from the nested structure
            task_input = task_input["input"]
            logger.debug(f"Using inner input for task with keys: {list(task_input.keys())}")
        
        # Log detailed structure of task input for debugging
        if isinstance(task_input, dict):
            logger.debug(f"SoftwareEngineerAgent({self.specialty.lower()}) received input of type: dict")
            logger.debug(f"SoftwareEngineerAgent input keys: {list(task_input.keys())}")
            
            # Additional detailed logging for project_dir
            if "project_dir" in task_input:
                logger.debug(f"PROJECT DEBUG: Input contains project_dir of type {type(task_input['project_dir'])}: {task_input['project_dir']}")
            elif "project_title" in task_input:
                logger.debug(f"PROJECT DEBUG: Input contains project_title but NO project_dir: {task_input['project_title']}")
            else:
                logger.debug(f"PROJECT DEBUG: Input contains neither project_dir nor project_title")
        else:
            logger.debug(f"SoftwareEngineerAgent({self.specialty.lower()}) received input of type: {type(task_input).__name__}")
            
        try:
            # Get the project directory, creating it if it doesn't exist
            project_title = None
            project_dir = None
            
            if isinstance(task_input, dict):
                # First check for project_title
                if "project_title" in task_input:
                    project_title = task_input["project_title"]
                    logger.debug(f"PROJECT DEBUG: Found project_title in task_input: {project_title}")
                
                # Then check for project_dir
                if "project_dir" in task_input:
                    project_dir = task_input["project_dir"]
                    logger.debug(f"PROJECT DEBUG: Found project_dir in task_input: {project_dir}")
                elif "input" in task_input and isinstance(task_input["input"], dict) and "project_dir" in task_input["input"]:
                    project_dir = task_input["input"]["project_dir"]
                    logger.debug(f"PROJECT DEBUG: Found project_dir in task_input['input']: {project_dir}")
            
            # If we have a project_dir but no title, try to extract title
            if project_dir and not project_title:
                try:
                    # Extract title from directory name
                    dir_name = str(project_dir).split("_", 2)[-1]
                    project_title = dir_name.replace("_", " ")
                    logger.debug(f"PROJECT DEBUG: Extracted project_title from directory: {project_title}")
                except Exception as e:
                    logger.error(f"Error extracting project title from directory: {str(e)}")
                    project_title = "Software Project"
            
            # If we don't have a project title, use a default
            if not project_title:
                project_title = "Software Project"
                logger.debug(f"PROJECT DEBUG: Using default project_title: {project_title}")
            
            # If we don't have a project directory, create one
            if not project_dir:
                logger.debug(f"PROJECT DEBUG: No project_dir provided, creating a new one")
                project_dir = get_project_directory(project_title)
                logger.warning(f"Project directory not provided, creating new one for {project_title}")
            else:
                # Ensure it's a Path object
                if not isinstance(project_dir, Path):
                    project_dir = Path(project_dir)
                    logger.debug(f"PROJECT DEBUG: Converted project_dir to Path: {project_dir}")
                
                logger.info(f"Using existing project directory: {project_dir}")
                
            # Extract more specific input based on the role
            
            # Determine the output to use based on the role
            if self.specialty == "backend":
                # Debug the backend-specific logic
                logger.debug(f"Generating backend implementation...")
                
                # Implement the backend
                implementation_output = self._implement_components(str(task_input), project_dir, project_title)
                
                # The _implement_components method already processes and saves files, so we can return its result directly
                agent_log(self.name, "execute", f"Successfully implemented backend components")
                return implementation_output
                
            elif self.specialty == "frontend":
                # Debug the frontend-specific logic
                logger.debug(f"Generating frontend implementation...")
                
                # Implement the frontend
                implementation_output = self._implement_components(str(task_input), project_dir, project_title)
                
                # The _implement_components method already processes and saves files, so we can return its result directly
                agent_log(self.name, "execute", f"Successfully implemented frontend components")
                return implementation_output
                
            else:
                # Default: Return the task input with added project info
                result = {
                    "status": "success",
                    "message": f"{self.specialty} execution completed",
                    "data": task_input,
                    "project_dir": project_dir,
                    "project_title": project_title
                }
                
                agent_log(self.name, "execute", f"Execution completed with default result")
                return result
                
        except Exception as e:
            error_message = f"Error during execution: {str(e)}"
            agent_log(self.name, "error", error_message)
            
            # Return error information
            return {
                "status": "error",
                "message": error_message,
                "error": str(e),
                "traceback": str(sys.exc_info())
            }

    def _implement_components(self, tasks: str, project_dir: Path, project_title: str) -> Dict[str, Any]:
        """Implement components based on the task plan.
        
        Args:
            tasks: Task descriptions for this engineer's specialty.
            project_dir: Path to the project directory.
            project_title: Title of the project.
            
        Returns:
            A dictionary with the implemented components.
        """
        agent_log(
            self.name,
            "execute",
            f"Implementing {self.specialty} components based on tasks"
        )
        
        # Check if this is a game implementation
        is_game = False
        if "game" in project_title.lower() or "flappy" in project_title.lower() or "flappy" in tasks.lower():
            is_game = True
            
        # Customize prompt based on specialty and project type
        if is_game and self.specialty == "frontend":
            prompt = f"""
            # Frontend Game Implementation Task
            {tasks}
            
            # Project Title
            {project_title}
            
            # Task
            Create a complete, fully functional implementation of the game described in the tasks.
            
            ## Required Files
            You MUST create these exact files with proper names:
            1. `index.html` - The main HTML file with proper doctype, head and body
            2. `game.js` - The main JavaScript game logic
            3. `styles.css` - The CSS styles for the game
            
            ## Implementation Guidelines
            - Create a COMPLETE implementation that works when all files are in the same directory
            - Include proper HTML structure with <!DOCTYPE html>, <html>, <head>, and <body> tags
            - Use canvas for rendering the game
            - Include all necessary game logic (collision detection, scoring, physics)
            - Ensure all files reference each other correctly with proper paths
            - Include clear comments explaining game mechanics
            - Create a polished, visually appealing game
            
            Format your code with proper indentation and structure. Include filename at the beginning of each code block.
            """
        elif self.specialty == "frontend":
            prompt = f"""
            # Frontend Tasks
            {tasks}
            
            # Project Title
            {project_title}
            
            # Task
            Implement complete frontend components that work together. For each component:
            1. Provide the full implementation code (in Markdown code blocks)
            2. Place HTML files in the root directory with proper structure and DOCTYPE
            3. Place CSS files in a 'css' directory and JS files in a 'js' directory
            4. Ensure all files reference each other with the correct paths
            5. Create polished, fully functional UI components
            
            Format your code with proper indentation and structure. Include filename at the beginning of each code block.
            """
        else:
            # Default prompt for other specialties
            prompt = f"""
            # {self.specialty.capitalize()} Tasks
            {tasks}
            
            # Project Title
            {project_title}
            
            # Task
            Implement the {self.specialty} components described in the tasks above. For each component:
            1. Provide the full implementation code (in Markdown code blocks)
            2. Include any necessary configuration files
            3. Add brief comments explaining your implementation decisions
            4. Provide usage examples for key components
            
            Format your code with proper indentation and structure. Include filename at the beginning of each code block.
            """
        
        # Get model client
        client = self.get_model_client()
        
        try:
            # Generate implementation
            logger.debug(f"Generating {self.specialty} implementation...")
            response = self.generate_text(prompt)
            logger.debug(f"Generated implementation, length: {len(response)}")
            
            # Process and save the implementation
            logger.debug(f"Processing implementation output...")
            result = process_implementation_output(project_dir, self.specialty, response)
            logger.debug(f"Saved {len(result.get('saved_files', []))} files")
            
            # Create project log
            log_details = {
                "implementation_doc": result.get("implementation_doc", ""),
                "component_type": self.specialty,
                "saved_files": len(result.get("saved_files", [])),
                "project_title": project_title
            }
            create_or_update_project_log(
                project_dir,
                f"{self.specialty}-implementation",
                self.name,
                f"Implemented {self.specialty} components",
                log_details
            )
            
            # Log to agent.log.md
            self.log_to_agent_file(
                project_dir=project_dir,
                action_type=f"{self.specialty}-implementation",
                input_summary=f"{self.specialty.capitalize()} tasks for {project_title}",
                output_summary=f"Generated {len(result.get('saved_files', []))} {self.specialty} component files",
                details={
                    "implementation_doc": result.get("implementation_doc", ""),
                    "files": [os.path.basename(f) for f in result.get("saved_files", [])][:5]
                }
            )
            
            # For frontend game projects, also create an explicit test example
            if is_game and self.specialty == "frontend":
                # Create a simple README with game instructions
                readme_content = f"""# {project_title}

## How to Run the Game
1. Open `index.html` in your web browser
2. Click or press Space to make the bird flap
3. Avoid hitting the pipes
4. Try to get the highest score possible!

## Files
- `index.html` - Main HTML file
- `game.js` - Game logic and functionality
- `styles.css` - Game styling

Enjoy playing!
"""
                readme_path = project_dir / "README.md"
                with open(readme_path, 'w') as f:
                    f.write(readme_content)
                    
                # Also ensure the main files exist
                for required_file in ["index.html", "js/game.js", "css/styles.css"]:
                    required_path = project_dir / required_file
                    if not required_path.exists():
                        required_path.parent.mkdir(parents=True, exist_ok=True)
                        logger.warning(f"Required file {required_file} not found, creating empty file")
                        with open(required_path, 'w') as f:
                            f.write(f"// {required_file} - Empty placeholder - needs implementation")
            
            # Structure the output
            implementation = {
                "timestamp": datetime.now().isoformat(),
                "engineer": self.name,
                "specialty": self.specialty,
                "implementation": response,
                "files": result.get("saved_files", []),
                "project_title": project_title,
                "project_dir": str(project_dir)
            }
            
            agent_log(
                self.name,
                "execute",
                f"Successfully implemented {self.specialty} components"
            )
            
            return implementation
        except Exception as e:
            error_msg = f"Error in SoftwareEngineerAgent ({self.specialty}): {str(e)}"
            logger.error(error_msg)
            agent_log(self.name, "error", error_msg)
            
            # Check for common error patterns and attempt recovery
            recovered_implementation = None
            
            # Check for permission denied on URLs (common error with //localhost paths)
            if isinstance(e, PermissionError) and "//" in str(e):
                logger.info("Attempting to recover from URL path error...")
                try:
                    # Extract the problematic URL from the error
                    import re
                    url_match = re.search(r"'(//[^']*)'", str(e))
                    if url_match:
                        bad_path = url_match.group(1)
                        fixed_url = "http:" + bad_path
                        logger.info(f"Found bad URL format: {bad_path}, fixing to {fixed_url}")
                        
                        # Modified prompt to emphasize URL format
                        fixed_prompt = prompt + f"""
                        
                        CRITICAL FIX REQUIRED: In your previous attempt, you incorrectly used '{bad_path}' 
                        which was treated as a file path. Always use full URLs with protocol like '{fixed_url}'.
                        """
                        
                        # Regenerate implementation with fixed prompt
                        agent_log(self.name, "recovery", f"Retrying with fixed URL format: {fixed_url}")
                        
                        # Get model client
                        client = self.get_model_client()
                        
                        # Generate implementation with fixed prompt
                        logger.debug(f"Regenerating {self.specialty} implementation with URL fix...")
                        response = self.generate_text(fixed_prompt)
                        
                        # Process and save the implementation
                        logger.debug(f"Processing regenerated implementation output...")
                        result = process_implementation_output(project_dir, self.specialty, response)
                        
                        # Log the recovery
                        recovery_details = {
                            "original_error": str(e),
                            "recovery_action": f"Fixed URL format from '{bad_path}' to '{fixed_url}'",
                            "implementation_doc": result.get("implementation_doc", ""),
                            "component_type": self.specialty,
                            "saved_files": len(result.get("saved_files", [])),
                            "project_title": project_title
                        }
                        
                        create_or_update_project_log(
                            project_dir,
                            "recovery",
                            self.name,
                            f"Recovered from URL format error in {self.specialty} implementation",
                            recovery_details
                        )
                        
                        # Log recovery to agent.log.md
                        self.log_to_agent_file(
                            project_dir=project_dir,
                            action_type="error-recovery",
                            input_summary=f"{self.specialty.capitalize()} tasks for {project_title}",
                            output_summary=f"Recovered from URL format error: '{bad_path}' → '{fixed_url}'",
                            details=recovery_details
                        )
                        
                        # Return recovered implementation
                        recovered_implementation = {
                            "timestamp": datetime.now().isoformat(),
                            "engineer": self.name,
                            "specialty": self.specialty,
                            "implementation": response,
                            "files": result.get("saved_files", []),
                            "project_title": project_title,
                            "project_dir": str(project_dir),
                            "recovery_note": f"Automatically recovered from URL path error: '{bad_path}' → '{fixed_url}'"
                        }
                        
                        agent_log(
                            self.name,
                            "execute",
                            f"Successfully recovered and implemented {self.specialty} components"
                        )
                except Exception as recovery_error:
                    logger.error(f"Recovery attempt failed: {str(recovery_error)}")
                    agent_log(self.name, "error", f"Recovery attempt failed: {str(recovery_error)}")
                    
                    # Log the failed recovery attempt
                    self.log_to_agent_file(
                        project_dir=project_dir,
                        action_type="failed-recovery",
                        input_summary=f"{self.specialty.capitalize()} tasks for {project_title}",
                        output_summary=f"Recovery attempt failed: {str(recovery_error)}",
                        details={
                            "original_error": str(e),
                            "recovery_error": str(recovery_error)
                        }
                    )
            
            # Log the original error to project log if no recovery
            if recovered_implementation is None:
                error_details = {"error_message": str(e)}
                create_or_update_project_log(
                    project_dir,
                    "error",
                    self.name,
                    f"Error during {self.specialty} implementation",
                    error_details
                )
                
                # Log error to agent.log.md
                self.log_to_agent_file(
                    project_dir=project_dir,
                    action_type="error",
                    input_summary=f"{self.specialty.capitalize()} tasks for {project_title}",
                    output_summary=f"Error: {str(e)}",
                    details={"error_type": type(e).__name__}
                )
                
                raise
            
            return recovered_implementation

    def _implement_revisions(self, revision_plan: str, project_dir: Path, project_title: str) -> Dict[str, Any]:
        """Implement revisions based on revision plan.
        
        Args:
            revision_plan: The revision plan from the architect.
            project_dir: The project directory.
            project_title: The project title.
            
        Returns:
            A dictionary with the revised components.
        """
        agent_log(
            self.name,
            "execute",
            f"Implementing revisions for {self.specialty} based on {len(str(revision_plan))} char plan"
        )
        
        # If revision_plan is a dict, try to extract a string version
        if isinstance(revision_plan, dict):
            logger.info("Revision plan is a dictionary, extracting relevant content")
            # Try common keys that might contain the actual revisions
            for key in ["revisions", "revision_plan", "review", "project_review", "changes", "recommendations"]:
                if key in revision_plan and isinstance(revision_plan[key], str):
                    revision_plan = revision_plan[key]
                    logger.info(f"Extracted revision plan from key '{key}'")
                    break
            # If we still have a dict, try to stringify it
            if isinstance(revision_plan, dict):
                revision_plan = str(revision_plan)
                
        # Gather context from the existing codebase
        logger.info("Gathering context from existing codebase")
        
        # Map to appropriate directory
        if self.specialty == "backend":
            component_dir = project_dir / "src" / "server"
            component_type = "backend"
        elif self.specialty == "frontend":
            component_dir = project_dir / "src" / "components" 
            component_type = "frontend"
        elif self.specialty == "infrastructure":
            component_dir = project_dir / "infra"
            component_type = "infrastructure"
        else:
            component_dir = project_dir / "src"
            component_type = "general"
            
        # Create an inventory of existing files to reference
        existing_files = []
        try:
            if component_dir.exists():
                for file_path in component_dir.glob("**/*"):
                    if file_path.is_file():
                        rel_path = file_path.relative_to(project_dir)
                        existing_files.append(str(rel_path))
                
                logger.info(f"Found {len(existing_files)} existing files in {component_type} directory")
                
                # Also search for files in related directories if needed
                if len(existing_files) < 5 and component_type == "backend":
                    # Look in src directory too for backend files
                    src_dir = project_dir / "src"
                    for file_path in src_dir.glob("**/*"):
                        if file_path.is_file() and file_path.parent != component_dir:
                            rel_path = file_path.relative_to(project_dir)
                            existing_files.append(str(rel_path))
        except Exception as e:
            logger.warning(f"Error gathering existing files: {str(e)}")
            
        # Get architecture plan if it exists
        architecture_plan = ""
        arch_path = project_dir / "docs" / "architecture.md"
        if arch_path.exists():
            try:
                with open(arch_path, 'r') as f:
                    architecture_plan = f.read()
                logger.info("Loaded architecture plan from docs/architecture.md")
            except Exception as e:
                logger.warning(f"Error reading architecture plan: {str(e)}")
        
        # Construct the prompt for the model
        prompt = f"""
        # Revision Information
        {revision_plan}
        
        # Architecture Plan
        {architecture_plan}
        
        # Task
        Implement the necessary revisions to the {self.specialty} components of the project.
        
        # Existing Files in the Codebase
        The following files already exist in the codebase:
        {chr(10).join("- " + file for file in existing_files)}
        
        IMPORTANT: When modifying existing files, make sure to use the EXACT filenames listed above.
        When creating new files, follow the naming patterns and directory structure seen in the existing files.
        
        Please provide your implementation, including:
        1. A summary of changes made
        2. Complete file content for any new or significantly modified files
        3. For minor changes, specify which lines were modified and how
        
        Format your code files with triple backticks and include the filename:
        ```
        path/to/filename.ext
        // Code content here
        ```
        """
        
        # Get model client
        client = self.get_model_client()
        
        # Generate revisions using the model
        response = self.generate_text(prompt)
        
        # Process and save the revisions output
        revisions_output = process_implementation_output(
            project_dir, 
            f"{self.specialty}/revisions", 
            response
        )
        
        # Structure the output
        revisions = {
            "timestamp": datetime.now().isoformat(),
            "engineer": self.name,
            "specialty": self.specialty,
            "revised_system": response,
            "revision_plan": revision_plan,
            "project_title": project_title,
            "project_dir": str(project_dir),
            "saved_files": revisions_output["saved_files"]
        }
        
        agent_log(
            self.name,
            "execute",
            f"Successfully implemented revisions for {self.specialty} components and saved to {project_dir / self.specialty / 'revisions'}"
        )
        
        return revisions
    
    def _fix_bugs(self, test_results: str, project_dir: Path, project_title: str) -> Dict[str, Any]:
        """Fix bugs identified in test results."""
        prompt = f"""
        # Test Results
        {test_results}
        
        # Task
        Fix the identified bugs by:
        - Analyzing bugs related to {self.specialty} components
        - For each bug:
          * Describe the root cause
          * Provide the fix with complete file content
          * Explain how the fix resolves the issue
        
        Format your response as a structured bug fix document with complete fixed files.
        For each code file, use the format:
        ```language
        filepath/filename.ext
        // Fixed code content
        ```
        """
        
        # Get model client
        client = self.get_model_client()
        
        # Generate bug fixes using the model
        response = self.generate_text(prompt)
        
        # Process and save the bug fixes output
        fixes_output = process_implementation_output(
            project_dir, 
            f"{self.specialty}/fixes", 
            response
        )
        
        # Structure the output
        fixes = {
            "timestamp": datetime.now().isoformat(),
            "engineer": self.name,
            "specialty": self.specialty,
            "fixed_system": response,
            "test_results": test_results,
            "project_title": project_title,
            "project_dir": str(project_dir),
            "saved_files": fixes_output["saved_files"]
        }
        
        agent_log(
            self.name,
            "execute",
            f"Successfully fixed bugs in {self.specialty} components and saved to {project_dir / self.specialty / 'fixes'}"
        )
        
        return fixes
    
    def _integrate_components(self, components: Dict[str, Any], project_dir: Path, project_title: str) -> Dict[str, Any]:
        """Integrate all components into a complete system."""
        agent_log(
            self.name,
            "execute",
            f"Integrating components for {project_title}"
        )
        
        # Components might be wrapped in our task result format
        backend_components = None
        frontend_components = None 
        infrastructure_components = None
        
        # Log the component structure received
        logger.debug(f"Received components for integration: {list(components.keys())}")
        
        # Try different ways of extracting components
        if isinstance(components, dict):
            # Direct dictionary with component keys
            if "backend_components" in components:
                logger.debug("Found direct backend_components key")
                backend_components = components.get("backend_components", "")
                frontend_components = components.get("frontend_components", "")
                infrastructure_components = components.get("infrastructure_components", "")
            
            # Results dictionary with task names as keys
            elif "backend-implementation" in components:
                logger.debug("Found backend-implementation task key")
                backend_data = components.get("backend-implementation", {})
                frontend_data = components.get("frontend-implementation", {})
                infra_data = components.get("infrastructure-implementation", {})
                
                # Extract data from the results format
                if isinstance(backend_data, dict) and "data" in backend_data:
                    backend_components = backend_data["data"]
                if isinstance(frontend_data, dict) and "data" in frontend_data:
                    frontend_components = frontend_data["data"]
                if isinstance(infra_data, dict) and "data" in infra_data:
                    infrastructure_components = infra_data["data"]
        
        # If components still None, log error
        if backend_components is None or frontend_components is None or infrastructure_components is None:
            logger.error(f"Failed to extract components for integration. Input keys: {list(components.keys())}")
            error_msg = "Missing required components for integration"
            agent_log(self.name, "error", error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "project_title": project_title,
                "project_dir": str(project_dir)
            }
            
        prompt = f"""
        # Component Implementations
        
        ## Backend Components
        {backend_components}
        
        ## Frontend Components
        {frontend_components}
        
        ## Infrastructure Components
        {infrastructure_components}
        
        # Task
        Integrate all components into a complete system by:
        - Describing how components interact with each other
        - Providing configuration for connecting components
        - Documenting the system startup sequence
        - Creating deployment instructions
        - Including a system verification checklist
        
        Format your response as a structured integration document.
        For any new or modified integration files, use the format:
        ```language
        filepath/filename.ext
        // Integration code content
        ```
        """
        
        # Get model client
        client = self.get_model_client()
        
        # Generate integration document using the model
        response = self.generate_text(prompt)
        
        # Save the integration document
        integration_path = project_dir / "integration.md"
        with open(integration_path, 'w') as f:
            f.write(response)
        
        # Extract and save any code blocks from the integration document
        saved_files = save_code_blocks_from_text(project_dir, "integration", response)
        
        # Structure the output
        integrated_system = {
            "timestamp": datetime.now().isoformat(),
            "engineer": self.name,
            "integrated_system": response,
            "backend_components": backend_components,
            "frontend_components": frontend_components,
            "infrastructure_components": infrastructure_components,
            "project_title": project_title,
            "project_dir": str(project_dir),
            "integration_doc": str(integration_path),
            "saved_files": [str(path) for path in saved_files]
        }
        
        agent_log(
            self.name,
            "execute",
            f"Successfully integrated all components into a complete system and saved to {integration_path}"
        )
        
        return integrated_system 