# code_agent_v2.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import black

from agents_manifest.base_types import (
    AgentConfig, Capability, Workflow, WorkflowStep, WorkflowStepType,
    WorkflowStepResponse, ActionType
)
from agents_manifest.ui_components import (
    CodeEditorComponent, MarkdownComponent, FormComponent, FormField, TableComponent, TableColumn
)
from agents_manifest.workflow_manager import workflow_step

# Input/Output Models
class CodeInput(BaseModel):
    content: str
    language: str = "python"
    context: Optional[Dict[str, Any]] = None

class ReviewResult(BaseModel):
    approved: bool
    comments: str
    suggestions: List[str]

# Define the workflow
CODE_REVIEW_WORKFLOW = Workflow(
    id="code_review",
    name="Interactive Code Review",
    description="Multi-step code review process with UI interactions",
    steps=[
        WorkflowStep(id="upload", type=WorkflowStepType.START),
        WorkflowStep(id="analyze", type=WorkflowStepType.UI_STEP),
        WorkflowStep(id="improve", type=WorkflowStepType.UI_STEP),
        WorkflowStep(id="score", type=WorkflowStepType.UI_STEP),
        WorkflowStep(id="review", type=WorkflowStepType.UI_STEP),
        WorkflowStep(id="complete", type=WorkflowStepType.END)
    ],
    initial_step="upload"
)

code_assistant_v2_app = AgentConfig(
    name="Code Assistant V2",
    version="2.0.0",
    description="UI-driven code review and improvement system",
    capabilities=[
        Capability(
            skill_path=["Development", "Code Review"],
            metadata={
                "languages": ["python", "javascript", "typescript"],
                "features": ["formatting", "style analysis", "improvement suggestions"]
            }
        )
    ],
    workflows=[CODE_REVIEW_WORKFLOW]
)

@workflow_step(
    agent_config=code_assistant_v2_app,
    workflow_id="code_review",
    step_id="upload",
    name="Code Upload",
    description="Initial code upload step",
    action_type=ActionType.CUSTOM_UI,
    ui_components=[
        CodeEditorComponent(
            key="code_input",
            title="Source Code",
            language="python",
            content="# Paste your code here",
            options={
                "minimap": {"enabled": True},
                "lineNumbers": "on"
            }
        ),
        FormComponent(
            key="language_selector",
            title="Code Settings",
            submit_action="select_language",
            fields=[
                FormField(
                    name="language",
                    label="Language",
                    type="select",
                    options=[
                        {"label": "Python", "value": "python"},
                        {"label": "JavaScript", "value": "javascript"},
                        {"label": "TypeScript", "value": "typescript"}
                    ]
                )
            ]
        )
    ]
)
async def handle_upload(data: Dict[str, Any]) -> WorkflowStepResponse:
    """Handle initial code upload."""
    code_content = data.get("code_input", {}).get("content", "")
    language = data.get("language_selector", {}).get("language", "python")

    return WorkflowStepResponse(
        data={"original_code": code_content, "language": language},
        context_updates={"code": code_content, "language": language},
        next_step_id="analyze"
    )

@workflow_step(
    agent_config=code_assistant_v2_app,
    workflow_id="code_review",
    step_id="analyze",
    name="Code Analysis",
    description="Analyze code and provide initial feedback",
    action_type=ActionType.CUSTOM_UI,
    ui_components=[
        CodeEditorComponent(
            key="code_display",
            title="Code Analysis",
            language="python",
            readonly=True
        ),
        MarkdownComponent(
            key="analysis_result",
            title="Analysis Results"
        )
    ]
)
async def handle_analysis(data: Dict[str, Any]) -> WorkflowStepResponse:
    """Analyze code and provide feedback."""
    code = data["context"]["code"]
    analysis_md = f"""## Code Analysis Results
### Metrics
- Lines of Code: {len(code.splitlines())}
- Function Count: {code.count('def ')}
- Class Count: {code.count('class ')}

### Suggested Improvements
1. ✨ Consider adding type hints
2. 📝 Add docstrings for better documentation
3. 🔍 Review error handling practices

Would you like to apply automatic improvements?"""

    return WorkflowStepResponse(
        data={"analysis": analysis_md},
        ui_updates=[
            {"key": "code_display", "state": {"content": code}},
            {"key": "analysis_result", "state": {"content": analysis_md}}
        ],
        next_step_id="improve"
    )

