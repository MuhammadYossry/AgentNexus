
from typing import List, Dict, Any, Optional, Callable, Union
from loguru import logger
import re

from pydantic import BaseModel
from agents_manifest.base_types import (
    AgentConfig, Capability, UIComponentUpdate, WorkflowStepResponse,
    Workflow, WorkflowStep, WorkflowStepType
)
from agents_manifest.manifest_generator import configure_agent, ActionType
from agents_manifest.ui_components import (
    CodeEditorComponent, MarkdownComponent, TableComponent,
    FormComponent, TableColumn, FormField
)
from agents_manifest.workflow_manager import workflow_step
from agents.ui_components.code_agent_v2 import (
    code_input, language_selector, handle_analyze_continue_submit,
    code_display, analysis_result, improved_code, improvement_notes,
    handle_improve_continue_submit, quality_metrics, continue_form,
    final_code, approval_form, completion_summary, analyze_continue
)
from agents.models.code_agent_v2 import (
    extract_input_data, analyze_function_complexity, calculate_quality_metrics,
    generate_improved_code, generate_improvements_summary
)

# Define a more structured code agent config
CODE_REVIEW_CAPABILITIES = [
    Capability(
        skill_path=["Development", "Code Review"],
        metadata={
            "languages": ["python", "javascript", "typescript"],
            "features": ["formatting", "style analysis", "improvement suggestions"]
        }
    ),
    Capability(
        skill_path=["Development", "Code Quality"],
        metadata={
            "features": ["performance analysis", "error detection", "best practices"]
        }
    )
]

# Define code review workflow
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
# Create agent config with the workflow
code_agent_v2_app = AgentConfig(
    name="Code Assistant V2",
    version="2.0.0",
    description="Advanced code review and improvement agent with workflow support",
    base_path="/agents/code-assistant-v2",
    capabilities=CODE_REVIEW_CAPABILITIES,
    workflows=[CODE_REVIEW_WORKFLOW]
)

# Define workflow step handlers
@workflow_step(
    agent_config=code_agent_v2_app,
    workflow_id="code_review",
    step_id="upload",
    name="Code Upload",
    description="Initial code upload step",
    ui_components=[code_input, language_selector]
)
async def handle_upload_step(input_data) -> WorkflowStepResponse:
    """Handle initial code upload."""
    logger.debug(f"Handle upload step called with data type: {type(input_data)}")
    # Extract data safely
    extracted = extract_input_data(input_data)
    context = extracted['context']
    form_data = extracted['form_data']
    session_id = extracted['session_id']

    # Process form submissions and actions
    if form_data:
        action = form_data.get("action")
        component_key = form_data.get("component_key")
        logger.debug(f"Processing action {action} for component {component_key}")
        # Handle form submission to advance to next step
        if action == "submit" and component_key == "language_selector":
            # Get the code from the editor and language from the form
            values = form_data.get("values", {})
            language = values.get("language", "python")
            code_content = context.get("code", code_input.editor_content)
            # Store in context and move to next step
            return WorkflowStepResponse(
                data={"status": "setup_complete", "session_id": session_id},
                ui_updates=[],
                next_step_id="analyze",  # Advance to analysis step
                context_updates={
                    "language": language,
                    "original_code": code_content,  # Always set both code keys
                    "code": code_content
                }
            )
        # Let the component event handlers handle other actions
        elif action in ["format", "save"]:
            # Let the event dispatcher handle these events
            # Just return a minimal response
            return WorkflowStepResponse(
                data={"status": "event_handled", "session_id": session_id},
                ui_updates=[],
                context_updates={},
                next_step_id=None  # Stay on current step
            )
    # Initial step load
    code_content = context.get("code", code_input.editor_content)
    language = context.get("language", "python")
    # Return response with initial UI updates
    return WorkflowStepResponse(
        data={"status": "ready", "session_id": session_id},
        ui_updates=[
            UIComponentUpdate(
                key="code_input",
                state={"editor_content": code_content}
            ),
            UIComponentUpdate(
                key="language_selector",
                state={"values": {"language": language}}
            )
        ],
        context_updates={
            "code": code_content,
            "original_code": code_content,  # Always set both keys
            "language": language
        }
    )

