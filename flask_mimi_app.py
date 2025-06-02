#!/usr/bin/env python3
"""
MiMi Web Application
A web-based interface for the MiMi multi-agent AI framework.
"""

import os
import sys
import json
import time
import threading
import queue
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response

# Add MiMi to path if not already there
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

try:
    # Import MiMi modules
    from mimi.core.runner import ProjectRunner
    from mimi.utils.logger import task_log as original_task_log
    from mimi.utils.logger import agent_log as original_agent_log
    from mimi.utils import ensure_project_directory_exists
except ImportError:
    print("MiMi framework not found. Make sure you're running from the MiMi directory.")
    sys.exit(1)

# Create Flask app
app = Flask(__name__)

# Ensure projects directory exists
projects_dir = ensure_project_directory_exists()

# Global variables
active_tasks = {}  # Track active tasks and their start times
tasks_queue = queue.Queue()  # Queue for task status updates
agents_queue = queue.Queue()  # Queue for agent status updates
result_queue = queue.Queue()  # Queue for final results
error_queue = queue.Queue()  # Queue for errors

# Create a directory for templates if it doesn't exist
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)

# Create templates
with open(templates_dir / "index.html", "w") as f:
    f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MiMi Web Interface</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            padding: 20px;
            background-color: #f8f9fa;
        }
        .card {
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .log-container {
            height: 300px;
            overflow-y: auto;
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #dee2e6;
            font-family: monospace;
        }
        .log-entry {
            margin: 0;
            padding: 2px 0;
        }
        .task-started { color: #007bff; }
        .task-processing { color: #6f42c1; }
        .task-completed { color: #28a745; }
        .task-error { color: #dc3545; }
        .agent-message { color: #6610f2; }
        .status-bar {
            background-color: #e9ecef;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        #taskTable th, #taskTable td {
            padding: 8px;
        }
        #progress-bar {
            height: 20px;
        }
        .nav-tabs {
            margin-bottom: 20px;
        }
        #results-json {
            white-space: pre-wrap;
            font-family: monospace;
        }
        #agent-list {
            list-style-type: none;
            padding-left: 0;
        }
        #agent-list li {
            padding: 8px;
            border-bottom: 1px solid #dee2e6;
        }
        .dark-mode {
            background-color: #343a40;
            color: #f8f9fa;
        }
        .dark-mode .card {
            background-color: #212529;
            color: #f8f9fa;
        }
        .dark-mode .log-container {
            background-color: #495057;
            color: #f8f9fa;
            border-color: #6c757d;
        }
        .dark-mode .status-bar {
            background-color: #212529;
            color: #f8f9fa;
        }
        .dark-mode .table {
            color: #f8f9fa;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h2>MiMi Multi-Agent AI Framework</h2>
                        <div>
                            <button id="themeToggle" class="btn btn-outline-secondary btn-sm">Dark Mode</button>
                            <button id="aboutBtn" class="btn btn-outline-info btn-sm">About</button>
                        </div>
                    </div>
                    <div class="card-body">
                        <form id="runForm">
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <label for="projectName" class="form-label">Project Name</label>
                                    <input type="text" class="form-control" id="projectName" required>
                                </div>
                                <div class="col-md-6">
                                    <label for="configFile" class="form-label">Config File (Optional)</label>
                                    <input type="file" class="form-control" id="configFile" accept=".json">
                                </div>
                            </div>
                            <div class="mb-3">
                                <label for="promptInput" class="form-label">Enter your prompt</label>
                                <textarea class="form-control" id="promptInput" rows="4" required></textarea>
                            </div>
                            <button type="submit" class="btn btn-primary w-100" id="runButton">Run</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-12">
                <div class="status-bar">
                    <div class="progress mb-2" id="progress-container">
                        <div id="progress-bar" class="progress-bar" role="progressbar" style="width: 0%;" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">0%</div>
                    </div>
                    <div id="status-text">Status: Ready</div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-12">
                <ul class="nav nav-tabs" id="myTab" role="tablist">
                    <li class="nav-item" role="presentation">
                        <button class="nav-link active" id="log-tab" data-bs-toggle="tab" data-bs-target="#log" type="button" role="tab" aria-controls="log" aria-selected="true">Log</button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="tasks-tab" data-bs-toggle="tab" data-bs-target="#tasks" type="button" role="tab" aria-controls="tasks" aria-selected="false">Tasks</button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="agents-tab" data-bs-toggle="tab" data-bs-target="#agents" type="button" role="tab" aria-controls="agents" aria-selected="false">Agents</button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="results-tab" data-bs-toggle="tab" data-bs-target="#results" type="button" role="tab" aria-controls="results" aria-selected="false">Results</button>
                    </li>
                </ul>
                <div class="tab-content" id="myTabContent">
                    <div class="tab-pane fade show active" id="log" role="tabpanel" aria-labelledby="log-tab">
                        <div class="log-container" id="logContainer">
                            <p class="log-entry"><strong>Welcome to MiMi</strong></p>
                            <p class="log-entry">The Multi-agent, Multi-model AI Framework</p>
                            <p class="log-entry">Enter a prompt and click Run to start.</p>
                        </div>
                    </div>
                    <div class="tab-pane fade" id="tasks" role="tabpanel" aria-labelledby="tasks-tab">
                        <div class="table-responsive">
                            <table class="table table-striped" id="taskTable">
                                <thead>
                                    <tr>
                                        <th>Task</th>
                                        <th>Status</th>
                                        <th>Agent</th>
                                        <th>Duration</th>
                                    </tr>
                                </thead>
                                <tbody id="taskTableBody">
                                    <!-- Tasks will be added here -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div class="tab-pane fade" id="agents" role="tabpanel" aria-labelledby="agents-tab">
                        <ul class="list-group" id="agent-list">
                            <!-- Agents will be added here -->
                        </ul>
                    </div>
                    <div class="tab-pane fade" id="results" role="tabpanel" aria-labelledby="results-tab">
                        <div class="card">
                            <div class="card-body">
                                <pre id="results-json">No results yet.</pre>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal for About -->
    <div class="modal fade" id="aboutModal" tabindex="-1" aria-labelledby="aboutModalLabel" aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="aboutModalLabel">About MiMi</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <h4>MiMi Multi-Agent AI Framework</h4>
                    <p>A powerful framework for orchestrating multiple AI agents to work together.</p>
                    <p><strong>Features:</strong></p>
                    <ul>
                        <li>Multiple specialized agents</li>
                        <li>Task parallelization</li>
                        <li>Multi-model support</li>
                        <li>Structured output and visualization</li>
                    </ul>
                    <p><strong>Version:</strong> 1.0</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Elements
            const runForm = document.getElementById('runForm');
            const runButton = document.getElementById('runButton');
            const logContainer = document.getElementById('logContainer');
            const progressBar = document.getElementById('progress-bar');
            const statusText = document.getElementById('status-text');
            const taskTableBody = document.getElementById('taskTableBody');
            const agentList = document.getElementById('agent-list');
            const resultsJson = document.getElementById('results-json');
            const themeToggle = document.getElementById('themeToggle');
            const aboutBtn = document.getElementById('aboutBtn');
            const aboutModal = new bootstrap.Modal(document.getElementById('aboutModal'));
            
            // Variables
            let taskCount = 0;
            let completedTasks = 0;
            let taskSource = null;
            let agentSource = null;
            let resultSource = null;
            
            // Theme toggle
            themeToggle.addEventListener('click', function() {
                document.body.classList.toggle('dark-mode');
                if (document.body.classList.contains('dark-mode')) {
                    themeToggle.textContent = 'Light Mode';
                    themeToggle.classList.replace('btn-outline-secondary', 'btn-outline-light');
                } else {
                    themeToggle.textContent = 'Dark Mode';
                    themeToggle.classList.replace('btn-outline-light', 'btn-outline-secondary');
                }
            });
            
            // About button
            aboutBtn.addEventListener('click', function() {
                aboutModal.show();
            });
            
            // Run form submission
            runForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                // Clear previous results
                logContainer.innerHTML = '';
                taskTableBody.innerHTML = '';
                agentList.innerHTML = '';
                resultsJson.textContent = 'No results yet.';
                
                // Reset counters
                taskCount = 0;
                completedTasks = 0;
                
                // Get form values
                const projectName = document.getElementById('projectName').value;
                const promptInput = document.getElementById('promptInput').value;
                const configFile = document.getElementById('configFile').files[0];
                
                // Show loading state
                runButton.disabled = true;
                progressBar.style.width = '0%';
                progressBar.textContent = '0%';
                statusText.textContent = 'Status: Initializing...';
                
                // Add initial log
                addLogEntry(`Starting project: ${projectName}`, 'heading');
                addLogEntry(`Prompt: ${promptInput}`, 'normal');
                
                // Close any existing event sources
                if (taskSource) taskSource.close();
                if (agentSource) agentSource.close();
                if (resultSource) resultSource.close();
                
                // Set up new SSE connections
                setupTaskStream();
                setupAgentStream();
                setupResultStream();
                
                // Send run request
                const formData = new FormData();
                formData.append('project_name', projectName);
                formData.append('prompt', promptInput);
                if (configFile) {
                    formData.append('config_file', configFile);
                }
                
                fetch('/run', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        statusText.textContent = 'Status: Running...';
                    } else {
                        statusText.textContent = `Status: Error - ${data.message}`;
                        addLogEntry(`Error: ${data.message}`, 'task-error');
                        runButton.disabled = false;
                    }
                })
                .catch(error => {
                    statusText.textContent = `Status: Error - ${error.message}`;
                    addLogEntry(`Error: ${error.message}`, 'task-error');
                    runButton.disabled = false;
                });
            });
            
            // Set up Server-Sent Events for task updates
            function setupTaskStream() {
                taskSource = new EventSource('/task-events');
                
                taskSource.addEventListener('message', function(e) {
                    const data = JSON.parse(e.data);
                    
                    // Update tasks table
                    updateTaskTable(data);
                    
                    // Add log entry
                    const logClass = `task-${data.status}`;
                    let logText = `[${data.timestamp}] Task '${data.task_name}': ${data.status}`;
                    if (data.agent && data.agent !== 'Unknown') {
                        logText += ` (Agent: ${data.agent})`;
                    }
                    if (data.description && data.description !== data.task_name) {
                        logText += `\\n    ${data.description}`;
                    }
                    addLogEntry(logText, logClass);
                    
                    // Update progress
                    updateProgress();
                });
                
                taskSource.addEventListener('error', function(e) {
                    console.error("Error in task stream:", e);
                    taskSource.close();
                });
            }
            
            // Set up Server-Sent Events for agent updates
            function setupAgentStream() {
                agentSource = new EventSource('/agent-events');
                
                agentSource.addEventListener('message', function(e) {
                    const data = JSON.parse(e.data);
                    
                    // Add to agent list if not already there
                    const agentExists = Array.from(agentList.children).some(li => 
                        li.textContent.startsWith(`Agent: ${data.agent_name}`)
                    );
                    
                    if (!agentExists) {
                        const li = document.createElement('li');
                        li.className = 'list-group-item';
                        li.textContent = `Agent: ${data.agent_name}`;
                        agentList.appendChild(li);
                    }
                    
                    // Add log entry
                    const logText = `[${data.timestamp}] Agent '${data.agent_name}' | ${data.action}: ${data.message}`;
                    addLogEntry(logText, 'agent-message');
                });
                
                agentSource.addEventListener('error', function(e) {
                    console.error("Error in agent stream:", e);
                    agentSource.close();
                });
            }
            
            // Set up Server-Sent Events for result updates
            function setupResultStream() {
                resultSource = new EventSource('/result-events');
                
                resultSource.addEventListener('message', function(e) {
                    const data = JSON.parse(e.data);
                    
                    if (data.type === 'result') {
                        // Display results
                        resultsJson.textContent = JSON.stringify(data.result, null, 2);
                        
                        // Update UI
                        runButton.disabled = false;
                        progressBar.style.width = '100%';
                        progressBar.textContent = '100%';
                        statusText.textContent = 'Status: Completed';
                        
                        // Switch to results tab
                        document.getElementById('results-tab').click();
                        
                        // Add completion log
                        addLogEntry('Project completed successfully', 'heading');
                        
                        // Close streams
                        closeStreams();
                    } else if (data.type === 'error') {
                        // Handle error
                        runButton.disabled = false;
                        progressBar.style.width = '0%';
                        statusText.textContent = `Status: Error - ${data.message}`;
                        
                        // Add error log
                        addLogEntry(`Error: ${data.message}`, 'task-error');
                        
                        // Close streams
                        closeStreams();
                    }
                });
                
                resultSource.addEventListener('error', function(e) {
                    console.error("Error in result stream:", e);
                    resultSource.close();
                });
            }
            
            // Close all event streams
            function closeStreams() {
                if (taskSource) taskSource.close();
                if (agentSource) agentSource.close();
                if (resultSource) resultSource.close();
            }
            
            // Add a log entry
            function addLogEntry(text, className) {
                const entry = document.createElement('p');
                entry.className = 'log-entry';
                if (className) {
                    entry.classList.add(className);
                }
                entry.textContent = text;
                logContainer.appendChild(entry);
                logContainer.scrollTop = logContainer.scrollHeight;
            }
            
            // Update the tasks table
            function updateTaskTable(data) {
                let row = null;
                
                // Find existing row or create new one
                const rows = taskTableBody.getElementsByTagName('tr');
                for (let i = 0; i < rows.length; i++) {
                    const cells = rows[i].getElementsByTagName('td');
                    if (cells[0].textContent === data.task_name) {
                        row = rows[i];
                        break;
                    }
                }
                
                if (!row) {
                    // Create new row for this task
                    row = document.createElement('tr');
                    taskTableBody.appendChild(row);
                    taskCount++;
                    
                    row.innerHTML = `
                        <td>${data.task_name}</td>
                        <td>${data.status}</td>
                        <td>${data.agent}</td>
                        <td>${data.elapsed > 0 ? data.elapsed.toFixed(2) + 's' : ''}</td>
                    `;
                } else {
                    // Update existing row
                    const cells = row.getElementsByTagName('td');
                    cells[1].textContent = data.status;
                    cells[2].textContent = data.agent;
                    if (data.elapsed > 0) {
                        cells[3].textContent = data.elapsed.toFixed(2) + 's';
                    }
                }
                
                // Apply status-based styling
                if (data.status === 'completed') {
                    row.className = 'table-success';
                    completedTasks++;
                } else if (data.status === 'error') {
                    row.className = 'table-danger';
                } else if (data.status === 'processing') {
                    row.className = 'table-info';
                } else if (data.status === 'started') {
                    row.className = 'table-primary';
                }
            }
            
            // Update progress indicator
            function updateProgress() {
                if (taskCount === 0) return;
                
                const percent = Math.round((completedTasks / taskCount) * 100);
                progressBar.style.width = `${percent}%`;
                progressBar.textContent = `${percent}%`;
                statusText.textContent = `Status: ${completedTasks}/${taskCount} tasks completed`;
            }
        });
    </script>
