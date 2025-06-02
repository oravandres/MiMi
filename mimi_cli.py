#!/usr/bin/env python3
"""
MiMi CLI Interface
A simple command-line interface for MiMi with colorful output.
"""

import os
import sys
import json
import time
import threading
from pathlib import Path

# Colors and formatting for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Add MiMi to path if not already there
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

try:
    # Import MiMi modules
    from mimi.core.runner import ProjectRunner
    from mimi.utils.logger import task_log as original_task_log
    from mimi.utils.logger import agent_log as original_agent_log
except ImportError:
    print(f"{Colors.RED}MiMi framework not found. Make sure you're running from the MiMi directory.{Colors.ENDC}")
    sys.exit(1)

# Global variables
active_tasks = {}  # Track active tasks and their start times
runner_thread = None
should_stop = False
tasks = []
agents = []

# Task log interceptor
def task_log_intercept(task_name, status, message, data=None):
    # Store task start time
    if status == "started":
        active_tasks[task_name] = time.time()
    
    # Calculate elapsed time for completed tasks
    elapsed = 0.0
    if status == "completed" and task_name in active_tasks:
        elapsed = time.time() - active_tasks[task_name]
        active_tasks.pop(task_name, None)
    
    # Extract additional info
    agent = data.get("agent", "Unknown") if data else "Unknown"
    description = data.get("description", message) if data else message
    
    # Format status with colors
    if status == "started":
        status_colored = f"{Colors.BLUE}{status}{Colors.ENDC}"
    elif status == "completed":
        status_colored = f"{Colors.GREEN}{status}{Colors.ENDC}"
    elif status == "error":
        status_colored = f"{Colors.RED}{status}{Colors.ENDC}"
    elif status == "processing":
        status_colored = f"{Colors.YELLOW}{status}{Colors.ENDC}"
    else:
        status_colored = status
    
    # Add task to tasks list or update existing one
    found = False
    for i, task in enumerate(tasks):
        if task["name"] == task_name:
            tasks[i] = {
                "name": task_name,
                "status": status,
                "agent": agent,
                "elapsed": elapsed if elapsed > 0 else 0,
                "description": description
            }
            found = True
            break
    
    if not found:
        tasks.append({
            "name": task_name,
            "status": status,
            "agent": agent,
            "elapsed": elapsed if elapsed > 0 else 0,
            "description": description
        })
    
    # Print task status
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] Task {Colors.BOLD}'{task_name}'{Colors.ENDC}: {status_colored}")
    
    if agent and agent != "Unknown":
        print(f"  Agent: {Colors.CYAN}{agent}{Colors.ENDC}")
    
    if description and description != task_name and description != message:
        print(f"  Description: {description}")
    
    if elapsed > 0:
        print(f"  Duration: {elapsed:.2f}s")
    
    # Call original function
    if original_task_log:
        original_task_log(task_name, status, message, data)

# Agent log interceptor
def agent_log_intercept(agent_name, action, message, data=None):
    # Add agent to agents list if not already there
    if agent_name not in [a["name"] for a in agents]:
        agents.append({
            "name": agent_name,
            "actions": []
        })
    
    # Add action to agent's actions
    for agent in agents:
        if agent["name"] == agent_name:
            agent["actions"].append({
                "action": action,
                "message": message,
                "timestamp": time.strftime("%H:%M:%S")
            })
    
    # Format action with colors
    if action == "error":
        action_colored = f"{Colors.RED}{action}{Colors.ENDC}"
    elif action == "completed":
        action_colored = f"{Colors.GREEN}{action}{Colors.ENDC}"
    elif action == "execute":
        action_colored = f"{Colors.YELLOW}{action}{Colors.ENDC}"
    else:
        action_colored = action
    
    # Print agent status
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] Agent {Colors.CYAN}{agent_name}{Colors.ENDC} | {action_colored}: {message}")
    
    # Call original function
    if original_agent_log:
        original_agent_log(agent_name, action, message, data)