@workflow_step(
    agent_config=code_agent_v2_app,
    workflow_id="code_review",
    step_id="analyze",
    name="Code Analysis",
    description="Analyze code and provide initial feedback",
    ui_components=[code_display, analysis_result, analyze_continue]
)
async def handle_analyze_step(input_data) -> WorkflowStepResponse:
    """Handle the analysis step of the workflow."""
    logger.debug(f"Handle analyze step called with data type: {type(input_data)}")
    # Extract data safely
    extracted = extract_input_data(input_data)
    context = extracted['context']
    form_data = extracted['form_data']
    session_id = extracted['session_id']
    # Check for form submissions
    if form_data and form_data.get("action") == "submit":
        component_key = form_data.get("component_key")
        # Make sure we're handling the right component
        if component_key == "analyze_continue":
            # Get the code from context - try both keys
            original_code = context.get("original_code") or context.get("code", "")
            # Move to the next step (improve)
            return WorkflowStepResponse(
                data={"status": "analysis_complete", "session_id": session_id},
                ui_updates=[],
                next_step_id="improve",
                context_updates={
                    # Preserve the current context
                    "original_code": original_code,
                    "code": original_code,
                    "language": context.get("language", "python"),
                    "analysis": context.get("analysis", ""),
                    "metrics": context.get("metrics", [])
                }
            )
    try:
        # Try to get code from context, checking all possible keys
        original_code = context.get("original_code") or context.get("code", "")
        language = context.get("language", "python")
        if not original_code:
            return WorkflowStepResponse(
                data={"status": "error", "message": "No code to analyze", "session_id": session_id},
                ui_updates=[
                    UIComponentUpdate(
                        key="analysis_result",
                        state={"markdown_content": "## Error\n\nNo code to analyze. Please go back to the upload step."}
                    )
                ]
            )
        # Analyze code and generate metrics
        functions = analyze_function_complexity(original_code)
        metrics = calculate_quality_metrics(original_code, language)
        # Create function list for the report
        function_list = "\n".join([
            f"* `{name}`: {details['complexity']} complexity, {details['lines']} lines" +
            (", has docstring" if details['has_docstring'] else ", missing docstring") +
            (", has type hints" if details['has_typehints'] else ", missing type hints")
            for name, details in functions.items()
        ])
        # Generate analysis report
        analysis_text = f"""## Code Analysis Results

### Functions Analyzed
{function_list}

### Key Findings
- {'✅' if len(functions) > 0 else '❌'} Found {len(functions)} functions
- {'✅' if all(f['has_docstring'] for f in functions.values()) else '❌'} Documentation: {sum(1 for f in functions.values() if f['has_docstring'])}/{len(functions)} functions have docstrings
- {'✅' if all(f['has_typehints'] for f in functions.values()) else '❌'} Type Hints: {sum(1 for f in functions.values() if f['has_typehints'])}/{len(functions)} functions have type hints
- {'✅' if all(f['complexity'] < 5 for f in functions.values()) else '❌'} Complexity: {sum(1 for f in functions.values() if f['complexity'] < 5)}/{len(functions)} functions have low complexity

### Improvement Opportunities
1. Add proper docstrings to all functions
2. Add type hints to function parameters and return values
3. Replace bare except blocks with specific exception handling
4. Break down complex functions into smaller, more focused ones

Click the 'Continue to Improvement Phase' button below to proceed.
"""
        # Store analysis in context and return
        return WorkflowStepResponse(
            data={"status": "analysis_complete", "functions_found": len(functions), "session_id": session_id},
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
            context_updates={
                "analysis": analysis_text,
                "metrics": metrics,
                "original_code": original_code,  # Make sure code is preserved
                "code": original_code
            }
        )
    except Exception as e:
        logger.error(f"Error analyzing code: {str(e)}")
        return WorkflowStepResponse(
            data={"status": "error", "message": str(e), "session_id": session_id},
            ui_updates=[
                UIComponentUpdate(
                    key="analysis_result",
                    state={"markdown_content": f"## Error\n\nAn error occurred during analysis: {str(e)}"}
                )
            ]
        )

