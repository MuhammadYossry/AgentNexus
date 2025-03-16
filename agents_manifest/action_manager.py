# action_manager.py
from typing import Dict, Callable, Optional, List, Any, Type
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Response
import inspect
from functools import wraps
from loguru import logger
from pathlib import Path
from jinja2 import Template
from agents_manifest.base_types import ActionType, AgentConfig, slugify, UIResponse
from agents_manifest.ui_components import UIComponent
from agents_manifest.event_dispatcher import global_event_dispatcher

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
        logger.debug(f"Decorating function: {func.__name__}")
        template_path = None
        if response_template_md is not None:
            template_path = Path(__file__).parent / "templates" / response_template_md
            logger.debug(f"Template path: {template_path}")
        sig = inspect.signature(func)
        input_model = next(
            (param.annotation for param in sig.parameters.values() 
             if hasattr(param.annotation, 'model_json_schema')),
            None
        )
        output_model = (
            func.__annotations__.get('return').__args__[0] 
            if hasattr(func.__annotations__.get('return', None), '__origin__')
            else func.__annotations__.get('return')
        )
        action_slug = slugify(name)
        # Register UI components with global dispatcher
        if ui_components:
            for component in ui_components:
                # Register component and its handlers with the global dispatcher
                global_event_dispatcher.register_component_handlers(component)
                # Additional registration for action handlers
                if hasattr(component, 'action_handlers') and component.action_handlers:
                    for action, handler in component.action_handlers.handlers.items():
                        global_event_dispatcher.register_action_handler(
                            component_key=component.key,
                            action=action,
                            handler=handler
                        )
                    # Register default handler if present
                    if component.action_handlers.default_handler:
                        global_event_dispatcher.register_action_handler(
                            component_key=component.key,
                            action='__default__',
                            handler=component.action_handlers.default_handler
                        )
        # Wrap the original function to handle UI components and event dispatching
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Get input data
                input_data = args[0] if args else next(iter(kwargs.values()), None)
                logger.debug(f"Input data received: {input_data}")

                # Handle UI component registration
                if ui_components:
                    for component in ui_components:
                        global_event_dispatcher.register_component_handlers(component)
                        logger.debug(f"Registered handlers for component: {component.key}")

                # Check for event dispatching
                if hasattr(input_data, 'event') and input_data.event:
                    target_component_key = getattr(input_data, 'component_key', None)
                    if not target_component_key:
                        logger.warning("No component_key provided for event dispatch")
                        raise HTTPException(status_code=400, detail="Missing component_key for event")

                    try:
                        # Dispatch event through global dispatcher
                        result = await global_event_dispatcher.dispatch_event(
                            component_key=target_component_key,
                            event_name=input_data.event,
                            event_data=input_data.dict() if hasattr(input_data, 'dict') else input_data
                        )
                        logger.debug(f"Event dispatch result: {result}")
                        # Convert to UIResponse if needed
                        if result:
                            if isinstance(result, dict):
                                ui_updates = result.pop('ui_updates', []) if isinstance(result.get('ui_updates'), list) else []
                                return UIResponse(data=result, ui_updates=ui_updates)
                            elif not isinstance(result, UIResponse):
                                return UIResponse(data=result, ui_updates=[])
                        return result

                    except Exception as e:
                        logger.error(f"Event dispatch failed: {str(e)}")
                        # Fall through to regular function execution

                # Execute original function
                result = await func(*args, **kwargs)

                # Handle response template
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
                if endpoint_info.metadata.action_type == ActionType.CUSTOM_UI:
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
        endpoint_info = ActionEndpointInfo(
            metadata=ActionMetadata(
                action_type=action_type,
                name=name,
                description=description,
                response_template_md=str(template_path) if template_path else None,
                workflow_id=workflow_id,
                step_id=step_id,
                ui_components=ui_components or [],
                allow_dynamic_ui=allow_dynamic_ui
            ),
            input_model=input_model,
            output_model=output_model,
            handler=func,
            schema_definitions=schema_definitions,
            examples=examples
        )
        get_action_registry(agent_config.name).register_action(action_slug, endpoint_info)
        wrapper.ui_components = ui_components
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