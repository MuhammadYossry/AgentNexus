---
title: "Basic Concepts"
description: "Learn the fundamental concepts of the AgentNexus framework"
lead: "Understanding the core building blocks that make up the AgentNexus framework."
date: 2025-03-25T08:00:00+00:00
lastmod: 2025-03-25T08:00:00+00:00
draft: false
images: []
menu:
  docs:
    parent: "getting-started"
weight: 220
toc: true
---

## Core AgentNexus Concepts

Before diving into building agents, it's helpful to understand the fundamental concepts that make up the AgentNexus framework.

## Agents

An **agent** is the primary entity in AgentNexus. It represents an AI assistant with specific capabilities and actions.

### AgentConfig

Agents are defined using the `AgentConfig` class, which specifies metadata and capabilities:

```python
from agentnexus.base_types import AgentConfig, Capability

my_agent = AgentConfig(
    name="My Assistant",
    version="1.0.0",
    description="A helpful assistant for various tasks",
    capabilities=[
        Capability(
            skill_path=["Utilities", "Text", "Formatting"],
            metadata={"features": ["Summarization", "Translation"]}
        )
    ]
)
```

### Capabilities

**Capabilities** define what an agent can do. They are organized into skill paths with metadata:

```python
Capability(
    skill_path=["Development", "Code", "Analysis"],
    metadata={
        "languages": ["Python", "JavaScript"],
        "features": ["Quality", "Formatting", "Performance"]
    }
)
```

## Actions

**Actions** are specific functions that an agent can perform. They are defined using the `agent_action` decorator.

### Action Types

AgentNexus supports several types of actions:

- `ActionType.TALK`: Conversational interactions
- `ActionType.GENERATE`: Content generation
- `ActionType.QUESTION`: Information gathering
- `ActionType.CUSTOM_UI`: UI-driven interactions

### Defining Actions

Actions are connected to agents through decorators:

```python
from agentnexus.action_manager import agent_action
from agentnexus.base_types import ActionType

@agent_action(
    agent_config=my_agent,
    action_type=ActionType.GENERATE,
    name="Summarize Text",
    description="Create a concise summary of a longer text"
)
async def summarize_text(input_data):
    text = input_data.text
    # Summarization logic
    summary = text[:100] + "..."  # Simplified example
    return {"summary": summary, "original_length": len(text)}
```

## UI Components

AgentNexus provides several UI components for interactive agent interfaces.

### Component Types

- `FormComponent`: Interactive forms for data collection
- `TableComponent`: Tabular data display with interactions
- `CodeEditorComponent`: Code editing with syntax highlighting
- `MarkdownComponent`: Formatted text display

### Component Definition

Components are defined as objects:

```python
from agentnexus.ui_components import FormComponent, FormField

user_info_form = FormComponent(
    component_key="user_info",
    title="User Information",
    form_fields=[
        FormField(
            field_name="name",
            label_text="Full Name",
            field_type="text",
            is_required=True
        ),
        FormField(
            field_name="age",
            label_text="Age",
            field_type="number"
        )
    ]
)
```

### Event Handlers

Components can include event handlers for interactivity:

```python
code_editor = CodeEditorComponent(
    component_key="code_input",
    title="Source Code",
    programming_language="python",
    editor_content="# Enter code here",
    event_handlers={
        "format": handle_code_format,
        "save": handle_code_save
    }
)
```

## Workflows

**Workflows** are multi-step processes with state management. They guide users through a series of interactions.

### Workflow Definition

Workflows are defined as a sequence of steps:

```python
from agentnexus.base_types import Workflow, WorkflowStep

MY_WORKFLOW = Workflow(
    id="data_processing",
    name="Data Processing Workflow",
    description="Process data through multiple steps",
    steps=[
        WorkflowStep(id="upload"),
        WorkflowStep(id="validate"),
        WorkflowStep(id="process"),
        WorkflowStep(id="visualize")
    ],
    initial_step="upload"
)
```

### Workflow Steps

Steps are implemented using the `workflow_step` decorator:

```python
from agentnexus.workflow_manager import workflow_step
from agentnexus.base_types import WorkflowStepResponse

@workflow_step(
    agent_config=my_agent,
    workflow_id="data_processing",
    step_id="upload",
    name="Data Upload",
    ui_components=[upload_form]
)
async def handle_upload_step(input_data) -> WorkflowStepResponse:
    # Step implementation
    return WorkflowStepResponse(
        data={"status": "upload_complete"},
        ui_updates=[],
        next_step_id="validate",
        context_updates={"file_path": "/tmp/data.csv"}
    )
```

## Context Management

AgentNexus maintains state across interactions through **context**.

### Context Updates

Context can be updated at each step:

```python
return WorkflowStepResponse(
    data={"status": "complete"},
    ui_updates=[
        UIComponentUpdate(
            key="result_display",
            state={"content": "Analysis complete!"}
        )
    ],
    context_updates={
        "analysis_result": result,
        "timestamp": datetime.now().isoformat()
    }
)
```

### Session Management

For longer-term state, AgentNexus provides session management:

```python
from agentnexus.session_manager import session_manager

# Create a session
session_id = session_manager.create_session()

# Update session
session_manager.update_session(session_id, {
    "user_preferences": {"theme": "dark"},
    "history": ["previous_action"]
})

# Get session data
session = session_manager.get_session(session_id)
```

## Event System

AgentNexus uses an event system to handle component interactions.

### Event Dispatching

Events are dispatched from components to handlers:

```python
# Event handler implementation
async def handle_form_submit(
    action: str,
    data: Dict[str, Any],
    component_key: str,
    **kwargs
) -> WorkflowStepResponse:
    # Process form submission
    values = data.get("values", {})
    # ...
    return WorkflowStepResponse(...)
```

## FastAPI Integration

AgentNexus integrates with FastAPI for API endpoints.

### Agent Manager

The `AgentManager` connects agents to a FastAPI app:

```python
from fastapi import FastAPI
from agentnexus.manifest_generator import AgentManager

app = FastAPI()
agent_manager = AgentManager(base_url="http://localhost:8000")
agent_manager.add_agent(my_agent)
agent_manager.setup_agents(app)
```

### Auto-Generated Endpoints

AgentNexus automatically creates several endpoints:

- `/agents.json`: List all available agents
- `/agents/{agent_slug}.json`: Get detailed agent manifest
- `/agents/{agent_slug}/actions/{action_name}`: Trigger agent actions
- `/agents/{agent_slug}/workflows/{workflow_id}/steps/{step_id}`: Execute workflow steps

## Data Models

AgentNexus uses Pydantic models for data validation.

### Input/Output Models

Define input and output structures using Pydantic:

```python
from pydantic import BaseModel, Field

class SummarizeInput(BaseModel):
    text: str = Field(..., description="Text to summarize")
    max_length: int = Field(100, description="Maximum summary length")

class SummarizeOutput(BaseModel):
    summary: str
    original_length: int
    reduction_percentage: float
```

## Common Patterns

### Agent Setup

```python
# Define agent
my_agent = AgentConfig(...)

# Create actions
@agent_action(agent_config=my_agent, ...)
async def action1(input_data):
    # ...

# Set up FastAPI integration
app = FastAPI()
agent_manager = AgentManager(base_url="...")
agent_manager.add_agent(my_agent)
agent_manager.setup_agents(app)
```

### Workflow Implementation

```python
# Define workflow
MY_WORKFLOW = Workflow(...)

# Implement steps
@workflow_step(
    agent_config=my_agent,
    workflow_id="my_workflow",
    step_id="step1",
    # ...
)
async def handle_step1(input_data) -> WorkflowStepResponse:
    # ...
```

### UI Component Events

```python
# Create component with event handler
my_component = FormComponent(
    # ...
    event_handlers={
        "submit": handle_form_submit
    }
)

# Implement handler
async def handle_form_submit(action, data, component_key, **kwargs):
    # ...
    return WorkflowStepResponse(...)
```

## Next Steps

Now that you understand the basic concepts of AgentNexus:

- Follow the [Quick Start](../quick-start) guide to build your first agent
- Learn about [Project Organization](../project-organization) best practices
- Explore detailed documentation of [Core Concepts](../../core-concepts/)