---
title: "Code Editor Components"
description: "Working with code editing and analysis components"
lead: "Code editor components provide an interactive way to edit, format, and analyze code with syntax highlighting and specialized actions."
date: 2025-03-25T08:00:00+00:00
lastmod: 2025-03-25T08:00:00+00:00
draft: false
images: []
menu:
  docs:
    parent: "ui-components"
weight: 430
toc: true
---

## Introduction to Code Editor Components

The `CodeEditorComponent` provides a specialized interface for working with code, featuring syntax highlighting, formatting, and code-specific actions. These components are perfect for:

- Code generation and editing
- Code analysis and review
- Demonstration of code examples
- Interactive programming tutorials
- Code improvement workflows

Code editors are particularly powerful when combined with code-focused agents that can analyze, transform, and improve code.

## Basic Code Editor Structure

A basic code editor component includes programming language, content, and event handlers:

```python
from agentnexus.ui_components import CodeEditorComponent

python_editor = CodeEditorComponent(
    component_key="python_editor",
    title="Python Code",
    programming_language="python",
    editor_content="def hello_world():\n    print('Hello, world!')",
    editor_theme="vs-dark",
    editor_height="400px",
    event_handlers={
        "format": handle_code_format,
        "save": handle_code_save
    }
)
```

## Code Editor Parameters

The `CodeEditorComponent` class accepts these parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `component_key` | `str` | Unique identifier for this component (required) |
| `title` | `str` | Human-readable title for the editor |
| `programming_language` | `str` | Language for syntax highlighting (required) |
| `editor_content` | `str` | Initial code content |
| `editor_theme` | `Optional[str]` | Theme for the editor (default: "vs-dark") |
| `is_readonly` | `bool` | Whether the editor is read-only (default: False) |
| `editor_height` | `str` | Height of the editor (default: "400px") |
| `available_actions` | `List[str]` | List of available actions |
| `editor_options` | `Dict[str, Any]` | Additional editor configuration options |
| `event_handlers` | `Dict[str, Callable]` | Functions that handle editor events |

## Supported Languages

Code editors support many programming languages, including:

- `python`: Python
- `javascript`: JavaScript
- `typescript`: TypeScript
- `java`: Java
- `csharp`: C#
- `cpp`: C++
- `go`: Go
- `rust`: Rust
- `html`: HTML
- `css`: CSS
- `json`: JSON
- `yaml`: YAML
- `sql`: SQL
- `shell`: Shell/Bash

## Editor Themes

Code editors support various themes, including:

- `vs-dark`: Dark Visual Studio theme (default)
- `vs-light`: Light Visual Studio theme
- `hc-black`: High Contrast Dark theme
- `hc-light`: High Contrast Light theme

## Editor Options

You can customize the editor behavior with options:

```python
code_editor = CodeEditorComponent(
    component_key="code_editor",
    programming_language="javascript",
    editor_content="// JavaScript code here",
    editor_options={
        "minimap": {"enabled": True},  # Show minimap
        "lineNumbers": "on",           # Show line numbers
        "folding": True,               # Enable code folding
        "wordWrap": "on",              # Enable word wrapping
        "autoIndent": "full",          # Auto-indentation
        "tabSize": 2                   # Tab size in spaces
    }
)
```

## Event Handling

Code editors emit events that can be handled by your agent:

```python
from typing import Dict, Any
from agentnexus.base_types import WorkflowStepResponse, UIComponentUpdate

async def handle_code_format(
    action: str,
    data: Dict[str, Any],
    component_key: str,
    **kwargs
) -> WorkflowStepResponse:
    """Handle code formatting."""
    # Extract code from data
    code = data.get("code", "")
    language = data.get("language", "python")

    # Format the code (simplified example)
    if language == "python":
        import black
        try:
            formatted_code = black.format_str(code, mode=black.FileMode())
        except Exception as e:
            return WorkflowStepResponse(
                data={"error": str(e)},
                ui_updates=[],
                context_updates={}
            )
    else:
        # For other languages, just return the original code
        formatted_code = code

    # Return formatted code
    return WorkflowStepResponse(
        data={"formatted": True},
        ui_updates=[
            UIComponentUpdate(
                key=component_key,
                state={"editor_content": formatted_code}
            )
        ],
        context_updates={
            "formatted_code": formatted_code
        }
    )
```

### Code Editor Events

Code editors support these events:

| Event | Description | Data Provided |
|-------|-------------|---------------|
| `format` | Format code | Code content, language |
| `save` | Save code | Code content, language |
| `lint` | Lint code for errors | Code content, language |
| `change` | Code content changed | Code content, language |
| `add_types` | Add type hints (Python) | Code content |
| `add_docs` | Add documentation | Code content |

### Custom Code Actions

You can define custom actions for code editors:

