"""Agent implementation for MiMi."""

import sys
from pathlib import Path

# Add vendor directory to path to find pydantic
vendor_path = Path(__file__).parent.parent / "vendor"
if vendor_path.exists() and str(vendor_path) not in sys.path:
    sys.path.append(str(vendor_path))

from typing import Any, Dict, List, Optional, Union, Callable
import uuid

from pydantic import BaseModel, Field, ConfigDict

from mimi.models.ollama import OllamaClient, get_ollama_client
from mimi.utils.logger import agent_log, logger
from mimi.utils.output_manager import create_or_update_agent_log


# Import subtask via string to avoid circular imports
SubTask = None

def get_subtask_class():
    """Get the SubTask class, importing it only when needed."""
    global SubTask
    if SubTask is None:
        from mimi.core.task import SubTask
    return SubTask


class Agent(BaseModel):
    """An agent that can perform tasks using a specific model."""

    name: str = Field(..., description="Unique name of the agent")
    role: str = Field(..., description="The role or specialty of the agent")
    description: str = Field(
        ..., description="Detailed description of the agent's capabilities"
    )
    model_name: str = Field(..., description="Name of the model used by the agent")
    model_provider: str = Field(
        "ollama", description="Provider of the model (e.g., 'ollama')"
    )
    model_settings: Dict[str, Any] = Field(
        default_factory=dict, description="Configuration for the model"
    )
    
    # Optional system prompt to give the agent context
    system_prompt: Optional[str] = Field(
        None, description="System prompt for the agent"
    )
    
    # Whether agent supports subtask creation
    supports_subtasks: bool = Field(
        default=False, description="Whether the agent supports breaking tasks into subtasks"
    )

    # Model client (populated at runtime)
    _model_client: Optional[Any] = None

    # Pydantic v2 configuration
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def initialize(self) -> None:
        """Initialize the agent and its model client."""
        # We'll move the logging to after model client initialization
        # to combine with model client log
        
        if self.model_provider.lower() == "ollama":
            base_url = self.model_settings.get("base_url", "http://localhost:11434")
            temperature = self.model_settings.get("temperature", 0.7)
            stream = self.model_settings.get("stream", False)
            
            # Pass suppress_log=True to prevent separate logging in the client
            self._model_client = get_ollama_client(
                model_name=self.model_name,
                base_url=base_url,
                temperature=temperature,
                suppress_log=True,  # Add parameter to suppress separate logging
                stream=stream
            )
            
            # Combined log message for both agent and model initialization
            logger.info(
                f"Initialized agent '{self.name}' with role '{self.role}' using {self.model_provider} model: {self.model_name}"
            )
        else:
            # Log for non-Ollama providers
            logger.info(f"Initializing agent '{self.name}' with role '{self.role}'")
            raise ValueError(f"Unsupported model provider: {self.model_provider}")

    def get_model_client(self) -> Any:
        """Get the model client, initializing if needed.
        
        Returns:
            The model client.
        """
        if self._model_client is None:
            self.initialize()
            
        return self._model_client

    def log_to_agent_file(
        self, 
        project_dir: Any, 
        action_type: str, 
        input_summary: Any, 
        output_summary: Any, 
        details: Optional[Dict[str, Any]] = None,
        log_format: str = "markdown",
        async_log: bool = False
    ) -> None:
        """Log agent action to the agent log file.
        
        Args:
            project_dir: The project directory path.
            action_type: The type of action being performed.
            input_summary: The input to the agent (any type).
            output_summary: The output from the agent (any type).
            details: Optional additional details about the action.
            log_format: Format for logging - "markdown" or "json"
            async_log: Whether to perform logging asynchronously (requires asyncio)
        """
        try:
            if async_log:
                # Import here to avoid circular imports
                import asyncio
                
                # Define async logging function
                async def _async_log():
                    try:
                        # Include agent role and other metadata in details
                        full_details = details.copy() if details else {}
                        full_details.update({
                            "agent_role": self.role,
                            "model_name": self.model_name,
                            "model_provider": self.model_provider
                        })
                        
                        # Import here to avoid circular imports
                        from mimi.utils.output_manager import create_or_update_agent_log
                        
                        create_or_update_agent_log(
                            project_dir=project_dir,
                            agent_name=self.name,
                            action_type=action_type,
                            input_summary=input_summary,
                            output_summary=output_summary,
                            details=full_details,
                            log_format=log_format
                        )
                    except Exception as e:
                        # Don't let logging errors interrupt the agent
                        from mimi.utils.logger import logger
                        logger.error(f"Error in async agent logging: {str(e)}")
                
                # Schedule the async task
                if asyncio.iscoroutinefunction(asyncio.get_event_loop):
                    # Python 3.10+
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(_async_log())
                        else:
                            loop.run_until_complete(_async_log())
                    except RuntimeError:
                        # Fallback if no event loop
                        asyncio.run(_async_log())
                else:
                    # Python 3.7-3.9
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.ensure_future(_async_log())
                        else:
                            loop.run_until_complete(_async_log())
                    except RuntimeError:
                        # Fallback if no event loop
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(_async_log())
            else:
                # Synchronous logging
                # Include agent role and other metadata in details
                full_details = details.copy() if details else {}
                full_details.update({
                    "agent_role": self.role,
                    "model_name": self.model_name,
                    "model_provider": self.model_provider
                })
                
                # Log to the agent log file
                from mimi.utils.output_manager import create_or_update_agent_log
                
                create_or_update_agent_log(
                    project_dir=project_dir,
                    agent_name=self.name,
                    action_type=action_type,
                    input_summary=input_summary,
                    output_summary=output_summary,
                    details=full_details,
                    log_format=log_format
                )
        except Exception as e:
            # Don't let logging errors interrupt the agent
            from mimi.utils.logger import logger
            logger.error(f"Error logging to agent log file: {str(e)}")

    def execute(self, task_input: Any) -> Any:
        """Execute a task with the given input.
        
        This is a base implementation that should be overridden by specialized agents.
        
        Args:
            task_input: The input to the agent.
            
        Returns:
            The output from the agent.
        """
        agent_log(self.name, "execute", f"Executing task with input: {task_input}")
        
        try:
            # Placeholder for actual agent behavior
            result = task_input
            
            # Get project directory from task input if available
            project_dir = None
            if isinstance(task_input, dict) and "project_dir" in task_input:
                project_dir = task_input["project_dir"]
            
            # Log execution to agent log file if we have a project directory
            if project_dir:
                self.log_to_agent_file(
                    project_dir=project_dir,
                    action_type="execute",
                    input_summary=str(task_input),
                    output_summary=str(result),
                    details={"agent_role": self.role}
                )
            
            agent_log(self.name, "execute", f"Execution completed with result: {result}")
            return result
            
        except Exception as e:
            error_message = f"Error during execution: {str(e)}"
            agent_log(self.name, "error", error_message)
            
            # Attempt to recover from common errors
            recovered_result = self._attempt_error_recovery(e, task_input)
            
            # If recovery was successful, return the recovered result
            if recovered_result is not None:
                # Get project directory from task input if available
                project_dir = None
                if isinstance(task_input, dict) and "project_dir" in task_input:
                    project_dir = task_input["project_dir"]
                
                # Log recovery to agent log file if we have a project directory
                if project_dir:
                    self.log_to_agent_file(
                        project_dir=project_dir,
                        action_type="error-recovery",
                        input_summary=str(task_input),
                        output_summary=str(recovered_result),
                        details={
                            "agent_role": self.role,
                            "original_error": str(e),
                            "recovery_method": "automatic"
                        }
                    )
                
                agent_log(self.name, "execute", f"Recovered from error, completed with result: {recovered_result}")
                return recovered_result
            
            # If no recovery is possible, re-raise the exception with more context
            raise RuntimeError(f"Agent '{self.name}' with role '{self.role}' failed: {error_message}") from e

    def _attempt_error_recovery(self, error: Exception, task_input: Any) -> Optional[Any]:
        """Attempt to recover from common errors.
        
        Args:
            error: The exception that was caught.
            task_input: The original input to the agent.
            
        Returns:
            Recovered result if recovery was successful, None otherwise.
        """
        error_str = str(error)
        
        # Check for common error patterns
        if isinstance(error, PermissionError) and "//" in error_str:
            # Likely a URL being treated as a file path
            agent_log(self.name, "recovery", "Detected URL being treated as file path")
            
            # Extract the problematic path/URL from the error message
            import re
            url_match = re.search(r"'(//[^']*)'", error_str)
            if url_match:
                bad_path = url_match.group(1)
                
                # Attempt to fix the URL format
                if bad_path.startswith("//"):
                    fixed_url = "http:" + bad_path
                    agent_log(self.name, "recovery", f"Converted {bad_path} to {fixed_url}")
                    
                    # If the task input is a dictionary, try to replace the bad path
                    if isinstance(task_input, dict):
                        # Deep copy to avoid modifying the original
                        import copy
                        modified_input = copy.deepcopy(task_input)
                        
                        # Recursively search and replace the bad path in the input
                        self._replace_in_dict(modified_input, bad_path, fixed_url)
                        
                        # Return a modified result with explanation
                        return {
                            "fixed_input": modified_input,
                            "recovery_message": f"Fixed URL format from '{bad_path}' to '{fixed_url}'",
                            "original_error": str(error),
                            "recommendation": "Use proper URL format with http:// or https:// prefix"
                        }
        
        # Check for file not found errors
        elif isinstance(error, FileNotFoundError):
            agent_log(self.name, "recovery", "Detected file not found error")
            
            # Extract the missing file path
            import re
            path_match = re.search(r"'([^']*)'", error_str)
            if path_match:
                missing_path = path_match.group(1)
                
                # Check if this is a directory issue
                from pathlib import Path
                parent_dir = Path(missing_path).parent
                if not parent_dir.exists():
                    # Directory doesn't exist, suggest creating it
                    return {
                        "recovery_message": f"Directory '{parent_dir}' does not exist",
                        "original_error": str(error),
                        "recommendation": f"Create directory with: os.makedirs('{parent_dir}', exist_ok=True)"
                    }
        
        # If no specific recovery was possible
        agent_log(self.name, "recovery", "Could not automatically recover from error")
        return None

    def _replace_in_dict(self, d: Dict[Any, Any], old_value: str, new_value: str) -> None:
        """Recursively replace occurrences of old_value with new_value in a dictionary.
        
        Args:
            d: The dictionary to process.
            old_value: The value to search for.
            new_value: The replacement value.
        """
        if not isinstance(d, dict):
            return
        
        for key, value in d.items():
            if isinstance(value, str) and old_value in value:
                d[key] = value.replace(old_value, new_value)
            elif isinstance(value, dict):
                self._replace_in_dict(value, old_value, new_value)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, str) and old_value in item:
                        value[i] = item.replace(old_value, new_value)
                    elif isinstance(item, dict):
                        self._replace_in_dict(item, old_value, new_value)

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "Agent":
        """Create an agent from a configuration dictionary.
        
        Args:
            config: Dictionary with agent configuration.
            
        Returns:
            An initialized Agent instance.
        """
        # Handle the config rename from model_config to model_settings
        if "model_config" in config and "model_settings" not in config:
            config["model_settings"] = config.pop("model_config")
            
        agent = cls(**config)
        return agent

    def create_subtasks(self, task_input: Any) -> List[Any]:
        """Create subtasks from the given task input.
        
        This is a base implementation that can be overridden by specialized agents
        that support subtask creation.
        
        Args:
            task_input: The input to the agent.
            
        Returns:
            A list of SubTask objects.
        """
        if not self.supports_subtasks:
            agent_log(self.name, "subtasks", f"Agent does not support subtask creation")
            return []
            
        # Base implementation doesn't create subtasks
        agent_log(self.name, "subtasks", f"Creating subtasks not implemented for base Agent class")
        return []
        
    def execute_subtask(self, subtask: Any) -> Any:
        """Execute a single subtask.
        
        Args:
            subtask: The subtask to execute.
            
        Returns:
            The output from the subtask execution.
        """
        agent_log(self.name, "execute_subtask", f"Executing subtask: {subtask.name}")
        
        # Get model client if needed
        model_client = self.get_model_client()
        
        # Process the subtask based on its name and content
        if subtask.name.startswith("chunk_"):
            # Process a list chunk
            result = []
            for item in subtask.input_data:
                # Apply some processing - for demonstration, just increment numbers
                if isinstance(item, (int, float)):
                    result.append(item + 1)
                else:
                    result.append(item)
            return result
            
        elif subtask.name.startswith("dict_chunk_"):
            # Process a dictionary chunk
            result = {}
            for key, value in subtask.input_data.items():
                # Apply some processing - for demonstration, just increment numeric values
                if isinstance(value, (int, float)):
                    result[key] = value + 1
                else:
                    result[key] = value
            return result
            
        elif subtask.name.startswith("text_chunk_"):
            # Process a text chunk - for demonstration, just convert to uppercase
            return subtask.input_data.upper()
            
        else:
            # Default processing
            if isinstance(subtask.input_data, (int, float)):
                return subtask.input_data + 1
            elif isinstance(subtask.input_data, str):
                return f"Processed: {subtask.input_data}"
            else:
                return subtask.input_data
    
    def combine_subtask_results(self, subtasks: List[Any], original_input: Any) -> Any:
        """Combine the results of multiple subtasks.
        
        Args:
            subtasks: The list of subtasks with their results.
            original_input: The original task input.
            
        Returns:
            The combined output from all subtasks.
        """
        agent_log(self.name, "combine", f"Combining results from {len(subtasks)} subtasks")
        
        # Extract results from subtasks
        results = [st.result for st in subtasks]
        
        # Combine based on the type of the first result
        if all(isinstance(r, list) for r in results if r is not None):
            # Combine lists
            combined = []
            for result in results:
                if result is not None:
                    combined.extend(result)
            return combined
            
        elif all(isinstance(r, dict) for r in results if r is not None):
            # Combine dictionaries
            combined = {}
            for result in results:
                if result is not None:
                    combined.update(result)
            return combined
            
        elif all(isinstance(r, str) for r in results if r is not None):
            # Combine strings
            return "".join(r for r in results if r is not None)
            
        else:
            # Default combination - return a dictionary of results
            combined_result = {}
            
            # Include the original input in the combined result
            if isinstance(original_input, dict):
                combined_result.update(original_input)
            
            # Add each subtask result to the combined result
            for i, result in enumerate(results):
                combined_result[f"subtask_{i+1}_result"] = result
                
            return combined_result


