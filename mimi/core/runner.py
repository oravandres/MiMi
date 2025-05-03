"""Runners for executing projects and tasks in MiMi."""

from typing import Any, Dict, List, Optional, Union, Set
import concurrent.futures
from concurrent.futures import Future
import threading
import time

from mimi.core.project import Project
from mimi.core.task import Task
from mimi.utils.logger import logger, project_log, task_log


class TaskRunner:
    """Runner for executing individual tasks."""

    def __init__(self, task: Task, agent_lookup: Dict[str, Any]) -> None:
        """Initialize the task runner.
        
        Args:
            task: The task to execute.
            agent_lookup: Dictionary mapping agent names to agent objects.
        """
        self.task = task
        self.agent_lookup = agent_lookup
        task_log(
            task.name,
            "init",
            f"Task runner initialized for task '{task.name}'",
        )
        
    def run(self, input_data: Any) -> Any:
        """Execute the task with the provided input.
        
        Args:
            input_data: Input data for the task.
            
        Returns:
            The output from the task execution.
        """
        task_log(
            self.task.name,
            "started",
            f"Executing task with agent '{self.task.agent}'",
        )
        
        result = self.task.execute(self.agent_lookup, input_data)
        
        task_log(
            self.task.name,
            "completed",
            f"Stored result in output key '{self.task.output_key}'",
        )
        
        task_log(
            self.task.name,
            "completed",
            f"Task '{self.task.name}' completed",
        )
        
        return result


