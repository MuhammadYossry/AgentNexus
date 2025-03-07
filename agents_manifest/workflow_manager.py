from typing import Dict, Callable, Optional, List, Tuple, Any, Type
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Path as FastAPIPath
from functools import wraps
from loguru import logger
from dataclasses import dataclass
from pathlib import Path
import inspect
from agents_manifest.base_types import (
    WorkflowStepType, BaseMetadata, AgentConfig,
    Workflow, WorkflowStepMetadata, WorkflowStep,
    ActionType, slugify
)
from agents_manifest.ui_components import UIComponent
from agents_manifest.session_manager import SessionManager

class WorkflowRegistry:
    """Enhanced registry for workflow definitions and handlers."""
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.step_handlers: Dict[Tuple[str, str], Callable] = {}
        self.handler_metadata: Dict[Tuple[str, str], WorkflowStepMetadata] = {}
        logger.debug("Initialized new WorkflowRegistry")

    def register_workflow(self, workflow: Workflow):
        """Register a workflow definition."""
        try:
            logger.debug(f"Registering workflow: {workflow.id}")
            if workflow.id in self.workflows:
                logger.warning(f"Overwriting existing workflow: {workflow.id}")
            self.workflows[workflow.id] = workflow
            logger.info(f"Successfully registered workflow: {workflow.id}")
        except Exception as e:
            logger.error(f"Error registering workflow {workflow.id}: {str(e)}")
            raise

    def register_step_handler(
        self, 
        workflow_id: str, 
        step_id: str, 
        handler: Callable,
        metadata: Dict[str, Any]
    ):
        """Register a handler function and its metadata for a workflow step."""
        try:
            key = (workflow_id, step_id)
            logger.debug(f"Registering step handler: {workflow_id}/{step_id}")
            
            # Extract models from handler if not in metadata
            if not metadata.input_model or not metadata.output_model:
                sig = inspect.signature(handler)
                
                # Get input model
                metadata.input_model = next(
                    (param.annotation for param in sig.parameters.values() 
                     if hasattr(param.annotation, 'model_json_schema')),
                    None
                )
                
                # Get output model
                return_annotation = handler.__annotations__.get('return')
                metadata.output_model = (
                    return_annotation.__args__[0] 
                    if hasattr(return_annotation, '__origin__')
                    else return_annotation
                ) if return_annotation else None

            self.step_handlers[key] = handler
            self.handler_metadata[key] = metadata
            logger.info(f"Successfully registered step handler: {workflow_id}/{step_id}")
        except Exception as e:
            logger.error(f"Error registering step handler {workflow_id}/{step_id}: {str(e)}")
            raise

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            logger.warning(f"Workflow not found: {workflow_id}")
        return workflow

    def get_step_handler(self, workflow_id: str, step_id: str) -> Optional[Tuple[Callable, WorkflowStepMetadata]]:
        """Get handler function and metadata for a workflow step."""
        key = (workflow_id, step_id)
        logger.debug(f"Getting step handler for: {workflow_id}/{step_id}")
        logger.debug(f"Registered handlers: {list(self.step_handlers.keys())}")
        
        handler = self.step_handlers.get(key)
        metadata = self.handler_metadata.get(key)
        
        if handler and metadata:
            return handler, metadata
        logger.warning(f"Step handler not found: {workflow_id}/{step_id}")
        return None


agent_workflow_registries: Dict[str, WorkflowRegistry] = {}

def get_workflow_registry(agent_name: str) -> WorkflowRegistry:
    """Get or create workflow registry for an agent."""
    agent_slug = slugify(agent_name)
    if agent_slug not in agent_workflow_registries:
        agent_workflow_registries[agent_slug] = WorkflowRegistry()
    return agent_workflow_registries[agent_slug]

def workflow_step(
    agent_config: AgentConfig,
    workflow_id: str,
    step_id: str,
    name: str,
    description: str,
    ui_components: Optional[List[UIComponent]] = None,
    allow_dynamic_ui: bool = True
) -> Callable:
    """decorator for UI-driven workflow steps."""
    def decorator(func: Callable) -> Callable:
        try:
            metadata = WorkflowStepMetadata(
                workflow_id=workflow_id,
                action_type=ActionType.CUSTOM_UI,
                step_id=step_id,
                name=name,
                description=description,
                ui_components=ui_components or [],
                allow_dynamic_ui=allow_dynamic_ui
            )
            registry = get_workflow_registry(agent_config.name)
            registry.register_step_handler(workflow_id, step_id, func, metadata)
            @wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    result = await func(*args, **kwargs)
                    if not isinstance(result, WorkflowStepResponse):
                        # Auto-wrap non-WorkflowStepResponse results
                        return WorkflowStepResponse(data=result)
                    return result
                except Exception as e:
                    logger.error(f"Error in workflow step {workflow_id}/{step_id}: {str(e)}")
                    raise
            return wrapper
        except Exception as e:
            logger.error(f"Error setting up workflow step {workflow_id}/{step_id}: {str(e)}")
            raise
    return decorator

