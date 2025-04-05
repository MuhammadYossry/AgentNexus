---
title: "Workflows"
description: "Building multi-step agent processes with state management"
lead: "Workflows allow you to create complex, multi-step agent interactions with preserved state and UI integration."
date: 2025-03-25T08:00:00+00:00
lastmod: 2025-03-25T08:00:00+00:00
draft: false
images: []
menu:
  docs:
    parent: "core-concepts"
weight: 330
toc: true
---

## Understanding Workflows

**Workflows** in AgentNexus are structured, multi-step processes that guide users through a series of interactions while maintaining state. They're ideal for complex tasks that require:

- Multiple steps to complete
- User input at various stages
- State persistence across steps
- Dynamic UI updates
- Branching logic based on user choices

Examples include:
- Multi-step forms and questionnaires
- Interactive code analysis pipelines
- Step-by-step travel booking processes
- Document creation wizards

## Workflow Structure

A workflow consists of these key elements:

1. **Workflow Definition**: Describes the workflow's structure, steps, and transitions
2. **Workflow Steps**: Individual stages in the process
3. **Step Handlers**: Functions that implement each step's behavior
4. **Context Management**: How state is preserved between steps
5. **UI Integration**: Components displayed at each step

## Defining Workflows

Workflows are defined using the `Workflow` class:

```python
from agentnexus.base_types import Workflow, WorkflowStep, WorkflowStepType

# Define a step-by-step code review workflow
CODE_REVIEW_WORKFLOW = Workflow(
    id="code_review",
    name="Interactive Code Review",
    description="Multi-step code review process with UI interactions",
    steps=[
        WorkflowStep(id="upload"),
        WorkflowStep(id="analyze"),
        WorkflowStep(id="improve"),
        WorkflowStep(id="score"),
        WorkflowStep(id="review"),
        WorkflowStep(id="complete", type=WorkflowStepType.END)
    ],
    initial_step="upload"
)
```

### Workflow Parameters

The `Workflow` class accepts these parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | `str` | Unique identifier for the workflow (required) |
| `name` | `str` | Human-readable name (required) |
| `description` | `str` | Detailed description of the workflow (required) |
| `steps` | `List[WorkflowStep]` | List of steps in the workflow (required) |
| `initial_step` | `str` | ID of the first step (required) |

### Step Definition

Steps are defined using the `WorkflowStep` class:

```python
WorkflowStep(
    id="analyze",  # Unique identifier for this step
    type=WorkflowStepType.UI_STEP,  # Step type (default is UI_STEP)
    action="analyze_code",  # Optional action name
    transitions=None  # Optional explicit transitions
)
```

### Step Types

AgentNexus supports several step types:

| Step Type | Description | Use Case |
|-----------|-------------|----------|
| `WorkflowStepType.START` | Initial workflow step | Entry point for workflows |
| `WorkflowStepType.UI_STEP` | Interactive step with UI | User input collection |
| `WorkflowStepType.END` | Final workflow step | Completion and summary |

## Implementing Workflow Steps

Steps are implemented using the `workflow_step` decorator, which associates a function with a specific workflow step:

```python
from agentnexus.workflow_manager import workflow_step
from agentnexus.base_types import WorkflowStepResponse

@workflow_step(
    agent_config=code_agent,
    workflow_id="code_review",
    step_id="upload",
    name="Code Upload",
    description="Initial code upload step",
    ui_components=[code_input, language_selector]
)
async def handle_upload_step(input_data) -> WorkflowStepResponse:
    """Handle initial code upload."""
    # Extract context and form data
    context = getattr(input_data, 'context', {}) or {}
    form_data = getattr(input_data, 'form_data', None)

    # Check for form submission
    if form_data and form_data.get("action") == "submit":
        # Extract form values
        values = form_data.get("values", {})
        language = values.get("language", "python")
        code_content = context.get("code", "")

        # Move to next step with context updates
        return WorkflowStepResponse(
            data={"status": "upload_complete"},
            ui_updates=[],
            next_step_id="analyze",  # Advance to analysis step
            context_updates={
                "language": language,
                "original_code": code_content,
                "code": code_content
            }
        )

    # Initial step load - return UI updates
    return WorkflowStepResponse(
        data={"status": "ready"},
        ui_updates=[
            UIComponentUpdate(
                key="code_input",
                state={"editor_content": context.get("code", "")}
            )
        ],
        context_updates={}
    )
```