class ProjectRunner:
    """Runner for executing entire projects."""

    def __init__(self, project: Project, parallel: bool = True, max_workers: int = 3) -> None:
        """Initialize the project runner.
        
        Args:
            project: The project to execute.
            parallel: Whether to execute independent tasks in parallel.
            max_workers: Maximum number of parallel workers.
        """
        self.project = project
        self.parallel = parallel
        self.max_workers = max_workers
        self.results = {}  # Store task results by name
        
        project_log(
            project.name,
            "init",
            f"Project runner initialized for project '{project.name}' (parallel={parallel}, max_workers={max_workers})",
        )
        
    def _run_task(self, task_name: str, task_input: Any) -> Dict[str, Any]:
        """Execute a single task and store its result.
        
        Args:
            task_name: Name of the task to execute.
            task_input: Input data for the task.
            
        Returns:
            A dictionary with the task result.
        """
        task = self.project.tasks[task_name]
        runner = TaskRunner(task, self.project.agents)
        
        project_log(
            self.project.name,
            "execute_task",
            f"Executing task '{task_name}'",
        )
        
        start_time = time.time()
        result = runner.run(task_input)
        duration = time.time() - start_time
        
        # Store the result with metadata
        with threading.Lock():
            self.results[task_name] = {
                "data": result,
                "duration": duration,
                "task": task_name,
                "output_key": task.output_key
            }
        
        project_log(
            self.project.name,
            "task_completed",
            f"Task '{task_name}' completed in {duration:.2f}s",
        )
        
        return self.results[task_name]
    
    def _get_ready_tasks(self, completed_tasks: Set[str]) -> List[str]:
        """Get tasks that are ready to execute based on dependencies.
        
        Args:
            completed_tasks: Set of already completed task names.
            
        Returns:
            List of task names that are ready to execute.
        """
        ready_tasks = []
        
        for task_name, task in self.project.tasks.items():
            # Skip if task is already completed
            if task_name in completed_tasks:
                continue
            
            # Skip if task is already being processed in an active future
            if hasattr(self, '_processing_tasks') and task_name in getattr(self, '_processing_tasks'):
                continue
                
            # Check if all dependencies are satisfied
            if all(dep in completed_tasks for dep in task.depends_on):
                ready_tasks.append(task_name)
        
        # Group tasks by dependency level for better batch processing
        if ready_tasks and self.parallel and len(ready_tasks) > 1:
            # Group by dependency pattern
            dependency_groups = {}
            for task_name in ready_tasks:
                task = self.project.tasks[task_name]
                
                # Create a key based on dependencies
                deps_key = ','.join(sorted(task.depends_on))
                if deps_key in dependency_groups:
                    dependency_groups[deps_key].append(task_name)
                else:
                    dependency_groups[deps_key] = [task_name]
            
            # Prioritize the largest group for this batch
            if dependency_groups:
                largest_group = max(dependency_groups.values(), key=len)
                
                # If we have more than one task in the largest group, focus on those
                if len(largest_group) > 1:
                    logger.info(f"Grouping {len(largest_group)} tasks with same dependency pattern for parallel execution")
                    return largest_group
        
        return ready_tasks
        
    def run(self, input_data: Any) -> Any:
        """Execute the project with the provided input.
        
        Tasks are executed in dependency order, with independent tasks running in parallel.
        
        Args:
            input_data: Input data for the project.
            
        Returns:
            The final result after executing all tasks.
        """
        project_log(
            self.project.name,
            "run",
            f"Running project '{self.project.name}' with parallel={self.parallel}",
            data={"input": input_data},
        )
        
        # Initialize the results dictionary with the input data
        self.results = {
            "input": {
                "data": input_data,
                "output_key": "input"
            }
        }
        
        # Get all tasks and track completed ones
        all_tasks = set(self.project.tasks.keys())
        completed_tasks = set()
        self._processing_tasks = set()  # Track tasks currently being processed
        
        # Create executor for parallel execution
        if self.parallel:
            executor_class = concurrent.futures.ThreadPoolExecutor
        else:
            # For sequential execution, we'll still use ThreadPoolExecutor but with max_workers=1
            executor_class = lambda max_workers: concurrent.futures.ThreadPoolExecutor(max_workers=1)
        
        with executor_class(max_workers=self.max_workers) as executor:
            # Continue until all tasks are completed
            while len(completed_tasks) < len(all_tasks):
                # Get tasks that are ready to execute
                ready_tasks = self._get_ready_tasks(completed_tasks)
                
                if not ready_tasks:
                    if len(completed_tasks) < len(all_tasks):
                        logger.warning(f"No tasks ready but not all completed. Possible circular dependency.")
                        break
                    else:
                        break
                
                # Log the batch of tasks to be executed
                project_log(
                    self.project.name,
                    "planning",
                    f"Executing batch of {len(ready_tasks)} tasks: {ready_tasks}",
                )
                
                # Prepare inputs for each ready task
                task_futures = {}
                
                for task_name in ready_tasks:
                    task = self.project.tasks[task_name]
                    
                    # Prepare input based on dependencies
                    if task.input_key == "":
                        # If no input key specified, use the entire results
                        task_input = {k: v["data"] for k, v in self.results.items()}
                    else:
                        # Handle special cases for integration and review tasks
                        if task_name == "integration":
                            # For integration task, pass the raw results dictionary
                            # This ensures all implementation results are available
                            logger.info(f"Preparing special input for integration task")
                            task_input = {
                                key: value for key, value in self.results.items()
                                if key in ("backend-implementation", "frontend-implementation", "infrastructure-implementation")
                            }
                            # Also include the task specifications
                            if "input" in self.results:
                                task_input["input"] = self.results["input"]
                        else:
                            # Regular input handling - find the dependency with the matching output key
                            found_input = False
                            for dep_name in task.depends_on:
                                dep_task = self.project.tasks.get(dep_name)
                                if dep_task and dep_task.output_key == task.input_key:
                                    if dep_name in self.results:
                                        task_input = self.results[dep_name]["data"]
                                        found_input = True
                                        break
                            
                            # If no matching output key found, use the input directly
                            if not found_input:
                                if task.input_key in input_data:
                                    task_input = input_data[task.input_key]
                                else:
                                    # Fall back to using the entire results object
                                    task_input = {k: v["data"] for k, v in self.results.items() if "data" in v}
                    
                    # Submit the task to the executor
                    future = executor.submit(self._run_task, task_name, task_input)
                    task_futures[future] = task_name
                    self._processing_tasks.add(task_name)  # Mark this task as being processed
                
                # Wait for all tasks in this batch to complete
                for future in concurrent.futures.as_completed(task_futures):
                    task_name = task_futures[future]
                    try:
                        result = future.result()
                        completed_tasks.add(task_name)
                        self._processing_tasks.remove(task_name)  # Remove task from processing set
                    except Exception as e:
                        # Make sure to remove task from processing set even on error
                        self._processing_tasks.remove(task_name)
                        logger.error(f"Error executing task '{task_name}': {str(e)}")
                        project_log(
                            self.project.name,
                            "error",
                            f"Error executing task '{task_name}': {str(e)}",
                        )
                        raise
        
        # Get final result
        final_result = {}
        for k, v in self.results.items():
            if k == "input":
                final_result[k] = v["data"]
            else:
                final_result[k] = v["data"]
        
        # Log completion with statistics
        task_stats = {task_name: f"{result['duration']:.2f}s" for task_name, result in self.results.items() if "duration" in result}
        total_tasks = len(all_tasks)
        parallel_batches = len(set(tuple(t.depends_on) for t in self.project.tasks.values()))
        
        project_log(
            self.project.name,
            "completed",
            f"Project '{self.project.name}' completed",
            data={
                "tasks_executed": total_tasks,
                "parallel_batches": parallel_batches,
                "task_durations": task_stats
            },
        )
        
        return final_result 