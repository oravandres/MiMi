#!/usr/bin/env python3
"""
MiMi Desktop Application
A graphical user interface for the MiMi multi-agent AI framework.
"""

import sys
import os
import json
import time
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, 
    QWidget, QTextEdit, QLineEdit, QLabel, QComboBox, QTabWidget,
    QTreeWidget, QTreeWidgetItem, QProgressBar, QSplitter, QFrame,
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal, Slot, QThread, QTimer
from PySide6.QtGui import QFont, QColor, QIcon, QPalette

# Add MiMi to path if it's not already there
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

# Import MiMi modules
try:
    from mimi.core.runner import ProjectRunner
    from mimi.utils.logger import logger, print_intro
    from mimi.utils import ensure_project_directory_exists
except ImportError:
    print("MiMi framework not found. Make sure you're running from the MiMi directory.")
    sys.exit(1)

class MimiWorker(QThread):
    """Worker thread to run MiMi tasks without blocking the UI."""
    finished = Signal(dict)
    progress = Signal(str, str, str, float)  # (task_name, status, agent, duration)
    agent_signal = Signal(str, str, str)  # (agent_name, action, message)
    error = Signal(str)

    def __init__(self, project_name, prompt, config_path=None):
        super().__init__()
        self.project_name = project_name
        self.prompt = prompt
        self.config_path = config_path

    def run(self):
        try:
            # Save original functions to restore later
            original_task_log = None
            original_agent_log = None
            
            # Helper functions to intercept log events
            def ui_task_log(task_name, status, message, data=None):
                # Extract additional info
                agent = data.get("agent", "Unknown") if data else "Unknown"
                duration = 0.0
                description = data.get("description", message) if data else message
                output_key = data.get("output_key", None) if data else None
                
                # Emit signal with relevant info
                self.progress.emit(task_name, status, agent, duration)
                
                # Call original if we stored it
                if original_task_log:
                    original_task_log(task_name, status, message, data)
                
            def ui_agent_log(agent_name, action, message, data=None):
                # Emit signal
                self.agent_signal.emit(agent_name, action, message)
                
                # Call original if we stored it
                if original_agent_log:
                    original_agent_log(agent_name, action, message, data)
            
            # Patch the logger functions
            from mimi.utils.logger import task_log, agent_log
            original_task_log = task_log
            original_agent_log = agent_log
            
            # Monkey patch the logging functions
            import mimi.utils.logger
            mimi.utils.logger.task_log = ui_task_log
            mimi.utils.logger.agent_log = ui_agent_log
            
            # Initialize the runner
            runner = ProjectRunner(self.project_name)
            
            # Load config if provided
            if self.config_path and os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                runner.load_config(config)
            
            # Run the project
            result = runner.run(self.prompt)
            
            # Restore original functions
            mimi.utils.logger.task_log = original_task_log
            mimi.utils.logger.agent_log = original_agent_log
            
            # Emit the result
            self.finished.emit(result)
        
        except Exception as e:
            # Restore original functions if needed
            import mimi.utils.logger
            if original_task_log:
                mimi.utils.logger.task_log = original_task_log
            if original_agent_log:
                mimi.utils.logger.agent_log = original_agent_log
                
            self.error.emit(str(e))


