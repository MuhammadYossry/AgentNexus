---
title: "Installation"
description: "How to install AgentNexus and set up your development environment"
lead: "Get AgentNexus installed and ready to use in your Python environment."
date: 2025-03-25T08:00:00+00:00
lastmod: 2025-03-25T08:00:00+00:00
draft: false
images: []
menu:
  docs:
    parent: "getting-started"
weight: 210
toc: true
---

## Requirements

Before installing AgentNexus, ensure your environment meets the following requirements:

- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **Dependencies**: FastAPI, Pydantic, Loguru, and other packages (automatically installed)

## Installation Methods

### Using pip (Recommended)

The simplest way to install AgentNexus is using pip:

```bash
pip install fast-agents
```

This will install AgentNexus and all its required dependencies.

### Using Poetry

If you're using Poetry for dependency management, you can add AgentNexus to your project:

```bash
poetry add fast-agents
```

### From Source

To install the latest development version from source:

```bash
git clone https://github.com/Relax-N-Tax/AgentHub.git
cd AgentHub
pip install -e .
```

## Verifying Installation

To verify that AgentNexus is installed correctly, run Python and import the package:

```python
import agentnexus
print(agentnexus.__version__)
```

If you see the version number without any errors, the installation was successful.

## Development Environment Setup

### Using Virtual Environments

It's recommended to use a virtual environment for development:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install AgentNexus
pip install fast-agents
```

### Development Dependencies

If you plan to contribute to AgentNexus or run its tests, install the development dependencies:

```bash
# If installed from PyPI
pip install fast-agents[dev]

# If installed from source
pip install -e ".[dev]"
```

## Optional Dependencies

### Redis for Session Management

For production environments, Redis is recommended for session management:

```bash
pip install fast-agents[redis]
```

This will install the required Redis client packages. You'll also need a Redis server running. See the [Session Management](../../core-concepts/session-management) section for configuration details.

### Frontend Development

If you plan to customize the UI components or develop frontend features:

```bash
pip install fast-agents[frontend]
```

## Environment Configuration

AgentNexus uses environment variables for configuration. You can set these in a `.env` file in your project directory:

```bash
# Basic settings
PROJECT_NAME="My Agent Project"

# LLM provider settings
LLM_PROVIDER="openai"  # or "qwen", etc.
LLM_BASE_URL="https://api.openai.com/v1"
LLM_API_KEY="your-api-key"
LLM_MODEL="gpt-4"
LLM_TIMEOUT=300

# Session settings (for Redis)
REDIS_HOST="localhost"
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=""
SESSION_TTL=3600  # 1 hour
```

## Troubleshooting

### Common Installation Issues

#### Package Conflicts

If you encounter package conflicts, try installing in an isolated environment:

```bash
python -m venv fresh-env
source fresh-env/bin/activate  # On Windows: fresh-env\Scripts\activate
pip install fast-agents
```

#### Outdated Pip

Ensure you have the latest version of pip:

```bash
pip install --upgrade pip
```

#### Missing System Dependencies

Some packages might require system-level dependencies. For example, on Ubuntu:

```bash
sudo apt-get update
sudo apt-get install python3-dev build-essential
```

### Getting Help

If you encounter issues not covered here:

1. Check the [GitHub issues](https://github.com/Relax-N-Tax/AgentHub/issues) for similar problems
2. Search the [discussions](https://github.com/Relax-N-Tax/AgentHub/discussions) for solutions
3. Open a new issue if your problem is unique

## Next Steps

Once you have AgentNexus installed, you're ready to:

- Learn about [Basic Concepts](../basic-concepts)
- Follow the [Quick Start](../quick-start) guide to build your first agent
- Understand [Project Organization](../project-organization) best practices