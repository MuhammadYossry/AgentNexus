"""
workflow step handlers with consistent context management.

This module provides a set of handlers that properly return WorkflowStepResponse objects
with reliable context management to ensure code and data are properly preserved between steps.
"""
from typing import Dict, Any, List, Optional
import black
import re
from fastapi import HTTPException
from loguru import logger

from agentnexus.base_types import WorkflowStepResponse, UIComponentUpdate
from agentnexus.ui_components import UIComponent

# Define standard context keys for consistent reference
CONTEXT_KEYS = {
    "CURRENT_CODE": "code",                # Current active code
    "ORIGINAL_CODE": "original_code",      # Original uploaded code
    "IMPROVED_CODE": "improved_code",      # Improved/enhanced code
    "FINAL_CODE": "final_code",            # Final approved code
    "LANGUAGE": "language",                # Programming language
    "ANALYSIS": "analysis",                # Analysis results
    "METRICS_DATA": "metrics_data"         # Code quality metrics
}

def get_current_code(context: Dict[str, Any], component_key: str = None) -> str:
    """Helper function to find the most up-to-date code version in context."""
    # Try component-specific code first
    if component_key and f"{component_key}_code" in context:
        return context[f"{component_key}_code"]
    # Try standard keys in order of preference
    for key in ["code", "improved_code", "original_code"]:
        if key in context and context[key]:
            return context[key]
    return ""

async def handle_code_format(
    action: str,
    data: Dict[str, Any],
    component_key: str,
    **kwargs
) -> WorkflowStepResponse:
    """Format code using Black and update both component-specific and standard keys."""
    logger.debug(f"Handling format event for code editor component {component_key}")
    # Extract code and language from data
    code = data.get("code") or data.get("editor_content", "")
    language = data.get("language", "python")
    context = kwargs.get("context", {})

    try:
        if language.lower() == "python":
            formatted_code = black.format_str(code, mode=black.FileMode())
        else:
            formatted_code = code
        logger.debug(f"Formatting successful")
        # Create context updates with both component-specific and standard keys
        context_updates = {
            f"{component_key}_code": formatted_code,  # Component-specific key
            f"{component_key}_formatted": formatted_code  # Formatted version
        }
        # Update standard keys based on component
        if component_key == "code_input":
            context_updates[CONTEXT_KEYS["CURRENT_CODE"]] = formatted_code
            context_updates[CONTEXT_KEYS["ORIGINAL_CODE"]] = formatted_code
        elif component_key == "improved_code":
            context_updates[CONTEXT_KEYS["CURRENT_CODE"]] = formatted_code
            context_updates[CONTEXT_KEYS["IMPROVED_CODE"]] = formatted_code
        return WorkflowStepResponse(
            data={
                "message": "Code formatted successfully",
                "formatted": True,
                "language": language
            },
            ui_updates=[
                UIComponentUpdate(
                    key=component_key,
                    state={"editor_content": formatted_code}
                )
            ],
            next_step_id=None,
            context_updates=context_updates
        )
    except Exception as e:
        logger.error(f"Error formatting code: {str(e)}")
        return WorkflowStepResponse(
            data={
                "message": f"Error formatting code: {str(e)}",
                "formatted": False,
                "language": language
            },
            ui_updates=[],
            next_step_id=None,
            context_updates={}
        )

async def handle_code_save(
    action: str,
    data: Dict[str, Any],
    component_key: str,
    **kwargs
) -> WorkflowStepResponse:
    """Save code to the context with consistent key naming."""
    logger.debug(f"Handling save event for code editor component {component_key}")
    # Extract code and language from data
    code = data.get("code") or data.get("editor_content", "")
    language = data.get("language", "python")
    context = kwargs.get("context", {})
    # Create context updates with both component-specific and standard keys
    context_updates = {
        f"{component_key}_code": code,  # Component-specific key
    }
    # Update standard keys based on component
    if component_key == "code_input":
        context_updates[CONTEXT_KEYS["CURRENT_CODE"]] = code
        context_updates[CONTEXT_KEYS["ORIGINAL_CODE"]] = code
    elif component_key == "improved_code":
        context_updates[CONTEXT_KEYS["CURRENT_CODE"]] = code
        context_updates[CONTEXT_KEYS["IMPROVED_CODE"]] = code
    elif component_key == "final_code":
        context_updates[CONTEXT_KEYS["CURRENT_CODE"]] = code
        context_updates[CONTEXT_KEYS["FINAL_CODE"]] = code
    else:
        # For any other component, just update current code
        context_updates[CONTEXT_KEYS["CURRENT_CODE"]] = code
    logger.debug(f"Saving code with updates: {context_updates.keys()}")
    return WorkflowStepResponse(
        data={
            "message": "Code saved successfully",
            "saved": True,
            "language": language
        },
        ui_updates=[],
        next_step_id=None,
        context_updates=context_updates
    )

