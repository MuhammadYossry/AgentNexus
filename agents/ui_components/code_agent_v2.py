from agents_manifest.ui_components import CodeEditorComponent, MarkdownComponent, FormComponent, FormField, TableComponent, TableColumn
from agents.ui_handlers.code_agent_v2 import (
    handle_code_format,
    handle_code_save,
    handle_analyze_continue_submit,
    handle_language_form_submit,
    handle_continue_form_submit,
    handle_improve_continue_submit,
    handle_approval_form_submit,
    handle_add_types,
    handle_add_docs
)

# Define components for upload step
code_input = CodeEditorComponent(
    component_key="code_input",
    title="Source Code",
    programming_language="python",
    editor_content="""
def fibonacci(n):
    if n <= 0:
        return []
    if n == 1:
        return [0]
    if n == 2:
        return [0, 1]

    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib

def calculate_statistics(numbers):
    total = sum(numbers)
    avg = total / len(numbers)
    sorted_nums = sorted(numbers)
    if len(numbers) % 2 == 0:
        median = (sorted_nums[len(numbers)//2] + sorted_nums[len(numbers)//2 - 1]) / 2
    else:
        median = sorted_nums[len(numbers)//2]
    
    return {"total": total, "average": avg, "median": median}

def process_data(data_list):
    results = []
    for item in data_list:
        try:
            value = item * 2
            results.append(value)
        except:
            # Some error
            pass
    return results
""",
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

language_selector = FormComponent(
    component_key="language_selector",
    title="Code Settings",
    form_fields=[
        FormField(
            field_name="language",
            label_text="Language",
            field_type="select",
            required=False,
            field_options=[
                {"value": "python", "label": "Python"},
                {"value": "javascript", "label": "JavaScript"},
                {"value": "typescript", "label": "TypeScript"}
            ]
        )
    ],
    event_handlers={
        "submit": handle_language_form_submit
    }
)

# Define components for analyze step
code_display = CodeEditorComponent(
    component_key="code_display",
    title="Code Analysis",
    programming_language="python",
    editor_content="",
    editor_theme="vs-dark",
    is_readonly=True
)

analysis_result = MarkdownComponent(
    component_key="analysis_result",
    title="Analysis Results",
    markdown_content="# Analysis Results"
)

# Define components for improve step
improved_code = CodeEditorComponent(
    component_key="improved_code",
    title="Improved Code",
    programming_language="python",
    editor_content="",
    editor_theme="vs-dark",
    event_handlers={
        "format": handle_code_format,
        "save": handle_code_save,
        "add_types": handle_add_types,
        "add_docs": handle_add_docs
    }
)

improvement_notes = MarkdownComponent(
    component_key="improvement_notes",
    title="Improvement Notes",
    markdown_content=""
)

# Define components for score step
quality_metrics = TableComponent(
    component_key="quality_metrics",
    title="Code Quality Metrics",
    columns=[
        TableColumn(field_name="metric", header_text="Metric", sortable=True),
        TableColumn(field_name="score", header_text="Score", sortable=True),
        TableColumn(field_name="description", header_text="Description", sortable=True)
    ],
    table_data=[]
)

continue_form = FormComponent(
    component_key="continue_form",
    title="Continue to Review",
    form_fields=[
        FormField(
            field_name="proceed",
            label_text="Proceed to Final Review",
            field_type="select",
            field_options=[
                {"value": "yes", "label": "Yes, continue"},
                {"value": "no", "label": "No, improve further"}
            ]
        )
    ],
    event_handlers={
        "submit": handle_continue_form_submit
    }
)

# Define components for review step
final_code = CodeEditorComponent(
    component_key="final_code",
    title="Final Code",
    programming_language="python",
    editor_content="",
    editor_theme="vs-dark",
    is_readonly=True
)

approval_form = FormComponent(
    component_key="approval_form",
    title="Review Decision",
    form_fields=[
        FormField(
            field_name="approved",
            label_text="Approve Changes",
            field_type="select",
            field_options=[
                {"value": "yes", "label": "Approve"},
                {"value": "no", "label": "Request Changes"}
            ]
        ),
        FormField(
            field_name="comments",
            label_text="Comments",
            field_type="text"
        )
    ],
    event_handlers={
        "submit": handle_approval_form_submit
    }
)

# Define components for complete step
completion_summary = MarkdownComponent(
    component_key="completion_summary",
    title="Review Complete",
    markdown_content=""
)

analyze_continue = FormComponent(
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
