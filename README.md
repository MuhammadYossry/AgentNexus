# AgentHub

AgentHub is a framework for building and managing AI agents with built-in support for workflows, actions, and automatic API generation. It provides a structured way to define agents, their capabilities, and workflows while automatically handling route generation and manifest creation.

## Table of Contents

1. [Overview](#overview)
2. [Key Features](#key-features)
3. [Project Structure](#project-structure)
4. [Getting Started](#getting-started)
   - [Installation with Poetry](#installation-with-poetry)
   - [Basic Setup](#basic-setup)
5. [Core Concepts](#core-concepts)
   - [Agent Configuration](#agent-configuration)
   - [Action Implementation](#action-implementation)
   - [Workflow Management](#workflow-management)
6. [API Documentation](#api-documentation)
7. [Example Agents](#example-agents)
8. [Running the Server](#running-the-server)

## Overview

AgentHub provides a framework for building AI agents with:
- Automatic API generation
- Workflow management
- Action registration
- Manifest generation
- Built-in documentation

The framework uses FastAPI under the hood and provides decorators for easy agent and workflow creation.

## Key Features

- **Declarative Agent Definition**: Define agents using simple Python classes and decorators
- **Automatic API Generation**: Routes are automatically created based on agent definitions
- **Workflow Support**: Built-in workflow management with state tracking
- **Action Management**: Easy registration and management of agent actions
- **Manifest Generation**: Automatic generation of agent manifests for discovery
- **Modular Design**: Clean separation of concerns between agents, workflows, and actions

## Project Structure

```
AgentHub/
├── agents_manifest/
│   ├── __init__.py
│   ├── base_types.py
│   ├── action_manager.py
│   ├── workflow_manager.py
│   ├── manifest_generator.py
│   └── templates/
├── agents/
│   ├── __init__.py
│   ├── code_agent_v2.py
│   └── flight_agent.py
├── pyproject.toml
├── poetry.lock
└── README.md
```

## Getting Started

### Installation with Poetry

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/AgentHub.git
   cd AgentHub
   ```

2. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

3. Activate the virtual environment:
   ```bash
   poetry shell
   ```

### Basic Setup

1. Create your main application file (`main.py`):
   ```python
   from fastapi import FastAPI
   from agents_manifest.manifest_generator import setup_agent_routes
   from agents.code_agent_v2 import v2_app as code_agent_v2_app

   app = FastAPI()

   # Mount agent apps
   app.mount("/v2/code_agent", code_agent_v2_app)

   # Set up routes
   setup_agent_routes(app)

   if __name__ == "__main__":
       import uvicorn
       uvicorn.run(app, host="0.0.0.0", port=9200)
   ```

## Core Concepts

### Agent Configuration

Use the `@configure_agent` decorator to define your agent:

```python
from fastapi import FastAPI
from agents_manifest.manifest_generator import configure_agent
from agents_manifest.base_types import Capability

app = FastAPI()

@configure_agent(
    app=app,
    base_url="http://localhost:9200",
    name="Code Assistant",
    version="1.0.0",
    description="AI-powered code generation assistant",
    capabilities=[
        Capability(
            skill_path=["Development", "Code Generation"],
            metadata={"languages": ["Python"]}
        )
    ]
)
class CodeAgent:
    pass
```

### Action Implementation

Use the `@agent_action` decorator to define agent actions:

```python
from agents_manifest.action_manager import agent_action
from agents_manifest.base_types import ActionType
from pydantic import BaseModel

class CodeRequest(BaseModel):
    prompt: str

class CodeResponse(BaseModel):
    code: str
    documentation: str

@agent_action(
    action_type=ActionType.GENERATE,
    name="Generate Code",
    description="Generate Python code from natural language description"
)
async def generate_code(request: CodeRequest) -> CodeResponse:
    # Implementation...
    return CodeResponse(
        code="# Your generated code",
        documentation="Code documentation"
    )
```

### Workflow Management

For more complex scenarios, use workflows:

```python
from agents_manifest.workflow_manager import Workflow, WorkflowStep, workflow_step

# Define workflow
CODE_GEN_WORKFLOW = Workflow(
    id="code_gen",
    name="Code Generation",
    steps=[
        WorkflowStep(
            id="initiate",
            type=WorkflowStepType.START,
            action="start_code_gen"
        ),
        # Add more steps...
    ]
)

# Implement workflow steps
@workflow_step(
    workflow_id="code_gen",
    step_id="initiate",
    action_type=ActionType.QUESTION,
    name="Start Code Generation"
)
async def start_code_gen(request: CodeRequest) -> CodeResponse:
    # Implementation...
    return CodeResponse(...)
```

## API Documentation

The framework automatically generates:
- OpenAPI documentation at `/docs`
- Agent manifests at `/agents.json`
- Workflow documentation at `/agents/{agent}/workflows`

## Example Agents

See the example agents in the `agents/` directory:
- `code_agent_v2.py`: Code generation agent
- `flight_agent.py`: Flight booking agent

## Running the Server

Start the development server:

```bash
poetry run uvicorn main:app --reload
```

Access the API at `http://localhost:9200` and documentation at `http://localhost:9200/docs`