improve_continue = FormComponent(
    component_key="improve_continue",
    title="Navigation",
    form_fields=[
        FormField(
            field_name="continue",
            label_text="Continue to Quality Scoring",
            field_type="select",
            field_options=[
                {"value": "yes", "label": "Continue"}
            ]
        )
    ],
    event_handlers={
        "submit": handle_improve_continue_submit
    }
)

@workflow_step(
    agent_config=code_agent_v2_app,
    workflow_id="code_review",
    step_id="improve",
    name="Code Improvement",
    description="Apply improvements to the code",
    ui_components=[improved_code, improvement_notes, improve_continue]  # Added improve_continue
)
async def handle_improve_step(input_data) -> WorkflowStepResponse:
    """Handle the improvement step of the workflow."""
    logger.debug(f"Handle improve step called with data type: {type(input_data)}")
    extracted = extract_input_data(input_data)
    context = extracted['context']
    form_data = extracted['form_data']
    session_id = extracted['session_id']

    # Check for form submission or actions
    if form_data:
        action = form_data.get("action")
        component_key = form_data.get("component_key")
        # Handle manual step advancement via the navigation component
        if action == "submit" and component_key == "improve_continue":
            # Get the current improved code - try both improved_code and current editor state
            improved_code_content = context.get("improved_code", "") or context.get("code", "")
            original_code = context.get("original_code", "")
            # Move to the next step (score)
            return WorkflowStepResponse(
                data={"status": "improvements_saved", "session_id": session_id},
                ui_updates=[],
                next_step_id="score",
                context_updates={
                    "improved_code": improved_code_content,
                    "original_code": original_code,
                    "code": improved_code_content,  # Set current code to improved version
                    "language": context.get("language", "python"),
                    "improvement_notes": context.get("improvement_notes", ""),
                    "analysis": context.get("analysis", "")
                }
            )
        # Let component event handlers handle format/add_types/add_docs
        elif action in ["format", "add_types", "add_docs", "save"]:
            # These events are handled by the global event dispatcher
            # Just return a minimal response to acknowledge
            return WorkflowStepResponse(
                data={"status": "event_handled", "session_id": session_id},
                ui_updates=[],
                context_updates={},
                next_step_id=None
            )
    # Initial step load - generate improved code if not already in context
    # Get the original code from context using different possible keys
    original_code = context.get("original_code") or context.get("code", "")
    # Generate improved version if not already in context
    if not context.get("improved_code"):
        try:
            improved_code_content = generate_improved_code(original_code)
            improvements_summary = generate_improvements_summary(original_code, improved_code_content)
            # Add navigation hint to the summary
            improvements_summary += "\n\n### Next Steps\n\nClick the 'Continue to Quality Scoring' button below when you're ready to proceed."
            # Store in context and update UI
            return WorkflowStepResponse(
                data={"status": "improvements_generated", "session_id": session_id},
                ui_updates=[
                    UIComponentUpdate(
                        key="improved_code",
                        state={"editor_content": improved_code_content}
                    ),
                    UIComponentUpdate(
                        key="improvement_notes",
                        state={"markdown_content": improvements_summary}
                    )
                ],
                context_updates={
                    "improved_code": improved_code_content,
                    "code": improved_code_content,  # Update current code too
                    "original_code": original_code,  # Preserve original
                    "improvement_notes": improvements_summary,
                    "language": context.get("language", "python")
                }
            )
        except Exception as e:
            logger.error(f"Error generating improvements: {str(e)}")
            return WorkflowStepResponse(
                data={"status": "error", "message": str(e), "session_id": session_id},
                ui_updates=[
                    UIComponentUpdate(
                        key="improvement_notes",
                        state={"markdown_content": f"## Error\n\nAn error occurred: {str(e)}"}
                    )
                ]
            )
    else:
        # Use existing improved code from context
        improved_code_content = context.get("improved_code", "")
        improvements_summary = context.get("improvement_notes", "")
        # Make sure we have the navigation hint
        if "Continue to Quality Scoring" not in improvements_summary:
            improvements_summary += "\n\n### Next Steps\n\nClick the 'Continue to Quality Scoring' button below when you're ready to proceed."
        return WorkflowStepResponse(
            data={"status": "ready", "session_id": session_id},
            ui_updates=[
                UIComponentUpdate(
                    key="improved_code",
                    state={"editor_content": improved_code_content}
                ),
                UIComponentUpdate(
                    key="improvement_notes",
                    state={"markdown_content": improvements_summary}
                )
            ],
            context_updates={
                "improved_code": improved_code_content,
                "code": improved_code_content,  # Set current code to improved version
                "improvement_notes": improvements_summary,
                "language": context.get("language", "python")
            }
        )

