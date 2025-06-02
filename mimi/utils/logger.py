"""Logging utilities for MiMi."""

import sys
from pathlib import Path
import os

# Add vendor directory to path to find loguru
vendor_path = Path(__file__).parent.parent / "vendor"
if vendor_path.exists() and str(vendor_path) not in sys.path:
    sys.path.append(str(vendor_path))

from typing import Any, Dict, List, Optional, Set, Union
import time

from loguru import logger as _logger

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.logging import RichHandler
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Rich library not found. Install it with 'pip install rich' for enhanced visualizations.")

# Console for rich output
console = Console() if RICH_AVAILABLE else None

# Allowed status/action types that will be logged
# Only logs with these status/action values will be shown
ALLOWED_LOG_TYPES: Set[str] = {"started", "execute", "completed", "error"}

# Task progress tracking
active_tasks = {}

def setup_logger(
    log_level: str = "DEBUG",
    log_file: Optional[str] = None,
    rotation: str = "10 MB",
    retention: str = "1 week",
    allowed_types: Optional[List[str]] = None,
    use_rich: bool = True
) -> None:
    """Configure the logger.

    Args:
        log_level: The log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to the log file.
        rotation: When to rotate the log file.
        retention: How long to keep log files.
        allowed_types: Optional list of status/action types to log. If None, uses ALLOWED_LOG_TYPES.
        use_rich: Whether to use rich formatting (if available).
    """
    global ALLOWED_LOG_TYPES
    
    # Update allowed types if provided
    if allowed_types is not None:
        ALLOWED_LOG_TYPES = set(allowed_types)
    
    _logger.remove()  # Remove default handlers
    
    # Add console handler
    if RICH_AVAILABLE and use_rich:
        # Use Rich for console logging
        _logger.add(
            RichHandler(
                console=console,
                rich_tracebacks=True,
                omit_repeated_times=False,
                show_level=True,
                show_path=False,
                markup=True,
                log_time_format="[%X]",
                level=log_level,
            ),
            format="{message}",  # Rich handler handles the formatting
        )
    else:
        # Fallback to regular console logging
        _logger.add(
            sys.stderr,
            level=log_level,
            format="{level} {time:YYYY-MM-DD HH:mm:ss} | {message}",
        )
    
    # Add file handler if specified
    if log_file:
        _logger.add(
            log_file,
            level=log_level,
            format="{level} | {time:YYYY-MM-DD HH:mm:ss} | {message}",
            rotation=rotation,
            retention=retention,
        )


# Convenience functions for structured logging
def agent_log(
    agent_name: str, action: str, message: str, data: Optional[Dict[str, Any]] = None
) -> None:
    """Log an agent action with structured data.
    
    Args:
        agent_name: Name of the agent.
        action: The action being performed.
        message: Log message.
        data: Optional additional data to log.
    """
    # Escape curly braces in the message to prevent KeyError in string formatting
    safe_message = str(message).replace("{", "{{").replace("}", "}}")
    
    if RICH_AVAILABLE and console:
        # Format message with Rich
        if action == "error":
            console.print(f"[bold red]Agent '{agent_name}'[/] | [red]{action}[/] | {safe_message}")
        elif action == "execute":
            console.print(f"[bold cyan]Agent '{agent_name}'[/] | [cyan]{action}[/] | {safe_message}")
        elif action == "completed":
            console.print(f"[bold green]Agent '{agent_name}'[/] | [green]{action}[/] | {safe_message}")
        else:
            console.print(f"[bold]Agent '{agent_name}'[/] | {action} | {safe_message}")
    else:
        # Fallback to regular logging
        _logger.info(
            f"Agent '{agent_name}' | {action} | {safe_message}",
            extra={"agent": agent_name, "action": action, "data": data or {}},
        )


def task_log(
    task_name: str, status: str, message: str, data: Optional[Dict[str, Any]] = None
) -> None:
    """Log a task event with structured data.
    
    Args:
        task_name: Name of the task.
        status: The status of the task (e.g., "started", "completed").
        message: Log message.
        data: Optional additional data to log.
    """
    # Escape curly braces in the message to prevent KeyError in string formatting
    safe_message = str(message).replace("{", "{{").replace("}", "}}")
    
    if RICH_AVAILABLE and console:
        # Format message with Rich
        if status == "started":
            # Store task start time
            active_tasks[task_name] = time.time()
            console.print(f"[bold blue]Task '{task_name}'[/] | [blue]{status}[/] | {safe_message}")
        elif status == "completed":
            # Calculate duration if we have the start time
            elapsed = 0.0  # Default value if no start time is found
            duration = ""
            if task_name in active_tasks:
                elapsed = time.time() - active_tasks[task_name]
                duration = f" (in {elapsed:.2f}s)"
                active_tasks.pop(task_name, None)
            
            # Get agent info from data if available
            agent_name = "Unknown"
            description = safe_message
            if data:
                if "agent" in data:
                    agent_name = data["agent"]
                if "description" in data:
                    description = data["description"]
            
            # Create a completion panel with structured format
            panel_content = f"""[bold blue]🔄 Task:[/] [bold green]{task_name}[/]
[bold yellow]📝 Description:[/] {description}
[bold cyan]👤 Agent:[/] {agent_name}
[bold green]⏱️ Duration:[/] {elapsed:.2f}s"""

            # Add output key info if available
            if data and "output_key" in data and data["output_key"]:
                panel_content += f"\n[bold magenta]📤 Output:[/] Stored result in output key '{data['output_key']}'"
            
            console.print(Panel(
                panel_content,
                title="✓ Task Completed",
                border_style="green",
                expand=False
            ))
        elif status == "error":
            console.print(f"[bold red]Task '{task_name}'[/] | [red]{status}[/] | {safe_message}")
        elif status == "warning":
            console.print(f"[bold yellow]Task '{task_name}'[/] | [yellow]{status}[/] | {safe_message}")
        elif status == "processing":
            console.print(f"[bold magenta]Task '{task_name}'[/] | [magenta]{status}[/] | {safe_message}")
        else:
            console.print(f"[bold]Task '{task_name}'[/] | {status} | {safe_message}")
    else:
        # Fallback to regular logging
        new_line = ("\n" + "=" * 150 + "\n") if status == 'completed' else ''
        _logger.info(
            f"Task '{task_name}' | {status} | {safe_message}{new_line}",
            extra={"task": task_name, "status": status, "data": data or {}},
        )


