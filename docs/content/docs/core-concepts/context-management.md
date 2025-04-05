---
title: "Context Management"
description: "Understanding state preservation between interactions in AgentNexus"
lead: "Context management enables preservation of state across workflow steps, agent actions, and user sessions, creating coherent multi-step interactions."
date: 2025-03-25T08:00:00+00:00
lastmod: 2025-03-25T08:00:00+00:00
draft: false
images: []
menu:
  docs:
    parent: "core-concepts"
weight: 360
toc: true
---

## Introduction to Context Management

AgentNexus provides a robust context management system that allows agents to maintain state across different types of interactions. This capability is crucial for:

- Multi-step workflows where data flows between steps
- UI-driven actions that need to preserve user inputs
- Long-running processes with multiple back-and-forth exchanges
- Sessions that maintain user state across separate requests

The context management system operates at several different levels, each serving a specific purpose:

1. **Workflow Context**: State shared between workflow steps
2. **Session Context**: Persistent state across multiple requests
3. **Component State**: UI component-specific state
4. **Agent Context**: Global agent-level state

## Workflow Context

Workflow context provides a shared data store that persists throughout the execution of a multi-step workflow. It allows data to flow naturally between steps.

### Context Structure

Workflow context is simply a dictionary of key-value pairs:

```python
context = {
    "user_name": "John Doe",
    "user_email": "john@example.com",
    "selected_options": ["option1", "option2"],
    "uploaded_file_path": "/tmp/uploads/document.pdf",
    "analysis_results": {"score": 0.85, "categories": ["A", "B"]},
    "timestamp": "2025-03-25T12:34:56"
}
```

### Updating Context

Context is updated through `WorkflowStepResponse` objects returned from step handlers:

```python
from agentnexus.base_types import WorkflowStepResponse

@workflow_step(
    agent_config=my_agent,
    workflow_id="user_onboarding",
    step_id="collect_info",
    # ...
)
async def handle_info_step(input_data) -> WorkflowStepResponse:
    """Handle information collection step."""
    # Extract existing context
    context = getattr(input_data, 'context', {}) or {}
    form_data = getattr(input_data, 'form_data', None)

    if form_data and form_data.get("action") == "submit":
        values = form_data.get("values", {})
        name = values.get("name", "")
        email = values.get("email", "")

        # Return response with context updates
        return WorkflowStepResponse(
            data={"status": "info_collected"},
            ui_updates=[],
            next_step_id="preferences",
            context_updates={
                "user_name": name,
                "user_email": email,
                "collection_time": datetime.now().isoformat()
            }
        )

    # Initial step load
    return WorkflowStepResponse(
        data={"status": "ready"},
        ui_updates=[],
        context_updates={}  # No updates for initial load
    )
```

### Accessing Context

Context is provided as part of the `input_data` parameter in step handlers:

```python
async def handle_preferences_step(input_data) -> WorkflowStepResponse:
    """Handle preferences collection step."""
    # Extract context safely with fallback to empty dict
    context = getattr(input_data, 'context', {}) or {}

    # Access values with defaults
    user_name = context.get("user_name", "Guest")
    user_email = context.get("user_email", "")

    # Use context values
    greeting = f"Hello, {user_name}! Set your preferences below."

    # Return response with UI updates reflecting context
    return WorkflowStepResponse(
        data={"status": "ready"},
        ui_updates=[
            UIComponentUpdate(
                key="greeting",
                state={"markdown_content": greeting}
            ),
            UIComponentUpdate(
                key="email_display",
                state={"markdown_content": f"Email: {user_email}"}
            )
        ],
        context_updates={}
    )
```

### Context Merging

When a step returns `context_updates`, they are merged with the existing context:

```python
# Existing context
context = {
    "user_name": "John",
    "user_email": "john@example.com",
    "preferences": {"theme": "dark"}
}

# Context updates from step
context_updates = {
    "user_name": "John Doe",  # Will overwrite existing value
    "preferences": {"notifications": True}  # Will be merged, not replaced
}

# Resulting context after proper merging
merged_context = {
    "user_name": "John Doe",  # Updated
    "user_email": "john@example.com",  # Unchanged
    "preferences": {
        "theme": "dark",  # Preserved from nested object
        "notifications": True  # Added to nested object
    }
}
```