class MimiApp(QMainWindow):
    """Main window for the MiMi application."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("MiMi Multi-Agent AI Framework")
        self.setMinimumSize(900, 700)
        
        # Ensure projects directory exists
        self.projects_dir = ensure_project_directory_exists()
        
        # Initialize UI
        self.setup_ui()
        
        # Add welcome message
        self.log_output.append("<h2>Welcome to MiMi</h2>")
        self.log_output.append("<p>The Multi-agent, Multi-model AI Framework</p>")
        self.log_output.append("<p>Enter a prompt and click Run to start.</p>")
        
        # Active worker thread
        self.worker = None
        
        # Timer for updating the UI
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(1000)  # Update every second
        
        # Apply initial theme
        self.apply_theme(is_dark=False)
        
    def setup_ui(self):
        """Set up the user interface."""
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # Top toolbar
        toolbar_layout = QHBoxLayout()
        
        # Dark mode toggle
        self.theme_toggle = QCheckBox("Dark Theme")
        self.theme_toggle.toggled.connect(self.toggle_theme)
        toolbar_layout.addWidget(self.theme_toggle)
        
        # Add spacer to push remaining items to the right
        toolbar_layout.addStretch()
        
        # About button
        about_button = QPushButton("About")
        about_button.clicked.connect(self.show_about)
        toolbar_layout.addWidget(about_button)
        
        main_layout.addLayout(toolbar_layout)
        
        # Create splitter for resizable sections
        splitter = QSplitter(Qt.Vertical)
        
        # Top section - Input area
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        
        # Project settings
        settings_layout = QHBoxLayout()
        
        # Project name input
        self.project_name_label = QLabel("Project Name:")
        self.project_name = QLineEdit()
        self.project_name.setPlaceholderText("Enter project name")
        settings_layout.addWidget(self.project_name_label)
        settings_layout.addWidget(self.project_name)
        
        # Config selection
        self.config_label = QLabel("Config:")
        self.config_combo = QComboBox()
        self.config_combo.addItem("Default", None)
        self.load_config_button = QPushButton("Load Config")
        self.load_config_button.clicked.connect(self.load_config)
        settings_layout.addWidget(self.config_label)
        settings_layout.addWidget(self.config_combo)
        settings_layout.addWidget(self.load_config_button)
        
        top_layout.addLayout(settings_layout)
        
        # Prompt input
        prompt_label = QLabel("Enter your prompt:")
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Describe what you want to create...")
        self.prompt_input.setMinimumHeight(100)
        
        top_layout.addWidget(prompt_label)
        top_layout.addWidget(self.prompt_input)
        
        # Run button
        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.run_mimi)
        self.run_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        top_layout.addWidget(self.run_button)
        
        # Add top widget to splitter
        splitter.addWidget(top_widget)
        
        # Bottom section - Output area with tabs
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        
        # Tabs for different views
        self.tabs = QTabWidget()
        
        # Log tab
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        log_layout.addWidget(self.log_output)
        self.tabs.addTab(log_tab, "Log")
        
        # Tasks tab
        tasks_tab = QWidget()
        tasks_layout = QVBoxLayout(tasks_tab)
        self.tasks_tree = QTreeWidget()
        self.tasks_tree.setHeaderLabels(["Task", "Status", "Agent", "Duration"])
        self.tasks_tree.setColumnWidth(0, 250)
        tasks_layout.addWidget(self.tasks_tree)
        self.tabs.addTab(tasks_tab, "Tasks")
        
        # Agents tab
        agents_tab = QWidget()
        agents_layout = QVBoxLayout(agents_tab)
        self.agents_list = QListWidget()
        agents_layout.addWidget(self.agents_list)
        self.tabs.addTab(agents_tab, "Agents")
        
        # Results tab
        results_tab = QWidget()
        results_layout = QVBoxLayout(results_tab)
        self.results_output = QTextEdit()
        self.results_output.setReadOnly(True)
        results_layout.addWidget(self.results_output)
        self.tabs.addTab(results_tab, "Results")
        
        # Add tabs to bottom layout
        bottom_layout.addWidget(self.tabs)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Ready")
        bottom_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Status: Ready")
        bottom_layout.addWidget(self.status_label)
        
        # Add bottom widget to splitter
        splitter.addWidget(bottom_widget)
        
        # Set initial sizes
        splitter.setSizes([300, 400])
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
        
        # Set main widget
        self.setCentralWidget(main_widget)
    
    def load_config(self):
        """Load a configuration file."""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "Select Config File", "", "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    config = json.load(f)
                
                # Add to combo box if not already there
                config_name = os.path.basename(file_path)
                existing_items = [self.config_combo.itemText(i) for i in range(self.config_combo.count())]
                
                if config_name not in existing_items:
                    self.config_combo.addItem(config_name, file_path)
                
                # Select the newly added config
                self.config_combo.setCurrentText(config_name)
                
                # Show confirmation
                self.log_output.append(f"<p>Loaded config: {config_name}</p>")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load config: {str(e)}")
    
    def run_mimi(self):
        """Run the MiMi framework with the current settings."""
        # Get input values
        project_name = self.project_name.text()
        prompt = self.prompt_input.toPlainText()
        config_path = self.config_combo.currentData()
        
        if not project_name:
            QMessageBox.warning(self, "Missing Information", "Please enter a project name.")
            return
        
        if not prompt:
            QMessageBox.warning(self, "Missing Information", "Please enter a prompt.")
            return
        
        # Clear previous results
        self.tasks_tree.clear()
        self.agents_list.clear()
        self.results_output.clear()
        self.log_output.clear()
        
        # Disable run button and show progress
        self.run_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Initializing...")
        self.status_label.setText("Status: Running")
        
        # Log the start
        self.log_output.append(f"<h3>Starting project: {project_name}</h3>")
        self.log_output.append(f"<p><b>Prompt:</b> {prompt}</p>")
        
        # Create and start worker thread
        self.worker = MimiWorker(project_name, prompt, config_path)
        self.worker.progress.connect(self.update_task_status)
        self.worker.agent_signal.connect(self.update_agent_status)
        self.worker.finished.connect(self.handle_results)
        self.worker.error.connect(self.handle_error)
        self.worker.start()
    
    @Slot(str, str, str, float)
    def update_task_status(self, task_name, status, agent, duration):
        """Update the status of a task in the UI."""
        # Find existing task or create new one
        found = False
        for i in range(self.tasks_tree.topLevelItemCount()):
            item = self.tasks_tree.topLevelItem(i)
            if item.text(0) == task_name:
                item.setText(1, status)
                item.setText(2, agent)
                
                # Only update duration if we have a real value
                if duration > 0:
                    item.setText(3, f"{duration:.2f}s")
                
                if status == "completed":
                    item.setBackground(1, QColor(200, 255, 200))  # Light green
                elif status == "error":
                    item.setBackground(1, QColor(255, 200, 200))  # Light red
                elif status == "processing":
                    item.setBackground(1, QColor(200, 200, 255))  # Light blue
                found = True
                break
        
        if not found and task_name:
            item = QTreeWidgetItem([task_name, status, agent, f"{duration:.2f}s" if duration > 0 else ""])
            if status == "completed":
                item.setBackground(1, QColor(200, 255, 200))
            elif status == "error":
                item.setBackground(1, QColor(255, 200, 200))
            elif status == "processing":
                item.setBackground(1, QColor(200, 200, 255))
            self.tasks_tree.addTopLevelItem(item)
        
        # Add log entry
        timestamp = time.strftime("%H:%M:%S")
        self.log_output.append(f"<p>[{timestamp}] Task '{task_name}': {status} (Agent: {agent})</p>")
        
        # Update progress estimation
        total_tasks = self.tasks_tree.topLevelItemCount()
        completed_tasks = 0
        for i in range(total_tasks):
            if self.tasks_tree.topLevelItem(i).text(1) == "completed":
                completed_tasks += 1
        
        if total_tasks > 0:
            progress_percent = (completed_tasks / total_tasks) * 100
            self.progress_bar.setValue(int(progress_percent))
            self.progress_bar.setFormat(f"Progress: {int(progress_percent)}%")
    
    @Slot(str, str, str)
    def update_agent_status(self, agent_name, action, message):
        """Update the status of an agent in the UI."""
        # Add to agent list if not already there
        found = False
        for i in range(self.agents_list.count()):
            item = self.agents_list.item(i)
            if item.text().startswith(f"Agent: {agent_name}"):
                found = True
                break
        
        if not found:
            agent_item = QListWidgetItem(f"Agent: {agent_name}")
            agent_item.setForeground(QColor(0, 128, 255))  # Blue color for agents
            self.agents_list.addItem(agent_item)
        
        # Add agent log entry
        timestamp = time.strftime("%H:%M:%S")
        
        # Style based on action
        if action == "error":
            log_entry = f"<p style='color:#CC0000'>[{timestamp}] Agent '{agent_name}' | {action}: {message}</p>"
        elif action == "completed":
            log_entry = f"<p style='color:#009900'>[{timestamp}] Agent '{agent_name}' | {action}: {message}</p>"
        elif action == "execute":
            log_entry = f"<p style='color:#0066CC'>[{timestamp}] Agent '{agent_name}' | {action}: {message}</p>"
        else:
            log_entry = f"<p>[{timestamp}] Agent '{agent_name}' | {action}: {message}</p>"
            
        self.log_output.append(log_entry)
        
        # Add to agent-specific log
        activity_item = QListWidgetItem(f"[{timestamp}] {action}: {message}")
        
        # Style based on action
        if action == "error":
            activity_item.setForeground(QColor(204, 0, 0))  # Red
        elif action == "completed":
            activity_item.setForeground(QColor(0, 153, 0))  # Green  
        elif action == "execute":
            activity_item.setForeground(QColor(0, 102, 204))  # Blue
    
    @Slot(dict)
    def handle_results(self, results):
        """Handle the results from the MiMi framework."""
        # Enable run button
        self.run_button.setEnabled(True)
        
        # Update status
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("Completed")
        self.status_label.setText("Status: Completed")
        
        # Display results
        self.results_output.clear()
        self.results_output.append(json.dumps(results, indent=2))
        
        # Switch to results tab
        self.tabs.setCurrentIndex(3)  # Results tab
        
        # Log completion
        self.log_output.append("<h3>Project completed successfully</h3>")
    
    @Slot(str)
    def handle_error(self, error_message):
        """Handle an error from the MiMi framework."""
        # Enable run button
        self.run_button.setEnabled(True)
        
        # Update status
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Error")
        self.status_label.setText(f"Status: Error - {error_message}")
        
        # Log error
        self.log_output.append(f"<p style='color:red'><b>Error:</b> {error_message}</p>")
        
        # Show error message
        QMessageBox.critical(self, "Error", f"An error occurred: {error_message}")
    
    def update_ui(self):
        """Update UI elements that need periodic updates."""
        # Currently nothing to update periodically
        pass

    def toggle_theme(self, is_dark):
        """Toggle between light and dark theme."""
        self.apply_theme(is_dark)
    
    def apply_theme(self, is_dark):
        """Apply the specified theme."""
        if is_dark:
            # Dark theme
            app = QApplication.instance()
            palette = QPalette()
            
            # Base colors
            palette.setColor(QPalette.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.WindowText, Qt.white)
            palette.setColor(QPalette.Base, QColor(35, 35, 35))
            palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ToolTipBase, QColor(25, 25, 25))
            palette.setColor(QPalette.ToolTipText, Qt.white)
            palette.setColor(QPalette.Text, Qt.white)
            palette.setColor(QPalette.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ButtonText, Qt.white)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.HighlightedText, Qt.black)
            
            # Set the dark palette
            app.setPalette(palette)
            
            # Style for run button
            self.run_button.setStyleSheet("""
                QPushButton {
                    background-color: #2C7744;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    font-size: 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #359A58;
                }
                QPushButton:pressed {
                    background-color: #1F5830;
                }
            """)
        else:
            # Light theme (default)
            app = QApplication.instance()
            app.setPalette(app.style().standardPalette())
            
            # Style for run button
            self.run_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    font-size: 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
            """)
    
    def show_about(self):
        """Show the about dialog."""
        about_text = """
        <h2>MiMi Multi-Agent AI Framework</h2>
        <p>A powerful framework for orchestrating multiple AI agents to work together.</p>
        <p>Features:</p>
        <ul>
            <li>Multiple specialized agents</li>
            <li>Task parallelization</li>
            <li>Multi-model support</li>
            <li>Structured output and visualization</li>
        </ul>
        <p>Version: 1.0</p>
        """
        
        QMessageBox.about(self, "About MiMi", about_text)


if __name__ == "__main__":
    # Create application
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Use Fusion style for a modern look
    
    # Set application icon
    # app.setWindowIcon(QIcon("mimi_icon.png"))
    
    # Create and show main window
    window = MimiApp()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec()) 