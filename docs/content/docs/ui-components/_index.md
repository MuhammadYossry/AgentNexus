---
title: "UI Components"
description: "Interactive UI components for building agent interfaces"
lead: "AgentNexus provides a rich set of UI components that enable interactive agent interfaces without writing frontend code."
date: 2025-03-25T08:00:00+00:00
lastmod: 2025-03-25T08:00:00+00:00
draft: false
images: []
weight: 400
---

# UI Components

AgentNexus includes a powerful UI component system that allows you to create rich, interactive agent interfaces directly from Python. These components handle rendering, user interaction, state management, and event processing.

## Available Components

{{< cards >}}
  {{< card link="ui-components/form-components" title="Form Components" icon="user-circle" subtitle="Interactive data collection forms" >}}
  {{< card link="ui-components/table-components" title="Table Components" icon="user-circle" subtitle="Tabular data display with interactions" >}}
  {{< card link="ui-components/code-editor-components" title="Code Editor Components" icon="user-circle" subtitle="Code editing with syntax highlighting" >}}
  {{< card link="ui-components/markdown-components" title="Markdown Components" icon="document-text" subtitle="Formatted text display" >}}
  {{< card link="ui-components/custom-components" title="Custom Components" icon="user-circle" subtitle="Creating your own components" >}}
{{< /cards >}}

## Key Benefits

AgentNexus UI components offer several advantages:

- **Declarative Syntax**: Define UI components directly in Python
- **Event Handling**: Built-in system for handling user interactions
- **State Management**: Automatic state preservation across interactions
- **Dynamic Updates**: Update components based on agent responses
- **Workflow Integration**: Seamless integration with multi-step workflows
- **No Frontend Code**: Create rich interfaces without JavaScript or HTML

## Component Architecture

All AgentNexus UI components follow a consistent architecture:

1. **Component Definition**: Python objects defining structure and behavior
2. **Event System**: Handlers for user interactions
3. **State Management**: Properties that define component appearance and behavior
4. **Update Mechanism**: System for modifying components based on agent responses

## Basic Example

Here's a simple example of defining and using a form component:

```python
from agentnexus.ui_components import FormComponent, FormField
from agentnexus.base_types import UIComponentUpdate, WorkflowStepResponse

# Define a form component
user_form = FormComponent(
    component_key="user_form",
    title="User Information",
    form_fields=[
        FormField(
            field_name="name",
            label_text="Full Name",
            field_type="text",
            is_required=True
        ),
        FormField(
            field_name="email",
            label_text="Email Address",
            field_type="email",
            is_required=True
        )
    ],
    event_handlers={
        "submit": handle_form_submit
    }
)

# Define an event handler
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
    email = values.get("email", "")

    # Return response with UI updates
    return WorkflowStepResponse(
        data={"status": "form_submitted"},
        ui_updates=[
            UIComponentUpdate(
                key="status_display",
                state={"markdown_content": f"Thank you, {name}!"}
            )
        ],
        context_updates={
            "user_name": name,
            "user_email": email
        }
    )
```

## Component Integration

Components are typically used in two ways:

### In Workflows

```python
@workflow_step(
    agent_config=my_agent,
    workflow_id="user_registration",
    step_id="collect_info",
    name="Collect User Information",
    ui_components=[user_form, status_display]
)
async def handle_user_info_step(input_data) -> WorkflowStepResponse:
    # Workflow step implementation
    # ...
```

### In UI-Driven Actions

```python
@agent_action(
    agent_config=my_agent,
    action_type=ActionType.CUSTOM_UI,
    name="Interactive Registration",
    description="Interactive user registration form",
    ui_components=[user_form, status_display]
)
async def interactive_registration(input_data) -> UIResponse:
    # Action implementation
    # ...
```

## Next Steps

<div class="row">
  <div class="col-md-6">
    <div class="card h-100">
      <div class="card-body">
        <h5 class="card-title">
          <a href="ui-components/form-components">Form Components →</a>
        </h5>
        <p class="card-text">
          Learn about creating interactive forms for data collection.
        </p>
      </div>
    </div>
  </div>
  <div class="col-md-6">
    <div class="card h-100">
      <div class="card-body">
        <h5 class="card-title">
          <a href="../core-concepts/ui-components">UI Concepts →</a>
        </h5>
        <p class="card-text">
          Review core concepts of the UI component system.
        </p>
      </div>
    </div>
  </div>
</div>