@workflow_step(
    agent_config=code_agent_v2_app,
    workflow_id="code_review",
    step_id="score",
    name="Code Quality Score",
    description="Score code quality across multiple dimensions",
    ui_components=[quality_metrics, improved_code, continue_form]
)
async def handle_score_step(input_data) -> WorkflowStepResponse:
    """Handle the scoring step of the workflow."""
    logger.debug(f"Handle score step called with data type: {type(input_data)}")
    # Extract data safely
    extracted = extract_input_data(input_data)
    context = extracted['context']
    form_data = extracted['form_data']
    session_id = extracted['session_id']
    logger.debug(f"Score step context keys: {list(context.keys())}")
    # Handle form submission
    if form_data:
        action = form_data.get("action")
        component_key = form_data.get("component_key")
        # Process continue form submission
        if action == "submit" and component_key == "continue_form":
            values = form_data.get("values", {})
            proceed = values.get("proceed", "yes")
            # Get the current improved code with fallbacks
            improved_code_content = (
                context.get("improved_code", "") or
                context.get(f"{component_key}_code", "") or
                context.get("improved_code", "")
            )
            # Get original code with fallbacks
            original_code = context.get("original_code", "") or context.get("code", "")
            # Log code content length for debugging
            logger.debug(f"Score step: proceeding to {'review' if proceed == 'yes' else 'improve'}")
            logger.debug(f"Score step: improved_code length: {len(improved_code_content)}")
            logger.debug(f"Score step: original_code length: {len(original_code)}")
            # Store decision and move to appropriate step
            if proceed == "yes":
                return WorkflowStepResponse(
                    data={"status": "proceeding_to_review", "session_id": session_id},
                    ui_updates=[],
                    next_step_id="review",
                    context_updates={
                        "proceed": proceed,
                        "improved_code": improved_code_content,
                        "original_code": original_code,
                        "code": improved_code_content,
                        "final_code": improved_code_content,  # Also set final_code
                        "metrics_data": context.get("metrics_data", []),
                        "language": context.get("language", "python")
                    }
                )
            else:
                return WorkflowStepResponse(
                    data={"status": "back_to_improvement", "session_id": session_id},
                    ui_updates=[],
                    next_step_id="improve",
                    context_updates={
                        "proceed": proceed,
                        "improved_code": improved_code_content,
                        "original_code": original_code,
                        "code": improved_code_content,
                        "metrics_data": context.get("metrics_data", []),
                        "language": context.get("language", "python")
                    }
                )
        # Handle code format action
        elif action == "format" and component_key == "improved_code":
            # Let the event handler handle this
            return WorkflowStepResponse(
                data={"status": "event_handled", "session_id": session_id},
                ui_updates=[],
                context_updates={},
                next_step_id=None
            )
    # Initial step load - calculate metrics
    # Try to get code from different possible keys
    improved_code_content = (
        context.get("improved_code", "") or
        context.get(f"{component_key}_code", "") or
        context.get("improved_code", "")
    )
    original_code = context.get("original_code", "") or context.get("code", "")
    # Log code content for debugging
    logger.debug(f"Score step initial load - improved_code length: {len(improved_code_content)}")
    logger.debug(f"Score step initial load - original_code length: {len(original_code)}")
    # Check if either is empty and try to fallback further
    if not improved_code_content and original_code:
        logger.warning("No improved code found, using original code as fallback")
        improved_code_content = original_code

    if improved_code_content:
        try:
            # Generate quality metrics
            metrics_data = calculate_quality_metrics(improved_code_content)

            return WorkflowStepResponse(
                data={"status": "metrics_calculated", "session_id": session_id},
                ui_updates=[
                    UIComponentUpdate(
                        key="quality_metrics",
                        state={"table_data": metrics_data}
                    ),
                    UIComponentUpdate(
                        key="improved_code",
                        state={"editor_content": improved_code_content}
                    )
                ],
                context_updates={
                    "metrics_data": metrics_data,
                    "improved_code": improved_code_content,
                    "original_code": original_code,
                    "code": improved_code_content,
                    "language": context.get("language", "python")
                }
            )
        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            return WorkflowStepResponse(
                data={"status": "error", "message": str(e), "session_id": session_id},
                ui_updates=[
                    UIComponentUpdate(
                        key="improved_code",
                        state={"editor_content": improved_code_content}
                    )
                ],
                context_updates={
                    "improved_code": improved_code_content,
                    "original_code": original_code,
                    "code": improved_code_content
                }
            )
    else:
        # If no code was found at all, return an error
        return WorkflowStepResponse(
            data={"status": "error", "message": "No improved code found", "session_id": session_id},
            ui_updates=[
                UIComponentUpdate(
                    key="improved_code",
                    state={"editor_content": "# No code found to display. Please go back to the improve step."}
                )
            ],
            context_updates={}
        )

