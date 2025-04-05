# action_manager.py
from typing import Dict, Callable, Optional, List, Any, Type, get_type_hints
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Response
import inspect
from functools import wraps
from loguru import logger
from pathlib import Path
from jinja2 import Template
from agentnexus.base_types import ActionType, AgentConfig, slugify, UIResponse
from agentnexus.ui_components import UIComponent
from agentnexus.event_dispatcher import global_event_dispatcher

class ActionMetadata(BaseModel):
    """Metadata container for capturing comprehensive information about an agent action."""
    action_type: ActionType
    name: str
    description: str
    response_template_md: Optional[str] = None
    workflow_id: Optional[str] = None
    step_id: Optional[str] = None
    allow_dynamic_ui: bool = False
    ui_components: List[UIComponent] = Field(default_factory=list)

class ActionEndpointInfo(BaseModel):
    """Aggregates all necessary details for registering and invoking an agent action."""
    metadata: ActionMetadata
    input_model: Type[BaseModel]
    output_model: Type[BaseModel]
    handler: Callable
    schema_definitions: Optional[Dict[str, Type[BaseModel]]] = None
    examples: Optional[Dict[str, List[Dict[str, Any]]]] = None
    route_path: Optional[str] = None

class ActionRegistry:
    """Registry for managing and discovering agent actions across the system."""
    def __init__(self):
        """Initialize an empty action registry."""
        self.actions: Dict[str, ActionEndpointInfo] = {}

    def register_action(self, action_slug: str, endpoint_info: ActionEndpointInfo):
        """Register a new action in the registry.

        Args:
            action_slug (str): Unique identifier for the action
            endpoint_info (ActionEndpointInfo): Comprehensive action details
        """
        logger.debug(f"Registering action: {action_slug}")
        self.actions[action_slug] = endpoint_info

    def get_action(self, action_slug: str) -> Optional[ActionEndpointInfo]:
        """Retrieve an action's endpoint information.

        Args:
            action_slug (str): Unique identifier for the action

        Returns:
            Optional[ActionEndpointInfo]: Action details if found
        """
        return self.actions.get(action_slug)

agent_registries: Dict[str, ActionRegistry] = {}

def get_action_registry(agent_name: str) -> ActionRegistry:
    """Retrieve or create an action registry for a specific agent.

    Args:
        agent_name (str): Name of the agent

    Returns:
        ActionRegistry: Registry for the specified agent
    """
    agent_slug = slugify(agent_name)
    if agent_slug not in agent_registries:
        agent_registries[agent_slug] = ActionRegistry()
    return agent_registries[agent_slug]

