# AgentNexus: Python Library for AI/LLM Agent Development with UI-Driven Workflows

[![CI/CD](MuhammadYossry/AgentNexus/actions/workflows/ci.yml/badge.svg)](https://github.com/MuhammadYossry/AgentNexus/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/agentnexus.svg)](https://badge.fury.io/py/agentnexus)
[![Python Versions](https://img.shields.io/pypi/pyversions/agentnexus.svg)](https://pypi.org/project/agentnexus/)

> ⚠️ **ALPHA STAGE**: This library is currently in alpha.

## 🚀 Overview

AgentNexus simplifies the creation of LLM and AI agents with interactive user interfaces and structured workflows. It automatically generates agent manifests to enable seamless discovery, distributed deployment, and cross-agent communication.

The library provides a declarative approach to building AI agents using Python decorators, allowing developers to focus on agent logic rather than infrastructure.

## 🌟 Key Features

### 🏗️ Advanced Agent Architecture
- **Declarative Development**: Create complex agents using intuitive Python decorators
- **Multi-Action Support**: Define multiple agent actions within a single agent
- **Workflow-Driven Design**: Build multi-step UI workflows with state management

### 🖥️ Event-Driven UI System
- **Rich Component Library**: Tables, forms, code editors, and markdown displays
- **Automatic Event Handling**: Simplified component event management
- **Context-Aware State**: Preserve state across workflow steps and sessions

### 🔍 Comprehensive Manifest Generation
- **Standard Protocol**: JSON schema for agents, actions, workflows, and UI components
- **Cross-Platform Compatibility**: Works with any platform supporting the manifest spec
- **Distributed Architecture**: Enables decentralized agent discovery and execution

## 📸 Screenshots

![UI Screenshot 1](https://github.com/user-attachments/assets/b7e47c80-8741-43b8-b492-591277710997)
![UI Screenshot 2](https://github.com/user-attachments/assets/0b4297c5-62c2-4df5-8154-39c2c37a277e)

## 🛠️ Installation

### Installing from PyPI (Recommended)

```bash
# Install the latest release
pip install agentnexus

# Or with a specific version
pip install agentnexus==0.1.0
```

### Installing with uv (Faster Installation)

```bash
pip install uv  # If you don't have uv installed
uv pip install agentnexus
```

## 🔧 Local Development

### Prerequisites
- Python 3.8+
- Git

### Install from Source
```bash
# Clone the repository
git clone https://github.com/MuhammadYossry/agentnexus.git
cd agentnexus

# Option 1: Using uv (recommended for faster dependency resolution)
pip install uv  # If you don't have uv installed
uv venv
uv pip install -r requirements.txt

# Option 2: Using pip and venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Running the Application
```bash
# Using uv
uv run uvicorn main:app --port 9200 --reload

# Using regular Python (if installed with venv)
uvicorn main:app --port 9200 --reload
```

The server will start at http://localhost:9200, and the auto-generated manifest will be available at http://localhost:9200/agents.json.

### Running Tests
```bash
# Using uv
uv run pytest

# Or using the included script
python run_tests.py
```

## 🚀 Quick Start

### Creating a Basic Agent

```python
from agentnexus.base_types import AgentConfig, Capability, ActionType
from agentnexus.action_manager import agent_action

# Define agent
my_agent = AgentConfig(
    name="Simple Assistant",
    version="1.0.0",
    description="Basic AI assistant with simple capabilities",
    capabilities=[
        Capability(
            skill_path=["Utilities", "Text"],
            metadata={"features": ["Summarization", "Translation"]}
        )
    ]
)

# Create an action
@agent_action(
    agent_config=my_agent,
    action_type=ActionType.GENERATE,
    name="Summarize Text",
    description="Creates a concise summary of longer text"
)
async def summarize_text(input_data):
    """Summarize the provided text."""
    text = input_data.text
    max_length = getattr(input_data, "max_length", 100)

    # Summarization logic would go here
    summary = text[:max_length] + "..."  # Simplified example

    return {"summary": summary, "original_length": len(text)}
```

### Setting Up FastAPI Integration

```python
from fastapi import FastAPI
from agentnexus.manifest_generator import AgentManager

app = FastAPI()
agent_manager = AgentManager(base_url="http://localhost:8000")
agent_manager.add_agent(my_agent)
agent_manager.setup_agents(app)

# Run with: uvicorn main:app --reload
```

## 📚 Key Concepts

- **Agent Config**: Defines an agent's metadata and capabilities
- **Actions**: Standalone agent capabilities, triggered via API endpoints
- **Workflows**: Multi-step processes with state management
- **UI Components**: Interactive UI elements with event handling
- **Context Management**: State preservation across workflow steps
- **Manifest**: Standardized JSON schema for agent discovery and integration

## 🌐 Auto-Generated Endpoints

The library automatically creates these endpoints:

- `GET /agents.json` - List all available agents
- `GET /agents/{agent_slug}.json` - Get detailed manifest for a specific agent
- `POST /agents/{agent_slug}/actions/{action_name}` - Trigger agent actions
- `POST /agents/{agent_slug}/workflows/{workflow_id}/steps/{step_id}` - Execute workflow steps

## 🧩 UI Components

AgentNexus includes several built-in UI components:

- **FormComponent**: Interactive forms for data collection
- **TableComponent**: Display and interact with tabular data
- **CodeEditorComponent**: Code editing with syntax highlighting
- **MarkdownComponent**: Formatted text display

## 📖 Documentation

Comprehensive documentation is under development. For now, please refer to the examples in the [`agents`](/agents) directory.

## 🛣️ Project Status

AgentNexus is in alpha stage and under active development. The API may change significantly before the first stable release. Current limitations include:

- Limited production testing
- Incomplete documentation
- Some API instability
- Limited example collection

## 🤝 Contributing

Contributions are welcome! Help us improve AgentNexus by:

1. Reporting bugs
2. Suggesting features
3. Submitting pull requests
4. Improving documentation

## 📜 License

[MIT License](LICENSE)

## 🌟 Star Us

If you find AgentNexus useful, please give us a star on [GitHub](https://github.com/MuhammadYossry/AgentNexus)!