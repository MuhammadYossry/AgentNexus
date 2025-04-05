---
title: "UI Components"
description: "Overview of the UI component system in AgentNexus"
lead: "AgentNexus provides a rich set of UI components that allow you to create interactive agent interfaces without writing frontend code."
date: 2025-03-25T08:00:00+00:00
lastmod: 2025-03-25T08:00:00+00:00
draft: false
images: []
menu:
  docs:
    parent: "core-concepts"
weight: 340
toc: true
---

## Introduction to UI Components

AgentNexus includes a powerful UI component system that allows you to create interactive agent interfaces declaratively in Python. These components:

- Render automatically in client applications
- Handle user interactions and events
- Maintain their own state
- Update dynamically based on agent responses
- Integrate seamlessly with workflows

This approach lets you create rich, interactive experiences without writing frontend code.

## Component Types

AgentNexus provides several built-in component types:

| Component Type | Description | Use Cases |
|----------------|-------------|-----------|
| `FormComponent` | Interactive data entry forms | User input collection, settings configuration |
| `TableComponent` | Tabular data display with interactions | Data display, selection interfaces, comparison views |
| `CodeEditorComponent` | Code editing with syntax highlighting | Code generation, editing, and review |
| `MarkdownComponent` | Formatted text display | Documentation, results display, instructions |

Each component type is specialized for specific interaction patterns and data types.

## Component Structure

All UI components share a common structure:

```python
from agentnexus.ui_components import UIComponent

# Base component structure
my_component = UIComponent(
    component_type="type",  # The type of component
    component_key="unique_key",  # Unique identifier for this component
    title="Component Title",  # Optional title
    metadata={},  # Optional metadata
    component_state={},  # Initial state
    supported_events=[],  # Events the component supports
    event_handlers={}  # Functions that handle events
)
```

### Common Properties

All components share these properties:

| Property | Type | Description |
|----------|------|-------------|
| `component_type` | `str` | The type of component (required) |
| `component_key` | `str` | Unique identifier for this component instance (required) |
| `title` | `Optional[str]` | Human-readable title for the component |
| `metadata` | `Dict[str, Any]` | Additional metadata about the component |
| `component_state` | `Dict[str, Any]` | Initial state of the component |
| `supported_events` | `List[str]` | Events the component can emit |
| `event_handlers` | `Dict[str, Callable]` | Functions that handle component events |

## Component Examples

### Form Component

Forms collect structured data from users:

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
        ),
        FormField(
            field_name="preferences",
            label_text="Preferences",
            field_type="checkbox",
            field_options=[
                {"value": "email", "label": "Email Updates"},
                {"value": "sms", "label": "SMS Notifications"}
            ]
        )
    ],
    event_handlers={
        "submit": handle_form_submit
    }
)
```

### Table Component

Tables display structured data with interactive features:

```python
from agentnexus.ui_components import TableComponent, TableColumn

results_table = TableComponent(
    component_key="results_table",
    title="Search Results",
    columns=[
        TableColumn(field_name="id", header_text="ID"),
        TableColumn(field_name="name", header_text="Name"),
        TableColumn(field_name="price", header_text="Price"),
        TableColumn(field_name="available", header_text="Available")
    ],
    table_data=[
        {"id": 1, "name": "Item A", "price": 19.99, "available": True},
        {"id": 2, "name": "Item B", "price": 29.99, "available": False}
    ],
    supported_events=["row_click", "sort"],
    event_handlers={
        "row_click": handle_row_selection,
        "sort": handle_table_sort
    }
)
```

### Code Editor Component

Code editors provide syntax highlighting and code-specific interactions:

```python
from agentnexus.ui_components import CodeEditorComponent

code_editor = CodeEditorComponent(
    component_key="code_editor",
    title="Source Code",
    programming_language="python",
    editor_content="def hello():\n    print('Hello, world!')",
    editor_theme="vs-dark",
    editor_height="400px",
    editor_options={
        "minimap": {"enabled": True},
        "lineNumbers": "on",
        "folding": True
    },
    event_handlers={
        "format": handle_code_format,
        "save": handle_code_save
    }
)
```

### Markdown Component

Markdown components display formatted text:

```python
from agentnexus.ui_components import MarkdownComponent

