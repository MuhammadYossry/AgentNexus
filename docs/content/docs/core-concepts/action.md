---
title: "Actions"
description: "Creating and registering agent actions in AgentNexus"
lead: "Actions define the specific functionalities that an agent can perform, from simple conversations to complex UI interactions."
date: 2025-03-25T08:00:00+00:00
lastmod: 2025-03-25T08:00:00+00:00
draft: false
images: []
menu:
  docs:
    parent: "core-concepts"
weight: 320
toc: true
---

## Understanding Agent Actions

**Actions** are the specific functions or capabilities that an agent can perform. They define how an agent responds to requests and what it can do. Think of actions as the methods or endpoints of your agent API.

Each action:
- Has a unique name and description
- Is connected to a specific agent
- Belongs to a specific action type
- Has defined input and output models
- Is registered via a decorator pattern
- Can include UI components for interaction

## Action Types

AgentNexus supports different types of actions through the `ActionType` enum:

| Action Type | Description | Use Case |
|-------------|-------------|----------|
| `TALK` | Conversational interactions | Question answering, chat interfaces |
| `GENERATE` | Content creation | Code generation, text creation, data generation |
| `QUESTION` | Information gathering | Forms, surveys, data collection |
| `CUSTOM_UI` | UI-driven interactions | Interactive workflows, visualization tools |

The action type affects how the action is represented in the agent manifest and influences the expected behavior.

## Defining Actions

Actions are defined using the `agent_action` decorator, which connects a Python function to an agent configuration.

### Basic Action Definition

```python
from agentnexus.action_manager import agent_action
from agentnexus.base_types import ActionType
from pydantic import BaseModel, Field

# Define input/output models
class SummarizeInput(BaseModel):
    text: str = Field(..., description="Text to summarize")
    max_length: int = Field(100, description="Maximum summary length")

class SummarizeOutput(BaseModel):
    summary: str
    original_length: int
    reduction_percentage: float

# Define the action
@agent_action(
    agent_config=content_agent,
    action_type=ActionType.GENERATE,
    name="Summarize Text",
    description="Creates a concise summary of longer text"
)
async def summarize_text(input_data: SummarizeInput) -> SummarizeOutput:
    """Summarize text to a specified maximum length."""
    text = input_data.text
    max_length = input_data.max_length

    # Simple implementation for demonstration
    summary = text[:max_length] + "..." if len(text) > max_length else text
    original_length = len(text)
    reduction = 1.0 - (len(summary) / original_length) if original_length > 0 else 0.0

    return SummarizeOutput(
        summary=summary,
        original_length=original_length,
        reduction_percentage=reduction * 100
    )
```

### Action Decorator Parameters

The `agent_action` decorator accepts several parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_config` | `AgentConfig` | The agent this action belongs to (required) |
| `action_type` | `ActionType` | The type of action (required) |
| `name` | `str` | Human-readable name of the action (required) |
| `description` | `str` | Detailed description of the action (required) |
| `response_template_md` | `Optional[str]` | Path to a markdown response template |
| `schema_definitions` | `Optional[Dict[str, Type[BaseModel]]]` | Additional schema definitions |
| `examples` | `Optional[Dict[str, List[Dict[str, Any]]]]` | Example requests/responses |
| `workflow_id` | `Optional[str]` | Associated workflow ID |
| `step_id` | `Optional[str]` | Associated workflow step ID |
| `ui_components` | `Optional[List[UIComponent]]` | UI components for this action |
| `allow_dynamic_ui` | `bool` | Whether to allow dynamic UI updates (default: False) |

## Data Models

Actions use Pydantic models to validate input and output data:

### Input Models

Input models define the expected parameters:

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class CodeGenerationInput(BaseModel):
    description: str = Field(..., description="Description of what the code should do")
    language: str = Field(..., description="Programming language")
    include_tests: bool = Field(False, description="Whether to include tests")
    frameworks: Optional[List[str]] = Field(None, description="Frameworks to use")
```

### Output Models

Output models define the response structure:

```python
class CodeGenerationOutput(BaseModel):
    code: str
    language: str
    tests: Optional[str] = None
    documentation: Optional[str] = None
    complexity: Optional[float] = None
```

### Model Schema Usage

AgentNexus automatically uses these models to:
- Validate incoming requests
- Generate OpenAPI documentation
- Create JSON schema in the agent manifest
- Provide type hints for development

## Action Handlers

The decorated function is the action handler, which processes the request and returns a response:

```python
@agent_action(
    agent_config=my_agent,
    action_type=ActionType.GENERATE,
    name="Generate Code",
    description="Generate code based on a description"
)
async def generate_code(input_data: CodeGenerationInput) -> CodeGenerationOutput:
    """Generate code based on the provided description."""
    # Access input parameters
    description = input_data.description
    language = input_data.language
    include_tests = input_data.include_tests

    # Generate code (placeholder implementation)
    code = f"// {language} code for: {description}\n\nfunction example() {{\n  // Implementation\n}}"

    # Generate tests if requested
    tests = None
    if include_tests:
        tests = f"// Tests for the code\ntest('example', () => {{\n  // Test implementation\n}});"

    # Return formatted response
    return CodeGenerationOutput(
        code=code,
        language=language,
        tests=tests,
        documentation=f"// Documentation for: {description}",
        complexity=1.0
    )
```

### Async Processing

All action handlers should be asynchronous (using `async def`), which allows for:
- Concurrent request handling
- Non-blocking I/O operations
- Better scalability
- Integration with other async services

## UI-Driven Actions

Actions with the `CUSTOM_UI` type can include UI components for interactive interfaces:

