# MiMi

Multi-Agent AI Tool for complex software development projects.

## Overview

MiMi is a Python framework that orchestrates multiple specialized AI agents to work together on complex tasks like software development, testing, and documentation. Each agent can use different models and they collaborate through structured workflows.

## Installation

```bash
git clone https://github.com/oravandres/MiMi.git
cd MiMi
./install.sh
```

## Usage

```bash
python -m mimi --config projects/advanced --description "Create javascript and html app of flappy bird, that I could run in easily, code must work easily with only index.html. Tests should be separately."
```

### Command Line Options

- `--config`: Path to project configuration (e.g., `projects/advanced`, `projects/simple`)
- `--description`: Description of what you want to build

## Available Projects

### Advanced Project (`projects/advanced`)
Full software engineering project with:
- Frontend architects, developers, and QA engineers
- Backend architects, developers, and QA engineers  
- Infrastructure architects and DevOps engineers
- Security engineers and performance testing
- Technical writers for documentation
- Integration testing and deployment

### Simple Project (`projects/simple`)
Basic project with fewer agents for simpler tasks.

## How It Works

1. **Architecture Phase**: Agents design the system architecture
2. **Development Phase**: Specialized agents implement components
3. **Testing Phase**: QA agents test the implementation
4. **Integration Phase**: Components are integrated and tested
5. **Documentation Phase**: Technical writers create documentation

## Requirements

- Python 3.10+
- Ollama running locally (default: `http://localhost:11434`)

## Output

Projects are created in timestamped directories under `Software/` with:
- Source code files
- Documentation  
- Test files
- Project logs

## Example Output Structure

```
Software/20250602_222648_Advanced_Software_Engineering_Project/
├── README.md
├── docs/
│   └── documentation.md
├── src/
│   └── [implementation files]
├── tests/
│   └── [test files]
└── project.log.md
```

## Configuration

Projects are configured with YAML files defining:
- Agents and their roles
- Task dependencies
- Model settings
- Workflow structure

See `projects/advanced/project.yaml` for a complete example. 