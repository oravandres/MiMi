"""Task implementation for MiMi."""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Add vendor directory to path to find pydantic
vendor_path = Path(__file__).parent.parent / "vendor"
if vendor_path.exists() and str(vendor_path) not in sys.path:
    sys.path.append(str(vendor_path))

from pydantic import BaseModel, Field

from mimi.utils.logger import logger, task_log


def _clean_verification_results(data: Any) -> Any:
    """Clean verification results to prevent them from accumulating.
    
    Args:
        data: The data to clean.
        
    Returns:
        Cleaned data with only essential information retained.
    """
    if not isinstance(data, dict):
        return data
        
    # For verification results (from AnalystAgent)
    if "status" in data and "message" in data:
        # This is probably a verification or feedback result
        # Keep the verification_results if present
        cleaned_result = {
            "status": data.get("status", "unknown"),
            "message": data.get("message", ""),
        }
        
        # Keep verification_results if present
        if "verification_results" in data:
            cleaned_result["verification_results"] = data["verification_results"]
            
        # Keep original data in a simplified form
        if "data" in data and isinstance(data["data"], dict):
            cleaned_data = {}
            
            # Always include input if present
            if "input" in data["data"]:
                cleaned_data["input"] = data["data"]["input"]
                
            # Include the most recent result
            result_keys = [k for k in data["data"] if k.startswith("result") and k[6:].isdigit()]
            if result_keys:
                latest_key = sorted(result_keys, key=lambda k: int(k[6:]))[-1]
                cleaned_data[latest_key] = data["data"][latest_key]
                
            cleaned_result["data"] = cleaned_data
            
        return cleaned_result
    
    # For regular data dictionaries
    cleaned = {}
    
    # Always keep the input
    if "input" in data:
        cleaned["input"] = data["input"]
    
    # Find all result keys (resultN) and keep only the latest one
    result_keys = []
    for key in data:
        if key.startswith("result") and key[6:].isdigit():
            result_keys.append(key)
    
    if result_keys:
        # Sort to find the latest result
        latest_result_key = sorted(result_keys, key=lambda k: int(k[6:]))[-1]
        cleaned[latest_result_key] = data[latest_result_key]
        
        # Also keep the latest verification and feedback for this result
        latest_num = latest_result_key[6:]  # Get the number part
        verified_key = f"verified{latest_num}"
        feedback_key = f"feedback{latest_num}"
        
        if verified_key in data:
            # Preserve the verification data structure
            cleaned[verified_key] = data[verified_key]
                
        if feedback_key in data:
            cleaned[feedback_key] = data[feedback_key]
    
    return cleaned


class Task(BaseModel):
    """A task that can be executed by an agent."""

    name: str = Field(..., description="Unique name of the task")
    description: str = Field(..., description="Description of what the task does")
    agent: str = Field(..., description="Name of the agent that will execute this task")
    input_key: Optional[str] = Field(
        None, description="Key to extract input from project data (if None, use all data)"
    )
    output_key: Optional[str] = Field(
        None, description="Key to store output in project data (if None, return as is)"
    )
    depends_on: List[str] = Field(
        default_factory=list, description="Names of tasks this task depends on"
    )

    def execute(self, agent_lookup: Dict[str, Any], input_data: Any) -> Any:
        """Execute the task using the specified agent.
        
        Args:
            agent_lookup: Dictionary mapping agent names to agent objects.
            input_data: Input data for the task.
            
        Returns:
            The output from the task execution.
            
        Raises:
            ValueError: If the specified agent is not found.
        """
        if self.agent not in agent_lookup:
            error_msg = f"Agent '{self.agent}' not found in agent lookup"
            task_log(self.name, "error", error_msg)
            raise ValueError(error_msg)
        
        agent = agent_lookup[self.agent]
        
        task_log(
            self.name, 
            "started", 
            f"Executing task with agent '{self.agent}'",
            data={"input": input_data},
        )
        
        # For Analyst and FeedbackProcessor agents, clean input data first
        # to prevent them from processing old results
        if agent.__class__.__name__ in ["AnalystAgent", "FeedbackProcessorAgent"]:
            if isinstance(input_data, dict):
                task_log(
                    self.name,
                    "processing",
                    "Cleaning input data for verification/feedback agent",
                )
                input_data = _clean_verification_results(input_data)
        
        # Extract the specific input if input_key is provided
        if self.input_key and isinstance(input_data, dict):
            if self.input_key in input_data:
                task_input = input_data[self.input_key]
                task_log(
                    self.name,
                    "processing",
                    f"Using input from key '{self.input_key}'",
                    data={"extracted_input": task_input},
                )
            else:
                warning_msg = f"Input key '{self.input_key}' not found in data, using full input"
                task_log(self.name, "warning", warning_msg)
                task_input = input_data
        else:
            task_input = input_data
        
        # Execute the task with the agent
        result = agent.execute(task_input)
        
        # Apply cleaning based on agent type
        if agent.__class__.__name__ in ["AnalystAgent", "FeedbackProcessorAgent"] and isinstance(result, dict):
            result = _clean_verification_results(result)
            task_log(
                self.name,
                "processing",
                f"Cleaned {agent.__class__.__name__} results to prevent data accumulation",
            )
        
        # Store the result under output_key if specified
        if self.output_key and isinstance(input_data, dict):
            output_data = input_data.copy()
            output_data[self.output_key] = result
            task_log(
                self.name,
                "completed",
                f"Stored result in output key '{self.output_key}'",
                data={"result": result},
            )
            return output_data
        else:
            task_log(
                self.name,
                "completed",
                "Task completed successfully",
                data={"result": result},
            )
            return result

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "Task":
        """Create a task from a configuration dictionary.
        
        Args:
            config: Dictionary with task configuration.
            
        Returns:
            An initialized Task instance.
        """
        return cls(**config) 