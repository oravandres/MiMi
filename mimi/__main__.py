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
        "-i", "--input", 
        required=True,
        help="Input value for the project"
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
    
    return parser.parse_args()


def main():
    """Run the MiMi framework with command line arguments."""
    args = parse_args()
    
    # Setup logging
    setup_logger(
        log_level=args.log_level,
        log_file=args.log_file,
    )
    
    try:
        # Load the project
        project = Project.from_config(args.config)
        
        # Create a runner
        runner = ProjectRunner(project)
        
        # Run the project
        result = runner.run({"input": args.input})
        
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
                    print(f"  Final approval: {result['final_approval'][:100]}...")
            
            # Display statistics about the run
            print("\nStatistics:")
            agent_stats = {}
            for agent_name, agent in project.agents.items():
                agent_stats[agent_name] = {
                    "role": agent.role,
                    "model": f"{agent.model_provider}/{agent.model_name}"
                }
            
            print(f"  Agents used: {len(agent_stats)}")
            for name, stats in agent_stats.items():
                print(f"  - {name} ({stats['role']}): {stats['model']}")
            
            print(f"  Tasks completed: {len(project.get_execution_order())}")
            print(f"  Workflow completed successfully!")
        else:
            print(f"  Final result: {result}")
            
        return 0
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main()) 