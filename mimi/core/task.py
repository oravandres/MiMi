"""Task implementation for MiMi."""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import uuid

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


class SubTask(BaseModel):
    """A subtask created when an agent splits a task into smaller units of work."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the subtask")
    parent_task_name: str = Field(..., description="Name of the parent task")
    name: str = Field(..., description="Name of the subtask")
    description: str = Field(..., description="Description of what the subtask does")
    input_data: Any = Field(..., description="Input data for the subtask")
    depends_on: List[str] = Field(
        default_factory=list, description="IDs of subtasks this one depends on"
    )
    result: Optional[Any] = Field(default=None, description="Result of the subtask execution")
    duration: Optional[float] = Field(default=None, description="Duration of the subtask execution in seconds")


class Task(BaseModel):
    """A task that can be executed by an agent."""

    name: str = Field(..., description="Unique name of the task")
    description: str = Field(..., description="Description of what the task does")
    agent: str = Field(..., description="Name of the agent that will execute this task")
    input_key: Optional[Union[str, List[str]]] = Field(
        None, description="Key(s) to extract input from project data (if None, use all data)"
    )
    output_key: Optional[str] = Field(
        None, description="Key to store output in project data (if None, return as is)"
    )
    depends_on: List[str] = Field(
        default_factory=list, description="Names of tasks this task depends on"
    )
    parallel_subtasks: bool = Field(
        default=True, description="Whether to execute subtasks in parallel if agent supports it"
    )
    # Additional field for sub-project tracking
    sub_project: Optional[str] = Field(
        None, description="Name of the sub-project this task belongs to"
    )
    # Internal field to store subtasks during execution
    subtasks: Dict[str, SubTask] = Field(default_factory=dict)
    
    # Pydantic v2 model config
    model_config = {"arbitrary_types_allowed": True, "protected_namespaces": ()}
    
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
        
        # Extract the specific input based on input_key (string or list)
        if self.input_key and isinstance(input_data, dict):
            if isinstance(self.input_key, str):
                # Single input key
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
                # Multiple input keys (list)
                collected_inputs = {}
                missing_keys = []
                
                for key in self.input_key:
                    if key in input_data:
                        collected_inputs[key] = input_data[key]
                    else:
                        missing_keys.append(key)
                
                if missing_keys:
                    warning_msg = f"Some input keys not found in data: {missing_keys}"
                    task_log(self.name, "warning", warning_msg)
                
                if not collected_inputs:
                    warning_msg = "None of the specified input keys found in data, using full input"
                    task_log(self.name, "warning", warning_msg)
                    task_input = input_data
                else:
                    task_log(
                        self.name,
                        "processing",
                        f"Using input from keys: {list(collected_inputs.keys())}",
                    )
                    task_input = collected_inputs
        else:
            task_input = input_data
        
        # Check if agent supports subtask creation
        if hasattr(agent, "create_subtasks") and callable(agent.create_subtasks) and self.parallel_subtasks:
            task_log(
                self.name,
                "processing",
                f"Agent '{self.agent}' supports subtask creation. Attempting to split task.",
            )
            
            # Clear any previous subtasks
            self.subtasks = {}
            
            # Ask the agent to create subtasks
            subtasks = agent.create_subtasks(task_input)
            
            if subtasks and isinstance(subtasks, list) and all(isinstance(st, SubTask) for st in subtasks):
                task_log(
                    self.name,
                    "processing",
                    f"Task split into {len(subtasks)} subtasks",
                )
                
                # Store subtasks
                for subtask in subtasks:
                    self.subtasks[subtask.id] = subtask
                
                # Execute subtasks (this will be handled by TaskRunner)
                # The actual parallel execution happens in the runner
                return self._execute_with_subtasks(agent, task_input)
        
        # Regular execution without subtasks
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

    def _execute_with_subtasks(self, agent: Any, task_input: Any) -> Any:
        """Execute task by running its subtasks.
        
        Args:
            agent: The agent to execute the subtasks.
            task_input: The original task input.
            
        Returns:
            The combined result from all subtasks.
        """
        # This method should be called by the TaskRunner
        # which will handle parallel execution of subtasks
        
        task_log(
            self.name,
            "processing",
            f"Task has {len(self.subtasks)} subtasks to execute",
        )
        
        # Let the agent handle the combining of subtask results
        # This will be replaced by actual subtask execution in the runner
        return agent.combine_subtask_results(list(self.subtasks.values()), task_input)

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "Task":
        """Create a task from a configuration dictionary.
        
        Args:
            config: Dictionary with task configuration.
            
        Returns:
            An initialized Task instance.
        """
        return cls(**config)
        
    def get_subtasks(self) -> List[SubTask]:
        """Get the list of subtasks for this task.
        
        Returns:
            List of subtasks.
        """
        return list(self.subtasks.values())
        
    def has_subtasks(self) -> bool:
        """Check if the task has subtasks.
        
        Returns:
            True if the task has subtasks, False otherwise.
        """
        return len(self.subtasks) > 0 