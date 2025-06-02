#!/usr/bin/env python3
"""Main entry point for the MiMi package."""

import argparse
import sys
from pathlib import Path

from mimi.core.project import Project
from mimi.core.runner import ProjectRunner
from mimi.utils.logger import setup_logger, print_intro, print_result_summary


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
    
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )
    
    return parser.parse_args()


def main():
    """Run the MiMi framework with command line arguments."""
    try:
        # Parse command line arguments
        args = parse_args()
        
        # Setup logging
        setup_logger(
            log_level=args.log_level,
            log_file=args.log_file,
            use_rich=not args.no_color,
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
        
        # Import logger here to avoid circular imports
        from mimi.utils.logger import logger
        
        # Load the project configuration
        logger.debug(f"Loading project from config directory: {config_dir}")
        project = Project.from_config(config_dir)
        
        # Create a project directory for output if needed
        from mimi.utils.output_manager import create_output_directory
        project_dir = create_output_directory(project.name)
        
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
            # Add project_dir to input data
            input_data = {"input": args.description, "project_dir": project_dir}
            logger.debug(f"Running project with input: {str(input_data).replace('{', '{{').replace('}', '}}')}")
            
            result = runner.run(input_data)
            
            # Print the result using enhanced output
            print_result_summary(result, project, args)
            
            return 0
            
        except Exception as e:
            print(f"Error running project: {str(e)}")
            import traceback
            traceback.print_exc()
            return 1
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 