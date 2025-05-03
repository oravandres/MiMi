"""Reviewer Agent implementation for MiMi."""

from datetime import datetime
from pathlib import Path
import re

from pydantic import Field

from mimi.core.agents.base_agent import Agent
from mimi.utils.logger import agent_log, logger
from mimi.utils.output_manager import (
    create_output_directory,
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


class ReviewerAgent(Agent):
    """Agent that reviews and evaluates the final project."""
    
    description: str = Field("A code reviewer that provides feedback on project quality", description="Detailed description of the reviewer's capabilities")
    role: str = Field("reviewer", description="Reviewer's role (e.g., 'backend', 'frontend', 'infrastructure')")
    
    def execute(self, task_input: any) -> any:
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
    
    def _review_component(self, documentation: str, full_input: dict, project_dir: Path, project_title: str, component_type: str) -> dict:
        """Review a specific component type against requirements."""
        # Try to find original requirements from the task chain
        original_requirements = ""
        for key in full_input:
            if key == "original_requirements":
                original_requirements = full_input[key]
                break
        
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
        response = self.generate_text(prompt)
        
        # Save the review document
        review_filename = f"{component_type}_review.md"
        review_path = project_dir / "docs" / review_filename
        review_path.parent.mkdir(exist_ok=True)
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
    
    def _consolidate_reviews(self, documentation: str, full_input: dict, project_dir: Path, project_title: str) -> dict:
        """Consolidate component reviews into a comprehensive project review."""
        # Extract component reviews
        backend_review = full_input.get("backend_review", "")
        frontend_review = full_input.get("frontend_review", "")
        infrastructure_review = full_input.get("infrastructure_review", "")
        
        # Try to find original requirements
        original_requirements = full_input.get("original_requirements", "")
        
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
        response = self.generate_text(prompt)
        
        # Save the consolidated review document
        review_path = project_dir / "docs" / "project_review.md"
        review_path.parent.mkdir(exist_ok=True)
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
    
    def _final_approval(self, revised_system: str, full_input: dict, project_dir: Path, project_title: str) -> dict:
        """Final review of the project after revisions."""
        # Try to find original requirements and previous review
        original_requirements = full_input.get("original_requirements", "")
        project_review = full_input.get("project_review", "")
        
        # Log what we have for debugging
        logger.debug(f"Final approval input keys: {list(full_input.keys())}")
        
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
            response = self.generate_text(prompt)
            
            # Save the final approval document
            approval_path = project_dir / "docs" / "final_approval.md"
            approval_path.parent.mkdir(exist_ok=True)
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