async def handle_language_form_submit(
    action: str,
    data: Dict[str, Any],
    component_key: str,
    **kwargs
) -> WorkflowStepResponse:
    """Handle language selector form submission with proper context passing."""
    logger.debug(f"Handling language form submit for {component_key}")
    # Extract form values
    values = data.get("values", {})
    language = values.get("language", "python")
    context = kwargs.get("context", {})
    logger.debug(f"Language form values: {values}")

    # Find the most up-to-date code version
    current_code = get_current_code(context, "code_input")
    # Create comprehensive context updates for transition
    context_updates = {
        CONTEXT_KEYS["LANGUAGE"]: language,
        "form_values": values
    }
    # Only add code if we found it
    if current_code:
        context_updates[CONTEXT_KEYS["CURRENT_CODE"]] = current_code
        context_updates[CONTEXT_KEYS["ORIGINAL_CODE"]] = current_code
    logger.debug(f"Language form proceeding to analyze with context: {context_updates.keys()}")
    return WorkflowStepResponse(
        data={
            "message": f"Language {language} selected",
            "action": action,
            "component_key": component_key,
            "values": values
        },
        ui_updates=[
            UIComponentUpdate(
                key=component_key,
                state={"values": values, "submitted": True}
            )
        ],
        next_step_id="analyze",  # Move to analysis step after language selection
        context_updates=context_updates
    )

async def handle_analyze_continue_submit(input_data: Dict[str, Any]) -> WorkflowStepResponse:
    """Handle continue button click after analysis with consistent context handling."""
    logger.debug("Handling analyze continue submit")
    # Extract context from input_data
    context = input_data.get("context", {})
    # Log context keys to help with debugging
    logger.debug(f"Context keys available: {list(context.keys())}")
    # Get the code from context with fallbacks
    original_code = context.get("original_code", "") or context.get("code", "")
    analysis = context.get("analysis", "")
    metrics = context.get("metrics", [])
    # Log what we found for debugging
    logger.debug(f"Found original code (length: {len(original_code)})")
    return WorkflowStepResponse(
        data={
            "message": "Analysis complete, moving to improvement phase",
            "action": "continue",
            "component_key": "analyze_continue"
        },
        ui_updates=[],
        next_step_id="improve",
        context_updates={
            "original_code": original_code,
            "code": original_code,
            "analysis": analysis,
            "metrics": metrics,
            "language": context.get("language", "python")
        }
    )

async def handle_continue_form_submit(
    action: str,
    data: Dict[str, Any],
    component_key: str,
    **kwargs
) -> WorkflowStepResponse:
    """Handle continue form submission with consistent context handling."""
    logger.debug(f"Handling continue form submit for {component_key}")
    # Extract form values
    values = data.get("values", {})
    proceed = values.get("proceed", "yes")
    context = kwargs.get("context", {})

    # Log context keys for debugging
    logger.debug(f"Continue form - context keys: {list(context.keys())}")
    # Determine best code version to carry forward with multiple fallbacks
    improved_code = (
        context.get("improved_code", "") or
        context.get("code", "") or
        context.get("improved_code_code", "")
    )
    original_code = context.get("original_code", "") or context.get("code", "")
    # Log code lengths for debugging
    logger.debug(f"Continue form - improved code length: {len(improved_code)}")
    logger.debug(f"Continue form - original code length: {len(original_code)}")
    return WorkflowStepResponse(
        data={
            "message": "Continue form submitted",
            "action": action,
            "component_key": component_key,
            "proceed": proceed
        },
        ui_updates=[
            UIComponentUpdate(
                key=component_key,
                state={"values": values, "submitted": True}
            )
        ],
        next_step_id="review" if proceed == "yes" else "improve"
    )

async def handle_improve_continue_submit(input_data: Dict[str, Any]) -> WorkflowStepResponse:
    """Handle continue button click after improvements with consistent context handling."""
    logger.debug("Handling improve continue submit")
    # Extract context from input_data - the parameter structure is key here
    context = input_data.get("context", {})
    # Log context keys to help with debugging
    logger.debug(f"Context keys available: {list(context.keys())}")
    # Get the current improved code with multiple fallbacks
    improved_code_content = (
        context.get("improved_code", "") or
        context.get("code", "") or
        context.get("improved_code_code", "")  # Check component-specific key too
    )

    # Also get original code with fallbacks
    original_code = context.get("original_code", "") or context.get("code", "")
    # Log what we found for debugging
    logger.debug(f"Found improved code (length: {len(improved_code_content)})")
    logger.debug(f"Found original code (length: {len(original_code)})")
    # Create comprehensive context updates
    context_updates = {
        "improved_code": improved_code_content,
        "original_code": original_code,
        "code": improved_code_content,  # Set current code to improved
        "language": context.get("language", "python"),
        "improvement_notes": context.get("improvement_notes", ""),
        "analysis": context.get("analysis", "")
    }
    return WorkflowStepResponse(
        data={
            "message": "Moving to code scoring",
            "action": "continue",
            "component_key": "improve_continue"
        },
        ui_updates=[],
        next_step_id="score",  # Move to scoring step
        context_updates=context_updates
    )