def handle_transitions(result: Any, step: WorkflowStep) -> Dict[str, Any]:
    """Process workflow transitions and data mapping."""
    try:
        response = {"result": result}
        if step.transitions:
            transition = step.transitions[0]  # Taking first transition for simplicity
            response["next_step"] = transition.target
            
            # Map data according to transition rules
            mapped_data = {}
            for mapping in transition.data_mapping:
                try:
                    if isinstance(result, dict):
                        mapped_data[mapping.target_field] = result.get(mapping.source_field)
                    elif hasattr(result, mapping.source_field):
                        mapped_data[mapping.target_field] = getattr(result, mapping.source_field)
                except Exception as e:
                    logger.error(f"Error mapping field {mapping.source_field}: {str(e)}")
                    
            response["next_data"] = mapped_data
            logger.debug(f"Processed transition to {transition.target} with {len(mapped_data)} mapped fields")
        return response
    except Exception as e:
        logger.error(f"Error handling transitions: {str(e)}")
        raise

def configure_workflow_routes(app: FastAPI, registry: WorkflowRegistry, agent_slug: str):
    """Configure workflow routes with enhanced error handling."""
    session_manager = SessionManager()
    logger.debug(f"Configuring workflow routes for agent: {agent_slug}")

    for workflow in registry.workflows.values():
        workflow_id = workflow.id
        logger.debug(f"Setting up routes for workflow: {workflow_id}")
        
        # Workflow start route
        path = f"/agents/{agent_slug}/workflow/{workflow_id}/start"
        logger.debug(f"Registering workflow start path: {path}")

        @app.post(f"/agents/{agent_slug}/workflow/{{workflow_id}}/start", description=f"Start the {workflow.name} workflow")
        async def start_workflow(
            # workflow_id: str = FastAPIPath(..., description="ID of the workflow to start"),
            data: Dict[str, Any] = None
        ):
            try:
                if data is None:
                    data = {}
                workflow = registry.get_workflow(workflow_id)
                if not workflow:
                    raise HTTPException(404, "Workflow not found")
                
                session_id = session_manager.create_session()
                session = {
                    "workflow_id": workflow_id,
                    "current_step": workflow.initial_step,
                    "context": data.get("context", {})
                }
                
                handler_info = registry.get_step_handler(workflow_id, workflow.initial_step)
                if not handler_info:
                    raise HTTPException(404, "Initial step handler not found")
                
                handler, metadata = handler_info
                response = await handler(data)
                
                # Update session with context and UI state
                session["context"].update(response.context_updates)
                session_manager.update_session(session_id, session)
                
                return {
                    "session_id": session_id,
                    "metadata": {
                        "name": metadata.name,
                        "description": metadata.description,
                        "ui_components": [comp.dict() for comp in metadata.ui_components]
                    },
                    "data": response.data,
                    "ui_updates": response.ui_updates,
                    "next_step": response.next_step_id
                }
            except Exception as e:
                logger.error(f"Error starting workflow: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        # Step execution route
        step_path = f"/agents/{agent_slug}/workflow/{workflow_id}/step/{{step_id}}"
        logger.debug(f"Registering workflow step path: {step_path}")

        @app.post(f"/agents/{agent_slug}/workflow/{{workflow_id}}/step/{{step_id}}")
        async def execute_step(
            workflow_id: str,
            step_id: str,
            data: Dict[str, Any],
        ):
            try:
                session_id = data.get("session_id")
                if not session_id:
                    raise HTTPException(400, "session_id required in request body")
                session = session_manager.get_session(session_id)
                if not session:
                    raise HTTPException(404, "Session expired or invalid")
                
                handler_info = registry.get_step_handler(workflow_id, step_id)
                if not handler_info:
                    raise HTTPException(404, "Step handler not found")
                
                handler, metadata = handler_info
                response = await handler({**data, "context": session["context"]})
                
                # Update session context
                session["context"].update(response.context_updates)
                
                # Handle navigation
                if response.next_step_id:
                    session["current_step"] = response.next_step_id
                    next_handler_info = registry.get_step_handler(workflow_id, response.next_step_id)
                    if not next_handler_info:
                        raise HTTPException(404, "Next step handler not found")
                    next_metadata = next_handler_info[1]
                    
                    # Include next step's UI components
                    return {
                        "session_id": session_id,
                        "metadata": {
                            "name": next_metadata.name,
                            "description": next_metadata.description,
                            "ui_components": [comp.dict() for comp in next_metadata.ui_components]
                        },
                        "data": response.data,
                        "ui_updates": response.ui_updates,
                        "next_step": response.next_step_id
                    }
                
                session_manager.update_session(session_id, session)
                return {
                    "session_id": session_id,
                    "data": response.data,
                    "ui_updates": response.ui_updates
                }
            except Exception as e:
                logger.error(f"Error executing step: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))