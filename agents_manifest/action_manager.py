# action_manager.py
from typing import Dict, Callable, Optional, List, Any, Type, Union
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Response
import inspect
import re
from loguru import logger
from datetime import datetime
from dataclasses import dataclass
from agents_manifest.base_types import ActionType, BaseMetadata

#XXX Duplicate
def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

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

# Global registry (one per agent)
_action_registry = ActionRegistry()

def get_action_registry() -> ActionRegistry:
    """Expose the global action registry."""
    return _action_registry

def agent_action(
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
        # Create endpoint info
        endpoint_info = ActionEndpointInfo(
            metadata=ActionMetadata(
                action_type=action_type,
                name=name,
                description=description,
                response_template_md=response_template_md,
                workflow_id=workflow_id,
                step_id=step_id
            ),
            input_model=input_model,
            output_model=output_model,
            handler=func,
            schema_definitions=schema_definitions,
            examples=examples
        )
        # Register immediately with global registry
        action_slug = slugify(name)
        _action_registry.register_action(action_slug, endpoint_info)

        return func

    return decorator

def configure_action_routes(app: FastAPI, registry: ActionRegistry, agent_slug: str):
    """Configure action routes for a FastAPI application."""
    logger.debug(f"Configuring action routes for agent {agent_slug}")
    
    for action_slug, endpoint_info in registry.actions.items():
        logger.debug(f"Setting up route for action {action_slug}")
        route_path = f"/agents/{agent_slug}/actions/{action_slug}"
        endpoint_info.route_path = route_path

        def create_handler(endpoint_info=endpoint_info):
            async def handle_action(data: endpoint_info.input_model):
                try:
                    result = await endpoint_info.handler(data)
                    if endpoint_info.metadata.response_template_md and isinstance(result, dict):
                        from jinja2 import Template
                        template_content = endpoint_info.metadata.response_template_md
                        rendered = Template(template_content).render(**result)
                        return Response(content=rendered, media_type="text/markdown")
                    return result
                except Exception as e:
                    logger.error(f"Error in action handler: {str(e)}")
                    raise HTTPException(status_code=500, detail=str(e))
            return handle_action

        # Add route to app
        handler = create_handler()
        app.post(route_path)(handler)
        logger.debug(f"Added route {route_path} for {action_slug}")