### Workflow Step Decorator

The `workflow_step` decorator accepts these parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_config` | `AgentConfig` | The agent this workflow belongs to (required) |
| `workflow_id` | `str` | Identifier of the workflow (required) |
| `step_id` | `str` | Identifier of the step within the workflow (required) |
| `name` | `str` | Human-readable name of the step (required) |
| `description` | `str` | Detailed description of the step (required) |
| `ui_components` | `Optional[List[UIComponent]]` | UI components for this step |
| `allow_dynamic_ui` | `bool` | Whether to allow dynamic UI updates (default: True) |

### Step Response

Workflow steps return a `WorkflowStepResponse` object that determines:
- What data to return to the client
- Which UI components to update
- What context to preserve for the next step
- Which step to transition to next

```python
return WorkflowStepResponse(
    data={"status": "analysis_complete", "functions_found": 5},
    ui_updates=[
        UIComponentUpdate(
            key="analysis_result",
            state={"markdown_content": analysis_text}
        )
    ],
    next_step_id="improve",  # Proceed to improvement step
    context_updates={
        "analysis": analysis_text,
        "metrics": metrics,
        "original_code": original_code
    }
)
```

### Response Parameters

The `WorkflowStepResponse` class accepts these parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `Dict[str, Any]` | Data to return to the client |
| `ui_updates` | `List[UIComponentUpdate]` | UI component updates |
| `next_step_id` | `Optional[str]` | ID of the next step (None to stay on current step) |
| `context_updates` | `Dict[str, Any]` | Updates to the workflow context |

## Context Management

Context is state data preserved between workflow steps. It's automatically managed by the workflow system.

### Context Updates

Each step can update the context:

```python
return WorkflowStepResponse(
    data={"status": "complete"},
    ui_updates=[],
    next_step_id="next_step",
    context_updates={
        "user_name": "John Doe",
        "selected_options": ["option1", "option2"],
        "timestamp": datetime.now().isoformat()
    }
)
```

### Accessing Context

The context is available in the `input_data` parameter of each step handler:

```python
async def handle_step(input_data) -> WorkflowStepResponse:
    # Extract context safely
    context = getattr(input_data, 'context', {}) or {}

    # Access context values with fallbacks
    user_name = context.get("user_name", "Guest")
    selected_options = context.get("selected_options", [])
    previous_data = context.get("previous_data", {})

    # Use context in processing
    # ...
```

### Context Best Practices

1. **Use consistent keys**: Maintain consistent naming for context keys
2. **Provide fallbacks**: Always use `.get()` with default values
3. **Minimize size**: Store only necessary data in context
4. **Preserve original data**: Keep original inputs alongside processed results
5. **Document context structure**: Document the expected context structure for each step

## UI Integration

Workflows integrate with UI components to create interactive experiences:

```python
# Define UI components for a step
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

language_selector = FormComponent(
    component_key="language_selector",
    title="Code Settings",
    form_fields=[
        FormField(
            field_name="language",
            label_text="Language",
            field_type="select",
            field_options=[
                {"value": "python", "label": "Python"},
                {"value": "javascript", "label": "JavaScript"}
            ]
        )
    ],
    event_handlers={
        "submit": handle_language_form_submit
    }
)

# Associate components with a workflow step
@workflow_step(
    agent_config=code_agent,
    workflow_id="code_review",
    step_id="upload",
    name="Code Upload",
    ui_components=[code_input, language_selector]
)
async def handle_upload_step(input_data) -> WorkflowStepResponse:
    # Step implementation
    # ...
