"""Directory utility functions for MiMi."""

import os
from pathlib import Path
import logging

from mimi.utils.logger import logger

def ensure_project_directory_exists(base_dir: str = "projects") -> Path:
    """
    Ensures the projects directory exists in the current working directory.
    Creates it if it doesn't exist, but only once.
    
    Args:
        base_dir: Directory name to create. Defaults to "projects".
        
    Returns:
        Path object to the created or existing directory.
    """
    # Use Path for cross-platform compatibility
    project_dir = Path(base_dir)
    
    if not project_dir.exists():
        try:
            project_dir.mkdir(exist_ok=True)
            logger.info(f"Created projects directory at: {project_dir.absolute()}")
        except Exception as e:
            logger.error(f"Failed to create projects directory: {e}")
    else:
        logger.debug(f"Projects directory already exists at: {project_dir.absolute()}")
    
    return project_dir 