@workflow_step(
    agent_config=code_agent_v2_app,
    workflow_id="code_review",
    step_id="review",
    name="Final Review",
    description="Review improvements and approve changes",
    ui_components=[final_code, approval_form]
)
async def handle_review_step(input_data) -> WorkflowStepResponse:
    """Handle the final review step of the workflow."""
    logger.debug(f"Handle review step called with data type: {type(input_data)}")
    # Extract data safely
    extracted = extract_input_data(input_data)
    context = extracted['context']
    form_data = extracted['form_data']
    session_id = extracted['session_id']
    # Handle form submission
    if form_data:
        action = form_data.get("action")
        component_key = form_data.get("component_key")
        if action == "submit" and component_key == "approval_form":
            values = form_data.get("values", {})
            approved = values.get("approved", "yes")
            comments = values.get("comments", "")
            # Get the code from context with fallbacks
            improved_code = context.get("improved_code", "") or context.get("code", "")
            original_code = context.get("original_code", "")
            # Store approval decision and move to complete step
            return WorkflowStepResponse(
                data={"status": "review_complete", "approved": approved == "yes", "session_id": session_id},
                ui_updates=[],
                next_step_id="complete",
                context_updates={
                    "approved": approved == "yes",
                    "comments": comments,
                    "improved_code": improved_code,
                    "original_code": original_code,
                    "code": improved_code,
                    "final_code": improved_code,
                    "language": context.get("language", "python"),
                    "metrics_data": context.get("metrics_data", [])
                }
            )
    # Initial step load - show final code for review
    # Get code from context with multiple fallbacks
    improved_code = context.get("improved_code", "") or context.get("code", "")
    original_code = context.get("original_code", "")
    # Log for debugging
    logger.debug(f"Review step - improved code length: {len(improved_code)}")
    logger.debug(f"Review step - context keys: {list(context.keys())}")
    if not improved_code:
        logger.error("No improved code found in context for review step")
        return WorkflowStepResponse(
            data={"status": "error", "message": "No improved code to review", "session_id": session_id},
            ui_updates=[
                UIComponentUpdate(
                    key="final_code",
                    state={"editor_content": "# Error: No improved code found to review"}
                )
            ]
        )

    return WorkflowStepResponse(
        data={"status": "ready", "session_id": session_id},
        ui_updates=[
            UIComponentUpdate(
                key="final_code",
                state={"editor_content": improved_code}
            )
        ],
        context_updates={
            "improved_code": improved_code,
            "original_code": original_code,
            "code": improved_code,
            "final_code": improved_code,
            "language": context.get("language", "python")
        }
    )

