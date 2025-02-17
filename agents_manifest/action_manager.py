# action_manager.py
from typing import Dict, Callable, Optional, List, Any, Type, Union
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Response
import inspect
import re
from loguru import logger
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from agents_manifest.base_types import ActionType, BaseMetadata, AgentConfig, slugify

@dataclass
class ActionMetadata:
    """Metadata for action endpoints."""
    action_type: ActionType
    name: str
    description: str
    response_template_md: Optional[str] = None
    workflow_id: Optional[str] = None
    step_id: Optional[str] = None

@dataclass
class ActionEndpointInfo:
    """Information about an action endpoint."""
    metadata: ActionMetadata
    input_model: Type[BaseModel]
    output_model: Type[BaseModel]
    handler: Callable
    schema_definitions: Optional[Dict[str, Type[BaseModel]]] = None
    examples: Optional[Dict[str, List[Dict[str, Any]]]] = None
    route_path: Optional[str] = None

class ActionRegistry:
    """Registry for agent actions and their handlers."""
    def __init__(self):
        self.actions: Dict[str, ActionEndpointInfo] = {}

    def register_action(self, action_slug: str, endpoint_info: ActionEndpointInfo):
        """Register an action endpoint."""
        logger.debug(f"Registering action: {action_slug}")
        self.actions[action_slug] = endpoint_info

    def get_action(self, action_slug: str) -> Optional[ActionEndpointInfo]:
        """Get action endpoint info by slug."""
        return self.actions.get(action_slug)

agent_registries: Dict[str, ActionRegistry] = {}

def get_action_registry(agent_name: str) -> ActionRegistry:
    """Get or create action registry for an agent."""
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
    step_id: Optional[str] = None
) -> Callable:
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
        endpoint_info = ActionEndpointInfo(
            metadata=ActionMetadata(
                action_type=action_type,
                name=name,
                description=description,
                response_template_md=str(template_path) if template_path else None,
                workflow_id=workflow_id,
                step_id=step_id
            ),
            input_model=input_model,
            output_model=output_model,
            handler=func,
            schema_definitions=schema_definitions,
            examples=examples
        )
        get_action_registry(agent_config.name).register_action(action_slug, endpoint_info)
        return func
    return decorator

def configure_action_routes(app: FastAPI, registry: ActionRegistry, agent_slug: str):
    logger.debug(f"Configuring routes for {agent_slug}")
    for action_slug, endpoint_info in registry.actions.items():
        route_path = f"/agents/{agent_slug}/actions/{action_slug}"
        endpoint_info.route_path = route_path
        logger.debug(f"Setting up route: {route_path}")
        @app.post(route_path)
        async def handle_action(
            request_data: endpoint_info.input_model,
            action_info: ActionEndpointInfo = endpoint_info
        ):
            try:
                result = await action_info.handler(request_data)
                if action_info.metadata.response_template_md:
                    template_path = Path(action_info.metadata.response_template_md)
                    if template_path.exists():
                        template_content = template_path.read_text()
                        from jinja2 import Template
                        rendered = Template(template_content).render(**result)
                        return Response(content=rendered, media_type="text/markdown")
                return result
            except Exception as e:
                logger.error(f"Error in action handler: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        # Add route to app
        handler = create_handler()
        app.post(route_path)(handler)
        logger.debug(f"Added route {route_path} for {action_slug}")