AgentNexus handles this merging automatically, preserving nested structures.

## Session Management

For longer-term state preservation across separate requests, AgentNexus provides session management.

### Session Creation

Sessions are created and managed through the `session_manager`:

```python
from agentnexus.session_manager import session_manager

# Create a new session
session_id = session_manager.create_session()

# Create session with initial context
session_id = session_manager.create_session(initial_context={
    "user_id": user_id,
    "start_time": datetime.now().isoformat()
})
```

### Workflow Sessions

For workflows, specialized workflow sessions are created:

```python
# Create a workflow session
session_id = session_manager.create_workflow_session(
    workflow_id="document_processing",
    initial_context={"document_id": doc_id}
)
```

### Updating Sessions

Sessions can be updated with new context data:

```python
# Update a session
session_manager.update_session(
    session_id=session_id,
    context_updates={
        "last_action": "document_uploaded",
        "progress": 0.25
    }
)
```

### Retrieving Sessions

Session data can be retrieved:

```python
# Get session data
session = session_manager.get_session(session_id)
document_id = session.get("document_id")
```

### Session Storage Backends

AgentNexus supports multiple session storage backends:

1. **Memory Storage** (default): Sessions stored in memory (for development)
2. **Redis Storage**: Sessions stored in Redis (for production)

Configuration for Redis:

```python
# Environment variables for Redis configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
SESSION_TTL=3600  # Session timeout in seconds (1 hour)
```

The appropriate backend is selected automatically based on the environment.

## Component State

UI components maintain their own internal state, which can be updated through `UIComponentUpdate` objects:

```python
from agentnexus.base_types import UIComponentUpdate

# Update a component's state
return WorkflowStepResponse(
    data={},
    ui_updates=[
        UIComponentUpdate(
            key="data_table",
            state={"table_data": data, "selected_row": 2}
        ),
        UIComponentUpdate(
            key="status_message",
            state={"markdown_content": "Data loaded successfully."}
        )
    ],
    context_updates={}
)
```

Each component type has specific state properties:

### Form Component State

```python
form_state = {
    "values": {
        "name": "John Doe",
        "email": "john@example.com"
    },
    "errors": {
        "email": "Invalid email format"
    },
    "disabled": False,
    "loading": False
}
```

### Table Component State

```python
table_state = {
    "table_data": [
        {"id": 1, "name": "Item A", "price": 29.99},
        {"id": 2, "name": "Item B", "price": 49.99}
    ],
    "selected_rows": [0],
    "sort_field": "price",
    "sort_direction": "asc",
    "page": 1,
    "rows_per_page": 10
}
```

### Code Editor Component State

```python
editor_state = {
    "editor_content": "def hello_world():\n    print('Hello, world!')",
    "language": "python",
    "theme": "vs-dark",
    "readonly": False
}
```

### Markdown Component State

```python
markdown_state = {
    "markdown_content": "# Hello\n\nThis is **formatted** text.",
    "content_style": {"backgroundColor": "#f5f5f5"}
}
```

## Context Hierarchies

AgentNexus context management operates in a hierarchical structure:

1. **Session Context**: Highest level, persists across requests
   - **Workflow Context**: Persists within a workflow execution
     - **Step Context**: Local to a specific workflow step
       - **Component State**: Specific to individual UI components

Changes flow upward through this hierarchy, with component state updates potentially triggering step context updates, which in turn update workflow context and finally session context.

## Context Scope and Lifetime

Different context types have different lifetimes:

| Context Type | Lifetime | Storage Location | Use Case |
|--------------|----------|------------------|----------|
| Session | Minutes to hours | Server (Memory/Redis) | User identification, long-term state |
| Workflow | Duration of workflow | Workflow engine | Data flow between steps |
| Step | Single step execution | Step handler | Local calculations, temporary data |
| Component | UI component lifecycle | Component state | UI display, user interaction |

## Advanced Context Techniques

### Deep Merging

AgentNexus supports deep merging of nested objects in context:

```python
# Original context
context = {
    "settings": {
        "display": {
            "theme": "light",
            "font_size": 12
        },
        "notifications": {
            "email": True,
            "sms": False
        }
    }
}

# Context update
context_updates = {
    "settings": {
        "display": {
            "theme": "dark"  # Only update theme
        }
    }
}

# Result after deep merge
result = {
    "settings": {
        "display": {
            "theme": "dark",     # Updated
            "font_size": 12      # Preserved
        },
        "notifications": {
            "email": True,       # Preserved
            "sms": False         # Preserved
        }
    }
}
```

### Context Validation

For more robust applications, you can implement context validation:

```python
def validate_context(context, required_fields):
    """Validate that required fields exist in context."""
    missing = []
    for field in required_fields:
        if field not in context:
            missing.append(field)
    return missing

async def handle_step(input_data):
    """Handle workflow step with context validation."""
    context = getattr(input_data, 'context', {}) or {}

    # Validate required context
    missing = validate_context(context, ["user_id", "document_id"])
    if missing:
        return WorkflowStepResponse(
            data={"status": "error", "message": f"Missing required context: {', '.join(missing)}"},
            ui_updates=[
                UIComponentUpdate(
                    key="error_message",
                    state={"markdown_content": f"Error: Missing {', '.join(missing)}"}
                )
            ],
            context_updates={}
        )

    # Continue with step implementation
    # ...
```

### Context Transformation

You can transform context data as it moves between steps:

```python
def transform_for_display(raw_data):
    """Transform raw context data for display."""
    return {
        "display_name": f"{raw_data.get('first_name', '')} {raw_data.get('last_name', '')}",
        "formatted_date": raw_data.get('date').strftime("%B %d, %Y"),
        "status_label": "Active" if raw_data.get('status') == 1 else "Inactive"
    }

async def handle_display_step(input_data):
    """Handle display step with context transformation."""
    context = getattr(input_data, 'context', {}) or {}

    # Transform context for display
    display_data = transform_for_display(context)

    return WorkflowStepResponse(
        data={"status": "ready"},
        ui_updates=[
            UIComponentUpdate(
                key="display",
                state={"markdown_content": f"# User: {display_data['display_name']}\n\nStatus: {display_data['status_label']}\nJoined: {display_data['formatted_date']}"}
            )
        ],
        context_updates={}
    )
```

## Context Security Considerations

When managing context, consider these security aspects:

1. **Sensitive Data**: Avoid storing sensitive information (passwords, tokens) in context
2. **Data Minimization**: Store only what's needed for the workflow
3. **Session Timeout**: Configure appropriate session timeouts (default: 1 hour)
4. **Context Isolation**: Ensure context from one session can't leak into another
5. **Validation**: Validate context data before use to prevent injection attacks

## Best Practices

### Context Design

1. **Consistent Keys**: Use consistent naming for context keys
2. **Documentation**: Document expected context structure
3. **Defaults**: Always provide defaults when accessing context
4. **Hierarchical Organization**: Use nested objects for related data
5. **Naming Conventions**: Use clear, descriptive names for context keys

### Context Operations

1. **Defensive Access**: Use `.get()` method with defaults for context access
2. **Validation**: Validate required context fields
3. **Immutability**: Treat input context as immutable, only modify through context_updates
4. **Transformation**: Transform data as needed between raw storage and display
5. **Cleanup**: Remove temporary or unnecessary data from context

### Example Context Pattern

A well-designed context structure might look like:

```python
context = {
    # User information
    "user": {
        "id": "u123456",
        "name": "John Doe",
        "email": "john@example.com",
        "preferences": {
            "theme": "dark",
            "notifications": True
        }
    },

    # Process state
    "process": {
        "current_step": "document_upload",
        "progress": 0.25,
        "started_at": "2025-03-25T10:30:00Z",
        "last_updated": "2025-03-25T10:35:12Z"
    },

    # Document information
    "document": {
        "id": "doc789",
        "name": "report.pdf",
        "size": 1452603,
        "upload_complete": True,
        "processing_status": "analyzing"
    },

    # Analysis results
    "analysis": {
        "completed": False,
        "results": None
    }
}
```

## Next Steps

- Learn about [Workflow Systems](../../workflow-system/) for comprehensive process management
- Understand [UI Components](../ui-components) for interactive interfaces
- Explore [Event Handling](../event-handling) for component interactions
- See how this all fits into the [Architecture](../../introduction/architecture) of AgentNexus