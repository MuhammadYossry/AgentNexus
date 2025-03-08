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
    ui_components: Optional[List[Union[UIComponent, Callable]]] = None,
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
        # Process components
        processed_components = []
        if ui_components:
            for component in ui_components:
                try:
                    # Handle both direct component instances and factory functions
                    if callable(component) and not isinstance(component, UIComponent):
                        try:
                            component_instance = component()
                            if isinstance(component_instance, UIComponent):
                                processed_components.append(component_instance)
                        except Exception as e:
                            logger.error(f"Error creating component from factory: {str(e)}")
                    elif isinstance(component, UIComponent):
                        processed_components.append(component)
                    else:
                        logger.warning(f"Invalid component: {type(component)}")
                except Exception as e:
                    logger.error(f"Error processing component: {str(e)}")
            # Register the processed components
            for component in processed_components:
                global_event_dispatcher.register_component(component)
                logger.debug(f"Registered component {component.component_key}")
                if hasattr(component, 'event_handlers'):
                    for event_type in component.event_handlers:
                        logger.debug(f"  - Event handler: {event_type}")
        # Apply the original agent_action decorator
        original_decorated_func = original_agent_action(
            agent_config=agent_config,
            action_type=action_type,
            name=name,
            description=description,
            ui_components=processed_components,
            **kwargs
        )(func)
        # Store UI components on the function for reference
        original_decorated_func.ui_components = processed_components
        # Get the expected input and output types from the function
        signature = inspect.signature(func)
        type_hints = get_type_hints(func)
        input_model_param = next(iter(signature.parameters.values()), None)
        input_model = input_model_param.annotation if input_model_param else None
        output_model = type_hints.get('return', None)

        @wraps(original_decorated_func)
        async def wrapper(*args, **kwargs):
            try:
                input_data = args[0] if args else list(kwargs.values())[0] if kwargs else None
                if not input_data:
                    return await original_decorated_func(*args, **kwargs)

                if hasattr(input_data, 'action') and input_data.action:
                    target_component_key = getattr(input_data, 'component_key', None)

                    # Find appropriate component if no key provided
                    if not target_component_key and processed_components:
                        for component in processed_components:
                            if (hasattr(component, 'supported_events') and
                                input_data.action in component.supported_events):
                                target_component_key = component.component_key
                                break
                            elif (hasattr(component, 'available_actions') and
                                  input_data.action in component.available_actions):
                                target_component_key = component.component_key
                                break

                    if target_component_key:
                        try:
                            event_data = input_data.dict() if hasattr(input_data, 'dict') else vars(input_data)
                            # Map action to event name if needed
                            event_name = input_data.action
                            if input_data.action == 'select_seat':
                                event_name = 'row_click'
                            elif input_data.action == 'search_seats':
                                event_name = 'submit'
                            # Try event dispatch first
                            try:
                                result = await global_event_dispatcher.dispatch_event(
                                    component_key=target_component_key,
                                    event_name=event_name,
                                    event_data=event_data
                                )
                            except EventDispatchError:
                                # Fall back to action dispatch
                                result = await global_event_dispatcher.dispatch_action(
                                    component_key=target_component_key,
                                    action_name=input_data.action,
                                    action_data=event_data
                                )

                            if result:
                                if isinstance(result, output_model):
                                    return result
                                if hasattr(output_model, 'parse_obj'):
                                    return output_model.parse_obj(result)
                                elif hasattr(output_model, 'model_validate'):
                                    return output_model.model_validate(result)
                                return result
                        except EventDispatchError as e:
                            logger.warning(f"Dispatch failed: {str(e)}")
                return await original_decorated_func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in enhanced agent action: {str(e)}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        wrapper.event_dispatcher = global_event_dispatcher
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