"""Research Analyst Agent implementation for MiMi."""

from datetime import datetime
from pathlib import Path
import re
import json

from mimi.core.agents.base_agent import Agent
from mimi.utils.logger import agent_log, logger
from mimi.utils.output_manager import (
    create_output_directory,
    save_project_metadata,
    create_or_update_project_log
)


def get_project_directory(project_title: str) -> Path:
    """Get the project directory, creating it if it doesn't exist.
    
    Args:
        project_title: The title of the project.
        
    Returns:
        The path to the project directory.
    """
    return create_output_directory(project_title)


class ResearchAnalystAgent(Agent):
    """Agent that analyzes project requirements and prepares specifications."""
    
    def execute(self, task_input: any) -> any:
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
            response = self.generate_text(prompt)
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