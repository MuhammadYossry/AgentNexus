---
title: "Getting Started"
description: "Start building AI/LLM agents with AgentNexus"
lead: "Get up and running with AgentNexus and build your first agent in minutes."
date: 2025-03-25T08:00:00+00:00
lastmod: 2025-03-25T08:00:00+00:00
draft: false
images: []
weight: 200
---

# Getting Started with AgentNexus

Welcome to AgentNexus! This section will guide you through the process of setting up the framework and building your first agent.

## What You'll Learn

{{< cards >}}
  {{< card link="installation" title="Installation" icon="arrow-down" subtitle="Set up AgentNexus in your environment" >}}
  {{< card link="basic-concepts" title="Basic Concepts" icon="academic-cap" subtitle="Learn the core concepts of AgentNexus" >}}
  {{< card link="quick-start" title="Quick Start" subtitle="Build your first agent in minutes" >}}
  {{< card link="project-organization" title="Project Organization" icon="folder" subtitle="Best practices for organizing your agent projects" >}}
{{< /cards >}}

## Prerequisites

Before you begin, make sure you have:

- Python 3.8 or higher installed
- Basic familiarity with Python and async programming concepts
- Basic understanding of FastAPI (helpful but not required)
- A development environment set up for Python

## Quick Installation

If you're eager to get started, here's the quick installation command:

```bash
pip install agentnexus
```

For more detailed installation instructions and options, see the [Installation](installation) page.

## Hello, Agent!

Here's a minimal example of a AgentNexus agent to give you a taste of the framework:

```python
from fastapi import FastAPI
from agentnexus.base_types import AgentConfig, Capability, ActionType
from agentnexus.action_manager import agent_action
from agentnexus.manifest_generator import AgentManager

# Create agent configuration
hello_agent = AgentConfig(
    name="Hello Agent",
    version="1.0.0",
    description="A simple hello world agent"
)

# Define an agent action
@agent_action(
    agent_config=hello_agent,
    action_type=ActionType.TALK,
    name="Say Hello",
    description="Responds with a greeting"
)
async def say_hello(input_data):
    name = getattr(input_data, "name", "World")
    return {"greeting": f"Hello, {name}!"}

# Set up FastAPI app with agent
app = FastAPI()
agent_manager = AgentManager(base_url="http://localhost:8000")
agent_manager.add_agent(hello_agent)
agent_manager.setup_agents(app)

# Run with: uvicorn main:app --reload
```

## Next Steps

<div class="row">
  <div class="col-md-6">
    <div class="card h-100">
      <div class="card-body">
        <h5 class="card-title">
          <a href="getting-started/installation">Installation →</a>
        </h5>
        <p class="card-text">
          Install AgentNexus and set up your development environment.
        </p>
      </div>
    </div>
  </div>
  <div class="col-md-6">
    <div class="card h-100">
      <div class="card-body">
        <h5 class="card-title">
          <a href="getting-started/basic-concepts">Basic Concepts →</a>
        </h5>
        <p class="card-text">
          Learn the fundamental concepts of AgentNexus.
        </p>
      </div>
    </div>
  </div>
</div>