async def handle_approval_form_submit(
    action: str,
    data: Dict[str, Any],
    component_key: str,
    **kwargs
) -> WorkflowStepResponse:
    """Handle approval form submission with consistent context handling."""
    logger.debug(f"Handling approval form submit for {component_key}")
    # Extract form values
    values = data.get("values", {})
    approved = values.get("approved", "yes")
    comments = values.get("comments", "")
    context = kwargs.get("context", {})

    # Determine best code version to carry forward
    improved_code = context.get(CONTEXT_KEYS["IMPROVED_CODE"], "")
    current_code = context.get(CONTEXT_KEYS["CURRENT_CODE"], improved_code)
    logger.debug(f"Approval form proceeding to {'complete' if approved == 'yes' else 'improve'}")
    return WorkflowStepResponse(
        data={
            "message": "Approval form submitted",
            "action": action,
            "component_key": component_key,
            "approved": approved == "yes",
            "comments": comments
        },
        ui_updates=[
            UIComponentUpdate(
                key=component_key,
                state={"values": values, "submitted": True}
            )
        ],
        next_step_id="complete" if approved == "yes" else "improve",
        context_updates={
            "approved": approved == "yes",
            "comments": comments,
            "form_values": values,
            # Preserve code values
            CONTEXT_KEYS["CURRENT_CODE"]: current_code,
            CONTEXT_KEYS["IMPROVED_CODE"]: improved_code,
            CONTEXT_KEYS["FINAL_CODE"]: current_code if approved == "yes" else ""
        }
    )

async def handle_add_types(
    action: str,
    data: Dict[str, Any],
    component_key: str,
    **kwargs
) -> WorkflowStepResponse:
    """Handle add types event for code editor with consistent context updates."""
    logger.debug(f"Handling add types for {component_key}")
    # Extract code and context
    code = data.get("code") or data.get("editor_content", "")
    context = kwargs.get("context", {})
    # Simplified type addition for demonstration
    typed_code = code.replace("def fibonacci(n):", "def fibonacci(n: int) -> list:")
    typed_code = typed_code.replace("def calculate_statistics(numbers):",
                                 "def calculate_statistics(numbers: list) -> dict:")
    typed_code = typed_code.replace("def process_data(data_list):",
                                 "def process_data(data_list: list) -> list:")
    logger.debug(f"Added type annotations to code")
    # Create comprehensive context updates
    context_updates = {
        f"{component_key}_code": typed_code,
        CONTEXT_KEYS["IMPROVED_CODE"]: typed_code,
        CONTEXT_KEYS["CURRENT_CODE"]: typed_code,
        "has_type_annotations": True
    }
    return WorkflowStepResponse(
        data={
            "message": "Type annotations added",
            "action": action,
            "component_key": component_key,
            "status": "types_added"
        },
        ui_updates=[
            UIComponentUpdate(
                key=component_key,
                state={"editor_content": typed_code}
            )
        ],
        next_step_id=None,  # Adding types doesn't change workflow step
        context_updates=context_updates
    )

async def handle_add_docs(
    action: str,
    data: Dict[str, Any],
    component_key: str,
    **kwargs
) -> WorkflowStepResponse:
    """Handle add docs event for code editor with consistent context updates."""
    logger.debug(f"Handling add docs for {component_key}")
    # Extract code and context
    code = data.get("code") or data.get("editor_content", "")
    context = kwargs.get("context", {})
    # Generate an improved version with docstrings
    func_pattern = r'def\s+(\w+)\s*\('
    functions = re.findall(func_pattern, code)
    documented_code = code
    for func in functions:
        if f'def {func}(' in documented_code and '"""' not in documented_code.split(f'def {func}(')[1].split('\n')[0:3]:
            indentation = re.search(rf'([ \t]*)def\s+{func}\s*\(', documented_code).group(1)
            docstring = f'\n{indentation}    """\n{indentation}    {func} function.\n{indentation}    \n{indentation}    Returns:\n{indentation}        Result of the operation.\n{indentation}    """\n'
            documented_code = re.sub(rf'def\s+{func}\s*\([^)]*\):\s*\n',
                                   lambda m: m.group(0) + docstring,
                                   documented_code)
    logger.debug(f"Added docstrings to code")

    # Create comprehensive context updates
    context_updates = {
        f"{component_key}_code": documented_code,
        CONTEXT_KEYS["IMPROVED_CODE"]: documented_code,
        CONTEXT_KEYS["CURRENT_CODE"]: documented_code,
        "has_documentation": True
    }
    return WorkflowStepResponse(
        data={
            "message": "Documentation added",
            "action": action,
            "component_key": component_key,
            "status": "docs_added"
        },
        ui_updates=[
            UIComponentUpdate(
                key=component_key,
                state={"editor_content": documented_code}
            )
        ],
        next_step_id=None,  # Adding docs doesn't change workflow step
        context_updates=context_updates
    )