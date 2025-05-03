"""Software Engineer AI Super Agent implementation for MiMi."""

from typing import Any, Dict, List, Optional, Union, Callable
import json
import os
from datetime import datetime
from pathlib import Path
import re

from pydantic import BaseModel, Field, ConfigDict

from mimi.core.agent import Agent
from mimi.utils.logger import agent_log, logger
from mimi.utils.output_manager import (
    create_output_directory,
    process_implementation_output,
    save_documentation, 
    save_code_blocks_from_text,
    save_project_metadata,
    create_or_update_project_log
)

# Add a global variable to track the project directory across agents
_project_directory: Optional[Path] = None

def get_project_directory(project_title: str) -> Path:
    """Get the project directory, creating it if it doesn't exist.
    
    Args:
        project_title: The title of the project.
        
    Returns:
        The path to the project directory.
    """
    global _project_directory
    if _project_directory is None:
        _project_directory = create_output_directory(project_title)
    return _project_directory


class ResearchAnalystAgent(Agent):
    """Agent that analyzes project requirements and prepares specifications."""
    
    def execute(self, task_input: Any) -> Any:
        """Analyze project requirements and prepare detailed specifications.
        
        Args:
            task_input: A dictionary containing project requirements.
            
        Returns:
            A dictionary with detailed project specifications.
        """
        agent_log(
            self.name,
            "execute",
            f"Analyzing project requirements: {task_input.get('input', str(task_input))}"
        )
        
        # Extract requirements from input
        requirements = task_input.get("project_requirements", task_input)
        logger.debug(f"Extracted requirements: {str(requirements)[:200]}...")
        
        # Create system prompt for analyzing requirements
        system_prompt = """
        You are an expert Research Analyst for software projects. Your task is to:
        1. Analyze the given project requirements carefully
        2. Break down the requirements into functional and non-functional components
        3. Identify technical challenges and potential solutions
        4. Prepare a detailed specification document for the architect to use
        
        Provide a comprehensive analysis that will help the architect design the system.
        """
        
        # Construct the prompt for the model
        prompt = f"""
        # Project Requirements
        {requirements}
        
        # Task
        Analyze these requirements and prepare detailed specifications including:
        - Project overview and goals
        - Functional requirements (detailed)
        - Non-functional requirements (performance, security, scalability, etc.)
        - Technical challenges and potential approaches
        - Required technologies and components
        - Any assumptions or constraints
        
        Format your response as a structured specification document.
        """
        
        # Get model client
        client = self.get_model_client()
        logger.debug(f"Got model client: {client.__class__.__name__}")
        
        try:
            # Generate specifications using the model
            logger.debug("Calling model generate() method...")
            response = client.generate(prompt, system_prompt=system_prompt)
            logger.debug(f"Received response from model, length: {len(response)}")
            
            # Extract project title from the response or use a default
            project_title = "Task Management Application"
            title_match = re.search(r'#\s+(.+?)\n', response)
            if title_match:
                project_title = title_match.group(1).strip()
                logger.debug(f"Extracted project title: {project_title}")
            else:
                logger.debug(f"Could not extract project title, using default: {project_title}")
            
            # Get or create project directory
            logger.debug(f"Creating project directory for title: {project_title}")
            project_dir = get_project_directory(project_title)
            
            # Save the specifications to the project directory
            specs_path = project_dir / "docs" / "specifications.md"
            specs_path.parent.mkdir(exist_ok=True)
            logger.debug(f"Writing specifications to: {specs_path}")
            with open(specs_path, 'w') as f:
                f.write(response)
            
            # Save the original requirements
            req_path = project_dir / "docs" / "requirements.md"
            logger.debug(f"Writing requirements to: {req_path}")
            with open(req_path, 'w') as f:
                f.write(str(requirements))
            
            # Save project metadata
            metadata = {
                "project_title": project_title,
                "timestamp": datetime.now().isoformat(),
                "analyst": self.name,
                "specifications_path": str(specs_path),
                "requirements_path": str(req_path)
            }
            logger.debug(f"Saving project metadata: {json.dumps(metadata)[:200]}...")
            save_project_metadata(project_dir, metadata)
            
            # Create project log
            log_details = {
                "specifications_file": str(specs_path),
                "requirements_file": str(req_path),
                "project_title": project_title
            }
            logger.debug("Creating project log file...")
            create_or_update_project_log(
                project_dir,
                "requirements-analysis",
                self.name,
                "Analyzed requirements and created specifications",
                log_details
            )
            
            # Log to agent.log.md
            self.log_to_agent_file(
                project_dir=project_dir,
                action_type="requirements-analysis",
                input_summary=str(requirements)[:200] + "..." if len(str(requirements)) > 200 else str(requirements),
                output_summary=f"Generated specifications document ({len(response)} chars)",
                details={
                    "project_title": project_title,
                    "specifications_file": str(specs_path),
                    "requirements_file": str(req_path)
                }
            )
            
            # Structure the output
            specifications = {
                "timestamp": datetime.now().isoformat(),
                "analyst": self.name,
                "project_specifications": response,
                "original_requirements": requirements,
                "project_title": project_title,
                "project_dir": str(project_dir)
            }
            
            agent_log(
                self.name,
                "execute",
                f"Successfully generated project specifications and saved to {specs_path}"
            )
            
            return specifications
        except Exception as e:
            error_msg = f"Error in ResearchAnalystAgent: {str(e)}"
            logger.error(error_msg)
            agent_log(self.name, "error", error_msg)
            
            # Log the error to project log if we have a project directory
            if 'project_dir' in locals():
                error_details = {"error_message": str(e)}
                create_or_update_project_log(
                    project_dir,
                    "error",
                    self.name,
                    "Error during requirements analysis",
                    error_details
                )
                
                # Log error to agent.log.md
                self.log_to_agent_file(
                    project_dir=project_dir,
                    action_type="error",
                    input_summary=str(requirements)[:100] + "..." if len(str(requirements)) > 100 else str(requirements),
                    output_summary=f"Error: {str(e)}",
                    details={"error_type": type(e).__name__}
                )
            
            raise