class AnalystAgent(Agent):
    """Agent that analyzes and verifies number additions."""
    
    def execute(self, task_input: Any) -> Any:
        """Verify that the addition was performed correctly.
        
        Args:
            task_input: A dictionary containing input value and result.
            
        Returns:
            The verified result if correct, or a dictionary with error details if incorrect.
        """
        agent_log(
            self.name,
            "execute",
            f"Analyzing addition: {str(task_input)}",
        )
        
        try:
            # Find only the most recent result key to verify
            result_keys = []
            for key in task_input:
                if key.startswith("result") and key[6:].isdigit():
                    result_keys.append(key)
            
            if not result_keys:
                agent_log(self.name, "warning", "No result keys found, nothing to verify")
                return {
                    "status": "warning", 
                    "message": "No result keys found to verify",
                    "data": task_input
                }
            
            # Get the most recent result (highest number)
            latest_result_key = sorted(result_keys, key=lambda k: int(k[6:]))[-1]
            result_data = task_input[latest_result_key]
            
            # Get the input value
            input_value = task_input.get("input")
            if input_value is None:
                agent_log(self.name, "error", "Input value not found in task input")
                return {
                    "status": "error", 
                    "message": "Input value not found",
                    "data": task_input
                }
            
            # For simple results (not detailed)
            if not isinstance(result_data, dict):
                number_to_add = int(latest_result_key[6:])  # Extract number from result key
                expected_result = input_value + number_to_add
                if abs(expected_result - result_data) < 1e-6:  # Using epsilon for float comparison
                    agent_log(self.name, "execute", f"Verified: {input_value} + {number_to_add} = {result_data}")
                    return {
                        "status": "success",
                        "message": "Calculation verified successfully",
                        "data": {
                            "input": input_value,
                            latest_result_key: result_data,
                        },
                        "verification_results": [{
                            "operation": f"{input_value} + {number_to_add}",
                            "expected": expected_result,
                            "actual": result_data,
                            "is_correct": True
                        }]
                    }
                else:
                    error_message = f"Calculation error: expected {input_value} + {number_to_add} = {expected_result}, but got {result_data}"
                    agent_log(self.name, "error", error_message)
                    return {
                        "status": "error",
                        "message": error_message,
                        "data": {
                            "input": input_value,
                            latest_result_key: result_data,
                        },
                        "verification_results": [{
                            "operation": f"{input_value} + {number_to_add}",
                            "expected": expected_result,
                            "actual": result_data,
                            "is_correct": False
                        }]
                    }
            
            # For detailed results with steps
            input_value = result_data.get("input_value")
            number_added = result_data.get("number_added")
            repetitions = result_data.get("repetitions", 1)
            total_added = result_data.get("total_added")
            reported_result = result_data.get("result")
            steps = result_data.get("steps", [])
            
            if input_value is None or reported_result is None:
                agent_log(self.name, "error", "Required data missing from result")
                return {
                    "status": "error",
                    "message": "Required data missing from result",
                    "data": result_data
                }
            
            # Verify final result
            expected_result = input_value + total_added
            final_result_correct = abs(expected_result - reported_result) < 1e-6
            
            # Verify each step
            step_verification_results = []
            all_steps_correct = True
            
            if steps:
                current = input_value
                for i, step in enumerate(steps):
                    step_number = step.get("step")
                    before = step.get("value_before")
                    after = step.get("value_after")
                    added = step.get("added")
                    
                    # Check if this step's starting value matches the previous step's ending value
                    if abs(before - current) > 1e-6:
                        all_steps_correct = False
                        step_verification_results.append({
                            "step": step_number,
                            "operation": f"Step {step_number}: {before} should be {current}",
                            "expected": current,
                            "actual": before,
                            "is_correct": False
                        })
                    
                    # Check if the addition was performed correctly
                    expected_after = before + added
                    step_correct = abs(expected_after - after) < 1e-6
                    if not step_correct:
                        all_steps_correct = False
                    
                    step_verification_results.append({
                        "step": step_number,
                        "operation": f"Step {step_number}: {before} + {added}",
                        "expected": expected_after,
                        "actual": after,
                        "is_correct": step_correct
                    })
                    
                    current = after
                
                # Check if the final step result matches the reported final result
                if abs(current - reported_result) > 1e-6:
                    all_steps_correct = False
                    step_verification_results.append({
                        "step": "final",
                        "operation": f"Final result should match last step",
                        "expected": current,
                        "actual": reported_result,
                        "is_correct": False
                    })
            
            # Overall verification result
            if final_result_correct and all_steps_correct:
                agent_log(self.name, "execute", f"Verified: {input_value} + ({number_added} × {repetitions}) = {reported_result}")
                return {
                    "status": "success",
                    "message": "All calculations verified successfully",
                    "data": {
                        "input": input_value,
                        latest_result_key: result_data,
                    },
                    "verification_results": [{
                        "operation": f"{input_value} + ({number_added} × {repetitions})",
                        "expected": expected_result,
                        "actual": reported_result,
                        "is_correct": True,
                        "steps": step_verification_results
                    }]
                }
            else:
                errors = []
                if not final_result_correct:
                    errors.append(f"Final result {reported_result} should be {expected_result}")
                
                if not all_steps_correct:
                    errors.append("One or more calculation steps are incorrect")
                
                error_message = f"Calculation errors: {', '.join(errors)}"
                agent_log(self.name, "error", error_message)
                return {
                    "status": "error",
                    "message": error_message,
                    "data": {
                        "input": input_value,
                        latest_result_key: result_data,
                    },
                    "verification_results": [{
                        "operation": f"{input_value} + ({number_added} × {repetitions})",
                        "expected": expected_result,
                        "actual": reported_result,
                        "is_correct": final_result_correct,
                        "steps": step_verification_results
                    }]
                }
                
        except Exception as e:
            error_message = f"Error verifying calculation: {str(e)}"
            agent_log(self.name, "error", error_message)
            return {
                "status": "error",
                "message": error_message,
                "data": task_input
            }