```

### UI Updates

Steps can update UI components:

```python
return WorkflowStepResponse(
    data={"status": "analysis_complete"},
    ui_updates=[
        UIComponentUpdate(
            key="code_display",
            state={"editor_content": original_code}
        ),
        UIComponentUpdate(
            key="analysis_result",
            state={"markdown_content": analysis_text}
        )
    ],
    next_step_id="improve",
    context_updates={
        "analysis": analysis_text
    }
)
```

### Component Event Handling

Components can have their own event handlers:

```python
# Define a component with event handlers
analysis_continue = FormComponent(
    component_key="analyze_continue",
    title="Navigation",
    form_fields=[
        FormField(
            field_name="continue",
            label_text="Continue to Improvement Phase",
            field_type="select",
            field_options=[
                {"value": "yes", "label": "Continue"}
            ]
        )
    ],
    event_handlers={
        "submit": handle_analyze_continue_submit
    }
)

# Implement event handler
async def handle_analyze_continue_submit(input_data: Dict[str, Any]) -> WorkflowStepResponse:
    """Handle continue button click after analysis."""
    # Extract context
    context = input_data.get("context", {})
    # Return response to proceed to next step
    return WorkflowStepResponse(
        data={"message": "Analysis complete, moving to improvement phase"},
        ui_updates=[],
        next_step_id="improve",
        context_updates={
            "original_code": context.get("original_code", ""),
            "analysis": context.get("analysis", "")
        }
    )
```

## Workflow Registration

Workflows need to be registered with an agent:

```python
# Create agent config with the workflow
code_agent = AgentConfig(
    name="Code Assistant",
    version="2.0.0",
    description="Advanced code review and improvement agent",
    capabilities=[
        # Capabilities...
    ],
    workflows=[CODE_REVIEW_WORKFLOW]  # Register workflow here
)
```

### Automatic Endpoint Generation

When a workflow is registered, AgentNexus automatically creates these endpoints:

- `POST /agents/{agent_slug}/workflows/{workflow_id}/start`: Start the workflow
- `POST /agents/{agent_slug}/workflows/{workflow_id}/steps/{step_id}`: Execute a specific step
- `POST /agents/{agent_slug}/workflows/{workflow_id}/steps/{step_id}/preview`: Preview a step's UI

## Workflow Sessions

AgentNexus manages workflow sessions, which maintain state between requests:

```python
# Create a new session for a workflow
session_id = session_manager.create_workflow_session(
    workflow_id="code_review",
    initial_context={"code": "# Sample code"}
)

# Use session ID in subsequent requests
step_response = await process_workflow_step(
    workflow_id="code_review",
    step_id="upload",
    data={"session_id": session_id}
)
```

### Session Storage

Sessions can be stored in:
- Memory (default, for development)
- Redis (recommended for production)

Configure Redis through environment variables:
```
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
SESSION_TTL=3600  # 1 hour
```

## State Management Patterns

### Linear Flow

A simple sequential workflow:
```
Upload → Analyze → Improve → Review → Complete
```

### Branching Flow

A workflow with conditional branches:
```
Upload → Analyze → [if errors] → Fix Errors → Analyze
                 → [if no errors] → Generate Docs → Complete
```

### Loop-Back Flow

A workflow that can return to previous steps:
```
Upload → Analyze → Improve → Score → [if score < threshold] → Improve
                                   → [if score >= threshold] → Complete
```

## Complete Workflow Example

Here's a complete workflow example for a document processing system:

```python
# 1. Define the workflow
DOCUMENT_WORKFLOW = Workflow(
    id="document_processing",
    name="Document Processing",
    description="Process documents through multiple steps",
    steps=[
        WorkflowStep(id="upload"),
        WorkflowStep(id="validate"),
        WorkflowStep(id="transform"),
        WorkflowStep(id="review"),
        WorkflowStep(id="complete", type=WorkflowStepType.END)
    ],
    initial_step="upload"
)