```python
code_editor = CodeEditorComponent(
    component_key="code_editor",
    title="Python Code",
    programming_language="python",
    editor_content="def hello():\n    print('Hello')",
    available_actions=["format", "save", "add_types", "add_docs", "optimize"],
    event_handlers={
        "format": handle_code_format,
        "save": handle_code_save,
        "add_types": handle_add_types,
        "add_docs": handle_add_docs,
        "optimize": handle_optimize_code
    }
)
```

## Code Editor Updates

You can update code editors dynamically:

```python
# Update code content
return WorkflowStepResponse(
    data={"code_generated": True},
    ui_updates=[
        UIComponentUpdate(
            key="code_editor",
            state={"editor_content": generated_code}
        )
    ],
    context_updates={
        "generated_code": generated_code
    }
)

# Update editor options
return WorkflowStepResponse(
    data={"options_updated": True},
    ui_updates=[
        UIComponentUpdate(
            key="code_editor",
            state={"editor_options": {"readOnly": True}}
        )
    ],
    context_updates={}
)
```

## Advanced Code Editor Features

### Read-Only Mode

Create a read-only editor for displaying code without allowing edits:

```python
code_display = CodeEditorComponent(
    component_key="code_display",
    title="Generated Code",
    programming_language="python",
    editor_content="# Generated code will appear here",
    is_readonly=True,
    editor_theme="vs-light"
)
```

### Diff Viewing

Set up editors to show code differences:

```python
original_code = CodeEditorComponent(
    component_key="original_code",
    title="Original Code",
    programming_language="python",
    editor_content=original_version,
    editor_theme="vs-light",
    is_readonly=True
)

improved_code = CodeEditorComponent(
    component_key="improved_code",
    title="Improved Code",
    programming_language="python",
    editor_content=improved_version,
    editor_theme="vs-light"
)
```

### Code Actions

Implement specialized code actions for specific languages:

```python
async def handle_add_types(
    action: str,
    data: Dict[str, Any],
    component_key: str,
    **kwargs
) -> WorkflowStepResponse:
    """Add type hints to Python code."""
    code = data.get("code", "")

    # Simple example of adding type hints
    import re

    # Add return type hints to functions
    typed_code = re.sub(
        r'def ([a-zA-Z0-9_]+)\((.*?)\):',
        r'def \1(\2) -> Any:',
        code
    )

    # Add parameter type hints (simplified)
    typed_code = re.sub(
        r'def ([a-zA-Z0-9_]+)\(([a-zA-Z0-9_]+)(, )?([^)]*)\)',
        r'def \1(\2: Any\3\4)',
        typed_code
    )

    return WorkflowStepResponse(
        data={"types_added": True},
        ui_updates=[
            UIComponentUpdate(
                key=component_key,
                state={"editor_content": typed_code}
            )
        ],
        context_updates={
            "typed_code": typed_code
        }
    )
```

### Code Analysis

Integrate code analysis with the editor:

```python
async def handle_code_analyze(
    action: str,
    data: Dict[str, Any],
    component_key: str,
    **kwargs
) -> WorkflowStepResponse:
    """Analyze code and provide feedback."""
    code = data.get("code", "")
    language = data.get("language", "python")

    # Perform code analysis (simplified example)
    analysis_results = {
        "line_count": len(code.splitlines()),
        "character_count": len(code),
        "function_count": code.count("def ") if language == "python" else 0,
        "class_count": code.count("class ") if language == "python" else 0,
        "issues": []
    }

    # Check for common issues (simplified)
    if language == "python":
        if "except:" in code:
            analysis_results["issues"].append("Bare 'except:' clause found")
        if "import *" in code:
            analysis_results["issues"].append("Wildcard import found")

    # Format analysis as markdown
    analysis_md = f"""
## Code Analysis

- Lines: {analysis_results['line_count']}
- Characters: {analysis_results['character_count']}
- Functions: {analysis_results['function_count']}
- Classes: {analysis_results['class_count']}

### Issues Found

{"- " + '\\n- '.join(analysis_results['issues']) if analysis_results['issues'] else "No issues found"}
"""

    return WorkflowStepResponse(
        data={"analysis_complete": True},
        ui_updates=[
            UIComponentUpdate(
                key="analysis_display",
                state={"markdown_content": analysis_md}
            )
        ],
        context_updates={
            "code_analysis": analysis_results
        }
    )
```

## Common Code Editor Patterns

### Code Generation and Review