class FeedbackProcessorAgent(Agent):
    """Agent that processes verification results and provides feedback."""
    
    def execute(self, task_input: Any) -> Any:
        """Process verification results and provide feedback.
        
        Args:
            task_input: A dictionary containing verification results.
            
        Returns:
            Feedback about the verification results.
        """
        agent_log(
            self.name,
            "execute",
            f"Processing verification results: {str(task_input)}",
        )
        
        try:
            # Find the latest verification result
            verified_keys = []
            for key in task_input:
                if key.startswith("verified") and key[8:].isdigit():
                    verified_keys.append(key)
            
            if not verified_keys:
                agent_log(self.name, "warning", "No verification results found")
                return {
                    "status": "warning",
                    "message": "No verification results to process",
                    "continue": True,
                    "original_data": task_input
                }
            
            # Get the most recent verification (highest number)
            latest_verified_key = sorted(verified_keys, key=lambda k: int(k[8:]))[-1]
            verification_result = task_input[latest_verified_key]
            
            # Process the verification result
            if isinstance(verification_result, dict):
                status = verification_result.get("status", "unknown")
                message = verification_result.get("message", "")
                verification_data = verification_result.get("verification_results", [])
                
                if status == "success":
                    agent_log(self.name, "execute", "Verification passed! All calculations are correct.")
                    
                    # Get detailed information about the operation
                    operation_summary = ""
                    if verification_data:
                        operation = verification_data[0].get("operation", "")
                        if operation:
                            operation_summary = f" Verified operation: {operation}"
                            
                        # If there are steps, include a summary
                        steps = verification_data[0].get("steps", [])
                        if steps:
                            step_count = len(steps)
                            operation_summary += f" ({step_count} steps verified)"
                    
                    return {
                        "status": "success",
                        "message": f"All calculations are correct!{operation_summary}",
                        "continue": True,
                        "original_data": task_input
                    }
                elif status == "error":
                    # Gather all error details
                    details = []
                    
                    for result in verification_data:
                        operation = result.get("operation", "unknown")
                        expected = result.get("expected", "unknown")
                        actual = result.get("actual", "unknown")
                        
                        if operation:
                            details.append(f"Operation: {operation}, Expected: {expected}, Actual: {actual}")
                        
                        # Add details about any failed steps
                        steps = result.get("steps", [])
                        if steps:
                            failed_steps = [s for s in steps if not s.get("is_correct", True)]
                            for step in failed_steps:
                                step_op = step.get("operation", "")
                                step_expected = step.get("expected", "")
                                step_actual = step.get("actual", "")
                                details.append(f"  - {step_op}, Expected: {step_expected}, Actual: {step_actual}")
                    
                    error_details = "\n".join(details)
                    agent_log(self.name, "error", f"Verification failed: {message}\nDetails: {error_details}")
                    
                    feedback_message = f"Error detected: {message}"
                    if details:
                        feedback_message += f"\nDetails:\n{error_details}"
                        feedback_message += "\nPlease check the calculations and try again."
                    
                    return {
                        "status": "error",
                        "message": feedback_message,
                        "details": details,
                        "continue": False,  # Signal to halt workflow on error
                        "original_data": task_input
                    }
                else:
                    # Unknown status
                    agent_log(self.name, "warning", f"Unknown status in verification result: {status}")
                    return {
                        "status": "warning",
                        "message": f"Received unknown verification status: {status}",
                        "continue": True,  # Continue by default
                        "original_data": task_input
                    }
            else:
                # Not a dictionary
                agent_log(self.name, "warning", f"Unexpected format for verification result: {verification_result}")
                return {
                    "status": "warning",
                    "message": "Unexpected format for verification result",
                    "continue": True,
                    "original_data": task_input
                }
        
        except Exception as e:
            error_message = f"Error processing verification results: {str(e)}"
            agent_log(self.name, "error", error_message)
            return {
                "status": "error",
                "message": error_message,
                "continue": False,  # Halt on unexpected errors
                "original_data": task_input
            }