</body>
</html>""")

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
    
    # Create task event
    task_event = {
        "task_name": task_name,
        "status": status,
        "agent": agent,
        "elapsed": elapsed,
        "description": description,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }
    
    # Add to queue
    tasks_queue.put(task_event)
    
    # Call original function
    if original_task_log:
        original_task_log(task_name, status, message, data)

# Agent log interceptor
def agent_log_intercept(agent_name, action, message, data=None):
    # Create agent event
    agent_event = {
        "agent_name": agent_name,
        "action": action,
        "message": message,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }
    
    # Add to queue
    agents_queue.put(agent_event)
    
    # Call original function
    if original_agent_log:
        original_agent_log(agent_name, action, message, data)

# Flask routes
@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/run', methods=['POST'])
def run_mimi():
    """Run the MiMi framework."""
    # Get form data
    project_name = request.form.get('project_name')
    prompt = request.form.get('prompt')
    
    if not project_name or not prompt:
        return jsonify({
            "status": "error",
            "message": "Project name and prompt are required"
        })
    
    # Check for config file
    config_path = None
    if 'config_file' in request.files:
        config_file = request.files['config_file']
        if config_file.filename:
            # Save config file
            config_path = os.path.join(current_dir, 'temp_config.json')
            config_file.save(config_path)
    
    # Clear any existing events in queues
    while not tasks_queue.empty():
        tasks_queue.get()
    
    while not agents_queue.empty():
        agents_queue.get()
    
    while not result_queue.empty():
        result_queue.get()
    
    while not error_queue.empty():
        error_queue.get()
    
    # Start a thread to run MiMi
    thread = threading.Thread(
        target=run_mimi_thread,
        args=(project_name, prompt, config_path)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "status": "success",
        "message": "MiMi is running"
    })

@app.route('/task-events')
def task_events():
    """Stream task events using Server-Sent Events."""
    def generate():
        while True:
            try:
                # Try to get a task event from the queue with timeout
                task_event = tasks_queue.get(timeout=1)
                yield f"data: {json.dumps(task_event)}\n\n"
            except queue.Empty:
                # Send a ping to keep the connection alive
                yield f"data: {json.dumps({'ping': True})}\n\n"
            except Exception as e:
                print(f"Error in task events: {str(e)}")
                break
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/agent-events')
def agent_events():
    """Stream agent events using Server-Sent Events."""
    def generate():
        while True:
            try:
                # Try to get an agent event from the queue with timeout
                agent_event = agents_queue.get(timeout=1)
                yield f"data: {json.dumps(agent_event)}\n\n"
            except queue.Empty:
                # Send a ping to keep the connection alive
                yield f"data: {json.dumps({'ping': True})}\n\n"
            except Exception as e:
                print(f"Error in agent events: {str(e)}")
                break
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/result-events')
def result_events():
    """Stream result events using Server-Sent Events."""
    def generate():
        while True:
            try:
                # First check for errors
                try:
                    error_message = error_queue.get_nowait()
                    yield f"data: {json.dumps({'type': 'error', 'message': error_message})}\n\n"
                    break
                except queue.Empty:
                    pass
                
                # Then check for results
                try:
                    result = result_queue.get_nowait()
                    yield f"data: {json.dumps({'type': 'result', 'result': result})}\n\n"
                    break
                except queue.Empty:
                    pass
                
                # Send a ping to keep the connection alive
                yield f"data: {json.dumps({'type': 'ping'})}\n\n"
                time.sleep(1)
            except Exception as e:
                print(f"Error in result events: {str(e)}")
                break
    
    return Response(generate(), mimetype='text/event-stream')

def run_mimi_thread(project_name, prompt, config_path=None):
    """Run MiMi in a background thread."""
    # Monkey patch the logger functions
    import mimi.utils.logger
    mimi.utils.logger.task_log = task_log_intercept
    mimi.utils.logger.agent_log = agent_log_intercept
    
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
        
        # Add result to queue
        result_queue.put(result)
        
    except Exception as e:
        # Add error to queue
        error_queue.put(str(e))
    finally:
        # Restore original logger functions
        mimi.utils.logger.task_log = original_task_log
        mimi.utils.logger.agent_log = original_agent_log
        
        # Clean up config file if it was created
        if config_path and os.path.exists(config_path):
            try:
                os.remove(config_path)
            except:
                pass

if __name__ == '__main__':
    # Check if Flask is installed
    try:
        import flask
        print("Starting MiMi Web Interface...")
        print("Go to http://127.0.0.1:5000 in your browser to access the interface")
        app.run(debug=True)
    except ImportError:
        print("Flask is not installed. Please install it with: pip install flask")
        sys.exit(1) 