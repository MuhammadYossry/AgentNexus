from agents_manifest.ui_components import CodeEditorComponent, MarkdownComponent
from agents.ui_handlers.code_agent_v1 import handle_code_analyze, handle_code_format

main_editor = CodeEditorComponent(
    component_key="main_editor",
    title="Source Code",
    programming_language="python",
    editor_content="# Enter your Python code here\n\ndef example_function():\n    print('Hello, world!')",
    editor_options={
        "minimap": {"enabled": True},
        "lineNumbers": "on",
        "folding": True,
        "formatOnPaste": True,
    },
    supported_events=["analyze", "format"],
    event_handlers={  # Add event handlers directly
        "analyze": handle_code_analyze,
        "format": handle_code_format
    }
)
analysis_output = MarkdownComponent(
    component_key="analysis_output",
    title="Analysis Results",
    markdown_content="*Submit code for analysis by clicking action buttons*",
    content_style={"padding": "1rem", "backgroundColor": "#f5f5f5"}
)