@workflow_step(
    agent_config=code_assistant_v2_app,
    workflow_id="code_review",
    step_id="improve",
    name="Code Improvement",
    description="Apply improvements to the code",
    action_type=ActionType.CUSTOM_UI,
    ui_components=[
        CodeEditorComponent(
            key="improved_code",
            title="Improved Code",
            language="python",
            actions=["format", "add_types", "add_docs"]
        ),
        MarkdownComponent(
            key="improvement_notes",
            title="Improvement Notes"
        )
    ]
)
async def handle_improvement(data: Dict[str, Any]) -> WorkflowStepResponse:
    """Apply code improvements."""
    # Need to move and abstract the context retrieval logic
    code = data["context"]["context"]["code"]
    action = data.get("action")

    if action == "format":
        improved_code = black.format_str(code, mode=black.FileMode())
    else:
        improved_code = code

    return WorkflowStepResponse(
        data={"improved_code": improved_code},
        ui_updates=[
            {"key": "improved_code", "state": {"content": improved_code}},
            {"key": "improvement_notes", "state": {
                "content": "✅ Applied code formatting\n🔄 Ready for scoring"
            }}
        ],
        next_step_id="score"
    )

@workflow_step(
    agent_config=code_assistant_v2_app,
    workflow_id="code_review",
    step_id="review",
    name="Final Review",
    description="Review improvements and approve changes",
    action_type=ActionType.CUSTOM_UI,
    ui_components=[
        CodeEditorComponent(
            key="final_code",
            title="Final Code",
            language="python",
            readonly=True
        ),
        FormComponent(
            key="approval_form",
            title="Review Decision",
            submit_action="submit_review",
            fields=[
                FormField(
                    name="approved",
                    label="Approve Changes",
                    type="select",
                    options=[
                        {"label": "Approve", "value": "yes"},
                        {"label": "Request Changes", "value": "no"}
                    ]
                ),
                FormField(
                    name="comments",
                    label="Comments",
                    type="text"
                )
            ]
        )
    ]
)
async def handle_review(data: Dict[str, Any]) -> WorkflowStepResponse:
    """Handle final review decision."""
    approval = data.get("approval_form", {}).get("approved") == "yes"
    if approval:
        next_step = "complete"
        message = "✅ Changes approved and finalized"
    else:
        next_step = "improve"
        message = "🔄 Requested additional improvements"

    return WorkflowStepResponse(
        data={"approved": approval, "message": message},
        ui_updates=[
            {"key": "improvement_notes", "state": {"content": message}}
        ],
        next_step_id=next_step
    )

@workflow_step(
    agent_config=code_assistant_v2_app,
    workflow_id="code_review",
    step_id="complete",
    name="Review Complete",
    description="Final completion step of code review",
    action_type=ActionType.CUSTOM_UI,
    ui_components=[
        MarkdownComponent(
            key="completion_summary",
            title="Review Complete"
        )
    ]
)
async def handle_completion(data: Dict[str, Any]) -> WorkflowStepResponse:
    """Handle workflow completion."""
    return WorkflowStepResponse(
        data={"status": "completed"},
        ui_updates=[
            {"key": "completion_summary", "state": {
                "content": "## Code Review Complete\n\nThe code has been successfully reviewed and approved. All changes have been applied."
            }}
        ],
        next_step_id=None
    )

@workflow_step(
    agent_config=code_assistant_v2_app,
    workflow_id="code_review",
    step_id="score",
    name="Code Quality Scoring",
    description="Score code quality across multiple dimensions",
    action_type=ActionType.CUSTOM_UI,
    ui_components=[
        TableComponent(
            key="quality_metrics",
            title="Code Quality Metrics",
            columns=[
                TableColumn(field="metric", header="Metric"),
                TableColumn(field="score", header="Score"),
                TableColumn(field="description", header="Description")
            ],
            data=[]
        ),
        CodeEditorComponent(
            key="scored_code",
            title="Improved Code",
            language="python",
            readonly=True
        ),
        FormComponent(
            key="continue_form",
            title="Continue to Review",
            submit_action="continue_to_review",
            fields=[
                FormField(
                    name="proceed",
                    label="Proceed to Final Review",
                    type="select",
                    options=[
                        {"label": "Yes, continue", "value": "yes"},
                        {"label": "No, improve further", "value": "no"}
                    ]
                )
            ]
        )
    ]
)
async def handle_scoring(data: Dict[str, Any]) -> WorkflowStepResponse:
    """Score code quality across multiple dimensions."""
    code = data["context"]["context"]["code"]
    # Generate quality metrics
    metrics = [
        {
            "metric": "Readability",
            "score": "8/10",
            "description": "Code is generally readable but could use more descriptive names"
        },
        {
            "metric": "Documentation",
            "score": "6/10",
            "description": "Some docstrings present, but more detailed explanations needed"
        },
        {
            "metric": "Complexity",
            "score": "9/10",
            "description": "Low cyclomatic complexity, good flow structure"
        },
        {
            "metric": "Type Safety",
            "score": "5/10",
            "description": "Limited type annotations present"
        },
        {
            "metric": "Error Handling",
            "score": "7/10",
            "description": "Basic error handling present, but could be more robust"
        }
    ]

    next_step = "review"
    return WorkflowStepResponse(
        data={
            "metrics": metrics,
            "code": code
        },
        ui_updates=[
            {"key": "quality_metrics", "state": {"data": metrics}},
            {"key": "scored_code", "state": {"content": code}}
        ],
        next_step_id=next_step
    )