# 2. Create agent with workflow
document_agent = AgentConfig(
    name="Document Processor",
    version="1.0.0",
    description="Process and transform documents",
    capabilities=[
        Capability(
            skill_path=["Documents", "Processing"],
            metadata={"formats": ["Text", "CSV", "JSON"]}
        )
    ],
    workflows=[DOCUMENT_WORKFLOW]
)

# 3. Define UI components
document_uploader = FormComponent(
    component_key="document_uploader",
    title="Document Upload",
    form_fields=[
        FormField(
            field_name="document_type",
            label_text="Document Type",
            field_type="select",
            field_options=[
                {"value": "text", "label": "Text"},
                {"value": "csv", "label": "CSV"},
                {"value": "json", "label": "JSON"}
            ]
        ),
        FormField(
            field_name="content",
            label_text="Document Content",
            field_type="textarea"
        )
    ]
)

document_display = MarkdownComponent(
    component_key="document_display",
    title="Document Preview",
    markdown_content="Upload a document to see preview."
)

# 4. Implement the upload step
@workflow_step(
    agent_config=document_agent,
    workflow_id="document_processing",
    step_id="upload",
    name="Document Upload",
    description="Upload a document for processing",
    ui_components=[document_uploader, document_display]
)
async def handle_upload_step(input_data) -> WorkflowStepResponse:
    """Handle document upload."""
    # Extract context and form data
    context = getattr(input_data, 'context', {}) or {}
    form_data = getattr(input_data, 'form_data', None)

    # Check for form submission
    if form_data and form_data.get("action") == "submit":
        # Extract form values
        values = form_data.get("values", {})
        document_type = values.get("document_type", "text")
        content = values.get("content", "")

        # Display preview
        preview = f"```\n{content[:100]}...\n```" if len(content) > 100 else f"```\n{content}\n```"

        # Move to next step with context updates
        return WorkflowStepResponse(
            data={"status": "upload_complete"},
            ui_updates=[
                UIComponentUpdate(
                    key="document_display",
                    state={"markdown_content": f"## Document Preview ({document_type})\n\n{preview}"}
                )
            ],
            next_step_id="validate",
            context_updates={
                "document_type": document_type,
                "content": content,
                "uploaded_at": datetime.now().isoformat()
            }
        )

    # Initial step load
    return WorkflowStepResponse(
        data={"status": "ready"},
        ui_updates=[],
        context_updates={}
    )

# 5. Implement additional steps
# (validate, transform, review, complete)
```

## Best Practices

### Workflow Design

1. **Clear Step Purposes**: Give each step a single, well-defined purpose
2. **Intuitive Progression**: Design workflows with a natural, logical flow
3. **Meaningful Context**: Use context to preserve important state
4. **Responsive UI**: Update UI components to reflect the current state
5. **Proper Error Handling**: Handle errors gracefully at each step

### Performance Considerations

1. **Minimize Context Size**: Store only what's needed in context
2. **Use Async Operations**: Keep steps non-blocking with async operations
3. **Consider Session TTL**: Set appropriate session timeouts
4. **Progressive Loading**: Load data progressively rather than all at once

### Testing Workflows

Test each step independently and as part of the entire workflow:

```python
async def test_upload_step():
    # Create test input
    input_data = SimpleNamespace(
        context={},
        form_data={
            "action": "submit",
            "component_key": "document_uploader",
            "values": {
                "document_type": "text",
                "content": "Sample document content"
            }
        }
    )

    # Call step handler directly
    result = await handle_upload_step(input_data)

    # Verify response
    assert isinstance(result, WorkflowStepResponse)
    assert result.next_step_id == "validate"
    assert "document_type" in result.context_updates
    assert "content" in result.context_updates
    # More assertions...
```

## Next Steps

- Learn about [UI Components](../ui-components) in detail
- Understand [Event Handling](../event-handling) for component interactions
- Explore [Context Management](../context-management) in depth
- See how workflows fit into the overall [Architecture](../../introduction/architecture)