```python
from agentnexus.ui_components import FormComponent, FormField, MarkdownComponent
from agentnexus.base_types import UIComponentUpdate, UIResponse

# Define UI components
input_form = FormComponent(
    component_key="code_input",
    title="Code Generation Input",
    form_fields=[
        FormField(
            field_name="description",
            label_text="Code Description",
            field_type="textarea",
            is_required=True
        ),
        FormField(
            field_name="language",
            label_text="Language",
            field_type="select",
            field_options=[
                {"value": "python", "label": "Python"},
                {"value": "javascript", "label": "JavaScript"}
            ]
        )
    ]
)

output_display = MarkdownComponent(
    component_key="code_output",
    title="Generated Code",
    markdown_content="Code will appear here."
)

# Define UI-driven action
@agent_action(
    agent_config=code_agent,
    action_type=ActionType.CUSTOM_UI,
    name="Interactive Code Generator",
    description="Generate code with an interactive UI",
    ui_components=[input_form, output_display]
)
async def interactive_code_generator(input_data) -> UIResponse:
    """Handle interactive code generation."""
    # Check for form submission
    if hasattr(input_data, 'form_data') and input_data.form_data:
        form_data = input_data.form_data
        if form_data.get("action") == "submit" and form_data.get("component_key") == "code_input":
            # Extract form values
            values = form_data.get("values", {})
            description = values.get("description", "")
            language = values.get("language", "python")

            # Generate code
            code_block = f"```{language}\n# {description}\n\ndef example():\n    pass\n```"

            # Return UI response with updates
            return UIResponse(
                data={"generated": True, "language": language},
                ui_updates=[
                    UIComponentUpdate(
                        key="code_output",
                        state={"markdown_content": f"## Generated Code\n\n{code_block}"}
                    )
                ]
            )

    # Initial state
    return UIResponse(
        data={"ready": True},
        ui_updates=[]
    )
```

### UI Response Structure

UI-driven actions return a `UIResponse` object with:
- `data`: The response data as a dictionary
- `ui_updates`: A list of `UIComponentUpdate` objects for modifying UI component state

## Examples with Templates

Actions can use markdown templates for formatted responses:

```python
@agent_action(
    agent_config=report_agent,
    action_type=ActionType.GENERATE,
    name="Generate Report",
    description="Creates a formatted report from data",
    response_template_md="templates/report_template.md"
)
async def generate_report(input_data: ReportInput) -> ReportOutput:
    # Process input and generate report data
    title = f"Report: {input_data.title}"
    sections = [{"heading": "Introduction", "content": "This is the introduction."}]
    summary = "Executive summary of the report."

    # Return data that will be used in the template
    return ReportOutput(
        title=title,
        sections=sections,
        summary=summary,
        generated_at=datetime.now().isoformat()
    )
```

The template file (`templates/report_template.md`):

```markdown
# {{title}}

*Generated: {{generated_at}}*

## Executive Summary

{{summary}}

{% for section in sections %}
## {{section.heading}}

{{section.content}}
{% endfor %}
```

## Action Registration and Routing

When you apply the `agent_action` decorator, the action is automatically:

1. Registered with the agent's action registry
2. Assigned a unique slug based on the action name
3. Configured with FastAPI when `setup_agents()` is called
4. Added to the agent's manifest

The resulting API endpoint follows this pattern:
```
/agents/{agent_slug}/actions/{action_slug}
```

For example:
```
/agents/content-assistant/actions/summarize-text
```

## Action Examples

You can provide usage examples for your actions:

```python
@agent_action(
    agent_config=math_agent,
    action_type=ActionType.GENERATE,
    name="Calculate Expression",
    description="Evaluates mathematical expressions",
    examples={
        "validRequests": [
            {"expression": "2 + 2 * 3"},
            {"expression": "sin(30) + cos(60)"}
        ]
    }
)
async def calculate_expression(input_data: CalculationInput) -> CalculationOutput:
    # Implementation
    pass
```

These examples appear in:
- The auto-generated API documentation
- The agent manifest's examples section
- Client code generation tools

## Best Practices

### Action Design

1. **Clear Purpose**: Each action should have a single, clear purpose
2. **Descriptive Names**: Use descriptive names that indicate what the action does
3. **Comprehensive Models**: Define thorough input/output models with descriptions
4. **Proper Types**: Use the appropriate action type for the intended behavior
5. **Concise Implementation**: Keep action handlers focused and concise

### Error Handling

Implement proper error handling in your actions:

```python
@agent_action(
    agent_config=my_agent,
    action_type=ActionType.GENERATE,
    name="Process Data",
    description="Process data with error handling"
)
async def process_data(input_data: DataInput) -> DataOutput:
    try:
        # Process data
        result = perform_processing(input_data.data)
        return DataOutput(
            processed=True,
            result=result,
            error=None
        )
    except ValueError as e:
        # Handle validation errors
        return DataOutput(
            processed=False,
            result=None,
            error=f"Validation error: {str(e)}"
        )
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Error processing data: {str(e)}")
        return DataOutput(
            processed=False,
            result=None,
            error=f"Processing error: {str(e)}"
        )
```

### Testing Actions

Create tests for your actions to ensure they work correctly:

```python
async def test_summarize_text():
    # Prepare test input
    input_data = SummarizeInput(
        text="This is a long text that needs to be summarized for testing purposes.",
        max_length=20
    )

    # Call the action handler directly
    result = await summarize_text(input_data)

    # Verify the result
    assert isinstance(result, SummarizeOutput)
    assert len(result.summary) <= 23  # max_length + "..."
    assert result.original_length == len(input_data.text)
    assert result.reduction_percentage > 0
```

## Next Steps

- Learn about [Workflows](../workflows) for multi-step processes
- Explore [UI Components](../ui-components) for interactive interfaces
- Understand [Event Handling](../event-handling) for component interactions
- See how [Context Management](../context-management) preserves state