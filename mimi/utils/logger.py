"""Logging utilities for MiMi."""

import sys
from pathlib import Path
import os

# Add vendor directory to path to find loguru
vendor_path = Path(__file__).parent.parent / "vendor"
if vendor_path.exists() and str(vendor_path) not in sys.path:
    sys.path.append(str(vendor_path))

from typing import Any, Dict, List, Optional, Set, Union

from loguru import logger as _logger

# Allowed status/action types that will be logged
# Only logs with these status/action values will be shown
ALLOWED_LOG_TYPES: Set[str] = {"started", "execute", "completed", "error"}

def setup_logger(
    log_level: str = "DEBUG",
    log_file: Optional[str] = None,
    rotation: str = "10 MB",
    retention: str = "1 week",
    allowed_types: Optional[List[str]] = None,
) -> None:
    """Configure the logger.

    Args:
        log_level: The log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to the log file.
        rotation: When to rotate the log file.
        retention: How long to keep log files.
        allowed_types: Optional list of status/action types to log. If None, uses ALLOWED_LOG_TYPES.
    """
    global ALLOWED_LOG_TYPES
    
    # Update allowed types if provided
    if allowed_types is not None:
        ALLOWED_LOG_TYPES = set(allowed_types)
    
    _logger.remove()  # Remove default handlers
    
    # Add console handler
    _logger.add(
        sys.stderr,
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
    )
    
    # Add file handler if specified
    if log_file:
        _logger.add(
            log_file,
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
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
    # Skip logging if action is not in allowed types
    if action not in ALLOWED_LOG_TYPES:
        return
    
    # Escape curly braces in the message to prevent KeyError in string formatting
    safe_message = str(message).replace("{", "{{").replace("}", "}}")
    
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
    # Skip logging if status is not in allowed types
    if status not in ALLOWED_LOG_TYPES:
        print(f"Skipping log for task '{task_name}' with status '{status}'")
        return
    
    # Escape curly braces in the message to prevent KeyError in string formatting
    safe_message = str(message).replace("{", "{{").replace("}", "}}")
    
    _logger.info(
        f"Task '{task_name}' | {status} | {safe_message}{'\\n' if status == 'completed' else ''}",
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
    # Skip logging if status is not in allowed types
    if status not in ALLOWED_LOG_TYPES:
        return
    
    # Escape curly braces in the message to prevent KeyError in string formatting
    safe_message = str(message).replace("{", "{{").replace("}", "}}")
    
    _logger.info(
        f"Project '{project_name}' | {status} | {safe_message}",
        extra={"project": project_name, "status": status, "data": data or {}},
    )


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