def print_progress():
    """Print progress summary."""
    total_tasks = len(tasks)
    if total_tasks == 0:
        return
    
    completed_tasks = len([t for t in tasks if t["status"] == "completed"])
    progress_percent = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
    
    # Create a progress bar
    bar_width = 40
    filled_width = int(bar_width * progress_percent / 100)
    bar = '█' * filled_width + ' ' * (bar_width - filled_width)
    
    print(f"\n{Colors.BOLD}Progress:{Colors.ENDC} [{Colors.GREEN}{bar}{Colors.ENDC}] {progress_percent:.0f}%")
    print(f"{Colors.BOLD}Tasks:{Colors.ENDC} {completed_tasks}/{total_tasks} completed\n")

def print_task_summary():
    """Print a summary of all tasks."""
    if not tasks:
        print(f"{Colors.YELLOW}No tasks have been run yet.{Colors.ENDC}")
        return
    
    print(f"\n{Colors.HEADER}{Colors.BOLD}Task Summary:{Colors.ENDC}")
    print(f"{'Task Name':<30} {'Status':<15} {'Agent':<20} {'Duration':<10}")
    print("-" * 80)
    
    for task in tasks:
        # Format status with colors
        if task["status"] == "completed":
            status_colored = f"{Colors.GREEN}{task['status']}{Colors.ENDC}"
        elif task["status"] == "error":
            status_colored = f"{Colors.RED}{task['status']}{Colors.ENDC}"
        elif task["status"] == "processing":
            status_colored = f"{Colors.YELLOW}{task['status']}{Colors.ENDC}"
        elif task["status"] == "started":
            status_colored = f"{Colors.BLUE}{task['status']}{Colors.ENDC}"
        else:
            status_colored = task["status"]
        
        # Format duration
        duration = f"{task['elapsed']:.2f}s" if task['elapsed'] > 0 else "-"
        
        print(f"{task['name']:<30} {status_colored:<30} {task['agent']:<20} {duration:<10}")
    
    print("-" * 80)

def print_agent_summary():
    """Print a summary of all agents."""
    if not agents:
        print(f"{Colors.YELLOW}No agents have been used yet.{Colors.ENDC}")
        return
    
    print(f"\n{Colors.HEADER}{Colors.BOLD}Agent Summary:{Colors.ENDC}")
    for agent in agents:
        print(f"\n{Colors.CYAN}{Colors.BOLD}Agent: {agent['name']}{Colors.ENDC}")
        
        if not agent["actions"]:
            print(f"  {Colors.YELLOW}No actions recorded{Colors.ENDC}")
        else:
            for action in agent["actions"]:
                # Format action with colors
                if action["action"] == "error":
                    action_colored = f"{Colors.RED}{action['action']}{Colors.ENDC}"
                elif action["action"] == "completed":
                    action_colored = f"{Colors.GREEN}{action['action']}{Colors.ENDC}"
                elif action["action"] == "execute":
                    action_colored = f"{Colors.YELLOW}{action['action']}{Colors.ENDC}"
                else:
                    action_colored = action["action"]
                
                print(f"  [{action['timestamp']}] {action_colored}: {action['message']}")

def run_mimi(project_name, prompt, config_path=None):
    """Run MiMi with the given parameters."""
    global should_stop, tasks, agents
    
    # Clear previous task and agent data
    tasks = []
    agents = []
    
    # Monkey patch the logger functions
    import mimi.utils.logger
    mimi.utils.logger.task_log = task_log_intercept
    mimi.utils.logger.agent_log = agent_log_intercept
    
    try:
        # Print info
        print(f"\n{Colors.HEADER}{Colors.BOLD}Starting MiMi Project: {project_name}{Colors.ENDC}")
        print(f"{Colors.BOLD}Prompt:{Colors.ENDC} {prompt}\n")
        
        # Initialize the runner
        runner = ProjectRunner(project_name)
        
        # Load config if provided
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            runner.load_config(config)
            print(f"{Colors.BOLD}Using config:{Colors.ENDC} {config_path}\n")
        
        # Run the project
        start_time = time.time()
        result = runner.run(prompt)
        end_time = time.time()
        
        # Print completion message
        elapsed = end_time - start_time
        print(f"\n{Colors.GREEN}{Colors.BOLD}Project completed successfully in {elapsed:.2f}s{Colors.ENDC}")
        
        # Print task and agent summaries
        print_task_summary()
        print_agent_summary()
        
        # Print result
        print(f"\n{Colors.HEADER}{Colors.BOLD}Result:{Colors.ENDC}")
        print(json.dumps(result, indent=2))
        
        return result
        
    except Exception as e:
        print(f"\n{Colors.RED}{Colors.BOLD}Error: {str(e)}{Colors.ENDC}")
        return None
    finally:
        # Restore original logger functions
        mimi.utils.logger.task_log = original_task_log
        mimi.utils.logger.agent_log = original_agent_log

