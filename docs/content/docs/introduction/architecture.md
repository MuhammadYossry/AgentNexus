---
title: "Architecture"
description: "The architectural design and components of the AgentNexus framework"
lead: "Understanding how the components of AgentNexus fit together to create a cohesive agent development framework."
date: 2025-03-25T08:00:00+00:00
lastmod: 2025-03-25T08:00:00+00:00
draft: false
images: []
menu:
  docs:
    parent: "introduction"
weight: 130
toc: true
---

## Architectural Overview

AgentNexus follows a modular, layered architecture designed to separate concerns while providing integrated functionality. This design allows developers to focus on agent behavior rather than infrastructure.

### High-Level Architecture

<div class="text-center pb-4">
  <img src="../images/architecture-diagram.png" alt="AgentNexus Architecture Diagram" class="img-fluid rounded">
</div>

The AgentNexus framework consists of several key layers:

1. **Agent Definition Layer**: Defines agent capabilities and metadata
2. **Action Management Layer**: Handles agent actions and their execution
3. **Workflow Management Layer**: Manages multi-step processes
4. **UI Component Layer**: Provides interactive UI components
5. **Event Dispatch Layer**: Manages event handling and routing
6. **Session Management Layer**: Handles state persistence
7. **Manifest Generation Layer**: Creates standardized agent manifests

Each layer interacts with the others through well-defined interfaces, creating a cohesive system that simplifies agent development.

## Core Components

### AgentConfig

The `AgentConfig` class is the foundation of agent definition. It includes essential metadata such as name, version, description, and capabilities:

```python
code_agent = AgentConfig(
    name="Code Assistant",
    version="2.0.0",
    description="Advanced code review and improvement agent",
    capabilities=[
        Capability(
            skill_path=["Development", "Code Generation"],
            metadata={"languages": ["Python", "JavaScript"]}
        )
    ]
)
```

### ActionManager

The `ActionManager` handles the registration and execution of agent actions. The `agent_action` decorator connects these actions to the agent:

```python
@agent_action(
    agent_config=code_agent,
    action_type=ActionType.GENERATE,
    name="Format Code",
    description="Format code according to best practices"
)
async def format_code(input_data):
    # Implementation...
```

### WorkflowManager

The `WorkflowManager` orchestrates multi-step processes with state management. Workflows are defined as a series of steps:

```python
CODE_REVIEW_WORKFLOW = Workflow(
    id="code_review",
    name="Interactive Code Review",
    description="Multi-step code review process",
    steps=[
        WorkflowStep(id="upload"),
        WorkflowStep(id="analyze"),
        WorkflowStep(id="improve"),
        WorkflowStep(id="review")
    ],
    initial_step="upload"
)
```

Each step is implemented using the `workflow_step` decorator:

```python
@workflow_step(
    agent_config=code_agent,
    workflow_id="code_review",
    step_id="analyze",
    name="Code Analysis",
    ui_components=[code_display, analysis_result]
)
async def handle_analyze_step(input_data) -> WorkflowStepResponse:
    # Step implementation...
```

### UI Components

AgentNexus provides a range of UI components for building interactive interfaces:

```python
code_input = CodeEditorComponent(
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

The framework includes several component types:
- `FormComponent`
- `TableComponent`
- `CodeEditorComponent`
- `MarkdownComponent`

### EventDispatcher

The `EventDispatcher` manages component events and routes them to appropriate handlers:

```python
# Global event dispatcher instance
global_event_dispatcher = ComponentEventDispatcher()

# Register component with dispatcher
global_event_dispatcher.register_component(component)

# Register event handler
global_event_dispatcher.register_event_handler(
    component_key="code_input",
    event_name="format",
    handler=handle_code_format
)
```

### SessionManager

The `SessionManager` maintains state across interactions:

```python
# Session management example
session_id = session_manager.create_session()
session_manager.update_session(session_id, {
    "context": {"key": "value"}
})
```

### AgentManager

The `AgentManager` coordinates the setup and configuration of agents:

```python
app = FastAPI()
agent_manager = AgentManager(base_url="http://localhost:9000")
agent_manager.add_agent(code_agent_app)
agent_manager.setup_agents(app)
```

### ManifestGenerator

The `ManifestGenerator` creates standardized JSON manifests for agent discovery:

```python
@app.get("/agents/{agent_slug}.json")
async def get_agent_manifest(agent_slug: str):
    return agent_registries[agent_slug].generate_manifest()
```

## Data Flow

AgentNexus implements a standard flow for handling agent interactions:

1. **Request Ingress**: Incoming requests arrive via FastAPI endpoints
2. **Action/Workflow Routing**: Requests are routed to the appropriate action or workflow step
3. **Component Event Handling**: Component interactions are processed by event handlers
4. **Context Management**: State is managed throughout the interaction
5. **Response Generation**: Structured responses are generated, including UI updates
6. **Session Persistence**: Session state is preserved for future interactions

## Integration Points

AgentNexus provides several integration points:

### LLM Integration

The framework includes a standardized interface for integrating with language models:

```python
llm_client = create_llm_client()
response = await llm_client.complete(
    prompt=prompt,
    system_message="You are an expert travel planner.",
    temperature=0.7
)
```

### FastAPI Integration

AgentNexus generates FastAPI endpoints automatically:

```python
app = FastAPI()
agent_manager = AgentManager(base_url="http://localhost:9000")
agent_manager.add_agent(code_agent_app)
agent_manager.setup_agents(app)
```

### Redis Integration (Optional)

For production environments, AgentNexus supports Redis for session management:

```python
# Redis configuration is read from environment variables
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
```

## System Requirements

AgentNexus is designed to work with:

- Python 3.8+
- FastAPI
- Pydantic
- Redis (optional, for production session management)

## Design Principles

The architecture of AgentNexus is guided by several key principles:

1. **Separation of Concerns**: Each component has a specific, well-defined role
2. **Declarative APIs**: Use decorators and configuration objects over imperative code
3. **Context Preservation**: Maintain state throughout complex interactions
4. **Component Reusability**: UI components are self-contained and reusable
5. **Event-Driven Interaction**: Handle UI events through a consistent system
6. **Standard Interfaces**: Consistent patterns for defining and using agents

## Next Steps

- See how AgentNexus [compares to alternatives](../comparisons)
- [Install the framework](../../getting-started/installation) and get started
- Explore [core concepts](../../core-concepts/) in more detail