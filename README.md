# MiMi

AI Tool for running Multi Agent Multi Model Projects.

## Overview

MiMi is a Python framework for creating and running AI systems with multiple specialized agents working together. Each agent can use a different model, and they communicate through a structured workflow to solve complex tasks. Inspired by crewAI, MiMi provides a clean, modular design for building multi-agent systems.

## Features

- **Multiple Specialized Agents** - Create agents with different roles and capabilities
- **Flexible Task Configuration** - Define tasks with dependencies and data flow
- **YAML Configuration** - Easy to use configuration files for projects
- **Model Integration** - Support for Ollama and extensible for other providers
- **Comprehensive Logging** - Detailed logging of agent and task activities
- **Clean Architecture** - Following SOLID principles and best practices

## Requirements

- Python 3.10+
- Ollama (for running the sample project)

## Installation

```bash
# Clone the repository
git clone https://github.com/oravandres/MiMi.git
cd MiMi

# Run the installation script
./install.sh
```

The install script will:
- Optionally initialize a git repository
- Create a Python virtual environment
- Install dependencies from requirements.txt
- Set up PYTHONPATH

### Manual Installation

If you prefer to install manually:

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt  # Basic dependencies
# OR
pip install -r requirements-dev.txt  # Including development tools

# Set PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

## Quick Start

```python
from mimi.core.project import Project
from mimi.core.runner import ProjectRunner

# Load a project from configuration
project = Project.from_config("projects/sample/config")

# Run the project
runner = ProjectRunner(project)
result = runner.run({"input": 5})
print(f"Result: {result}")
```

### Command Line Usage

```bash
# Run a project from the command line
python -m mimi --config projects/sample/config --input 5
```

## Sample Project

The repository includes a sample project with 5 number-adding agents:

- **Agent-1** adds 1 to the input number
- **Agent-2** adds 2 to the input number
- **Agent-3** adds 3 to the input number
- **Agent-4** adds 4 to the input number
- **Agent-5** adds 5 to the input number

Each agent logs its operations and the result of its calculation.

### Running the Sample

```bash
# Run the sample script
python examples/run_sample_project.py 10
```

## Advanced Sample Project

The repository includes an advanced sample project with 5 number-adding agents and verification:

- **Agent-1** adds 1 to the input number, 5 times
- **Agent-2** adds 2 to the input number, 5 times
- **Agent-3** adds 3 to the input number, 5 times
- **Agent-4** adds 4 to the input number, 5 times
- **Agent-5** adds 5 to the input number, 5 times

Each agent logs its operations and provides detailed step-by-step breakdown of each calculation.

### Advanced Workflow Design

The workflow follows this pattern:

1. **Multi-Step Addition**: Each NumberAdderAgent performs its addition operation multiple times (5 repetitions)
2. **Detailed Verification**: The AnalystAgent verifies all calculation steps for accuracy
3. **Comprehensive Feedback**: The FeedbackProcessorAgent processes verification results and provides detailed feedback
4. **Sequential Processing**: After verification, the workflow moves to the next agent

For example, if the input is 10:
- Agent-1 adds 1 five times: 10 → 11 → 12 → 13 → 14 → 15 (total: +5)
- Analyst verifies each step of the calculation
- Feedback is provided
- Agent-2 adds 2 five times: 10 → 12 → 14 → 16 → 18 → 20 (total: +10)
- And so on...

### Running the Sample

```bash
# Run the sample script
python examples/run_sample_project.py 10
```

## Multi-Step Verification

The verification system has been enhanced to support multi-step calculations:

### Enhanced Number Adder Agent

The NumberAdderAgent now supports:

- **Repetitions**: Configurable number of times to apply the addition
- **Step Tracking**: Detailed recording of each calculation step
- **Rich Output**: Structured output with all calculation details for verification

### Advanced Analyst Verification

The AnalystAgent now performs:

- **Multi-Step Verification**: Checks each individual calculation step
- **Sequence Validation**: Ensures steps follow a logical sequence
- **Comprehensive Error Detection**: Identifies exactly which steps contain errors
- **Detailed Reporting**: Provides complete verification results with step-by-step analysis

### Configuration Example

In agents.yaml:
```yaml
  - name: "agent-1"
    type: "number_adder"
    role: "Number Adder (+1)"
    description: "Agent that adds 1 to the input number 5 times"
    model_name: "model-name"
    model_provider: "ollama"
    number_to_add: 1
    repetitions: 5
    model_settings:
      base_url: "http://localhost:11434"
      temperature: 0.1
```

