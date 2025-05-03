"""Configuration utilities for MiMi."""

import sys
from pathlib import Path
import os
import yaml
from typing import Any, Dict, List, Optional, Union

# Add vendor directory to path to find pydantic
vendor_path = Path(__file__).parent.parent / "vendor"
if vendor_path.exists() and str(vendor_path) not in sys.path:
    sys.path.append(str(vendor_path))

from pydantic import BaseModel

from mimi.utils.logger import logger


class ConfigLoadError(Exception):
    """Exception raised when a configuration file cannot be loaded."""

    pass


def load_yaml_config(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Load a YAML configuration file.
    
    Args:
        file_path: Path to the YAML file.
        
    Returns:
        Dict containing the configuration.
        
    Raises:
        ConfigLoadError: If the file cannot be loaded or parsed.
    """
    try:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
            
        with open(path, "r") as file:
            config = yaml.safe_load(file)
            
        if not isinstance(config, dict):
            raise ValueError(f"Invalid configuration format in {file_path}. Expected a dictionary.")
            
        return config
    except (yaml.YAMLError, FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load configuration from {file_path}: {str(e)}")
        raise ConfigLoadError(f"Failed to load configuration: {str(e)}") from e


def load_project_config(config_dir: Union[str, Path]) -> Dict[str, Any]:
    """Load a complete project configuration from a directory.
    
    Expects 'project.yaml' in the config directory.
    
    Args:
        config_dir: Directory containing configuration files.
        
    Returns:
        Dict containing the complete project configuration.
        
    Raises:
        ConfigLoadError: If the project file cannot be loaded.
    """
    config_path = Path(config_dir)
    
    try:
        # Load the project configuration from project.yaml
        project_config = load_yaml_config(config_path / "project.yaml")
        
        # Extract agents from the project config
        agents_config = {"agents": project_config.get("agents", [])}
        
        # Extract tasks from each sub-project
        all_tasks = []
        for sub_project in project_config.get("sub_projects", []):
            tasks = sub_project.get("tasks", [])
            # Annotate tasks with their sub-project
            for task in tasks:
                task["sub_project"] = sub_project.get("name")
            all_tasks.extend(tasks)
        
        tasks_config = {"tasks": all_tasks}
        
        # Return a structure similar to the old format for compatibility
        return {
            "project": project_config,
            "agents": agents_config,
            "tasks": tasks_config,
        }
    except ConfigLoadError as e:
        logger.error(f"Failed to load project configuration from {config_dir}: {str(e)}")
        raise ConfigLoadError(f"Failed to load project configuration: {str(e)}") from e 