class ArchitectAgent(Agent):
    """Agent that creates architecture plans and divides work into tasks."""
    
    def execute(self, task_input: Any) -> Any:
        """Create architecture design or divide work into tasks.
        
        Args:
            task_input: A dictionary containing specifications or architecture plan.
            
        Returns:
            A dictionary with an architecture plan or engineering tasks.
        """
        agent_log(
            self.name,
            "execute",
            f"Creating architecture or task plan"
        )
        
        # Determine the task type based on the input
        if isinstance(task_input, dict) and "stage" in task_input:
            stage = task_input["stage"]
            
            # Execute the appropriate method based on stage
            if stage == "architecture":
                result = self._create_architecture(task_input)
            elif stage == "task_planning":
                result = self._create_task_plan(task_input)
            else:
                error_msg = f"Unknown stage: {stage}"
                agent_log(self.name, "error", error_msg)
                raise ValueError(error_msg)
        else:
            # Default to architecture creation if no stage specified
            result = self._create_architecture(task_input)
        
        return result

    def _create_architecture(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """Create a software architecture plan based on specifications."""
        agent_log(
            self.name,
            "execute",
            f"Creating architecture plan based on specs"
        )
        
        # Get project specifications from input
        specifications = task_input.get("project_specifications", "")
        if not specifications:
            specifications = task_input.get("specs", "")
        if not specifications:
            specifications = str(task_input)
            
        project_title = task_input.get("project_title", "Software Project")
        
        # Get the project directory
        project_dir = get_project_directory(project_title)
            
        # Create system prompt for architecture design
        system_prompt = """
        You are an expert Software Architect. Your task is to:
        1. Analyze the project specifications thoroughly
        2. Design a comprehensive architecture for the system
        3. Choose appropriate technologies and frameworks
        4. Define the major components, their responsibilities, and interactions
        
        Provide a well-structured architecture document that will guide the engineering team.
        
        IMPORTANT: When recommending components and file structure:
        - Specify clear, proper filenames following industry conventions
        - Use consistent naming patterns and appropriate file extensions
        - Recommend standard directory structures that follow best practices
        - Be precise about filenames in your architecture so engineers can implement them exactly
        - If you include example code, ensure filenames are correct and properly referenced
        """
        
        # Construct the prompt for the model
        prompt = f"""
        # Project Specifications
        {specifications}
        
        # Task
        Create a detailed architecture plan including:
        - System overview and architecture style (e.g., microservices, monolith, serverless)
        - Component diagram showing major parts of the system
        - Technology stack selection with justification
        - Data model and storage approach
        - API design and communication patterns
        - Security considerations
        - Deployment strategy
        
        Format your response as a structured architecture document.
        """
        
        # Get model client
        client = self.get_model_client()
        
        try:
            # Generate architecture plan using the model
            response = client.generate(prompt, system_prompt=system_prompt)
            
            # Save the architecture plan to the project directory
            arch_path = project_dir / "docs" / "architecture.md"
            arch_path.parent.mkdir(exist_ok=True)
            with open(arch_path, 'w') as f:
                f.write(response)
            
            # Create project log
            log_details = {
                "architecture_file": str(arch_path),
                "project_title": project_title
            }
            create_or_update_project_log(
                project_dir,
                "architecture-design",
                self.name,
                "Created architecture plan",
                log_details
            )
            
            # Log to agent.log.md
            self.log_to_agent_file(
                project_dir=project_dir,
                action_type="architecture-design",
                input_summary=f"Project specifications for {project_title}",
                output_summary=f"Generated architecture plan ({len(response)} chars)",
                details={
                    "architecture_file": str(arch_path)
                }
            )
            
            # Structure the output
            architecture = {
                "timestamp": datetime.now().isoformat(),
                "architect": self.name,
                "architecture_plan": response,
                "project_title": project_title,
                "project_dir": str(project_dir),
                "stage": "task_planning"  # Set next stage
            }
            
            agent_log(
                self.name,
                "execute",
                f"Successfully generated architecture plan and saved to {arch_path}"
            )
            
            return architecture
        except Exception as e:
            error_msg = f"Error in ArchitectAgent (architecture): {str(e)}"
            logger.error(error_msg)
            agent_log(self.name, "error", error_msg)
            
            # Log the error to project log
            error_details = {"error_message": str(e)}
            create_or_update_project_log(
                project_dir,
                "error",
                self.name,
                "Error during architecture design",
                error_details
            )
            
            # Log error to agent.log.md
            self.log_to_agent_file(
                project_dir=project_dir,
                action_type="error",
                input_summary=f"Project specifications for {project_title}",
                output_summary=f"Error: {str(e)}",
                details={"error_type": type(e).__name__}
            )
            
            raise

    def _create_task_plan(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """Create a task plan based on the architecture.
        
        Args:
            task_input: A dictionary containing the architecture plan.
            
        Returns:
            A dictionary with tasks for each engineer.
        """
        agent_log(
            self.name,
            "execute",
            f"Creating task plan"
        )
        
        # Extract architecture and other metadata
        architecture_plan = task_input.get("architecture_plan", "")
        project_title = task_input.get("project_title", "Unknown Project")
        project_dir_str = task_input.get("project_dir", None)
        
        if project_dir_str:
            project_dir = Path(project_dir_str)
        else:
            logger.warning(f"Project directory not provided, creating new one for {project_title}")
            project_dir = get_project_directory(project_title)
        
        # Create system prompt for task planning
        system_prompt = """
        You are an expert Project Manager dividing work into tasks. Your task is to:
        1. Analyze the architecture plan
        2. Break down the implementation into specific tasks
        3. Assign tasks to appropriate engineering roles (backend, frontend, infrastructure)
        4. Prioritize tasks based on dependencies
        
        Provide a detailed task plan that will guide the engineering team's implementation.
        """
        
        # Construct the prompt for the model
        prompt = f"""
        # Architecture Plan
        {architecture_plan}
        
        # Task
        Create a detailed implementation task plan including:
        - Backend tasks with specific components to implement
        - Frontend tasks with specific components to implement
        - Infrastructure tasks with specific components to implement
        - Priority order and dependencies between tasks
        - Acceptance criteria for each task
        
        Organize tasks by role (backend, frontend, infrastructure).
        """
        
        # Get model client
        client = self.get_model_client()
        
        try:
            # Generate task plan using the model
            response = client.generate(prompt, system_prompt=system_prompt)
            
            # Save the task plan to the project directory
            tasks_path = project_dir / "docs" / "tasks.md"
            tasks_path.parent.mkdir(exist_ok=True)
            with open(tasks_path, 'w') as f:
                f.write(response)
            
            # Create project log
            log_details = {
                "tasks_file": str(tasks_path),
                "project_title": project_title
            }
            create_or_update_project_log(
                project_dir,
                "task-planning",
                self.name,
                "Created implementation tasks",
                log_details
            )
            
            # Log to agent.log.md
            self.log_to_agent_file(
                project_dir=project_dir,
                action_type="task-planning",
                input_summary=f"Architecture plan for {project_title}",
                output_summary=f"Generated task plan ({len(response)} chars)",
                details={
                    "tasks_file": str(tasks_path)
                }
            )
            
            # Structure the output for each engineer
            task_plan = {
                "timestamp": datetime.now().isoformat(),
                "architect": self.name,
                "task_plan": response,
                "project_title": project_title,
                "project_dir": str(project_dir),
                "engineer_tasks": {
                    "backend": self._extract_backend_tasks(response),
                    "frontend": self._extract_frontend_tasks(response),
                    "infrastructure": self._extract_infrastructure_tasks(response)
                }
            }
            
            agent_log(
                self.name,
                "execute",
                f"Successfully generated task plan and saved to {tasks_path}"
            )
            
            return task_plan
        except Exception as e:
            error_msg = f"Error in ArchitectAgent (task planning): {str(e)}"
            logger.error(error_msg)
            agent_log(self.name, "error", error_msg)
            
            # Log the error to project log
            error_details = {"error_message": str(e)}
            create_or_update_project_log(
                project_dir,
                "error",
                self.name,
                "Error during task planning",
                error_details
            )
            
            # Log error to agent.log.md
            self.log_to_agent_file(
                project_dir=project_dir,
                action_type="error",
                input_summary=f"Architecture plan for {project_title}",
                output_summary=f"Error: {str(e)}",
                details={"error_type": type(e).__name__}
            )
            
            raise
            
    def _extract_backend_tasks(self, task_plan: str) -> str:
        """Extract backend tasks from the task plan.
        
        Args:
            task_plan: The full task plan.
            
        Returns:
            The backend-specific tasks.
        """
        # Simple extraction based on headers or sections
        backend_section = ""
        in_backend = False
        
        for line in task_plan.split('\n'):
            if re.search(r'#+ .*backend', line, re.IGNORECASE):
                in_backend = True
                backend_section += line + '\n'
            elif in_backend and re.search(r'#+ .*frontend|#+ .*infrastructure', line, re.IGNORECASE):
                in_backend = False
            elif in_backend:
                backend_section += line + '\n'
        
        return backend_section if backend_section else task_plan

    def _extract_frontend_tasks(self, task_plan: str) -> str:
        """Extract frontend tasks from the task plan.
        
        Args:
            task_plan: The full task plan.
            
        Returns:
            The frontend-specific tasks.
        """
        # Simple extraction based on headers or sections
        frontend_section = ""
        in_frontend = False
        
        for line in task_plan.split('\n'):
            if re.search(r'#+ .*frontend', line, re.IGNORECASE):
                in_frontend = True
                frontend_section += line + '\n'
            elif in_frontend and re.search(r'#+ .*backend|#+ .*infrastructure', line, re.IGNORECASE):
                in_frontend = False
            elif in_frontend:
                frontend_section += line + '\n'
        
        return frontend_section if frontend_section else task_plan

    def _extract_infrastructure_tasks(self, task_plan: str) -> str:
        """Extract infrastructure tasks from the task plan.
        
        Args:
            task_plan: The full task plan.
            
        Returns:
            The infrastructure-specific tasks.
        """
        # Simple extraction based on headers or sections
        infra_section = ""
        in_infra = False
        
        for line in task_plan.split('\n'):
            if re.search(r'#+ .*infrastructure|#+ .*devops', line, re.IGNORECASE):
                in_infra = True
                infra_section += line + '\n'
            elif in_infra and re.search(r'#+ .*backend|#+ .*frontend', line, re.IGNORECASE):
                in_infra = False
            elif in_infra:
                infra_section += line + '\n'
        
        return infra_section if infra_section else task_plan


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
        
        # Special handling for integration task - we detect this by checking if we're agent-1 and 
        # receiving a complex dictionary with the right implementation keys
        if (isinstance(task_input, dict) and 
            "backend-implementation" in task_input and 
            "frontend-implementation" in task_input and 
            "infrastructure-implementation" in task_input):
            
            logger.info("Detected integration task based on input structure")
            
            # Extract components from results dictionary
            backend_components = None
            frontend_components = None
            infrastructure_components = None
            
            # Try to extract the component data
            for key, value in task_input.items():
                if key == "backend-implementation" and isinstance(value, dict) and "data" in value:
                    backend_components = value["data"]
                    # Try to get project info
                    if isinstance(backend_components, dict):
                        project_title = backend_components.get("project_title", project_title)
                        project_dir_str = backend_components.get("project_dir", project_dir_str)
                
                if key == "frontend-implementation" and isinstance(value, dict) and "data" in value:
                    frontend_components = value["data"] 
                    # Try to get project info
                    if isinstance(frontend_components, dict):
                        project_title = frontend_components.get("project_title", project_title)
                        project_dir_str = frontend_components.get("project_dir", project_dir_str)
                
                if key == "infrastructure-implementation" and isinstance(value, dict) and "data" in value:
                    infrastructure_components = value["data"]
                    # Try to get project info
                    if isinstance(infrastructure_components, dict):
                        project_title = infrastructure_components.get("project_title", project_title)
                        project_dir_str = infrastructure_components.get("project_dir", project_dir_str)
            
            # If we found all components, process as integration task
            if backend_components and frontend_components and infrastructure_components:
                # Get project directory if available
                if project_dir_str:
                    project_dir = Path(project_dir_str)
                else:
                    logger.warning(f"Project directory not found in integration task components, creating new one for {project_title}")
                    project_dir = get_project_directory(project_title)
                
                # Create a clean components dictionary for the integration method
                components = {
                    "backend_components": backend_components,
                    "frontend_components": frontend_components,
                    "infrastructure_components": infrastructure_components
                }
                
                # Call integration method
                logger.info(f"Calling _integrate_components with extracted component data")
                return self._integrate_components(components, project_dir, project_title)
        
        # Original handling for other cases
        if isinstance(task_input, dict):
            project_title = task_input.get("project_title", "Unknown Project")
            project_dir_str = task_input.get("project_dir", None)
            
            # Log the keys for debugging
            logger.debug(f"SoftwareEngineerAgent input keys: {list(task_input.keys())}")
        elif isinstance(task_input, str) and len(task_input) > 0:
            # If we get a string directly, assume it's a revision plan
            logger.info("SoftwareEngineerAgent received string input, treating as revision plan")
            project_dir_str = get_project_directory(project_title)
            return self._implement_revisions(task_input, project_dir_str, project_title)
        
        if project_dir_str:
            project_dir = Path(project_dir_str)
        else:
            logger.warning(f"Project directory not provided, creating new one for {project_title}")
            project_dir = get_project_directory(project_title)
        
        agent_log(
            self.name,
            "execute",
            f"Implementing {self.specialty} components based on tasks"
        )
        
        try:
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
        
        # Determine the role-specific system prompt
        if self.specialty == "backend":
            system_prompt = """
            You are an expert Backend Engineer implementing server-side components. Your task is to:
            1. Create robust, maintainable backend code according to the task requirements
            2. Implement RESTful APIs, database models, and business logic
            3. Follow best practices for security, error handling, and performance
            4. Document your code and API endpoints
            
            Provide clear, well-structured implementation with proper error handling.
            
            IMPORTANT: When referencing URLs, always use the full form with protocol (http:// or https://), 
            never use //hostname notation as this might be confused with file paths. Example: use 
            'https://example.com' not '//example.com'.
            
            CRITICAL: Always use correct and precise filenames:
            - Use conventional and standard filenames (e.g., 'index.html', 'server.js', 'app.py')
            - Be consistent with extensions (.js for JavaScript, .py for Python, etc.)
            - Avoid special characters, spaces, or unusual prefixes in filenames
            - Each code block must have a clear, appropriate filename
            - Use lowercase for filenames unless the language convention requires otherwise
            - Follow standard naming conventions for the language (e.g., snake_case for Python, camelCase for JavaScript)
            - Use clear, descriptive names that indicate the file's purpose
            """
        elif self.specialty == "frontend":
            system_prompt = """
            You are an expert Frontend Engineer implementing client-side components. Your task is to:
            1. Create clean, maintainable frontend code according to the task requirements
            2. Implement user interfaces with appropriate HTML, CSS, and JavaScript
            3. Follow best practices for responsive design, accessibility, and performance
            4. Ensure consistent styling and user experience
            
            Provide clear, well-structured implementation with proper error handling and user feedback.
            
            CRITICAL: Always use correct and precise filenames:
            - Use conventional and standard filenames (e.g., 'index.html', 'styles.css', 'app.js')
            - Be consistent with extensions (.js for JavaScript, .css for CSS, .html for HTML)
            - Avoid special characters, spaces, or unusual prefixes in filenames
            - Each code block must have a clear, appropriate filename
            - Use lowercase for filenames unless the language convention requires otherwise
            - Use standard directory structure if creating multiple files (e.g., css/, js/, img/ folders)
            - Main HTML file should be named 'index.html' for web applications
            - Component files should follow framework conventions if applicable (e.g., 'Header.jsx' for React)
            """
        elif self.specialty == "infrastructure":
            system_prompt = """
            You are an expert Infrastructure Engineer implementing DevOps and deployment components. Your task is to:
            1. Create reliable, maintainable infrastructure code according to the task requirements
            2. Implement deployment scripts, configuration files, and CI/CD pipelines
            3. Follow best practices for security, scalability, and reliability
            4. Document your configuration and deployment processes
            
            Provide clear, well-structured implementation with proper error handling and logging.
            
            CRITICAL: Always use correct and precise filenames:
            - Use conventional and standard filenames (e.g., 'Dockerfile', 'docker-compose.yml', 'deploy.sh')
            - Be consistent with extensions (.yml for YAML, .sh for shell scripts, .tf for Terraform)
            - Avoid special characters, spaces, or unusual prefixes in filenames
            - Each code block must have a clear, appropriate filename
            - Config files should follow tool conventions (e.g., 'nginx.conf', '.github/workflows/deploy.yml')
            - Use lowercase for filenames unless the tool convention requires otherwise
            - Script files should include appropriate extensions and permissions
            """
        else:
            system_prompt = """
            You are an expert Software Engineer implementing components according to the task requirements.
            Create clean, maintainable, and well-documented code that follows best practices.
            
            CRITICAL: Always use correct and precise filenames:
            - Use conventional and standard filenames for your file type
            - Be consistent with file extensions appropriate for the language/technology
            - Avoid special characters, spaces, or unusual prefixes in filenames
            - Each code block must have a clear, appropriate filename
            - Use lowercase for filenames unless the convention requires otherwise
            - Follow naming conventions standard for the language/framework you're using
            """
        
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
            response = client.generate(prompt, system_prompt=system_prompt)
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
                        
                        # Modified system prompt to emphasize URL format
                        fixed_system_prompt = system_prompt + f"""
                        
                        CRITICAL FIX REQUIRED: In your previous attempt, you incorrectly used '{bad_path}' 
                        which was treated as a file path. Always use full URLs with protocol like '{fixed_url}'.
                        """
                        
                        # Regenerate implementation with fixed prompt
                        agent_log(self.name, "recovery", f"Retrying with fixed URL format: {fixed_url}")
                        
                        # Get model client
                        client = self.get_model_client()
                        
                        # Generate implementation with fixed prompt
                        logger.debug(f"Regenerating {self.specialty} implementation with URL fix...")
                        response = client.generate(prompt, system_prompt=fixed_system_prompt)
                        
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
        
        # Create appropriate system prompt for revisions
        if self.specialty == "backend":
            system_prompt = """
            You are an expert Backend Engineer implementing revisions to server-side components. Your task is to:
            1. Analyze the revision plan carefully
            2. Update or create backend code to address the required changes
            3. Ensure changes maintain or improve code quality and performance
            4. Document what changes you've made and why
            
            Provide a comprehensive implementation of the required revisions.
            
            CRITICAL: When modifying or creating files:
            - Use EXACT filenames that already exist in the codebase when modifying existing files
            - Follow the established project structure and naming conventions for new files
            - Maintain consistency with existing file extensions and naming patterns
            - Provide complete file contents when changes are substantial
            - For minor changes, clearly indicate which parts of the file are being modified
            """
        elif self.specialty == "frontend":
            system_prompt = """
            You are an expert Frontend Engineer implementing revisions to client-side components. Your task is to:
            1. Analyze the revision plan carefully
            2. Update or create frontend code to address the required changes
            3. Ensure changes maintain or improve UI/UX and performance
            4. Document what changes you've made and why
            
            Provide a comprehensive implementation of the required revisions.
            
            CRITICAL: When modifying or creating files:
            - Use EXACT filenames that already exist in the codebase when modifying existing files
            - Follow the established project structure and naming conventions for new files
            - Maintain consistency with existing file extensions and naming patterns
            - Provide complete file contents when changes are substantial
            - For minor changes, clearly indicate which parts of the file are being modified
            - Ensure HTML, CSS, and JavaScript files properly reference each other
            """
        elif self.specialty == "infrastructure":
            system_prompt = """
            You are an expert Infrastructure Engineer implementing revisions to deployment components. Your task is to:
            1. Analyze the revision plan carefully
            2. Update or create infrastructure code to address the required changes
            3. Ensure changes maintain or improve reliability and security
            4. Document what changes you've made and why
            
            Provide a comprehensive implementation of the required revisions.
            
            CRITICAL: When modifying or creating files:
            - Use EXACT filenames that already exist in the codebase when modifying existing files
            - Follow the established project structure and naming conventions for new files
            - Maintain consistency with existing file extensions and naming patterns
            - Provide complete file contents when changes are substantial
            - For minor changes, clearly indicate which parts of the file are being modified
            - Ensure configuration files follow the correct format and syntax
            """
        else:
            system_prompt = """
            You are an expert Software Engineer implementing revisions. Your task is to:
            1. Analyze the revision plan carefully
            2. Update or create code to address the required changes
            3. Ensure changes maintain or improve code quality
            4. Document what changes you've made and why
            
            Provide a comprehensive implementation of the required revisions.
            
            CRITICAL: When modifying or creating files:
            - Use EXACT filenames that already exist in the codebase when modifying existing files
            - Follow the established project structure and naming conventions for new files
            - Maintain consistency with existing file extensions and naming patterns
            - Provide complete file contents when changes are substantial
            - For minor changes, clearly indicate which parts of the file are being modified
            """
        
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
        response = client.generate(prompt, system_prompt=system_prompt)
        
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
        system_prompt = f"""
        You are an expert {self.specialty.capitalize()} Engineer. Your task is to:
        1. Review the test results and identified bugs
        2. Fix the issues in the {self.specialty} components
        3. Document the fixes applied
        
        Focus on resolving all identified issues while maintaining code quality.
        When providing code fixes, include complete file content and use this format:
        ```language
        filepath/filename.ext
        // Fixed code goes here
        ```
        """
        
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
        response = client.generate(prompt, system_prompt=system_prompt)
        
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
            
        system_prompt = """
        You are an expert Software Integration Engineer. Your task is to:
        1. Review all component implementations (backend, frontend, infrastructure)
        2. Integrate them into a cohesive system
        3. Document the integration process and configuration
        4. Provide instructions for deploying and running the system
        
        Focus on ensuring all components work together seamlessly.
        If you need to create or modify any configuration or connection files, use this format:
        ```language
        filepath/filename.ext
        // Integration code goes here
        ```
        """
        
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
        response = client.generate(prompt, system_prompt=system_prompt)
        
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
        
        # Get the project directory from the input
        project_title = None
        project_dir_str = None
        
        if isinstance(task_input, dict):
            project_title = task_input.get("project_title", "Software Project")
            project_dir_str = task_input.get("project_dir", None)
        
            # Get the project directory
            if project_dir_str:
                project_dir = Path(project_dir_str)
            else:
                project_dir = get_project_directory(project_title)
            
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
        
        # Default error case if we get here
        agent_log(self.name, "error", "Unrecognized input format")
        
        # Try to create a meaningful project directory for logging the error
        if not project_title:
            project_title = "Unknown Project"
        if not project_dir_str:
            project_dir = get_project_directory(project_title)
        
        # Log the error to the agent file
        self.log_to_agent_file(
            project_dir=project_dir,
            action_type="error",
            input_summary="Unrecognized input format",
            output_summary="Failed to parse input for QA testing",
            details={"input_type": str(type(task_input))}
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
        
        # Create system prompt for testing
        system_prompt = """
        You are an expert QA Engineer responsible for testing software. Your task is to:
        1. Analyze the integrated system to identify bugs, errors, and issues
        2. Test for functionality, performance, edge cases, and user experience
        3. Document each issue with clear steps to reproduce
        4. Prioritize issues by severity and impact
        
        Provide a thorough test report that will help engineers fix the identified issues.
        
        CRITICAL: When writing test files or referencing existing files:
        - Use precise, correct filenames that match exactly what's in the codebase
        - Maintain consistent file extensions appropriate for the test type
        - Follow established naming conventions for test files (e.g., 'test_*.py', '*_test.js')
        - Ensure test files reference the correct paths to implementation files
        - Be explicit about which file each test is targeting
        - Place test files in appropriate test directories matching project structure
        """
        
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
        response = client.generate(prompt, system_prompt=system_prompt)
        
        # Save the test results document
        test_results_path = project_dir / "tests" / "test_results.md"
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
        
        system_prompt = """
        You are an expert Technical Documentation Specialist. Your task is to:
        1. Review the fixed system and all available information
        2. Create comprehensive documentation for the system
        3. Include user guides, API documentation, and deployment instructions
        4. Ensure the documentation is clear, complete, and well-structured
        
        Focus on making the documentation useful for both users and developers.
        """
        
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
        response = client.generate(prompt, system_prompt=system_prompt)
        
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


class ReviewerAgent(Agent):
    """Agent that reviews and evaluates the final project."""
    
    def execute(self, task_input: Any) -> Any:
        """Review the project against initial requirements.
        
        Args:
            task_input: A dictionary containing documentation or revised system.
            
        Returns:
            A dictionary with project review or final approval.
        """
        
        
        # Get the project directory from the input
        project_title = task_input.get("project_title", "Software Project")
        project_dir_str = task_input.get("project_dir", None)
        
        agent_log(
            self.name,
            "execute",
            f"Reviewing project: {project_title}"
        )

        # Get the project directory
        if project_dir_str:
            project_dir = Path(project_dir_str)
        else:
            project_dir = get_project_directory(project_title)
        
        # Determine the review type and focus based on agent's role
        review_focus = "general"
        if hasattr(self, 'role'):
            role_lower = self.role.lower()
            if "backend" in role_lower:
                review_focus = "backend"
            elif "frontend" in role_lower:
                review_focus = "frontend"
            elif "infrastructure" in role_lower:
                review_focus = "infrastructure"
        
        logger.debug(f"ReviewerAgent role: {getattr(self, 'role', 'unknown')}, focus: {review_focus}")
        
        # Determine if this is a specialized component review, a consolidated review, or final approval
        if "documentation" in task_input:
            documentation = task_input.get("documentation", "")
            
            # Check if we have component reviews already available (for consolidation)
            has_component_reviews = any(k for k in task_input.keys() if k.endswith('_review') and k != 'project_review')
            
            if has_component_reviews:
                # Consolidate component reviews
                return self._consolidate_reviews(documentation, task_input, project_dir, project_title)
            else:
                # Do a specialized component review
                return self._review_component(documentation, task_input, project_dir, project_title, review_focus)
        elif "revised_system" in task_input:
            revised_system = task_input.get("revised_system", "")
            return self._final_approval(revised_system, task_input, project_dir, project_title)
        elif "integrated_fixes" in task_input:
            integrated_fixes = task_input.get("integrated_fixes", "")
            return self._final_approval(integrated_fixes, task_input, project_dir, project_title)
        else:
            agent_log(self.name, "error", "Unrecognized input format")
            return {
                "status": "error",
                "message": "Unrecognized input format for reviewer agent",
                "input_keys": list(task_input.keys())
            }
    
    def _review_component(self, documentation: str, full_input: Dict[str, Any], project_dir: Path, project_title: str, component_type: str) -> Dict[str, Any]:
        """Review a specific component type against requirements."""
        # Try to find original requirements from the task chain
        original_requirements = ""
        for key in full_input:
            if key == "original_requirements":
                original_requirements = full_input[key]
                break
        
        # Define component-specific system prompts
        component_prompts = {
            "backend": """
            You are an expert Backend Reviewer specializing in server-side components. Your task is to:
            1. Review the backend components against requirements and best practices
            2. Evaluate code quality, API design, data handling, and security
            3. Identify any performance bottlenecks or scalability issues
            4. Assess database design and query optimization
            5. Check error handling and logging approaches
            
            Focus on providing detailed feedback specific to backend components.
            """,
            "frontend": """
            You are an expert Frontend Reviewer specializing in client-side components. Your task is to:
            1. Review the frontend components against requirements and best practices
            2. Evaluate UI/UX design, responsiveness, and accessibility
            3. Assess component structure, state management, and data flow
            4. Check for proper error handling and user feedback
            5. Review performance optimizations and load times
            
            Focus on providing detailed feedback specific to frontend components.
            """,
            "infrastructure": """
            You are an expert Infrastructure Reviewer specializing in deployment and DevOps. Your task is to:
            1. Review the infrastructure components against requirements and best practices
            2. Evaluate deployment processes, CI/CD pipelines, and automation
            3. Assess security configurations, monitoring, and logging
            4. Check scalability, high availability, and disaster recovery
            5. Review environment configuration and management
            
            Focus on providing detailed feedback specific to infrastructure components.
            """,
            "general": """
            You are an expert Project Reviewer. Your task is to:
            1. Review the project documentation against the initial requirements
            2. Evaluate the project's completeness, quality, and adherence to requirements
            3. Identify any gaps, issues, or areas for improvement
            4. Provide a detailed assessment of the project
            
            Focus on being thorough and critical to ensure the project meets all requirements.
            """
        }
        
        system_prompt = component_prompts.get(component_type, component_prompts["general"])
        
        # Construct component-specific prompt
        prompt = f"""
        # Project Documentation
        {documentation}
        
        # Original Requirements
        {original_requirements}
        
        # Task
        Review the {component_type} components by:
        - Assessing how well they meet relevant requirements
        - Evaluating code quality, architecture, and implementation
        - Identifying any gaps, bugs, or missing features
        - Noting potential issues specific to {component_type}
        - Suggesting improvements or enhancements
        - Providing an overall assessment of the {component_type} components
        
        Format your response as a structured review document focusing specifically on {component_type} components.
        """
        
        # Get model client
        client = self.get_model_client()
        
        # Generate review using the model
        response = client.generate(prompt, system_prompt=system_prompt)
        
        # Save the review document
        review_filename = f"{component_type}_review.md"
        review_path = project_dir / "docs" / review_filename
        with open(review_path, 'w') as f:
            f.write(response)
        
        # Structure the output
        review = {
            "timestamp": datetime.now().isoformat(),
            "reviewer": self.name,
            f"{component_type}_review": response,
            "documentation": documentation,
            "original_requirements": original_requirements,
            "project_title": project_title,
            "project_dir": str(project_dir),
            "review_path": str(review_path),
            "component_type": component_type
        }
        
        agent_log(
            self.name,
            "execute",
            f"Successfully reviewed the {component_type} components and saved review to {review_path}"
        )
        
        return review
    
    def _consolidate_reviews(self, documentation: str, full_input: Dict[str, Any], project_dir: Path, project_title: str) -> Dict[str, Any]:
        """Consolidate component reviews into a comprehensive project review."""
        # Extract component reviews
        backend_review = full_input.get("backend_review", "")
        frontend_review = full_input.get("frontend_review", "")
        infrastructure_review = full_input.get("infrastructure_review", "")
        
        # Try to find original requirements
        original_requirements = full_input.get("original_requirements", "")
        
        system_prompt = """
        You are an expert Project Review Consolidator. Your task is to:
        1. Analyze separate reviews of backend, frontend, and infrastructure components
        2. Identify common themes, issues, and strengths across components
        3. Create a comprehensive project-level review that addresses system-wide concerns
        4. Prioritize issues and improvements based on severity and impact
        
        Focus on creating a balanced, thorough assessment that addresses how the components work together.
        """
        
        prompt = f"""
        # Component Reviews
        
        ## Backend Review
        {backend_review}
        
        ## Frontend Review
        {frontend_review}
        
        ## Infrastructure Review
        {infrastructure_review}
        
        # Project Documentation
        {documentation}
        
        # Original Requirements
        {original_requirements}
        
        # Task
        Consolidate these component reviews into a comprehensive project review by:
        - Summarizing key findings from all component reviews
        - Identifying cross-cutting concerns that affect multiple components
        - Evaluating how well components integrate with each other
        - Assessing overall project quality and alignment with requirements
        - Prioritizing issues by severity and providing actionable recommendations
        - Creating a final assessment (acceptable, needs minor revisions, needs major revisions)
        
        Format your response as a structured consolidated review document.
        """
        
        # Get model client
        client = self.get_model_client()
        
        # Generate consolidated review using the model
        response = client.generate(prompt, system_prompt=system_prompt)
        
        # Save the consolidated review document
        review_path = project_dir / "docs" / "project_review.md"
        with open(review_path, 'w') as f:
            f.write(response)
        
        # Structure the output
        review = {
            "timestamp": datetime.now().isoformat(),
            "reviewer": self.name,
            "project_review": response,
            "backend_review": backend_review,
            "frontend_review": frontend_review,
            "infrastructure_review": infrastructure_review,
            "documentation": documentation,
            "original_requirements": original_requirements,
            "project_title": project_title,
            "project_dir": str(project_dir),
            "review_path": str(review_path)
        }
        
        agent_log(
            self.name,
            "execute",
            f"Successfully consolidated component reviews into a project review and saved to {review_path}"
        )
        
        return review
    
    def _final_approval(self, revised_system: str, full_input: Dict[str, Any], project_dir: Path, project_title: str) -> Dict[str, Any]:
        """Final review of the project after revisions."""
        # Try to find original requirements and previous review
        original_requirements = full_input.get("original_requirements", "")
        project_review = full_input.get("project_review", "")
        
        # Log what we have for debugging
        logger.debug(f"Final approval input keys: {list(full_input.keys())}")
        
        system_prompt = """
        You are an expert Project Reviewer conducting a final assessment. Your task is to:
        1. Review the revised system against the original project review feedback
        2. Determine if all issues and gaps have been addressed
        3. Make a final approval decision on the project
        4. Provide a detailed assessment of the final state
        
        Focus on determining if the project now meets all requirements and is ready for delivery.
        """
        
        prompt = f"""
        # Revised System
        {revised_system}
        
        # Original Project Review
        {project_review}
        
        # Original Requirements
        {original_requirements}
        
        # Task
        Conduct a final review by:
        - Assessing how well the revisions address previous feedback
        - Verifying that all identified issues have been resolved
        - Evaluating if the project now meets all requirements
        - Making a final approval decision (approved, conditionally approved, rejected)
        - Providing a detailed justification for your decision
        
        Format your response as a structured final approval document.
        """
        
        # Get model client
        client = self.get_model_client()
        
        try:
            # Generate final approval using the model
            response = client.generate(prompt, system_prompt=system_prompt)
            
            # Save the final approval document
            approval_path = project_dir / "docs" / "final_approval.md"
            with open(approval_path, 'w') as f:
                f.write(response)
            
            # Structure the output
            final_approval = {
                "timestamp": datetime.now().isoformat(),
                "reviewer": self.name,
                "final_approval": response,
                "revised_system": revised_system,
                "project_review": project_review,
                "original_requirements": original_requirements,
                "project_title": project_title,
                "project_dir": str(project_dir),
                "approval_path": str(approval_path)
            }
            
            agent_log(
                self.name,
                "execute",
                f"Successfully completed final review and saved to {approval_path}"
            )
            
            return final_approval
            
        except Exception as e:
            error_msg = f"Error generating final approval: {str(e)}"
            agent_log(self.name, "error", error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "final_approval": error_msg
            }