instructions = MarkdownComponent(
    component_key="instructions",
    title="Getting Started",
    markdown_content="""
## Welcome to the Application

Follow these steps to get started:

1. Enter your information
2. Select your preferences
3. Click submit

**Note:** All fields marked with * are required.
    """,
    content_style={
        "padding": "1rem",
        "backgroundColor": "#f5f5f5"
    }
)
```

## Component Event Handling

Components can emit events that are handled by registered functions:

```python
async def handle_form_submit(
    action: str,
    data: Dict[str, Any],
    component_key: str,
    **kwargs
) -> WorkflowStepResponse:
    """Handle form submission."""
    # Extract form values
    values = data.get("values", {})
    name = values.get("name", "")
    age = values.get("age", 0)
    preferences = values.get("preferences", [])

    # Process form data
    # ...

    # Return response
    return WorkflowStepResponse(
        data={"submitted": True, "name": name},
        ui_updates=[
            UIComponentUpdate(
                key="status_display",
                state={"markdown_content": f"Thank you, {name}!"}
            )
        ],
        context_updates={
            "user_name": name,
            "user_age": age,
            "user_preferences": preferences
        }
    )
```

### Supported Events

Each component type supports specific events:

| Component Type | Supported Events |
|----------------|------------------|
| `FormComponent` | `submit`, `field_change`, `validation` |
| `TableComponent` | `row_click`, `sort`, `pagination` |
| `CodeEditorComponent` | `format`, `lint`, `save`, `change` |
| `MarkdownComponent` | (No events) |

### Event Handler Structure

Event handlers have a consistent structure:

```python
async def handle_event(
    action: str,           # The event name/action
    data: Dict[str, Any],  # Event data
    component_key: str,    # The component that emitted the event
    **kwargs               # Additional context
) -> Any:                  # Response (often WorkflowStepResponse)
    """Handle component event."""
    # Implementation
    # ...
```

## Component State Updates

Components can be updated dynamically through `UIComponentUpdate` objects:

```python
from agentnexus.base_types import UIComponentUpdate

# Update a component's state
update = UIComponentUpdate(
    key="results_table",  # Component key to update
    state={  # New state to apply
        "table_data": [
            {"id": 1, "name": "Item A", "price": 19.99, "available": True},
            {"id": 2, "name": "Item B", "price": 29.99, "available": False}
        ]
    }
)
```

### In Workflow Steps

Component updates are often returned from workflow steps:

```python
return WorkflowStepResponse(
    data={"status": "data_loaded"},
    ui_updates=[
        UIComponentUpdate(
            key="results_table",
            state={"table_data": new_data}
        ),
        UIComponentUpdate(
            key="status_display",
            state={"markdown_content": "Data loaded successfully."}
        )
    ],
    next_step_id="review",
    context_updates={"results": new_data}
)
```

### In UI-Driven Actions

Component updates can also be returned from UI-driven actions:

```python
return UIResponse(
    data={"status": "complete"},
    ui_updates=[
        UIComponentUpdate(
            key="code_editor",
            state={"editor_content": formatted_code}
        )
    ]
)
```

## Component Integration Patterns

### Workflow Integration

Components are most commonly used in workflows:

```python
@workflow_step(
    agent_config=document_agent,
    workflow_id="document_processing",
    step_id="edit",
    name="Document Editing",
    ui_components=[document_editor, save_button]
)
async def handle_edit_step(input_data) -> WorkflowStepResponse:
    # Step implementation
    # ...
```

### UI-Driven Action Integration

Components can also be used in UI-driven actions:

```python
@agent_action(
    agent_config=code_agent,
    action_type=ActionType.CUSTOM_UI,
    name="Code Editor",
    description="Interactive code editor",
    ui_components=[code_editor, output_display]
)
async def interactive_code_editing(input_data) -> UIResponse:
    # Action implementation
    # ...
```

### Context-Aware Components

Components can be populated based on workflow context:

```python
# Prepare UI components with context data
def prepare_components_with_context(components: List[UIComponent], context: Dict[str, Any]) -> List[Dict]:
    """Prepare UI components with session context data."""
    prepared_components = []
    for component in components:
        # Create a copy of the component data
        component_data = component.dict(exclude={'event_handlers'})

        # Pre-populate component state based on type and context
        if component.component_type == "code_editor" and component.component_key == "code_input":
            component_data["editor_content"] = context.get("code", "")
        elif component.component_type == "form" and component.component_key == "document_settings":
            component_data["initial_values"] = {
                "language": context.get("language", "en"),
                "format": context.get("format", "pdf")
            }

        prepared_components.append(component_data)
    return prepared_components