def project_log(
    project_name: str, status: str, message: str, data: Optional[Dict[str, Any]] = None
) -> None:
    """Log a project event with structured data.
    
    Args:
        project_name: Name of the project.
        status: The status of the project (e.g., "started", "completed").
        message: Log message.
        data: Optional additional data to log.
    """
    # Escape curly braces in the message to prevent KeyError in string formatting
    safe_message = str(message).replace("{", "{{").replace("}", "}}")
    
    if RICH_AVAILABLE and console:
        # Format message with Rich
        if status == "completed":
            console.print(Panel(
                f"[bold green]Project '{project_name}' completed![/]\n{safe_message}",
                title="✓ Project Completed",
                border_style="green",
                expand=False
            ))
        elif status == "init":
            console.print(f"[bold purple]Project '{project_name}'[/] | [purple]{status}[/] | {safe_message}")
        elif status == "planning":
            console.print(f"[bold yellow]Project '{project_name}'[/] | [yellow]{status}[/] | {safe_message}")
        elif status == "execute_task":
            console.print(f"[bold cyan]Project '{project_name}'[/] | [cyan]{status}[/] | {safe_message}")
        elif status == "task_completed":
            if data is not None and isinstance(data, dict) and "duration" in data:
                duration = data.get("duration", 0)
                console.print(f"[bold green]Project '{project_name}'[/] | [green]{status}[/] | {safe_message} in [bold]{duration:.2f}s[/]")
            else:
                console.print(f"[bold green]Project '{project_name}'[/] | [green]{status}[/] | {safe_message}")
        else:
            console.print(f"[bold]Project '{project_name}'[/] | {status} | {safe_message}")
    else:
        # Fallback to regular logging
        _logger.info(
            f"Project '{project_name}' | {status} | {safe_message}",
            extra={"project": project_name, "status": status, "data": data or {}},
        )


def print_intro():
    """Print an enhanced intro message for MiMi using Rich."""
    if RICH_AVAILABLE and console:
        console.print(Panel(
            "[bold cyan]Multi-agent, Multi-model AI Framework[/]",
            title="[bold blue]MiMi v1.0[/]",
            border_style="cyan",
            expand=False
        ))
    else:
        print("""
    ╔════════════════════════════════════════════════╗
    ║                                                ║
    ║                   MiMi v1.0                    ║
    ║     Multi-agent, Multi-model AI Framework      ║
    ║                                                ║
    ╚════════════════════════════════════════════════╝
    """)


def print_result_summary(result, project, args):
    """Print a formatted summary of the project results."""
    if not RICH_AVAILABLE or not console:
        return  # Only available with Rich
    
    # Create a results table
    results_table = Table(title="Results Summary", show_header=True, header_style="bold magenta")
    results_table.add_column("Category", style="dim")
    results_table.add_column("Details", style="cyan")
    
    # Show keys in the result
    result_keys = ", ".join(result.keys())
    results_table.add_row("Output Keys", result_keys)
    
    # Agent statistics
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
    
    # Agent statistics
    agent_count = len([a for a in agent_stats.values() if a["task_count"] > 0])
    task_count = len(task_counts)
    results_table.add_row("Agents Used", f"{agent_count} agents completed {task_count} tasks")
    
    # Top agents
    agents_sorted = sorted(agent_stats.items(), key=lambda x: x[1]["task_count"], reverse=True)
    top_agents = []
    for agent_name, stats in agents_sorted[:3]:  # Show top 3
        if stats["task_count"] > 0:
            top_agents.append(f"{agent_name} ({stats['role']}): {stats['task_count']} tasks")
    
    results_table.add_row("Top Agents", "\n".join(top_agents))
    
    # Parallel execution
    parallel_status = "Enabled" if args.parallel else "Disabled"
    results_table.add_row("Parallel Execution", f"{parallel_status} (max workers: {args.max_workers})")
    
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
        results_table.add_row("Max Parallel Tasks", f"{max_parallel} tasks with same dependencies")
        results_table.add_row("Parallel Task Group", ", ".join(max_parallel_tasks))
    
    # Success status
    results_table.add_row("Status", "[bold green]Workflow completed successfully![/]")
    
    # Print the table
    console.print(results_table)


def update_allowed_log_types(types: List[str]) -> None:
    """Update the list of allowed log types.
    
    Args:
        types: List of status/action types to allow in logs.
    """
    global ALLOWED_LOG_TYPES
    ALLOWED_LOG_TYPES = set(types)


# Initialize logger with default settings
setup_logger()

# Export the logger instance
logger = _logger 