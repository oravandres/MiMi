"""Task splitter agent for MiMi."""

import uuid
from typing import Any, Dict, List, Optional

from mimi.utils.logger import agent_log

from mimi.core.agents.base_agent import Agent, get_subtask_class


class TaskSplitterAgent(Agent):
    """An agent that can split tasks into subtasks and execute them in parallel."""
    
    # Set this to True to enable subtask creation
    supports_subtasks: bool = True
    
    # Number of subtasks to create (default to a reasonable number)
    num_subtasks: int = 4
    
    def create_subtasks(self, task_input: Any) -> List[Any]:
        """Create subtasks from the given task input.
        
        Args:
            task_input: The input to the agent.
            
        Returns:
            A list of SubTask objects.
        """
        agent_log(self.name, "subtasks", f"Creating {self.num_subtasks} subtasks")
        
        # Get the SubTask class via function to avoid circular imports
        SubTask = get_subtask_class()
        
        subtasks = []
        subtask_id = 1
        
        # Create subtasks based on input type
        if isinstance(task_input, list):
            # For lists, split the input data into chunks
            chunk_size = max(1, len(task_input) // self.num_subtasks)
            chunks = []
            
            # Split the list into chunks
            for i in range(0, len(task_input), chunk_size):
                chunks.append(task_input[i:i+chunk_size])
            
            # Create a subtask for each chunk
            for i, chunk in enumerate(chunks):
                subtask = SubTask(
                    parent_task_name="unknown_task",  # Will be set by TaskRunner
                    name=f"chunk_{i+1}",
                    description=f"Process list chunk {i+1} of {len(chunks)}",
                    input_data=chunk,
                    depends_on=[]
                )
                subtasks.append(subtask)
                subtask_id += 1
            
        elif isinstance(task_input, dict):
            # For dictionaries, split the keys into chunks
            keys = list(task_input.keys())
            chunk_size = max(1, len(keys) // self.num_subtasks)
            chunks = []
            
            # Split the keys into chunks
            for i in range(0, len(keys), chunk_size):
                chunks.append(keys[i:i+chunk_size])
            
            # Create a subtask for each chunk
            for i, chunk_keys in enumerate(chunks):
                chunk_data = {k: task_input[k] for k in chunk_keys}
                subtask = SubTask(
                    parent_task_name="unknown_task",  # Will be set by TaskRunner
                    name=f"dict_chunk_{i+1}",
                    description=f"Process dictionary chunk {i+1} of {len(chunks)}",
                    input_data=chunk_data,
                    depends_on=[]
                )
                subtasks.append(subtask)
                subtask_id += 1
                
        elif isinstance(task_input, str):
            # For strings, split by characters
            text_length = len(task_input)
            chunk_size = max(1, text_length // self.num_subtasks)
            chunks = []
            
            # Split the string into chunks
            for i in range(0, text_length, chunk_size):
                chunks.append(task_input[i:i+chunk_size])
            
            # Create a subtask for each chunk
            for i, chunk in enumerate(chunks):
                subtask = SubTask(
                    parent_task_name="unknown_task",  # Will be set by TaskRunner
                    name=f"text_chunk_{i+1}",
                    description=f"Process text chunk {i+1} of {len(chunks)}",
                    input_data=chunk,
                    depends_on=[]
                )
                subtasks.append(subtask)
                subtask_id += 1
        
        else:
            # For other types, create subtasks that operate on the whole input
            # but in different ways
            for i in range(self.num_subtasks):
                subtask = SubTask(
                    parent_task_name="unknown_task",  # Will be set by TaskRunner
                    name=f"subtask_{i+1}",
                    description=f"Process subtask {i+1} of {self.num_subtasks}",
                    input_data=task_input,
                    depends_on=[]
                )
                subtasks.append(subtask)
                subtask_id += 1
        
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
        """Execute the task with subtask parallelization if supported.
        
        This implementation directly uses the base implementation since we have
        already overridden create_subtasks, execute_subtask, and combine_subtask_results.
        The TaskRunner will handle the actual parallelization.
        
        Args:
            task_input: The input to the agent.
            
        Returns:
            The output from task execution.
        """
        agent_log(self.name, "execute", f"Executing task")
        
        # In this case, we'll just return the input since the TaskRunner will
        # take care of creating subtasks, executing them, and combining results.
        # This method is mainly for subclasses that want to customize behavior.
        return task_input 