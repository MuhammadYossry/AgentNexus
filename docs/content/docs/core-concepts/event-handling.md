---
title: "Event Handling"
description: "Understanding the event dispatch system in AgentNexus"
lead: "The event handling system enables communication between UI components and agent code, creating interactive and responsive user experiences."
date: 2025-03-25T08:00:00+00:00
lastmod: 2025-03-25T08:00:00+00:00
draft: false
images: []
menu:
  docs:
    parent: "core-concepts"
weight: 350
toc: true
---

## Introduction to Event Handling

AgentNexus uses an event-driven architecture to handle user interactions with UI components. This system allows components to emit events (like button clicks, form submissions, or table row selections) that trigger handler functions in your agent code.

The event handling system is designed to:

- Connect UI component interactions to agent logic
- Maintain a consistent pattern for handling different event types
- Support both synchronous and asynchronous event handlers
- Provide context and data about the triggering event
- Enable dynamic UI updates in response to user actions

## Event Handling Architecture

The event system consists of these key elements:

1. **Events**: Named actions like "submit", "row_click", or "format"
2. **Components**: UI elements that emit events
3. **Event Handlers**: Functions that process events and return responses
4. **Event Dispatcher**: Central system for routing events to handlers
5. **Component Registry**: Maintains relationships between components and handlers

### The Event Flow

When a user interacts with a component, the following process occurs:

1. The component emits an event with relevant data
2. The event is sent to the server via an API call
3. The `ComponentEventDispatcher` receives the event
4. The dispatcher identifies the appropriate handler
5. The handler processes the event and returns a response
6. The response may include UI updates that modify component state
7. The updated UI is rendered to the user

## Component Events

Each component type supports specific events. Here are the common events by component type:

### Form Component Events

| Event | Description | Data Provided |
|-------|-------------|---------------|
| `submit` | Form submission | Form values, action |
| `field_change` | Individual field change | Field name, new value |
| `validation` | Custom validation | Form values to validate |

### Table Component Events

| Event | Description | Data Provided |
|-------|-------------|---------------|
| `row_click` | Row selection | Row data, index |
| `sort` | Column sorting | Column name, direction |
| `pagination` | Page change | Page number, page size |

### Code Editor Component Events

| Event | Description | Data Provided |
|-------|-------------|---------------|
| `format` | Format code | Code content, language |
| `lint` | Lint code | Code content, language |
| `save` | Save code | Code content, language |
| `change` | Code content changed | Code content, language |

## Registering Event Handlers

Event handlers can be registered in several ways:

### 1. During Component Definition

```python
search_form = FormComponent(
    component_key="search_form",
    title="Search Products",
    form_fields=[
        # Form fields...
    ],
    event_handlers={
        "submit": handle_search_submit,
        "field_change": handle_field_change
    }
)
```

### 2. Component Properties

```python
data_table = TableComponent(
    component_key="data_table",
    title="Search Results",
    columns=[
        # Column definitions...
    ],
    on_row_click=handle_row_click,  # Property-based registration
    on_sort=handle_sort
)
```

### 3. Direct Registration with Dispatcher

```python
from agentnexus.event_dispatcher import global_event_dispatcher

global_event_dispatcher.register_event_handler(
    component_key="code_editor",
    event_name="format",
    handler=handle_code_format
)
```

## Implementing Event Handlers

Event handlers are functions that process events and return appropriate responses. Handlers should be asynchronous for optimal performance.

### Handler Signature

Event handlers follow this general signature:

```python
async def handle_event(
    action: str,           # The event name
    data: Dict[str, Any],  # Event data
    component_key: str,    # The component that emitted the event
    **kwargs               # Additional context
) -> Any:                  # Response (often WorkflowStepResponse or UIResponse)
    """Handle component event."""
    # Implementation
    # ...
```

### Handler Implementation Example

Here's an example of a form submission handler:

```python
from agentnexus.base_types import WorkflowStepResponse, UIComponentUpdate

async def handle_search_submit(
    action: str,
    data: Dict[str, Any],
    component_key: str,
    **kwargs
) -> WorkflowStepResponse:
    """Handle search form submission."""
    # Extract values from form submission
    values = data.get("values", {})
    query = values.get("query", "")
    category = values.get("category", "")

    # Perform search (your business logic)
    search_results = await perform_search(query, category)

    # Return response with UI updates
    return WorkflowStepResponse(
        data={"search_complete": True, "results_count": len(search_results)},
        ui_updates=[
            UIComponentUpdate(
                key="results_table",
                state={"table_data": search_results}
            ),
            UIComponentUpdate(
                key="status_message",
                state={"markdown_content": f"Found {len(search_results)} results for '{query}'"}
            )
        ],
        context_updates={
            "last_query": query,
            "last_category": category,
            "search_results": search_results
        }
    )
```

## Response Types

Event handlers can return different types of responses:

### WorkflowStepResponse

Used in workflow steps to manage step transitions and state:

```python
return WorkflowStepResponse(
    data={"status": "input_received"},
    ui_updates=[
        UIComponentUpdate(
            key="component_id",
            state={"updated_property": "new_value"}
        )
    ],
    next_step_id="next_step",  # Where to go next
    context_updates={"key": "value"}  # Update shared context
)
```

### UIResponse

Used in UI-driven actions to update the interface:

```python
return UIResponse(
    data={"operation_complete": True},
    ui_updates=[
        UIComponentUpdate(
            key="component_id",
            state={"updated_property": "new_value"}
        )
    ]
)
```

## The Component Event Dispatcher

The `ComponentEventDispatcher` is the central hub for event handling:

```python
from agentnexus.event_dispatcher import global_event_dispatcher

# Register a component
global_event_dispatcher.register_component(my_component)

# Register an event handler
global_event_dispatcher.register_event_handler(
    component_key="my_component",
    event_name="click",
    handler=handle_click
)

# Dispatch an event manually (rarely needed)
result = await global_event_dispatcher.dispatch_event(
    component_key="my_component",
    event_name="click",
    event_data={"click_pos": [10, 20]}
)
```

The dispatcher uses a singleton pattern, ensuring a single shared instance across your application.

## Event Context

Events often include context information to help handlers process them appropriately:

```python
class EventContext:
    context_type: str  # e.g., "row", "cell", "form"
    data: Dict[str, Any]  # Context-specific data
```

For example, a table row click event might include:

```python
{
    "context_type": "row",
    "data": {
        "row_index": 3,
        "row_data": {"id": 42, "name": "Product A", "price": 29.99}
    }
}
```

## Dynamic Actions

Some components like the `CodeEditorComponent` support dynamic actions beyond standard events:

```python
code_editor = CodeEditorComponent(
    component_key="code_editor",
    title="Code Editor",
    programming_language="python",
    editor_content="# Code here",
    available_actions=["format", "analyze", "add_docstrings", "add_types"],
    event_handlers={
        "format": handle_format,
        # Other standard handlers
    },
    action_handlers=ActionHandlerMap(
        handlers={
            "analyze": handle_analyze,
            "add_docstrings": handle_add_docstrings,
            "add_types": handle_add_types
        },
        default_handler=handle_default_action
    )
)
```

## Workflow Integration

Event handling integrates tightly with workflows:

```python
@workflow_step(
    agent_config=my_agent,
    workflow_id="my_workflow",
    step_id="input_step",
    name="Input Collection",
    ui_components=[input_form, help_text]
)
async def handle_input_step(input_data) -> WorkflowStepResponse:
    """Handle input collection step."""
    # Extract context and form data
    context = getattr(input_data, 'context', {}) or {}
    form_data = getattr(input_data, 'form_data', None)

    # Process form submission event
    if form_data and form_data.get("action") == "submit":
        # Handle form submission
        # ...
        return WorkflowStepResponse(
            data={"input_complete": True},
            ui_updates=[],
            next_step_id="processing_step",
            context_updates={"user_input": values}
        )

    # Initial step load
    return WorkflowStepResponse(
        data={"status": "ready"},
        ui_updates=[
            UIComponentUpdate(
                key="input_form",
                state={"values": {"field1": context.get("field1", "")}}
            )
        ],
        context_updates={}
    )
```

## Best Practices

### Event Handler Design

1. **Keep handlers focused**: Each handler should perform a specific task
2. **Use async functions**: Make handlers asynchronous for better performance
3. **Handle errors gracefully**: Implement proper error handling
4. **Extract data defensively**: Use `.get()` with defaults for data extraction
5. **Return appropriate responses**: Match the return type to the context

### Event Naming and Organization

1. **Consistent naming**: Use clear, consistent event names (`submit` not `process_form`)
2. **Component-specific events**: Use the events specified for each component type
3. **Custom events**: Document custom events clearly when extending functionality

### Context Management

1. **Preserve context**: Store important data in context for later use
2. **Minimize context size**: Only store what's needed in context
3. **Use context appropriately**: Handle session vs. step vs. component state

### Error Handling

Implement proper error handling in event handlers:

```python
async def handle_event(action, data, component_key, **kwargs):
    try:
        # Event handling logic
        # ...
        return response
    except ValidationError as e:
        # Handle validation errors
        return WorkflowStepResponse(
            data={"status": "validation_error", "errors": str(e)},
            ui_updates=[
                UIComponentUpdate(
                    key="error_message",
                    state={"markdown_content": f"Validation error: {str(e)}"}
                )
            ],
            context_updates={}
        )
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Error in event handler: {str(e)}")
        return WorkflowStepResponse(
            data={"status": "error", "message": str(e)},
            ui_updates=[
                UIComponentUpdate(
                    key="error_message",
                    state={"markdown_content": f"An error occurred: {str(e)}"}
                )
            ],
            context_updates={}
        )
```

## Next Steps

- Learn about [Context Management](../context-management) in depth
- Explore [UI Components](../../ui-components/) and their specific events
- See how events fit into [Workflows](../workflows)
- Review the [API Reference](../../api-reference/event-system) for complete details