@workflow_step(
    agent_config=code_agent_v2_app,
    workflow_id="code_review",
    step_id="complete",
    name="Review Complete",
    description="Final completion step of code review",
    ui_components=[completion_summary, final_code]
)
async def handle_complete_step(input_data) -> WorkflowStepResponse:
    """Handle the completion step of the workflow."""
    logger.debug(f"Handle complete step called with data type: {type(input_data)}")
    # Extract data safely
    extracted = extract_input_data(input_data)
    context = extracted['context']
    session_id = extracted['session_id']
    # Log context keys for debugging
    logger.debug(f"Complete step - context keys: {list(context.keys())}")
    # Get all necessary data from context with fallbacks
    approved = context.get("approved", False)
    comments = context.get("comments", "")
    improved_code = (
        context.get("improved_code", "") or
        context.get("final_code", "") or
        context.get("code", "")
    )
    original_code = context.get("original_code", "")
    # Log code lengths for debugging
    logger.debug(f"Complete step - improved code length: {len(improved_code)}")
    logger.debug(f"Complete step - original code length: {len(original_code)}")
    # Ensure we have code to work with
    if not improved_code and original_code:
        logger.warning("No improved code found, falling back to original code")
        improved_code = original_code
    elif not original_code and improved_code:
        logger.warning("No original code found, using improved code for both")
        original_code = improved_code
    elif not improved_code and not original_code:
        logger.error("No code found in context")
        improved_code = "# Error: No code found in context"
        original_code = "# Error: No code found in context"
    # Create metrics comparison
    try:
        original_metrics = calculate_quality_metrics(original_code)
        improved_metrics = calculate_quality_metrics(improved_code)
        original_overall = next((m for m in original_metrics if m["metric"] == "Overall Quality"), {}).get("score", "0/100")
        improved_overall = next((m for m in improved_metrics if m["metric"] == "Overall Quality"), {}).get("score", "0/100")
    except Exception as e:
        logger.error(f"Error calculating metrics: {str(e)}")
        original_overall = "N/A"
        improved_overall = "N/A"
    # Generate summary text
    status_text = "✅ Changes Approved" if approved else "❌ Changes Rejected"
    summary_text = f"""# Code Review Complete
## {status_text}

### Quality Improvement
- Original code quality: {original_overall}
- Improved code quality: {improved_overall}

### Review Comments
{comments if comments else "No comments provided."}

### Next Steps
1. Implement the approved changes in your codebase
2. Consider additional improvements based on the quality metrics
3. Apply similar patterns to other parts of your code

Thank you for using the Code Assistant!
"""
    # Return final response
    return WorkflowStepResponse(
        data={"status": "workflow_complete", "approved": approved, "session_id": session_id},
        ui_updates=[
            UIComponentUpdate(
                key="completion_summary",
                state={"markdown_content": summary_text}
            ),
            UIComponentUpdate(
                key="final_code",
                state={"editor_content": improved_code}
            )
        ],
        context_updates={
            "summary": summary_text,
            "improved_code": improved_code,
            "original_code": original_code,
            "final_code": improved_code,
            "code": improved_code
        }
    )