def run_mimi_thread(project_name, prompt, config_path=None):
    """Run MiMi in a background thread."""
    global runner_thread, should_stop
    
    if runner_thread and runner_thread.is_alive():
        print(f"{Colors.YELLOW}A project is already running.{Colors.ENDC}")
        return
    
    should_stop = False
    runner_thread = threading.Thread(
        target=run_mimi,
        args=(project_name, prompt, config_path)
    )
    runner_thread.daemon = True
    runner_thread.start()

def print_help():
    """Print the help message."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}MiMi CLI Interface{Colors.ENDC}")
    print(f"\n{Colors.BOLD}Available commands:{Colors.ENDC}")
    print(f"  {Colors.GREEN}run <project_name> <prompt>{Colors.ENDC} - Run a MiMi project")
    print(f"  {Colors.GREEN}config <config_path>{Colors.ENDC} - Use a config file for the next run")
    print(f"  {Colors.GREEN}tasks{Colors.ENDC} - Show a summary of tasks")
    print(f"  {Colors.GREEN}agents{Colors.ENDC} - Show a summary of agents")
    print(f"  {Colors.GREEN}progress{Colors.ENDC} - Show the current progress")
    print(f"  {Colors.GREEN}clear{Colors.ENDC} - Clear the screen")
    print(f"  {Colors.GREEN}help{Colors.ENDC} - Show this help message")
    print(f"  {Colors.GREEN}exit{Colors.ENDC} - Exit the program")

def main():
    """Main function to run the CLI."""
    config_path = None
    
    print(f"\n{Colors.BOLD}{Colors.HEADER}MiMi CLI Interface{Colors.ENDC}")
    print(f"Type {Colors.GREEN}help{Colors.ENDC} for a list of commands.\n")
    
    while True:
        try:
            cmd = input(f"{Colors.BOLD}MiMi>{Colors.ENDC} ").strip()
            
            if not cmd:
                continue
            
            parts = cmd.split()
            command = parts[0].lower()
            
            if command == "exit":
                break
            elif command == "help":
                print_help()
            elif command == "clear":
                os.system('cls' if os.name == 'nt' else 'clear')
            elif command == "run":
                if len(parts) < 3:
                    print(f"{Colors.RED}Usage: run <project_name> <prompt>{Colors.ENDC}")
                    continue
                
                project_name = parts[1]
                prompt = " ".join(parts[2:])
                run_mimi(project_name, prompt, config_path)
            elif command == "config":
                if len(parts) < 2:
                    print(f"{Colors.RED}Usage: config <config_path>{Colors.ENDC}")
                    continue
                
                config_path = parts[1]
                print(f"{Colors.GREEN}Config file set to: {config_path}{Colors.ENDC}")
            elif command == "tasks":
                print_task_summary()
            elif command == "agents":
                print_agent_summary()
            elif command == "progress":
                print_progress()
            else:
                print(f"{Colors.RED}Unknown command: {command}{Colors.ENDC}")
                print(f"Type {Colors.GREEN}help{Colors.ENDC} for a list of commands.")
        
        except KeyboardInterrupt:
            print("\nUse 'exit' to quit")
        except Exception as e:
            print(f"{Colors.RED}Error: {str(e)}{Colors.ENDC}")

if __name__ == "__main__":
    main() 