## Project Configuration

MiMi projects are configured using YAML files in a configuration directory:

### agents.yaml

```yaml
project_name: "My Project"
project_description: "Project description"

agents:
  - name: "agent-1"
    type: "number_adder"  # or "default" for a basic agent
    role: "Number Adder (+1)"
    description: "Agent that adds 1 to the input number"
    model_name: "model-name"
    model_provider: "ollama"
    number_to_add: 1  # specific to NumberAdderAgent
    model_settings:
      base_url: "http://localhost:11434"
      temperature: 0.1
  - name: "analyst"
    type: "analyst"
    role: "Addition Verifier"
    description: "Agent that verifies the addition operations"
    model_name: "deepsearch-r1"
    model_provider: "ollama"
    model_settings:
      base_url: "http://localhost:11434"
      temperature: 0.1
```

### tasks.yaml

```yaml
tasks:
  - name: "task-1"
    description: "Task description"
    agent: "agent-1"
    input_key: "input"  # Extract this key from the input data
    output_key: "result1"  # Store result under this key
    depends_on: []  # List of task names this task depends on
  - name: "verify-1"
    description: "Verify the addition of 1"
    agent: "analyst"
    output_key: "verified1"
    depends_on: ["add-1"]
```

## Creating Custom Agents

To create a custom agent, extend the base `Agent` class:

```python
from mimi.core.agent import Agent
from pydantic import Field

class MyCustomAgent(Agent):
    """Custom agent that does something specific."""
    
    custom_param: str = Field("default", description="Custom parameter")
    
    def execute(self, task_input):
        # Log the execution
        self.agent_log(
            self.name, 
            "execute", 
            f"Executing with input: {task_input}",
        )
        
        # Implement custom behavior
        result = do_something_with(task_input)
        
        # Log the result
        self.agent_log(
            self.name,
            "complete",
            f"Execution completed with result: {result}",
        )
        
        return result
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mimi
```

### Code Formatting

```bash
# Format code with Black
black .

# Lint with Ruff
ruff check .

# Type checking with mypy
mypy .
```

## Verification Agents

MiMi now includes verification agents that ensure calculations are performed correctly:

### Analyst Agent

The AnalystAgent verifies the correctness of calculations performed by NumberAdderAgents:

- Verifies that each addition operation was performed correctly
- Extracts input and result values and compares them with the expected result 
- Provides detailed verification results including operation, expected value, and actual value
- Identifies errors when calculations don't match expected results

### Feedback Processor Agent

The FeedbackProcessorAgent processes verification results and provides user-friendly feedback:

- Interprets verification results from the Analyst Agent
- Generates clear, human-readable feedback messages
- Makes workflow continuation decisions (continue or halt on error)
- Provides detailed error information when calculations are incorrect

### Verification Workflow

The verification workflow follows this pattern:

1. Number Adder Agent performs calculation
2. Analyst Agent verifies the calculation
3. Feedback Processor Agent handles verification results
4. Workflow continues or halts based on verification outcome

### Configuration Example

To add verification to your project, configure these agents and tasks:

In agents.yaml:
```yaml
  - name: "analyst"
    type: "analyst"
    role: "Addition Verifier"
    description: "Agent that verifies the addition operations"
    model_name: "model-name"
    model_provider: "ollama"
    model_settings:
      base_url: "http://localhost:11434"
      temperature: 0.1
      
  - name: "feedback-processor"
    type: "feedback_processor"
    role: "Feedback Provider"
    description: "Agent that processes verification results and provides feedback"
    model_name: "model-name"
    model_provider: "ollama"
    model_settings:
      base_url: "http://localhost:11434"
      temperature: 0.1
```

In tasks.yaml:
```yaml
  - name: "add-1"
    description: "Add 1 to the input"
    agent: "agent-1"
    input_key: "input"
    output_key: "result1"
    depends_on: []
    
  - name: "verify-1"
    description: "Verify the addition of 1"
    agent: "analyst"
    output_key: "verified1"
    depends_on: ["add-1"]
    
  - name: "feedback-1"
    description: "Process verification results"
    agent: "feedback-processor"
    input_key: "verified1"
    output_key: "feedback1"
    depends_on: ["verify-1"]
```

### Benefits

- **Calculation Integrity**: Ensures all calculations are performed correctly
- **Error Detection**: Immediately identifies and reports calculation errors
- **Workflow Control**: Prevents propagation of errors through the workflow
- **User Feedback**: Provides clear, detailed feedback about calculation status

## License

MIT License 