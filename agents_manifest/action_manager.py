# action_manager.py
from typing import Dict, Callable, Optional, List, Any, Type, Union
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Response
import inspect
import re
from functools import wraps
from loguru import logger
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from jinja2 import Template
from agents_manifest.base_types import ActionType, BaseMetadata, AgentConfig, slugify, UIComponentUpdate, UIResponse
from agents_manifest.ui_components import UIComponent
from agents_manifest.event_dispatcher import ComponentEventDispatcher

@dataclass
class ActionMetadata:
    """Metadata container for capturing comprehensive information about an agent action."""
    action_type: ActionType
    name: str
    description: str
    response_template_md: Optional[str] = None
    workflow_id: Optional[str] = None
    step_id: Optional[str] = None
    allow_dynamic_ui: bool = False
    ui_components: List[UIComponent] = field(default_factory=list)

@dataclass
class ActionEndpointInfo:
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
global_dispatcher = ComponentEventDispatcher()

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
                global_dispatcher.register_component_handlers(component)
                # Additional registration for action handlers
                if hasattr(component, 'action_handlers') and component.action_handlers:
                    for action, handler in component.action_handlers.handlers.items():
                        global_dispatcher.register_action_handler(
                            component_key=component.key,
                            action=action,
                            handler=handler
                        )
                    # Register default handler if present
                    if component.action_handlers.default_handler:
                        global_dispatcher.register_action_handler(
                            component_key=component.key,
                            action='__default__',
                            handler=component.action_handlers.default_handler
                        )
        # Wrap the original function to handle UI components and event dispatching
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Get input data
                print("DEBUGGING: Wrapper function entered")
                input_data = args[0] if args else next(iter(kwargs.values()), None)
                logger.debug(f"Input data received: {input_data}")
                # Register UI components with global dispatcher
                if ui_components:
                    for component in ui_components:
                        global_dispatcher.register_component_handlers(component)
                        logger.debug(f"Registered handlers for component: {component.key}")
                # Check for action dispatching if input has an action
                if hasattr(input_data, 'action') and input_data.action:
                    # Find the target component key
                    target_component_key = getattr(input_data, 'component_key', 'main_editor')
                    # Prepare data for dispatching
                    data_dict = input_data.dict() if hasattr(input_data, 'dict') else {}
                    try:
                        # Dispatch action through global dispatcher
                        result = await global_dispatcher.dispatch_action(
                            component_key=target_component_key,
                            action=input_data.action,
                            data=data_dict
                        )
                        logger.debug(f"Dispatch result: {result}")
                        # Convert to UIResponse if needed
                        if result and not isinstance(result, UIResponse):
                            result = UIResponse(
                                data=result.dict() if hasattr(result, 'dict') else result,
                                ui_updates=[]
                            )
                        return result
                    except EventDispatchError:
                        # Fall back to original function if dispatch fails
                        logger.warning(f"Event dispatch failed for action {input_data.action}")
                # Call original function if no action handling occurred
                result = await func(*args, **kwargs)
                # Handle response template if exists
                if template_path and template_path.exists():
                    template_content = template_path.read_text()
                    rendered = Template(template_content).render(
                        **result.dict() if hasattr(result, 'dict') else {}
                    )
                    return Response(content=rendered, media_type="text/markdown")
                return result
            except Exception as e:
                logger.error(f"Error in action handler: {str(e)}")
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

def configure_action_routes(app: FastAPI, registry: ActionRegistry, agent_slug: str):
    """Configure API routes for all actions in an agent's registry.

    Args:
        app (FastAPI): The FastAPI application instance
        registry (ActionRegistry): Registry of actions to configure
        agent_slug (str): Unique identifier for the agent
    """
    logger.debug(f"Configuring routes for {agent_slug}")
    for action_slug, endpoint_info in registry.actions.items():
        route_path = f"/agents/{agent_slug}/actions/{action_slug}"
        endpoint_info.route_path = route_path
        logger.debug(f"Setting up route: {route_path}")
        @app.post(route_path)
        async def handle_action(
            request_data: endpoint_info.input_model,
            ei: ActionEndpointInfo = endpoint_info
        ):
            try:
                result = await ei.handler(request_data)
                if ei.metadata.action_type == ActionType.CUSTOM_UI:
                    if isinstance(result, UIResponse):
                        return result
                    return UIResponse(data=result.dict(), ui_updates=[])
                if ei.metadata.response_template_md:
                    template_path = Path(ei.metadata.response_template_md)
                    if template_path.exists():
                        template_content = template_path.read_text()
                        rendered = Template(template_content).render(**result.dict())
                        return Response(content=rendered, media_type="text/markdown")
                return result
            except Exception as e:
                logger.error(f"Error in action handler: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        # Add route to app
        handler = create_handler()
        app.post(route_path)(handler)
        logger.debug(f"Added route {route_path} for {action_slug}")