```python
# Code description form
description_form = FormComponent(
    component_key="description_form",
    title="Code Requirements",
    form_fields=[
        FormField(
            field_name="description",
            label_text="Describe the code you need",
            field_type="textarea",
            is_required=True
        ),
        FormField(
            field_name="language",
            label_text="Programming Language",
            field_type="select",
            field_options=[
                {"value": "python", "label": "Python"},
                {"value": "javascript", "label": "JavaScript"},
                {"value": "java", "label": "Java"}
            ]
        )
    ],
    event_handlers={
        "submit": handle_description_submit
    }
)

# Generated code editor
generated_code = CodeEditorComponent(
    component_key="generated_code",
    title="Generated Code",
    programming_language="python",  # Will be updated based on form
    editor_content="# Code will appear here after generation",
    editor_theme="vs-dark",
    event_handlers={
        "format": handle_code_format,
        "save": handle_code_save
    }
)

# Analysis display
analysis_display = MarkdownComponent(
    component_key="analysis_display",
    title="Code Analysis",
    markdown_content="Submit code for analysis"
)
```

### Multi-Step Code Improvement

```python
# Step 1: Original code
original_code = CodeEditorComponent(
    component_key="original_code",
    title="Original Code",
    programming_language="python",
    editor_content="# Paste your code here",
    event_handlers={
        "save": handle_code_save
    }
)

# Step 2: Analysis
analysis_display = MarkdownComponent(
    component_key="analysis_display",
    title="Code Analysis",
    markdown_content="Code analysis will appear here"
)

# Step 3: Improved code
improved_code = CodeEditorComponent(
    component_key="improved_code",
    title="Improved Code",
    programming_language="python",
    editor_content="# Improved code will appear here",
    event_handlers={
        "format": handle_code_format,
        "add_types": handle_add_types,
        "add_docs": handle_add_docs
    }
)
```

### Interactive Coding Tutorial

```python
# Tutorial step explanation
tutorial_text = MarkdownComponent(
    component_key="tutorial_text",
    title="Step 1: Basic Function",
    markdown_content="""
## Creating Your First Function

In this step, you'll create a basic function that greets a user by name.
A Python function is defined using the `def` keyword, followed by the function name and parameters.

Try completing the function below by adding the code to print the greeting.
"""
)

# Exercise code editor
exercise_code = CodeEditorComponent(
    component_key="exercise_code",
    title="Exercise",
    programming_language="python",
    editor_content="def greet(name):\n    # Add your code here\n    pass\n\n# Test your function\ngreet('World')",
    event_handlers={
        "run": handle_code_run,
        "check": handle_solution_check,
        "hint": handle_provide_hint
    }
)

# Output display
output_display = MarkdownComponent(
    component_key="output_display",
    title="Output",
    markdown_content="Run your code to see the output"
)
```

## Integration with Analysis Tools

Code editors often work with analysis tools:

```python
async def handle_lint_code(
    action: str,
    data: Dict[str, Any],
    component_key: str,
    **kwargs
) -> WorkflowStepResponse:
    """Lint Python code for errors and style issues."""
    code = data.get("code", "")

    # Use pylint programmatically (simplified example)
    import io
    import sys
    from pylint import lint
    from pylint.reporters.text import TextReporter

    stdout = sys.stdout
    sys.stdout = string_io = io.StringIO()

    try:
        # Create a temporary file with the code
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w+") as temp:
            temp.write(code)
            temp.flush()

            # Run pylint on the temporary file
            lint_args = [
                "--disable=C0111",  # Disable missing docstring warning
                temp.name
            ]
            reporter = TextReporter(string_io)
            lint.Run(lint_args, reporter=reporter, exit=False)
    finally:
        sys.stdout = stdout

    lint_output = string_io.getvalue()

    # Format lint results as markdown
    lint_md = f"""
## Lint Results

```
{lint_output}
```
"""

    return WorkflowStepResponse(
        data={"lint_complete": True},
        ui_updates=[
            UIComponentUpdate(
                key="lint_results",
                state={"markdown_content": lint_md}
            )
        ],
        context_updates={
            "lint_results": lint_output
        }
    )
```

## Best Practices

### Code Editor Design

1. **Clear Titles**: Use descriptive titles for each editor
2. **Appropriate Height**: Set editor height based on expected code size
3. **Theme Consistency**: Use consistent themes across editors
4. **Read-Only When Appropriate**: Use read-only mode for display-only code
5. **Relevant Actions**: Include only actions relevant to the current task

### Code Interactions

1. **Meaningful Feedback**: Provide clear feedback for code actions
2. **Error Handling**: Gracefully handle code errors
3. **Format Preservation**: Maintain code formatting when possible
4. **Context Management**: Store code in context for workflow progression
5. **Language Detection**: Verify language matches editor settings

### Performance

1. **Code Size Limits**: Be mindful of very large code blocks
2. **Throttle Live Analysis**: Delay analysis for rapidly changing code
3. **Progressive Loading**: Load large code bases progressively
4. **Efficient Updates**: Update only what has changed
5. **Editor Options**: Disable heavy features for large files

## Next Steps

- Learn about [Markdown Components](../markdown-components) for formatted text display
- Explore [Custom Components](../custom-components) for specialized needs
- Understand how code editors work with [Workflows](../../core-concepts/workflows)
- See the [Code Assistant](../../examples/code-assistant) example for a complete implementation