```

## Advanced Component Features

### Dynamic Component Generation

Components can be created dynamically based on context:

```python
def create_dynamic_form(schema: Dict[str, Any]) -> FormComponent:
    """Create a form dynamically based on a schema."""
    fields = []
    for field_name, field_config in schema.items():
        field_type = field_config.get("type", "text")
        required = field_config.get("required", False)

        # Create appropriate field
        field = FormField(
            field_name=field_name,
            label_text=field_config.get("label", field_name),
            field_type=field_type,
            is_required=required
        )

        # Add options if applicable
        if field_type in ["select", "checkbox", "radio"]:
            field.field_options = [
                {"value": opt["value"], "label": opt["label"]}
                for opt in field_config.get("options", [])
            ]

        fields.append(field)

    # Create and return form component
    return FormComponent(
        component_key="dynamic_form",
        title=schema.get("title", "Dynamic Form"),
        form_fields=fields,
        event_handlers={"submit": handle_dynamic_form_submit}
    )
```

### Complex Form Validation

Forms can include custom validation logic:

```python
password_form = FormComponent(
    component_key="password_form",
    title="Change Password",
    form_fields=[
        FormField(
            field_name="current_password",
            label_text="Current Password",
            field_type="password",
            is_required=True
        ),
        FormField(
            field_name="new_password",
            label_text="New Password",
            field_type="password",
            is_required=True,
            validation={"pattern": "^(?=.*[A-Za-z])(?=.*\\d)[A-Za-z\\d]{8,}$"}
        ),
        FormField(
            field_name="confirm_password",
            label_text="Confirm Password",
            field_type="password",
            is_required=True
        )
    ],
    event_handlers={
        "submit": handle_password_change,
        "validation": validate_password_match
    }
)

async def validate_password_match(
    action: str,
    data: Dict[str, Any],
    component_key: str,
    **kwargs
) -> Dict[str, Any]:
    """Validate that passwords match."""
    values = data.get("values", {})
    new_password = values.get("new_password", "")
    confirm_password = values.get("confirm_password", "")

    if new_password and confirm_password and new_password != confirm_password:
        return {
            "valid": False,
            "errors": {
                "confirm_password": "Passwords do not match"
            }
        }

    return {"valid": True}
```

### Table Row Actions

Tables can include row-specific actions:

```python
user_table = TableComponent(
    component_key="user_table",
    title="User Management",
    columns=[
        TableColumn(field_name="id", header_text="ID"),
        TableColumn(field_name="name", header_text="Name"),
        TableColumn(field_name="email", header_text="Email"),
        TableColumn(field_name="actions", header_text="Actions")
    ],
    table_data=[
        {"id": 1, "name": "John Doe", "email": "john@example.com", "actions": ["edit", "delete"]},
        {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "actions": ["edit", "delete"]}
    ],
    supported_events=["row_action"],
    event_handlers={
        "row_action": handle_user_action
    }
)

async def handle_user_action(
    action: str,
    data: Dict[str, Any],
    component_key: str,
    **kwargs
) -> UIResponse:
    """Handle user table actions."""
    row_data = data.get("row_data", {})
    action_name = data.get("action_name", "")
    user_id = row_data.get("id")

    if action_name == "edit":
        # Handle edit action
        return UIResponse(
            data={"editing_user": user_id},
            ui_updates=[
                UIComponentUpdate(
                    key="user_form",
                    state={"values": row_data}
                )
            ]
        )
    elif action_name == "delete":
        # Handle delete action
        return UIResponse(
            data={"deleted_user": user_id},
            ui_updates=[
                UIComponentUpdate(
                    key="user_table",
                    state={"data_updates": [
                        {"row_match": {"id": user_id}, "action": "remove"}
                    ]}
                )
            ]
        )
```

## Component Best Practices

### Component Design

1. **Unique Keys**: Use descriptive, unique component keys
2. **Clear Titles**: Provide clear titles for all components
3. **Focused Purpose**: Each component should have a single purpose
4. **Consistent Naming**: Use consistent naming patterns for keys and fields
5. **Proper Event Handling**: Define appropriate event handlers

### Performance Considerations

1. **Minimize State Size**: Keep component state small and focused
2. **Selective Updates**: Update only what has changed
3. **Progressive Loading**: Load data as needed rather than all at once
4. **Debounce Events**: Debounce rapidly firing events like typing

### Accessibility

1. **Descriptive Labels**: Use clear labels for form fields
2. **Required Field Marking**: Clearly mark required fields
3. **Validation Messages**: Provide helpful validation messages
4. **Logical Tab Order**: Ensure a logical tab order in forms

## Next Steps

- Explore detailed documentation for each component type:
  - [Form Components](../../ui-components/form-components)
  - [Table Components](../../ui-components/table-components)
  - [Code Editor Components](../../ui-components/code-editor-components)
  - [Markdown Components](../../ui-components/markdown-components)
- Learn about [Event Handling](../event-handling) in depth
- Understand [Context Management](../context-management) for maintaining state