---
title: "Documentation"
description: "Python Library for AI/LLM Agent Development with UI-Driven Workflows and Actions"
lead: "A Python library that simplifies the creation of LLM and AI agents with UI-interactable APIs and automatic Agent manifest generation."
date: 2025-03-25T08:00:00+00:00
lastmod: 2025-03-25T08:00:00+00:00
draft: false
images: []
---

<div class="text-center">
  <h1>AgentNexus Python</h1>
  <p class="lead">Python Library for AI/LLM Agent Development with UI-Driven Workflows and Actions</p>
</div>

## Get Started

AgentNexus enables developers to build powerful AI/LLM agents with interactive UIs and structured workflows. Get started quickly with our step-by-step guides.

{{< cards >}}
  {{< card link="docs/introduction" title="Introduction" icon="book-open" subtitle="Learn what AgentNexus is and how it can help you" >}}
  {{< card link="docs/getting-started" title="Getting Started" subtitle="Install and build your first agent in minutes" >}}
  {{< card link="docs/core-concepts" title="Core Concepts" icon="academic-cap" subtitle="Understand the fundamental concepts of AgentNexus" >}}
  {{< card link="docs/examples" title="Examples" icon="code" subtitle="See AgentNexus in action with practical examples" >}}
{{< /cards >}}

## Key Features

AgentNexus provides a comprehensive framework for developing AI/LLM agents:

- **Declarative Development**: Create complex agents using intuitive Python decorators
- **Multi-Action Support**: Define multiple agent actions endpoints within a single agent
- **Workflow-Driven Design**: Build multi-step UI workflows with state management
- **Rich Component Library**: Tables, forms, code editors, and markdown displays
- **Automatic Event Handling**: Simplified component event management
- **Context-Aware State**: Preserve state across workflow steps and sessions

## Quick Example

```python
from agentnexus.base_types import AgentConfig, Capability, ActionType
from agentnexus.action_manager import agent_action

# Define agent configuration
my_agent = AgentConfig(
    name="Quick Example Agent",
    version="1.0.0",
    description="A simple example agent",
    capabilities=[
        Capability(
            skill_path=["Example", "Demonstration"],
            metadata={"example": True}
        )
    ]
)

# Create a simple action
@agent_action(
    agent_config=my_agent,
    action_type=ActionType.GENERATE,
    name="Simple Action",
    description="A simple example action"
)
async def simple_action(input_data):
    """Handle a simple action."""
    return {"result": f"Processed: {input_data.message}"}
```

## Need Help?

{{< cards >}}
  {{< card link="docs/api-reference" title="API Reference" icon="document-text" >}}
  {{< card link="docs/examples" title="Examples" icon="beaker" >}}
  {{< card link="https://github.com/MuhammadYossry/AgentNexus" title="GitHub" icon="github" >}}
{{< /cards >}}