def agent_action(
    agent_config: AgentConfig,
    action_type: ActionType,
    name: str,
    description: str,
    response_template_md: Optional[str] = None,
    schema_definitions: Optional[Dict[str, Type[BaseModel]]] = None,
    examples: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    workflow_id: Optional[str] = None,
    step_id: Optional[str] = None,
    ui_components: Optional[List[UIComponent]] = None,
    allow_dynamic_ui: bool = False
) -> Callable:
    """Decorator for registering agent actions with comprehensive metadata.

    Args:
        agent_config (AgentConfig): Configuration of the agent
        action_type (ActionType): Type of action being defined
        name (str): Human-readable name of the action
        description (str): Detailed description of the action

    Returns:
        Callable: Decorated action handler
    """
    def decorator(func: Callable) -> Callable:
        # Process template path if provided
        logger.debug(f"Decorating function: {func.__name__}")
        template_path = None
        if response_template_md is not None:
            template_path = Path(Path(__file__).parent, "templates", response_template_md)
            logger.debug(f"Template path: {template_path}")

        # Process UI components - handle both direct components and factories
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

            # Register the processed components with the global dispatcher
            for component in processed_components:
                global_event_dispatcher.register_component(component)
                logger.debug(f"Registered component {component.component_key}")
                # Register component event handlers
                if hasattr(component, 'event_handlers'):
                    for event_type, handler in component.event_handlers.items():
                        logger.debug(f"Registered event handler for {component.component_key}.{event_type}")

        # Extract function signature information
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)
        # Get input model
        input_model = next(
            (param.annotation for param in sig.parameters.values()
             if hasattr(param.annotation, 'model_json_schema')),
            None
        )
        # Get output model
        output_model = type_hints.get('return')
        if hasattr(output_model, '__origin__'):
            output_model = output_model.__args__[0]
        # Create action slug
        action_slug = slugify(name)

        # Create the wrapper function that handles events and dispatching
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Get input data
                input_data = args[0] if args else next(iter(kwargs.values()), None)
                logger.debug(f"Input data received: {type(input_data)}")

                # Check for component event handling
                if input_data and hasattr(input_data, 'action') and input_data.action:
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
                    # Try to dispatch the event if we have a component key
                    if target_component_key:
                        try:
                            event_data = input_data.dict() if hasattr(input_data, 'dict') else vars(input_data)
                            # Map action to event name if needed
                            event_name = input_data.action
                            if input_data.action == 'select_seat':
                                event_name = 'row_click'
                            elif input_data.action == 'search_seats':
                                event_name = 'submit'
                            # Try event dispatch
                            try:
                                result = await global_event_dispatcher.dispatch_event(
                                    component_key=target_component_key,
                                    event_name=event_name,
                                    event_data=event_data
                                )
                                logger.debug(f"Event dispatch result type: {type(result)}")
                                # Process the result
                                if result:
                                    # Try to convert to the expected output model if possible
                                    if isinstance(result, output_model):
                                        return result
                                    elif hasattr(output_model, 'parse_obj'):
                                        return output_model.parse_obj(result)
                                    elif hasattr(output_model, 'model_validate'):
                                        return output_model.model_validate(result)
                                    # Format result as UIResponse if needed
                                    if action_type == ActionType.CUSTOM_UI:
                                        if isinstance(result, UIResponse):
                                            return result
                                        elif isinstance(result, dict):
                                            ui_updates = result.pop('ui_updates', []) if isinstance(result.get('ui_updates'), list) else []
                                            return UIResponse(data=result, ui_updates=ui_updates)
                                        else:
                                            return UIResponse(data=result, ui_updates=[])
                                    return result
                            except EventDispatchError as e:
                                logger.warning(f"Event dispatch failed: {str(e)}")
                                # We'll fall through to the regular handler
                        except Exception as e:
                            logger.error(f"Error in event handling: {str(e)}")
                            # Continue to regular function execution on error
                # Execute original function if no event was handled
                result = await func(*args, **kwargs)
                # Handle response template if it exists
                if template_path and template_path.exists():
                    template_content = template_path.read_text()
                    try:
                        context = result.dict() if hasattr(result, 'dict') else result
                        rendered = Template(template_content).render(**context)
                        return Response(content=rendered, media_type="text/markdown")
                    except Exception as e:
                        logger.error(f"Template rendering failed: {str(e)}")
                        return result
                # Ensure proper response structure for UI actions
                if action_type == ActionType.CUSTOM_UI:
                    if isinstance(result, UIResponse):
                        return result
                    elif isinstance(result, dict) and 'ui_updates' in result:
                        return UIResponse(**result)
                    else:
                        return UIResponse(data=result, ui_updates=[])
                return result
            except Exception as e:
                logger.error(f"Error in action handler: {str(e)}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        # Create the endpoint info
        endpoint_info = ActionEndpointInfo(
            metadata=ActionMetadata(
                action_type=action_type,
                name=name,
                description=description,
                response_template_md=str(template_path) if template_path else None,
                workflow_id=workflow_id,
                step_id=step_id,
                ui_components=processed_components,
                allow_dynamic_ui=allow_dynamic_ui
            ),
            input_model=input_model,
            output_model=output_model,
            handler=wrapper,  # Use the wrapper as the handler
            schema_definitions=schema_definitions,
            examples=examples
        )
        # Register the action
        get_action_registry(agent_config.name).register_action(action_slug, endpoint_info)
        # Store UI components on the function for reference
        wrapper.ui_components = processed_components
        # Return the original function for decoration chaining
        return func
    return decorator

async def configure_action_routes(app: FastAPI, registry: ActionRegistry, agent_slug: str):
    """Configure API routes for all actions in an agent's registry."""
    logger.debug(f"Configuring routes for {agent_slug}")
    for action_slug, endpoint_info in registry.actions.items():
        route_path = f"/agents/{agent_slug}/actions/{action_slug}"
        endpoint_info.route_path = route_path
        logger.debug(f"Setting up route: {route_path}")
        # Create handler directly without await
        def create_handler(ei: ActionEndpointInfo = endpoint_info):
            async def handle_action(request_data: ei.input_model):
                try:
                    result = await ei.handler(request_data)
                    # Handle custom UI responses
                    if ei.metadata.action_type == ActionType.CUSTOM_UI:
                        if isinstance(result, UIResponse):
                            return result
                        elif isinstance(result, dict) and 'ui_updates' in result:
                            return UIResponse(**result)
                        else:
                            return UIResponse(data=result, ui_updates=[])
                    # Handle template responses
                    if ei.metadata.response_template_md:
                        template_path = Path(ei.metadata.response_template_md)
                        if template_path.exists():
                            try:
                                template_content = template_path.read_text()
                                context = result.dict() if hasattr(result, 'dict') else result
                                rendered = Template(template_content).render(**context)
                                return Response(content=rendered, media_type="text/markdown")
                            except Exception as e:
                                logger.error(f"Template rendering failed: {str(e)}")
                                return result
                    return result
                except Exception as e:
                    logger.error(f"Error in action handler: {str(e)}", exc_info=True)
                    raise HTTPException(status_code=500, detail=str(e))
            return handle_action

        # Add route to app
        handler = create_handler()
        app.post(route_path)(handler)
        logger.debug(f"Added route {route_path} for {action_slug}")