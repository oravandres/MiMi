#!/usr/bin/env python3
"""
MiMi Desktop Application using Tkinter
A graphical user interface for the MiMi multi-agent AI framework.
"""

import sys
import os
import json
import time
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from tkinter.font import Font

# Add MiMi to path if it's not already there
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

# Import MiMi modules
try:
    from mimi.core.runner import ProjectRunner
    from mimi.utils.logger import logger, task_log, agent_log, print_intro
    from mimi.utils import ensure_project_directory_exists
except ImportError:
    print("MiMi framework not found. Make sure you're running from the MiMi directory.")
    sys.exit(1)

class MimiTkApp:
    """Main application for the MiMi framework using Tkinter."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("MiMi Multi-Agent AI Framework")
        self.root.geometry("900x700")
        
        # Enable responsiveness
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        
        # Ensure projects directory exists
        self.projects_dir = ensure_project_directory_exists()
        
        # Store original logging functions
        self.original_task_log = task_log
        self.original_agent_log = agent_log
        
        # Set up UI components
        self.setup_ui()
        
        # Add welcome message
        self.log_output.insert(tk.END, "Welcome to MiMi\n", "heading")
        self.log_output.insert(tk.END, "The Multi-agent, Multi-model AI Framework\n\n", "subheading")
        self.log_output.insert(tk.END, "Enter a prompt and click Run to start.\n", "normal")
        
        # Set up worker thread
        self.worker_thread = None
        self.should_stop = False
        
        # Dictionary to track active tasks and their start times
        self.active_tasks = {}
        
    def setup_ui(self):
        """Set up all UI components."""
        # Top frame for settings
        self.top_frame = ttk.Frame(self.root, padding="10")
        self.top_frame.grid(row=0, column=0, sticky="ew")
        
        # Project settings
        ttk.Label(self.top_frame, text="Project Name:").grid(row=0, column=0, sticky="w", padx=5)
        self.project_name = ttk.Entry(self.top_frame, width=30)
        self.project_name.grid(row=0, column=1, sticky="ew", padx=5)
        
        ttk.Label(self.top_frame, text="Config:").grid(row=0, column=2, sticky="w", padx=5)
        self.config_combo = ttk.Combobox(self.top_frame, values=["Default"], state="readonly")
        self.config_combo.current(0)
        self.config_combo.grid(row=0, column=3, sticky="ew", padx=5)
        
        self.load_config_btn = ttk.Button(self.top_frame, text="Load Config", command=self.load_config)
        self.load_config_btn.grid(row=0, column=4, padx=5)
        
        # Toggle dark theme
        self.theme_var = tk.BooleanVar(value=False)
        self.theme_check = ttk.Checkbutton(
            self.top_frame, text="Dark Theme", variable=self.theme_var, 
            command=self.toggle_theme
        )
        self.theme_check.grid(row=0, column=5, padx=10)
        
        # About button
        self.about_btn = ttk.Button(self.top_frame, text="About", command=self.show_about)
        self.about_btn.grid(row=0, column=6, padx=5)
        
        # Prompt input
        ttk.Label(self.top_frame, text="Enter your prompt:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.prompt_frame = ttk.Frame(self.top_frame)
        self.prompt_frame.grid(row=2, column=0, columnspan=7, sticky="nsew", padx=5, pady=5)
        
        self.prompt_input = scrolledtext.ScrolledText(self.prompt_frame, height=5, wrap=tk.WORD)
        self.prompt_input.pack(fill=tk.BOTH, expand=True)
        
        # Run button
        self.run_button = ttk.Button(
            self.top_frame, text="Run", command=self.run_mimi,
            style="Accent.TButton"
        )
        self.run_button.grid(row=3, column=0, columnspan=7, sticky="ew", padx=5, pady=10)
        
        # Main content pane with notebook
        self.content_frame = ttk.Frame(self.root)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=1)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Log tab
        self.log_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.log_tab, text="Log")
        
        self.log_output = scrolledtext.ScrolledText(self.log_tab, wrap=tk.WORD)
        self.log_output.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for formatting
        self.log_output.tag_configure("heading", font=Font(family="Helvetica", size=16, weight="bold"))
        self.log_output.tag_configure("subheading", font=Font(family="Helvetica", size=12, weight="bold"))
        self.log_output.tag_configure("normal", font=Font(family="Helvetica", size=10))
        self.log_output.tag_configure("task_started", foreground="blue")
        self.log_output.tag_configure("task_completed", foreground="green")
        self.log_output.tag_configure("task_error", foreground="red")
        self.log_output.tag_configure("agent_message", foreground="purple")
        
        # Tasks tab
        self.tasks_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.tasks_tab, text="Tasks")
        
        # Create treeview for tasks
        self.tasks_tree = ttk.Treeview(
            self.tasks_tab, 
            columns=("task", "status", "agent", "duration"),
            show="headings"
        )
        self.tasks_tree.heading("task", text="Task")
        self.tasks_tree.heading("status", text="Status")
        self.tasks_tree.heading("agent", text="Agent")
        self.tasks_tree.heading("duration", text="Duration")
        
        self.tasks_tree.column("task", width=250)
        self.tasks_tree.column("status", width=100)
        self.tasks_tree.column("agent", width=150)
        self.tasks_tree.column("duration", width=100)
        
        # Add scrollbar to treeview
        tasks_scrollbar = ttk.Scrollbar(self.tasks_tab, orient="vertical", command=self.tasks_tree.yview)
        self.tasks_tree.configure(yscrollcommand=tasks_scrollbar.set)
        
        tasks_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tasks_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Agents tab
        self.agents_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.agents_tab, text="Agents")
        
        # Create listbox for agents
        self.agents_list = tk.Listbox(self.agents_tab)
        
        # Add scrollbar to listbox
        agents_scrollbar = ttk.Scrollbar(self.agents_tab, orient="vertical", command=self.agents_list.yview)
        self.agents_list.configure(yscrollcommand=agents_scrollbar.set)
        
        agents_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.agents_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Results tab
        self.results_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.results_tab, text="Results")
        
        self.results_output = scrolledtext.ScrolledText(self.results_tab, wrap=tk.WORD)
        self.results_output.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_frame = ttk.Frame(self.root, padding="5 0 5 5")
        self.status_frame.grid(row=2, column=0, sticky="ew")
        
        self.progress_bar = ttk.Progressbar(self.status_frame, mode="determinate")
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_label = ttk.Label(self.status_frame, text="Status: Ready")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Create custom style for buttons
        s = ttk.Style()
        s.configure("Accent.TButton", font=("Helvetica", 12))
    
    def toggle_theme(self):
        """Toggle between light and dark theme."""
        if self.theme_var.get():
            # Dark theme
            self.root.tk_setPalette(
                background='#333333',
                foreground='#FFFFFF',
                activeBackground='#666666',
                activeForeground='#FFFFFF')
        else:
            # Light theme (default)
            self.root.tk_setPalette(
                background=self.root.cget('background'),
                foreground=self.root.cget('foreground'))
    
    def load_config(self):
        """Load a configuration file."""
        file_path = filedialog.askopenfilename(
            title="Select Config File",
            filetypes=[("JSON Files", "*.json")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    config = json.load(f)
                
                # Add to combo box if not already there
                config_name = os.path.basename(file_path)
                if config_name not in self.config_combo["values"]:
                    values = list(self.config_combo["values"])
                    values.append(config_name)
                    self.config_combo["values"] = values
                
                # Select the newly added config
                self.config_combo.set(config_name)
                
                # Store file path
                self.config_path = file_path
                
                # Show confirmation
                self.log_output.insert(tk.END, f"Loaded config: {config_name}\n", "normal")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load config: {str(e)}")
    
    def run_mimi(self):
        """Run the MiMi framework with the current settings."""
        # Get input values
        project_name = self.project_name.get()
        prompt = self.prompt_input.get("1.0", tk.END).strip()
        
        if not project_name:
            messagebox.showwarning("Missing Information", "Please enter a project name.")
            return
        
        if not prompt:
            messagebox.showwarning("Missing Information", "Please enter a prompt.")
            return
        
        # Clear previous results
        self.tasks_tree.delete(*self.tasks_tree.get_children())
        self.agents_list.delete(0, tk.END)
        self.results_output.delete("1.0", tk.END)
        self.log_output.delete("1.0", tk.END)
        
        # Reset active tasks tracking
        self.active_tasks = {}
        
        # Disable run button and show progress
        self.run_button.configure(state="disabled")
        self.progress_bar["value"] = 0
        self.status_label.configure(text="Status: Running")
        
        # Log the start
        self.log_output.insert(tk.END, f"Starting project: {project_name}\n", "heading")
        self.log_output.insert(tk.END, f"Prompt: {prompt}\n\n", "normal")
        
        # Monkey patch the logger
        import mimi.utils.logger
        mimi.utils.logger.task_log = self.task_log_intercept
        mimi.utils.logger.agent_log = self.agent_log_intercept
        
        # Create and start worker thread
        self.should_stop = False
        self.worker_thread = threading.Thread(
            target=self.mimi_worker, 
            args=(project_name, prompt)
        )
        self.worker_thread.daemon = True
        self.worker_thread.start()
    
    def task_log_intercept(self, task_name, status, message, data=None):
        """Intercept task log calls to update the UI."""
        # Store task start time
        if status == "started":
            self.active_tasks[task_name] = time.time()
        
        # Calculate elapsed time for completed tasks
        elapsed = 0.0
        if status == "completed" and task_name in self.active_tasks:
            elapsed = time.time() - self.active_tasks[task_name]
            self.active_tasks.pop(task_name, None)
        
        # Extract additional info
        agent = data.get("agent", "Unknown") if data else "Unknown"
        description = data.get("description", message) if data else message
        
        # Update UI from main thread
        self.root.after(0, self.update_task_status, task_name, status, agent, elapsed, description)
        
        # Call original function if needed
        if self.original_task_log:
            self.original_task_log(task_name, status, message, data)
    
    def agent_log_intercept(self, agent_name, action, message, data=None):
        """Intercept agent log calls to update the UI."""
        # Update UI from main thread
        self.root.after(0, self.update_agent_status, agent_name, action, message)
        
        # Call original function if needed
        if self.original_agent_log:
            self.original_agent_log(agent_name, action, message, data)
    
    def update_task_status(self, task_name, status, agent, elapsed, description):
        """Update the task status in the UI."""
        # Find existing task or create new one
        task_id = None
        for item_id in self.tasks_tree.get_children():
            if self.tasks_tree.item(item_id)["values"][0] == task_name:
                task_id = item_id
                break
        
        # If task not found, create new entry
        if not task_id and task_name:
            task_id = self.tasks_tree.insert(
                "", "end", 
                values=(task_name, status, agent, f"{elapsed:.2f}s" if elapsed > 0 else "")
            )
        
        # Update existing entry
        if task_id:
            self.tasks_tree.item(
                task_id, 
                values=(task_name, status, agent, f"{elapsed:.2f}s" if elapsed > 0 else "")
            )
            
            # Set background color based on status
            if status == "completed":
                self.tasks_tree.item(task_id, tags=("completed",))
            elif status == "error":
                self.tasks_tree.item(task_id, tags=("error",))
            elif status == "processing":
                self.tasks_tree.item(task_id, tags=("processing",))
        
        # Add log entry
        timestamp = time.strftime("%H:%M:%S")
        tag = f"task_{status}" if status in ["started", "completed", "error"] else "normal"
        
        log_entry = f"[{timestamp}] Task '{task_name}': {status}"
        if agent and agent != "Unknown":
            log_entry += f" (Agent: {agent})"
        if description and description != task_name:
            log_entry += f"\n    {description}"
        log_entry += "\n"
        
        self.log_output.insert(tk.END, log_entry, tag)
        self.log_output.see(tk.END)
        
        # Update progress estimation
        self.update_progress()
    
    def update_agent_status(self, agent_name, action, message):
        """Update the agent status in the UI."""
        # Add to agent list if not already there
        agent_exists = False
        for i in range(self.agents_list.size()):
            if self.agents_list.get(i).startswith(f"Agent: {agent_name}"):
                agent_exists = True
                break
        
        if not agent_exists:
            self.agents_list.insert(tk.END, f"Agent: {agent_name}")
        
        # Add log entry
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] Agent '{agent_name}' | {action}: {message}\n"
        self.log_output.insert(tk.END, log_entry, "agent_message")
        self.log_output.see(tk.END)
    
    def update_progress(self):
        """Update the progress bar and status display."""
        # Count tasks
        all_tasks = self.tasks_tree.get_children()
        total_tasks = len(all_tasks)
        
        if total_tasks == 0:
            return
        
        # Count completed tasks
        completed_tasks = 0
        for task_id in all_tasks:
            if self.tasks_tree.item(task_id)["values"][1] == "completed":
                completed_tasks += 1
        
        # Update progress bar
        progress_percent = (completed_tasks / total_tasks) * 100
        self.progress_bar["value"] = progress_percent
        
        # Update status label
        self.status_label.configure(text=f"Status: {completed_tasks}/{total_tasks} tasks completed")
    
    def mimi_worker(self, project_name, prompt):
        """Worker function to run MiMi in a background thread."""
        config_path = getattr(self, "config_path", None)
        
        try:
            # Initialize the runner
            runner = ProjectRunner(project_name)
            
            # Load config if provided
            if config_path and os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                runner.load_config(config)
            
            # Run the project
            result = runner.run(prompt)
            
            # Display results
            self.root.after(0, self.handle_results, result)
            
        except Exception as e:
            # Handle errors
            self.root.after(0, self.handle_error, str(e))
        finally:
            # Restore original logging functions
            import mimi.utils.logger
            mimi.utils.logger.task_log = self.original_task_log
            mimi.utils.logger.agent_log = self.original_agent_log
    
    def handle_results(self, results):
        """Handle the results from the MiMi framework."""
        # Enable run button
        self.run_button.configure(state="normal")
        
        # Update status
        self.progress_bar["value"] = 100
        self.status_label.configure(text="Status: Completed")
        
        # Display results
        self.results_output.delete("1.0", tk.END)
        self.results_output.insert(tk.END, json.dumps(results, indent=2))
        
        # Switch to results tab
        self.notebook.select(self.results_tab)
        
        # Log completion
        self.log_output.insert(tk.END, "Project completed successfully\n", "heading")
    
    def handle_error(self, error_message):
        """Handle an error from the MiMi framework."""
        # Enable run button
        self.run_button.configure(state="normal")
        
        # Update status
        self.progress_bar["value"] = 0
        self.status_label.configure(text=f"Status: Error")
        
        # Log error
        self.log_output.insert(tk.END, f"Error: {error_message}\n", "task_error")
        
        # Show error message
        messagebox.showerror("Error", f"An error occurred: {error_message}")
    
    def show_about(self):
        """Show the about dialog."""
        about_text = """
MiMi Multi-Agent AI Framework

A powerful framework for orchestrating multiple AI agents to work together.

Features:
- Multiple specialized agents
- Task parallelization
- Multi-model support
- Structured output and visualization

Version: 1.0
        """
        
        messagebox.showinfo("About MiMi", about_text)


if __name__ == "__main__":
    # Create root window
    root = tk.Tk()
    
    # Create and start app
    app = MimiTkApp(root)
    
    # Run the main loop
    root.mainloop() 