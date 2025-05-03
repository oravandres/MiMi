#!/usr/bin/env python3
"""Main entry point for the MiMi package."""

import argparse
import sys
from pathlib import Path

from mimi.core.project import Project
from mimi.core.runner import ProjectRunner
from mimi.utils.logger import setup_logger


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="MiMi - Multi Agent Multi Model Framework")
    
    parser.add_argument(
        "-c", "--config", 
        required=True,
        help="Path to the project configuration directory"
    )
    
    parser.add_argument(
        "-d", "--description", 
        required=True,
        help="Project description input"
    )
    
    parser.add_argument(
        "-l", "--log-level", 
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level"
    )
    
    parser.add_argument(
        "--log-file", 
        help="Path to log file (if not specified, logs to console only)"
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true",
        default=True,
        help="Execute independent tasks in parallel (default: True)"
    )
    
    parser.add_argument(
        "--no-parallel",
        action="store_false",
        dest="parallel",
        help="Disable parallel execution of tasks"
    )
    
    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Maximum number of parallel workers (default: 4)"
    )
    
    return parser.parse_args()


def print_intro():
    """Print the MiMi framework introduction message."""
    print("""
    ╔════════════════════════════════════════════════╗
    ║                                                ║
    ║                   MiMi v1.0                    ║
    ║     Multi-agent, Multi-model AI Framework      ║
    ║                                                ║
    ╚════════════════════════════════════════════════╝
    """)


def main():
    """Run the MiMi framework with command line arguments."""
    try:
        # Parse command line arguments
        args = parse_args()
        
        # Setup logging
        setup_logger(
            log_level=args.log_level,
            log_file=args.log_file,
        )
        
        # Print the intro message
        print_intro()
        
        # Load the project from the specified config directory
        config_dir = Path(args.config)
        
        # If config_dir doesn't contain a project.yaml file, try appending "/config"
        if not (config_dir / "project.yaml").exists():
            config_dir = config_dir / "config"
            
            # Check if the config directory exists
            if not config_dir.exists() or not (config_dir / "project.yaml").exists():
                print(f"Error: Could not find project.yaml in {config_dir}. Please check the config path.")
                return 1
        
        project = Project.from_config(config_dir)
        
        # Create a project runner
        runner = ProjectRunner(
            project, 
            parallel=args.parallel, 
            max_workers=args.max_workers
        )
        
        # Initialize the project
        project.initialize()
        
        # Run the project
        try:
            result = runner.run({"input": args.description})
            
            # Print the result
            print("\nResults:")
            if isinstance(result, dict):
                # Display any result keys
                result_keys_found = False
                for key, value in result.items():
                    if key.startswith("result"):
                        print(f"  {key}: {value}")
                        result_keys_found = True
                
                # If no result keys, show final output keys
                if not result_keys_found:
                    print(f"  Final output contains keys: {', '.join(result.keys())}")
                    
                    # If there's a status or final_approval, show it
                    if "status" in result:
                        print(f"  Status: {result['status']}")
                    if "final_approval" in result:
                        # Check if final_approval is a string before slicing
                        final_approval = result['final_approval']
                        if isinstance(final_approval, str):
                            print(f"  Final approval: {final_approval[:100]}...")
                        else:
                            print(f"  Final approval: {str(final_approval)}")
            
                # Display statistics about the run
                print("\nStatistics:")
                agent_stats = {}
                task_counts = {}
                task_durations = {}
                
                # Collect agent usage statistics
                for agent_name, agent in project.agents.items():
                    agent_stats[agent_name] = {
                        "role": agent.role,
                        "model": f"{agent.model_provider}/{agent.model_name}",
                        "task_count": 0
                    }
                
                # Process results to get task stats
                for key, value in result.items():
                    if isinstance(value, dict) and "duration" in value:
                        task_name = value.get("task", key)
                        duration = value.get("duration", 0)
                        agent_name = None
                        
                        # Find the task in the project
                        if task_name in project.tasks:
                            task = project.tasks[task_name]
                            agent_name = task.agent
                            
                            # Update stats
                            task_durations[task_name] = duration
                            
                            if agent_name in agent_stats:
                                agent_stats[agent_name]["task_count"] += 1
                            
                            if task_name in task_counts:
                                task_counts[task_name] += 1
                            else:
                                task_counts[task_name] = 1
                
                # Collect task statistics from execution order
                if not task_durations:
                    execution_order = project.get_execution_order()
                    for task_name in execution_order:
                        task = project.tasks[task_name]
                        agent_name = task.agent
                        
                        if agent_name in agent_stats:
                            agent_stats[agent_name]["task_count"] += 1
                        
                        if task_name in task_counts:
                            task_counts[task_name] += 1
                        else:
                            task_counts[task_name] = 1
                
                # Display agent statistics
                agent_count = len([a for a in agent_stats.values() if a["task_count"] > 0])
                task_count = len(task_counts)
                print(f"  Used {agent_count} agents to complete {task_count} tasks")
                
                # Show busiest agents
                agents_sorted = sorted(agent_stats.items(), key=lambda x: x[1]["task_count"], reverse=True)
                print("  Top agents by task count:")
                for agent_name, stats in agents_sorted[:3]:  # Show top 3
                    if stats["task_count"] > 0:
                        print(f"    - {agent_name} ({stats['role']}): {stats['task_count']} tasks")
                
                # Show parallel execution metrics
                parallel_status = "Enabled" if args.parallel else "Disabled"
                print(f"\n  Parallel execution: {parallel_status} (max workers: {args.max_workers})")
                
                # Calculate parallel batches
                depends_on_groups = {}
                for task_name, task in project.tasks.items():
                    deps_key = ','.join(sorted(task.depends_on))
                    if deps_key in depends_on_groups:
                        depends_on_groups[deps_key].append(task_name)
                    else:
                        depends_on_groups[deps_key] = [task_name]
                
                # Find the most parallelizable task groups
                max_parallel = 0
                max_parallel_tasks = []
                
                for deps, tasks in depends_on_groups.items():
                    if len(tasks) > max_parallel:
                        max_parallel = len(tasks)
                        max_parallel_tasks = tasks
                
                if max_parallel > 1:
                    print(f"  Max parallel tasks: {max_parallel} tasks with same dependencies")
                    print(f"    Tasks: {', '.join(max_parallel_tasks)}")
                
                # Show timing info if available
                if task_durations:
                    print("\n  Task timing:")
                    sorted_durations = sorted(task_durations.items(), key=lambda x: x[1], reverse=True)
                    for task_name, duration in sorted_durations[:5]:  # Show top 5 longest tasks
                        print(f"    - {task_name}: {duration:.2f}s")
            
            print(f"\n  Workflow completed successfully!")
            return 0
            
        except Exception as e:
            print(f"Error running project: {str(e)}")
            import traceback
            traceback.print_exc()
            return 1
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main()) 