class TaskSplitterAgent(Agent):
    """An agent that can split tasks into subtasks and execute them in parallel."""
    
    # Set this to True to enable subtask creation
    supports_subtasks: bool = Field(default=True, description="Whether the agent supports breaking tasks into subtasks")
    
    # Number of subtasks to create (default to a reasonable number)
    num_subtasks: int = Field(default=4, description="Number of subtasks to create")
    
    def create_subtasks(self, task_input: Any) -> List[Any]:
        """Create subtasks from the given task input.
        
        Args:
            task_input: The input to the agent.
            
        Returns:
            A list of SubTask objects.
        """
        agent_log(self.name, "subtasks", f"Creating {self.num_subtasks} subtasks")
        
        # Get the SubTask class
        SubTask = get_subtask_class()
        
        # For demonstration purposes, let's split a list or dictionary task into smaller pieces
        subtasks = []
        
        if isinstance(task_input, list) and len(task_input) > 1:
            # Split list into chunks
            chunk_size = max(1, len(task_input) // self.num_subtasks)
            chunks = [task_input[i:i + chunk_size] for i in range(0, len(task_input), chunk_size)]
            
            # Create a subtask for each chunk
            for i, chunk in enumerate(chunks[:self.num_subtasks]):
                subtask = SubTask(
                    parent_task_name=self.name,
                    name=f"chunk_{i+1}",
                    description=f"Process list chunk {i+1} of {len(chunks)}",
                    input_data=chunk,
                    depends_on=[]
                )
                subtasks.append(subtask)
                
        elif isinstance(task_input, dict) and len(task_input) > 1:
            # Split dictionary into smaller dictionaries
            keys = list(task_input.keys())
            chunk_size = max(1, len(keys) // self.num_subtasks)
            chunks = [keys[i:i + chunk_size] for i in range(0, len(keys), chunk_size)]
            
            # Create a subtask for each chunk
            for i, chunk in enumerate(chunks[:self.num_subtasks]):
                chunk_dict = {k: task_input[k] for k in chunk}
                subtask = SubTask(
                    parent_task_name=self.name,
                    name=f"dict_chunk_{i+1}",
                    description=f"Process dictionary chunk {i+1} of {len(chunks)}",
                    input_data=chunk_dict,
                    depends_on=[]
                )
                subtasks.append(subtask)
                
        elif isinstance(task_input, str) and len(task_input) > 100:
            # Split text into chunks (for simple demonstration)
            chunk_size = max(50, len(task_input) // self.num_subtasks)
            chunks = [task_input[i:i + chunk_size] for i in range(0, len(task_input), chunk_size)]
            
            # Create a subtask for each chunk
            for i, chunk in enumerate(chunks[:self.num_subtasks]):
                subtask = SubTask(
                    parent_task_name=self.name,
                    name=f"text_chunk_{i+1}",
                    description=f"Process text chunk {i+1} of {len(chunks)}",
                    input_data=chunk,
                    depends_on=[]
                )
                subtasks.append(subtask)
        else:
            # For other input types, just create sequential subtasks with the same input
            for i in range(self.num_subtasks):
                subtask = SubTask(
                    parent_task_name=self.name,
                    name=f"subtask_{i+1}",
                    description=f"Process part {i+1} of the task",
                    input_data=task_input,
                    depends_on=[]
                )
                subtasks.append(subtask)
        
        agent_log(self.name, "subtasks", f"Created {len(subtasks)} subtasks")
        return subtasks
    
    def execute_subtask(self, subtask: Any) -> Any:
        """Execute a single subtask.
        
        Args:
            subtask: The subtask to execute.
            
        Returns:
            The output from the subtask execution.
        """
        agent_log(self.name, "execute_subtask", f"Executing subtask: {subtask.name}")
        
        # Get model client if needed
        model_client = self.get_model_client()
        
        # Process the subtask based on its name and content
        if subtask.name.startswith("chunk_"):
            # Process a list chunk
            result = []
            for item in subtask.input_data:
                # Apply some processing - for demonstration, just increment numbers
                if isinstance(item, (int, float)):
                    result.append(item + 1)
                else:
                    result.append(item)
            return result
            
        elif subtask.name.startswith("dict_chunk_"):
            # Process a dictionary chunk
            result = {}
            for key, value in subtask.input_data.items():
                # Apply some processing - for demonstration, just increment numeric values
                if isinstance(value, (int, float)):
                    result[key] = value + 1
                else:
                    result[key] = value
            return result
            
        elif subtask.name.startswith("text_chunk_"):
            # Process a text chunk - for demonstration, just convert to uppercase
            return subtask.input_data.upper()
            
        else:
            # Default processing
            if isinstance(subtask.input_data, (int, float)):
                return subtask.input_data + 1
            elif isinstance(subtask.input_data, str):
                return f"Processed: {subtask.input_data}"
            else:
                return subtask.input_data
    
    def combine_subtask_results(self, subtasks: List[Any], original_input: Any) -> Any:
        """Combine the results of multiple subtasks.
        
        Args:
            subtasks: The list of subtasks with their results.
            original_input: The original task input.
            
        Returns:
            The combined output from all subtasks.
        """
        agent_log(self.name, "combine", f"Combining results from {len(subtasks)} subtasks")
        
        # Extract results from subtasks
        results = [st.result for st in subtasks]
        
        # Combine based on the type of the first result
        if all(isinstance(r, list) for r in results if r is not None):
            # Combine lists
            combined = []
            for result in results:
                if result is not None:
                    combined.extend(result)
            return combined
            
        elif all(isinstance(r, dict) for r in results if r is not None):
            # Combine dictionaries
            combined = {}
            for result in results:
                if result is not None:
                    combined.update(result)
            return combined
            
        elif all(isinstance(r, str) for r in results if r is not None):
            # Combine strings
            return "".join(r for r in results if r is not None)
            
        else:
            # Default combination - return a dictionary of results
            combined_result = {}
            
            # Include the original input in the combined result
            if isinstance(original_input, dict):
                combined_result.update(original_input)
            
            # Add each subtask result to the combined result
            for i, result in enumerate(results):
                combined_result[f"subtask_{i+1}_result"] = result
                
            return combined_result
    
    def execute(self, task_input: Any) -> Any:
        """Execute a task with the given input.
        
        For this agent, the base execution is very simple as the
        main work happens in the subtask execution.
        
        Args:
            task_input: The input to the agent.
            
        Returns:
            The output from the agent.
        """
        agent_log(self.name, "execute", f"Preparing to process input with subtasks")
        
        # Do any necessary preprocessing
        # This method will typically be called before subtasks are created
        
        # The actual result will come from subtask execution
        return task_input 