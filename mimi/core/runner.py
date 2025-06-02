"""Runners for executing projects and tasks in MiMi."""

from typing import Any, Dict, List, Optional, Union, Set
import concurrent.futures
from concurrent.futures import Future
import threading
import time
from pathlib import Path

from mimi.core.project import Project
from mimi.core.task import Task, SubTask
from mimi.utils.logger import logger, project_log, task_log


class TaskRunner:
    """Runner for executing individual tasks."""

    def __init__(self, task: Task, agent_lookup: Dict[str, Any], max_subtask_workers: int = 4) -> None:
        """Initialize the task runner.
        
        Args:
            task: The task to execute.
            agent_lookup: Dictionary mapping agent names to agent objects.
            max_subtask_workers: Maximum number of parallel workers for subtasks.
        """
        self.task = task
        self.agent_lookup = agent_lookup
        self.max_subtask_workers = max_subtask_workers
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
            f"Runner executing task with agent '{self.task.agent}'",
        )
        
        # Execute the task, which may create subtasks
        result = self.task.execute(self.agent_lookup, input_data)
        
        # If the task created subtasks, execute them
        if self.task.has_subtasks():
            task_log(
                self.task.name,
                "subtasks",
                f"Task created {len(self.task.get_subtasks())} subtasks. Executing them.",
            )
            result = self._execute_subtasks(result)
        
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

    def _execute_subtasks(self, parent_result: Any) -> Any:
        """Execute subtasks in parallel and combine their results.
        
        Args:
            parent_result: The result from the parent task's execution.
            
        Returns:
            The combined result from all subtasks.
        """
        subtasks = self.task.get_subtasks()
        if not subtasks:
            return parent_result
            
        agent = self.agent_lookup[self.task.agent]
        results = {}
        
        # First, preprocess the subtasks to check dependencies
        subtask_map = {subtask.id: subtask for subtask in subtasks}
        dependency_map = {subtask.id: subtask.depends_on for subtask in subtasks}
        
        # Track completed subtasks
        completed_subtasks = set()
        
        # Create a new executor for subtasks
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_subtask_workers) as executor:
            # Continue until all subtasks are completed
            while len(completed_subtasks) < len(subtasks):
                # Find subtasks that are ready to execute (all dependencies satisfied)
                ready_subtasks = []
                for subtask_id, dependencies in dependency_map.items():
                    if subtask_id not in completed_subtasks and all(dep in completed_subtasks for dep in dependencies):
                        ready_subtasks.append(subtask_id)
                
                if not ready_subtasks:
                    if len(completed_subtasks) < len(subtasks):
                        logger.warning(f"No subtasks ready but not all completed. Possible circular dependency.")
                        break
                    else:
                        break
                
                task_log(
                    self.task.name,
                    "subtasks",
                    f"Executing batch of {len(ready_subtasks)} subtasks",
                )
                
                # Submit ready subtasks to the executor
                futures = {}
                for subtask_id in ready_subtasks:
                    subtask = subtask_map[subtask_id]
                    future = executor.submit(self._execute_single_subtask, subtask, agent)
                    futures[future] = subtask_id
                
                # Wait for submitted subtasks to complete
                for future in concurrent.futures.as_completed(futures):
                    subtask_id = futures[future]
                    try:
                        result = future.result()
                        subtask_map[subtask_id] = result  # Update subtask with result
                        completed_subtasks.add(subtask_id)
                    except Exception as e:
                        logger.error(f"Error executing subtask {subtask_id}: {str(e)}")
                        # Consider the subtask completed even if it failed
                        completed_subtasks.add(subtask_id)
        
        # Once all subtasks are completed, combine their results
        task_log(
            self.task.name,
            "subtasks",
            f"All subtasks completed. Combining results.",
        )
        
        subtasks_with_results = list(subtask_map.values())
        return agent.combine_subtask_results(subtasks_with_results, parent_result)
    
    def _execute_single_subtask(self, subtask: SubTask, agent: Any) -> SubTask:
        """Execute a single subtask and update it with the result.
        
        Args:
            subtask: The subtask to execute.
            agent: The agent to use for execution.
            
        Returns:
            The updated subtask object with result.
        """
        task_log(
            self.task.name,
            "subtask",
            f"Executing subtask '{subtask.name}'",
        )
        
        try:
            start_time = time.time()
            result = agent.execute_subtask(subtask)
            duration = time.time() - start_time
            
            # Update the subtask with the result and duration
            subtask.result = result
            subtask.duration = duration
            
            task_log(
                self.task.name,
                "subtask",
                f"Subtask '{subtask.name}' completed in {duration:.2f}s",
            )
            
            return subtask
        except Exception as e:
            logger.error(f"Error in subtask execution: {str(e)}")
            # Add error information to the subtask
            subtask.result = {"error": str(e)}
            subtask.duration = 0
            
            return subtask


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
        
    def _run_task(self, task_name: str, task_input: Any) -> Dict[str, Any]:
        """Execute a single task and store its result.
        
        Args:
            task_name: Name of the task to execute.
            task_input: Input data for the task.
            
        Returns:
            A dictionary with the task result.
        """
        task = self.project.tasks[task_name]
        runner = TaskRunner(task, self.project.agents, max_subtask_workers=4)
        
        project_log(
            self.project.name,
            "execute_task",
            f"Executing task '{task_name}'",
        )
        
        # Ensure project metadata is properly passed to each task
        if isinstance(task_input, dict):
            # Log detailed task input for debugging
            input_keys = list(task_input.keys()) if isinstance(task_input, dict) else []
            
            logger.debug(f"Task input type: {type(task_input)}")
            logger.debug(f"Task input: {str(task_input).replace('{', '{{').replace('}', '}}')}")

            # Log project metadata in task input
            if "project_dir" in task_input:
                logger.debug(
                    f"ProjectRunner._run_task for '{task_name}' - project_dir in input: "
                    f"type={type(task_input['project_dir'])}, value='{task_input['project_dir']}'"
                )
                # Check project_dir type and convert to Path if needed
                if not isinstance(task_input["project_dir"], Path):
                    project_dir_str = str(task_input["project_dir"])
                    task_input["project_dir"] = Path(project_dir_str)
                    logger.debug(f"Converted project_dir from string to Path: {task_input['project_dir']}")
            else:
                # Try to extract project_dir from input['input'] if it exists
                promoted = False
                if "input" in task_input and isinstance(task_input["input"], dict):
                    if "project_dir" in task_input["input"]:
                        task_input["project_dir"] = task_input["input"]["project_dir"]
                        logger.debug(f"Promoted project_dir from 'input' to top level: {task_input['project_dir']}")
                        promoted = True
                    # Also promote project_title if present in nested input
                    if "project_title" in task_input["input"]:
                        task_input["project_title"] = task_input["input"]["project_title"]
                        logger.debug(f"Promoted project_title from 'input' to top level: {task_input['project_title']}")
                if not promoted:
                    logger.debug(f"ProjectRunner._run_task for '{task_name}' - No project_dir in input (even after promotion). Keys: {input_keys}")
            # Always ensure we have project_title
            if "project_title" not in task_input:
                # Set from self.project.name as a last resort
                task_input["project_title"] = self.project.name
                logger.debug(f"Set project_title from self.project.name: {self.project.name}")
        
        # Execute the task
        time_start = time.time()
        result = runner.run(task_input)
        execution_time = time.time() - time_start
        
        # Make sure the result includes project_dir and title if they exist in input
        if isinstance(result, dict) and isinstance(task_input, dict):
            # Propagate project_dir to result
            if "project_dir" in task_input:
                found_project_dir = False
                
                # Check if project_dir already exists in result
                if "project_dir" in result:
                    found_project_dir = True
                elif "data" in result and isinstance(result["data"], dict) and "project_dir" in result["data"]:
                    # Extract project_dir from nested data
                    project_dir = result["data"]["project_dir"]
                    result["project_dir"] = project_dir
                    found_project_dir = True
                    logger.debug(f"Propagated project_dir from result.data to top level: {project_dir}")
                
                # If project_dir not found in result, add it from input
                if not found_project_dir:
                    result["project_dir"] = task_input["project_dir"]
                    logger.debug(f"Propagated project_dir to task result: {task_input['project_dir']}")
            
            # Propagate project_title to result
            if "project_title" in task_input and "project_title" not in result:
                result["project_title"] = task_input["project_title"]
                logger.debug(f"Propagated project_title to task result: {task_input['project_title']}")
        
        # Mark the task as completed
        project_log(
            self.project.name,
            "task_completed",
            f"Task '{task_name}' completed in {execution_time:.2f}s",
        )
        
        return result
    
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
                                        # Extract the specific value stored under the output_key
                                        # The task result is stored as: self.results[dep_name]["data"]
                                        # And the agent result was stored under the output_key by Task.execute()
                                        dep_result_data = self.results[dep_name]["data"]
                                        if isinstance(dep_result_data, dict) and dep_task.output_key in dep_result_data:
                                            task_input = dep_result_data[dep_task.output_key]
                                        else:
                                            # Fallback to the entire result if output_key not found
                                            task_input = dep_result_data
                                        found_input = True
                                        break
                            
                            # If no matching output key found, use the input directly
                            if not found_input:
                                if isinstance(task.input_key, str):
                                    # Handle single input key
                                    if task.input_key in input_data:
                                        task_input = input_data[task.input_key]
                                    else:
                                        # Fall back to using the entire results object
                                        task_input = {k: v["data"] for k, v in self.results.items() if "data" in v}
                                elif isinstance(task.input_key, list):
                                    # Handle list of input keys
                                    collected_inputs = {}
                                    for key in task.input_key:
                                        if key in input_data:
                                            collected_inputs[key] = input_data[key]
                                    
                                    if collected_inputs:
                                        task_input = collected_inputs
                                    else:
                                        # Fall back to using the entire results object
                                        task_input = {k: v["data"] for k, v in self.results.items() if "data" in v}
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
                        # Store the task result in the results dictionary with the proper structure
                        task = self.project.tasks[task_name]
                        self.results[task_name] = {
                            "data": result,
                            "output_key": task.output_key,
                            "duration": result.get("duration", 0.0) if isinstance(result, dict) else 0.0
                        }
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