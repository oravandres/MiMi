"""Base agent classes for MiMi."""

import sys
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging
import os

# Add vendor directory to path to find pydantic
vendor_path = Path(__file__).parent.parent.parent / "vendor"
if vendor_path.exists() and str(vendor_path) not in sys.path:
    sys.path.append(str(vendor_path))

from pydantic import BaseModel, Field, ConfigDict

# Import rich panel for pretty printing
from rich.panel import Panel

# Import the console from logger module
from mimi.utils.logger import console, agent_log, logger
from mimi.models.ollama import OllamaClient, get_ollama_client
from mimi.utils.output_manager import (
    create_or_update_agent_log
)

# Import subtask via function to avoid circular imports
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
    
    # System prompt is now required
    system_prompt: str = Field(
        ..., description="System prompt for the agent"
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
        """Initialize the agent with a model client."""
        base_url = self.model_settings.get("base_url", "http://localhost:11434")
        temperature = self.model_settings.get("temperature", 0.8)
        timeout = self.model_settings.get("timeout", 60)
        max_retries = self.model_settings.get("max_retries", 3)
        retry_delay = self.model_settings.get("retry_delay", 2)
        stream = self.model_settings.get("stream", True)
        
        # Initialize the model client based on provider
        if self.model_provider.lower() == "ollama":
            try:
                # Import here to avoid circular imports
                from mimi.models.ollama import OllamaClient
                
                # Create the client
                self._model_client = OllamaClient(
                    model_name=self.model_name,
                    base_url=base_url,
                    temperature=temperature,
                    timeout=timeout,  # Pass timeout to get_ollama_client
                    max_retries=max_retries,
                    retry_delay=retry_delay,
                    suppress_log=True,  # Add parameter to suppress separate logging
                    stream=stream,
                )
                
                # Check if Ollama server is running
                try:
                    self._model_client.initialize_connection()
                    # Combined log message for both agent and model initialization
                    panel_content = f"""[bold blue]🔄 Agent:[/] [bold green]{self.name}[/]
[bold yellow]📝 Role:[/] {self.role}
[bold cyan]🤖 Model:[/] {self.model_name} ({self.model_provider})
[bold green]⚙️ Settings:[/] timeout: {timeout}s, retries: {max_retries}"""

                    console.print(Panel(
                        panel_content,
                        title="✓ Agent Initialized",
                        border_style="green",
                        expand=False
                    ))
                except Exception as e:
                    logger.error(f"Failed to connect to Ollama server: {str(e)}")
                    # We still keep the client but it will report proper errors when used
                    logger.warning(f"Agent '{self.name}' initialized with potential connectivity issues. Tasks may fail when executed.")
            except Exception as e:
                logger.error(f"Error initializing Ollama client: {str(e)}")
                raise ValueError(f"Failed to initialize model client: {str(e)}")
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
        # Debug project_dir type and value
        logger.debug(f"log_to_agent_file called with project_dir type: {type(project_dir)}, value: '{project_dir}'")
        
        try:
            if async_log:
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
            logger.error(f"Error logging to agent log file: {str(e)}, project_dir type: {type(project_dir)}")

    def execute(self, task_input: Any) -> Any:
        """Execute a task with the given input.
        
        This is a base implementation that should be overridden by specialized agents.
        
        Args:
            task_input: The input to the agent.
            
        Returns:
            The output from the agent.
        """
        agent_log(self.name, "execute", f"Executing task")
        
        try:
            # Placeholder for actual agent behavior
            result = task_input
            
            # Get project directory from task input if available
            project_dir = None
            if isinstance(task_input, dict) and "project_dir" in task_input:
                project_dir = task_input["project_dir"]
                logger.debug(f"Found project_dir in task_input: {type(project_dir)}, value: '{project_dir}'")
            else:
                logger.debug(f"No project_dir found in task_input: {type(task_input)}")
            
            # Log execution to agent log file if we have a project directory
            if project_dir:
                self.log_to_agent_file(
                    project_dir=project_dir,
                    action_type="execute",
                    input_summary=str(task_input),
                    output_summary=str(result),
                    details={"agent_role": self.role}
                )
            
            agent_log(self.name, "execute", f"Execution completed with result")
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
                    logger.debug(f"[Recovery] Found project_dir in task_input: {type(project_dir)}, value: '{project_dir}'")
                
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

    def generate_text(self, prompt: str) -> str:
        """Generate text using the agent's model and system prompt.
        
        Args:
            prompt: The prompt to generate text from.
            
        Returns:
            The generated text.
        """
        client = self.get_model_client()
        
        # Use the agent's system_prompt when generating text
        return client.generate(prompt, system_prompt=self.system_prompt)

    def write_log_to_file(self, project_dir, content, subfolder, filename, create_dirs=True):
        """
        Writes agent output to a log file in the project directory.
        
        Args:
            project_dir (Path): Project directory path
            content (str): Content to write to the file
            subfolder (str): Subfolder within project directory (e.g., 'docs', 'src', 'tests')
            filename (str): Name of the file to write
            create_dirs (bool): Whether to create directories if they don't exist
            
        Returns:
            Path: Path to the written file or None if writing failed
        """
        try:
            # Ensure project_dir is a Path object
            if isinstance(project_dir, str):
                project_dir = Path(project_dir)
            
            # Create the target directory path
            target_dir = project_dir / subfolder
            if create_dirs:
                target_dir.mkdir(exist_ok=True, parents=True)
            
            # Create the file path
            file_path = target_dir / filename
            
            # Write the content to the file
            with open(file_path, 'w') as f:
                f.write(content)
                
            logging.info(f"Successfully wrote {filename} to {file_path}")
            return file_path
        except Exception as e:
            logging.error(f"Failed to write {filename}: {str(e)}")
            return None 