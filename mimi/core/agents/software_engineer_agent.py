"""Software Engineer Agent implementation for MiMi."""

from typing import Any, Dict, List, Optional, Union
import json
import os
from datetime import datetime
from pathlib import Path
import re

from pydantic import Field

from mimi.core.agents.base_agent import Agent
from mimi.utils.logger import agent_log, logger
from mimi.utils.output_manager import (
    create_output_directory,
    process_implementation_output,
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


class SoftwareEngineerAgent(Agent):
    """Agent that implements software components according to the architecture plan."""
    
    specialty: str = Field("backend", description="Engineer's specialty (backend, frontend, or infrastructure)")
    
    def execute(self, task_input: Any) -> Any:
        """Implement software components according to the task plan.
        
        Args:
            task_input: A dictionary containing the task plan and project information.
            
        Returns:
            A dictionary with the implemented components.
        """
        agent_log(
            self.name,
            "execute",
            f"Implementing {self.specialty} components"
        )
        
        # Log the input type for easier debugging
        input_type = type(task_input).__name__
        logger.debug(f"SoftwareEngineerAgent({self.specialty}) received input of type: {input_type}")
        
        # Extract tasks and project information
        project_title = "Unknown Project"
        project_dir_str = None
        
        # Extract project information first for all cases
        if isinstance(task_input, dict):
            # Look for project directory in the direct input
            project_title = task_input.get("project_title", "Unknown Project")
            project_dir_str = task_input.get("project_dir", None)
            
            # Also look for project info in nested results if not found
            if project_dir_str is None:
                # Check all nested dictionaries for project_dir
                for key, value in task_input.items():
                    if isinstance(value, dict):
                        if "project_dir" in value:
                            project_dir_str = value["project_dir"]
                            logger.info(f"Found project_dir in nested key '{key}'")
                        # Also check data field if present
                        elif "data" in value and isinstance(value["data"], dict) and "project_dir" in value["data"]:
                            project_dir_str = value["data"]["project_dir"]
                            logger.info(f"Found project_dir in nested data of key '{key}'")
                            
                        # Extract project title if not already found
                        if project_title == "Unknown Project":
                            if "project_title" in value:
                                project_title = value["project_title"]
                            elif "data" in value and isinstance(value["data"], dict) and "project_title" in value["data"]:
                                project_title = value["data"]["project_title"]
            
            # Log the keys for debugging
            logger.debug(f"SoftwareEngineerAgent input keys: {list(task_input.keys())}")
        elif isinstance(task_input, str) and len(task_input) > 0:
            # If we get a string directly, assume it's a revision plan
            logger.info("SoftwareEngineerAgent received string input, treating as revision plan")
        
        # Get or create project directory
        if project_dir_str:
            project_dir = Path(project_dir_str)
            logger.info(f"Using existing project directory: {project_dir}")
        else:
            project_dir = get_project_directory(project_title)
            logger.warning(f"Project directory not provided, creating new one for {project_title}")
        
        agent_log(
            self.name,
            "execute",
            f"Implementing {self.specialty} components based on tasks"
        )
        
        try:
            # Special handling for integration task - we detect this by checking if we have the right implementation keys
            if (isinstance(task_input, dict) and 
                ("backend-implementation" in task_input or 
                 "frontend-implementation" in task_input or 
                 "infrastructure-implementation" in task_input)):
                
                logger.info("Detected integration task based on input structure")
                
                # Extract components from results dictionary
                backend_components = None
                frontend_components = None
                infrastructure_components = None
                
                # Try to extract the component data
                for key, value in task_input.items():
                    if key == "backend-implementation" and isinstance(value, dict) and "data" in value:
                        backend_components = value["data"]
                    if key == "frontend-implementation" and isinstance(value, dict) and "data" in value:
                        frontend_components = value["data"] 
                    if key == "infrastructure-implementation" and isinstance(value, dict) and "data" in value:
                        infrastructure_components = value["data"]
                
                # If we found components, process as integration task
                if backend_components or frontend_components or infrastructure_components:
                    # Create a components dictionary for the integration method
                    components = {
                        "backend_components": backend_components or {},
                        "frontend_components": frontend_components or {},
                        "infrastructure_components": infrastructure_components or {}
                    }
                    
                    # Call integration method using the shared project directory
                    logger.info(f"Calling _integrate_components with extracted component data")
                    return self._integrate_components(components, project_dir, project_title)
            
            # Determine the action based on input
            if isinstance(task_input, dict):
                # Log key detection for debugging complex inputs
                revision_keys = [k for k in task_input.keys() if 'revision' in k.lower()]
                if revision_keys:
                    logger.debug(f"Found revision-related keys: {revision_keys}")
                
                if "task_plan" in task_input:
                    if "engineer_tasks" in task_input:
                        tasks = task_input["engineer_tasks"].get(self.specialty, task_input["task_plan"])
                    else:
                        tasks = task_input["task_plan"]
                    return self._implement_components(tasks, project_dir, project_title)
                elif "revision_plan" in task_input:
                    revision_plan = task_input["revision_plan"]
                    return self._implement_revisions(revision_plan, project_dir, project_title)
                elif "revisions" in task_input:
                    # Handle case where revision is under a different key name
                    revisions = task_input["revisions"]
                    return self._implement_revisions(revisions, project_dir, project_title)
                elif "architecture_plan" in task_input:
                    # Special case for when revision_plan is contained in the architecture_plan
                    architecture_plan = task_input["architecture_plan"]
                    return self._implement_revisions(architecture_plan, project_dir, project_title)
                elif "test_results" in task_input:
                    # Get test results, which could be a string or a complex object
                    test_results = task_input["test_results"]
                    if isinstance(test_results, dict):
                        # Extract the actual test results string
                        test_results_str = test_results.get("test_results", str(test_results))
                        # If we find an "error" status, use the message
                        if test_results.get("status") == "error":
                            test_results_str = test_results.get("message", test_results_str)
                    else:
                        test_results_str = str(test_results)
                    return self._fix_bugs(test_results_str, project_dir, project_title)
                elif "components" in task_input:
                    return self._integrate_components(task_input["components"], project_dir, project_title)
                # Special case for when we just get a testing result directly
                elif "status" in task_input and task_input.get("status") == "error" and "message" in task_input:
                    test_results_str = task_input.get("message", "Unknown error")
                    return self._fix_bugs(test_results_str, project_dir, project_title)
                # Handle output from AnalystAgent
                elif "status" in task_input and "message" in task_input and "data" in task_input:
                    # Extract requirements from AnalystAgent output
                    if task_input.get("status") == "warning" and "No requirements found" in task_input.get("message", ""):
                        # Create a simple project based on input value
                        if isinstance(task_input["data"], dict) and "input" in task_input["data"]:
                            input_data = task_input["data"]["input"]
                            if isinstance(input_data, dict) and "input" in input_data:
                                project_description = input_data["input"]
                                return self._implement_components(
                                    f"Create a {self.specialty} implementation for: {project_description}",
                                    project_dir, 
                                    project_description[:50] if len(project_description) > 50 else project_description
                                )
                    
                    # If there are requirements_analysis or architecture_recommendations, use those
                    if isinstance(task_input.get("data"), dict):
                        data = task_input["data"]
                        if "requirements_analysis" in data:
                            requirements = data["requirements_analysis"]
                            return self._implement_components(json.dumps(requirements), project_dir, project_title)
                        elif "architecture_recommendations" in data:
                            arch_recommendations = data["architecture_recommendations"]
                            return self._implement_components(json.dumps(arch_recommendations), project_dir, project_title)
                        elif "input" in data and isinstance(data["input"], dict) and "input" in data["input"]:
                            # Fallback to using the raw input
                            project_description = data["input"]["input"]
                            return self._implement_components(
                                f"Create a {self.specialty} implementation for: {project_description}",
                                project_dir, 
                                project_description[:50] if len(project_description) > 50 else project_description
                            )
                # Handle the full accumulated results dictionary
                elif len(task_input) > 3 and "input" in task_input:
                    # Check if this dictionary contains task results
                    task_results = {}
                    test_results = {}
                    
                    # Look for test result keys
                    for key in task_input:
                        if 'test' in key.lower() and isinstance(task_input[key], dict) and 'data' in task_input[key]:
                            test_results[key] = task_input[key]['data']
                    
                    if test_results:
                        # We found test results, handle as bug fixing
                        logger.info(f"Found test results in accumulated task dictionary: {list(test_results.keys())}")
                        return self._fix_bugs(json.dumps(test_results), project_dir, project_title)
                    
                    # Check if we can extract implementation tasks from the accumulated results
                    design_keys = [k for k in task_input.keys() if 'design' in k.lower() or 'architecture' in k.lower()]
                    for key in design_keys:
                        if isinstance(task_input[key], dict) and 'data' in task_input[key]:
                            task_results[key] = task_input[key]['data']
                    
                    if task_results:
                        # We found design/architecture documents, handle as implementation
                        logger.info(f"Found design documents in accumulated task dictionary: {list(task_results.keys())}")
                        design_docs = "\n\n".join([f"## {k}\n{json.dumps(v)}" for k, v in task_results.items()])
                        return self._implement_components(
                            f"Implement {self.specialty} components based on the following designs:\n\n{design_docs}",
                            project_dir, 
                            project_title
                        )
                    
                    # If we still can't determine the task, extract the original input and create something simple
                    input_data = task_input.get("input", {})
                    if isinstance(input_data, dict) and "input" in input_data:
                        project_description = input_data["input"]
                        return self._implement_components(
                            f"Create a {self.specialty} implementation for: {project_description}",
                            project_dir, 
                            project_description[:50] if len(project_description) > 50 else project_description
                        )
                    else:
                        error_msg = f"Unrecognized input format for SoftwareEngineerAgent. Type: {type(task_input).__name__}, Keys: {task_input.keys()}"
                        input_sample = str(task_input)[:500] + "..." if len(str(task_input)) > 500 else str(task_input)
                        logger.error(f"Input sample: {input_sample}")
                        agent_log(self.name, "error", error_msg)
                                
                        # Log the error to the agent file
                        self.log_to_agent_file(
                            project_dir=project_dir,
                            action_type="error",
                            input_summary="Invalid input structure",
                            output_summary=error_msg,
                            details={
                                "error_type": "InputError",
                                "input_type": type(task_input).__name__,
                                "input_keys": list(task_input.keys()),
                                "input_sample": input_sample
                            }
                        )
                        
                        raise ValueError(error_msg)
                # Handle case when project_review is passed from the reviewer and contains revision info
                elif "project_review" in task_input:
                    project_review = task_input["project_review"]
                    return self._implement_revisions(project_review, project_dir, project_title)
                # Check if any key contains revision info as a fallback
                else:
                    # Look for any key that might contain revision information
                    for key, value in task_input.items():
                        if isinstance(value, str) and len(value) > 100:
                            # If we find a reasonably sized string value, check if it looks like a revision plan
                            if "revision" in key.lower() or "review" in key.lower() or "implement" in key.lower():
                                logger.info(f"Using key '{key}' as revision plan")
                                return self._implement_revisions(value, project_dir, project_title)
                            elif "fix" in key.lower() or "bug" in key.lower() or "test" in key.lower():
                                logger.info(f"Using key '{key}' as test results")
                                return self._fix_bugs(value, project_dir, project_title)
            
            # If no specific input format is recognized, but we have project information,
            # check for any revision documents in the project directory and use them
            try:
                # Check multiple possible revision document locations
                revision_files = [
                    project_dir / "docs" / "project_review.md",
                    project_dir / "docs" / "revisions.md",
                    project_dir / "docs" / "review.md",
                    project_dir / "project_review.md"
                ]
                
                for rev_file in revision_files:
                    if rev_file.exists():
                        with open(rev_file, 'r') as f:
                            project_review = f.read()
                        logger.info(f"Using {rev_file.name} for revisions")
                        return self._implement_revisions(project_review, project_dir, project_title)
                
                # If we're here, we should check if there's a README or other documentation that might contain revision info
                potential_docs = [
                    project_dir / "README.md",
                    project_dir / "docs" / "README.md"
                ]
                
                for doc_file in potential_docs:
                    if doc_file.exists():
                        with open(doc_file, 'r') as f:
                            doc_content = f.read()
                        # Check if this document contains revision-like content
                        if "revision" in doc_content.lower() or "improvements" in doc_content.lower() or "changes" in doc_content.lower():
                            logger.info(f"Using {doc_file.name} for revisions")
                            return self._implement_revisions(doc_content, project_dir, project_title)
            except Exception as doc_error:
                logger.warning(f"Failed to read project review document: {str(doc_error)}")
            
            # If we get here, we couldn't figure out what to do
            # Add detailed logging of the input to help diagnose the issue
            input_keys = str(task_input.keys()) if isinstance(task_input, dict) else "N/A"
            input_sample = str(task_input)[:200] + "..." if len(str(task_input)) > 200 else str(task_input)
            
            error_msg = f"Unrecognized input format for SoftwareEngineerAgent. Type: {input_type}, Keys: {input_keys}"
            agent_log(self.name, "error", error_msg)
            logger.error(f"Input sample: {input_sample}")
            
            # Log the error to agent.log.md
            self.log_to_agent_file(
                project_dir=project_dir,
                action_type="error",
                input_summary="Invalid input structure",
                output_summary=error_msg,
                details={
                    "error_type": "InputError",
                    "input_type": input_type,
                    "input_keys": input_keys,
                    "input_sample": input_sample
                }
            )
            
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Error in SoftwareEngineerAgent ({self.specialty}): {str(e)}"
            logger.error(error_msg)
            agent_log(self.name, "error", error_msg)
            raise

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
        
        # Construct the prompt for the model
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