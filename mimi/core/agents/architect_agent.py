"""Architect Agent implementation for MiMi."""

from datetime import datetime
from pathlib import Path
import re
from typing import Any

from mimi.core.agents.base_agent import Agent
from mimi.utils.logger import agent_log, logger
from mimi.utils.output_manager import (
    create_output_directory,
    save_code_blocks_from_text,
    create_or_update_project_log
)


def get_project_directory(project_title: str, existing_dir: Path = None) -> Path:
    """Get the project directory, creating it if it doesn't exist.
    
    Args:
        project_title: The title of the project.
        existing_dir: An existing project directory to use instead of creating a new one.
        
    Returns:
        The path to the project directory.
    """
    # Get caller info for debugging
    import traceback
    stack = traceback.extract_stack()
    caller = stack[-2]  # Get caller info
    logger.debug(f"PROJECT DIR DEBUG: get_project_directory({project_title}) called from {caller.filename}:{caller.lineno}")
    
    # If an existing directory is provided, use it
    if existing_dir:
        logger.debug(f"Using existing project directory: {existing_dir}")
        return existing_dir
    
    # Create a path to the project directory using the output manager
    # This will create a new directory with the given title
    return create_output_directory(project_title)


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
        
        # Extract project information first
        project_title = "Software Project"
        project_dir_str = None
        
        if isinstance(task_input, dict):
            # Try to extract project information from various places
            project_title = task_input.get("project_title", "Software Project")
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
        
        # Get or create the project directory
        if project_dir_str:
            project_dir = Path(project_dir_str)
            logger.info(f"Using existing project directory: {project_dir}")
        else:
            project_dir = get_project_directory(project_title)
            logger.warning(f"Project directory not provided, creating new one for {project_title}")
        
        agent_log(
            self.name,
            "execute",
            f"Creating architecture plan based on specs"
        )
        
        # Determine the task type based on the input
        if isinstance(task_input, dict) and "stage" in task_input:
            stage = task_input["stage"]
            
            # Execute the appropriate method based on stage
            if stage == "architecture":
                result = self._create_architecture(task_input, project_dir)
            elif stage == "task_planning":
                result = self._create_task_plan(task_input, project_dir)
            else:
                error_msg = f"Unknown stage: {stage}"
                agent_log(self.name, "error", error_msg)
                raise ValueError(error_msg)
        else:
            # Default to architecture creation if no stage specified
            result = self._create_architecture(task_input, project_dir)
        
        return result

    def _create_architecture(self, task_input: dict, project_dir: Path) -> dict:
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
            response = self.generate_text(prompt)
            
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

    def _create_task_plan(self, task_input: dict, project_dir: Path) -> dict:
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
            response = self.generate_text(prompt)
            
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