#!/usr/bin/env python3
"""Example demonstrating task splitting and parallel subtask execution."""

import time
import sys
from pathlib import Path

# Add the parent directory to sys.path to find the mimi module
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from mimi.core.agent import TaskSplitterAgent
from mimi.core.task import Task
from mimi.core.project import Project
from mimi.core.runner import ProjectRunner
from mimi.utils.logger import setup_logger

def main():
    """Run a demonstration of task splitting and parallel subtask execution."""
    # Setup logging
    setup_logger(log_level="INFO")
    
    print("Creating a project with a task splitter agent...")
    
    # Create a task splitter agent
    agent = TaskSplitterAgent(
        name="splitter",
        role="task_splitter",
        description="Agent that splits tasks into subtasks",
        model_name="llama3",
        system_prompt="You are a specialized agent that divides complex tasks into smaller units for parallel processing.",
        num_subtasks=4
    )
    
    # Create a task that will use the agent
    list_task = Task(
        name="process_list",
        description="Process a list of numbers",
        agent="splitter",
        input_key="numbers",
        output_key="processed_numbers",
        parallel_subtasks=True  # Enable parallel subtask execution
    )
    
    dict_task = Task(
        name="process_dict",
        description="Process a dictionary of values",
        agent="splitter",
        input_key="dict_data",
        output_key="processed_dict",
        depends_on=["process_list"],  # This task depends on the list task
        parallel_subtasks=True
    )
    
    text_task = Task(
        name="process_text",
        description="Process a text string",
        agent="splitter",
        input_key="text",
        output_key="processed_text",
        depends_on=["process_dict"],  # This task depends on the dict task
        parallel_subtasks=True
    )
    
    # Create a project with the agent and tasks
    project = Project(
        name="subtasks-demo",
        description="Demonstration of subtask functionality",
        agents={"splitter": agent},
        tasks={
            "process_list": list_task,
            "process_dict": dict_task,
            "process_text": text_task
        }
    )
    
    # Create input data
    numbers = list(range(1, 21))  # List of numbers 1-20
    dict_data = {f"key_{i}": i for i in range(1, 21)}  # Dictionary with 20 key-value pairs
    text = "This is a sample text that will be split into multiple subtasks and processed in parallel."
    
    input_data = {
        "numbers": numbers,
        "dict_data": dict_data,
        "text": text
    }
    
    print(f"\nInput data:")
    print(f"- List: {numbers[:5]}... (20 items)")
    print(f"- Dictionary: {list(dict_data.items())[:3]}... (20 items)")
    print(f"- Text: {text}")
    
    # Create a project runner with parallel execution
    runner = ProjectRunner(project, parallel=True, max_workers=2)
    
    print("\nRunning the project with subtask support...")
    print("- Each task will be split into 4 subtasks")
    print("- Subtasks will be executed in parallel")
    
    # Track execution time
    start_time = time.time()
    
    # Run the project
    result = runner.run(input_data)
    
    duration = time.time() - start_time
    
    print(f"\nProject completed in {duration:.2f} seconds")
    
    # Print the results
    print("\nResults:")
    print(f"- Processed list: {result['process_list'][:5]}... ({len(result['process_list'])} items)")
    print(f"- Processed dict: {list(result['process_dict'].items())[:3]}... ({len(result['process_dict'])} items)")
    print(f"- Processed text: {result['process_text'][:50]}...")
    
    print("\nIn this example:")
    print("1. We created a TaskSplitterAgent that can split tasks into parallel subtasks")
    print("2. Each task was split into 4 subtasks that were executed in parallel")
    print("3. For list inputs, each number was incremented by 1")
    print("4. For dictionary inputs, each numeric value was incremented by 1")
    print("5. For text input, the text was converted to uppercase")
    print("\nThis pattern can be extended to implement complex distributed workflows!")

if __name__ == "__main__":
    main() 