"""
Enhanced agent action decorator with integrated UI component event handling.
"""
from typing import Dict, Any, List, Callable, Optional, Type, Union, get_type_hints
import inspect
from functools import wraps
import logging
from fastapi import HTTPException, Request
from pydantic import BaseModel

from agents_manifest.base_types import (
    AgentConfig, ActionType, UIResponse, UIComponentUpdate
)
from agents_manifest.manifest_generator import agent_action as original_agent_action
from agents_manifest.action_manager import get_action_registry
from agents_manifest.ui_components import UIComponent
from agents_manifest.event_dispatcher import global_event_dispatcher, EventDispatchError

logger = logging.getLogger(__name__)


def enhanced_agent_action(
    agent_config: AgentConfig,
    action_type: ActionType,
    name: str,
    description: str,
    ui_components: Optional[List[UIComponent]] = None,
    **kwargs
):
    """
    Enhanced agent_action decorator with integrated component event handling.
    
    This decorator extends the original agent_action decorator with
    automatic event handler registration and dispatching for UI components.
    
    Args:
        agent_config: The agent configuration
        action_type: The type of action (TALK, GENERATE, QUESTION, CUSTOM_UI)
        name: Human-readable name of the action
        description: Detailed description of the action
        ui_components: List of UI components for this action
        **kwargs: Additional arguments for the original agent_action decorator
        
    Returns:
        Decorated function with enhanced event handling capabilities
    """
    def decorator(func):
        # First, register all components with the global dispatcher
        if ui_components:
            global_event_dispatcher.register_components(ui_components)
            # Log the registered components and handlers
            for component in ui_components:
                logger.debug(
                    f"Registered component {component.component_key} with "
                    f"{len(component.event_handlers)} event handlers"
                )
                # Log action handlers for CodeEditorComponent
                if hasattr(component, 'action_handler_registry') and component.action_handler_registry:
                    handler_count = len(component.action_handler_registry.handler_functions)
                    logger.debug(
                        f"Component {component.component_key} has {handler_count} action handlers"
                    )
        # Apply the original agent_action decorator
        original_decorated_func = original_agent_action(
            agent_config=agent_config,
            action_type=action_type,
            name=name,
            description=description,
            ui_components=ui_components,
            **kwargs
        )(func)
        # Store UI components on the function for reference
        original_decorated_func.ui_components = ui_components
        # Get the expected input and output types from the function
        signature = inspect.signature(func)
        type_hints = get_type_hints(func)
        # Get input model from the first parameter type
        input_model_param = next(iter(signature.parameters.values()), None)
        input_model = input_model_param.annotation if input_model_param else None
        # Get output model from return type
        output_model = type_hints.get('return', None)

        # Wrap the decorated function to add event handling
        @wraps(original_decorated_func)
        async def wrapper(*args, **kwargs):
            try:
                # Get the input data from args or kwargs
                input_data = args[0] if args else list(kwargs.values())[0] if kwargs else None

                # If no input data, just call the original function
                if not input_data:
                    return await original_decorated_func(*args, **kwargs)

                # Check for actions to dispatch
                if hasattr(input_data, 'action') and input_data.action:
                    # Find the target component based on input data
                    target_component_key = getattr(input_data, 'component_key', None)

                    # If no specific component key provided, use the first component that matches the action
                    if not target_component_key and ui_components:
                        for component in ui_components:
                            if (hasattr(component, 'available_actions') and 
                                input_data.action in component.available_actions):
                                target_component_key = component.component_key
                                break

                    # If still no target, use the first code editor component
                    if not target_component_key and ui_components:
                        for component in ui_components:
                            if component.component_type == 'code_editor':
                                target_component_key = component.component_key
                                break

                    # If we found a target component, dispatch the action
                    if target_component_key:
                        try:
                            # Convert input_data to dict for dispatching
                            if hasattr(input_data, 'dict'):
                                action_data = input_data.dict()
                            else:
                                action_data = vars(input_data)

                            # Dispatch to the appropriate handler
                            result = await global_event_dispatcher.dispatch_action(
                                component_key=target_component_key,
                                action_name=input_data.action,
                                action_data=action_data
                            )

                            if result:
                                # If the result is already the expected output type, return it
                                if isinstance(result, output_model):
                                    return result
                                # Convert to the expected output type if possible
                                if hasattr(output_model, 'parse_obj'):
                                    return output_model.parse_obj(result)
                                elif hasattr(output_model, 'model_validate'):
                                    return output_model.model_validate(result)
                                # Fall back to just returning the result
                                return result
                        except EventDispatchError as e:
                            # Log the error but continue to allow the original function to handle it
                            logger.warning(f"Event dispatch failed: {str(e)}")
                # If we get here, either there was no action or dispatch failed
                # Fall back to the original function
                return await original_decorated_func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in enhanced agent action: {str(e)}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        # Add a reference to the global dispatcher
        wrapper.event_dispatcher = global_event_dispatcher
        # Return the enhanced wrapper
        return wrapper
    return decorator


# For backward compatibility, you can redefine the original agent_action
import sys
from agents_manifest import manifest_generator

# Replace the original agent_action with the enhanced version
manifest_generator.agent_action = enhanced_agent_action
sys.modules['agents_manifest.manifest_generator'].agent_action = enhanced_agent_action

# Provide the original for cases where it's needed
original_action = original_agent_action