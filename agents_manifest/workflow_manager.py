from typing import Dict, Callable, Optional, List, Tuple, Any, Type
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from functools import wraps
from loguru import logger
from dataclasses import dataclass
from pathlib import Path
import inspect
from agents_manifest.base_types import WorkflowStepType, BaseMetadata, Workflow, WorkflowStepMetadata, WorkflowStep
from agents_manifest.session_manager import SessionManager

# Global registry
_global_workflow_registry = None

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
        metadata: WorkflowStepMetadata
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

def get_workflow_registry() -> WorkflowRegistry:
    """Get or create global workflow registry."""
    global _global_workflow_registry
    if _global_workflow_registry is None:
        _global_workflow_registry = WorkflowRegistry()
    return _global_workflow_registry

def workflow_step(
    workflow_id: str,
    step_id: str,
    action_type: str,
    name: str,
    description: str,
    response_template_md: Optional[str] = None
):
    """Enhanced decorator to register workflow step handlers."""
    def decorator(func: Callable) -> Callable:
        try:
            logger.debug(f"Registering workflow step handler: {workflow_id}/{step_id}")
            
            # Create metadata
            metadata = WorkflowStepMetadata(
                workflow_id=workflow_id,
                step_id=step_id,
                action_type=action_type,
                name=name,
                description=description,
                response_template_md=response_template_md
            )
            
            # Register with global registry
            registry = get_workflow_registry()
            registry.register_step_handler(workflow_id, step_id, func, metadata)
            
            # Store metadata on function for backward compatibility
            @wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error in workflow step {workflow_id}/{step_id}: {str(e)}")
                    raise
            
            wrapper._workflow_metadata = metadata
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
        logger.debug(f"Setting up routes for workflow: {workflow.id}")
        
        # Workflow start route
        path = f"/agents/{agent_slug}/workflow/{workflow.id}/start"
        logger.debug(f"Registering workflow start path: {path}")

        @app.post(path, description=f"Start the {workflow.name} workflow")
        async def start_workflow(
            data: Dict[str, Any],
            current_workflow: Workflow = workflow
        ):
            try:
                logger.debug(f"Starting workflow {current_workflow.id} with data: {data}")
                step_info = registry.get_step_handler(current_workflow.id, current_workflow.initial_step)
                
                if not step_info:
                    msg = f"Initial step handler not found for workflow {current_workflow.id}"
                    logger.error(msg)
                    raise HTTPException(404, msg)
                
                session_id = session_manager.create_session()
                handler, metadata = step_info
                
                # Update session
                session_manager.update_session(session_id, {
                    "workflow_id": current_workflow.id,
                    "current_step": current_workflow.initial_step,
                    "context": data.get("context", {})
                })
                
                # Execute handler
                result = await handler(data)
                
                # Process result
                initial_step = next(s for s in current_workflow.steps if s.id == current_workflow.initial_step)
                step_result = handle_transitions(result, initial_step)
                step_result["session_id"] = session_id
                
                logger.info(f"Successfully started workflow {current_workflow.id}")
                return step_result
                
            except Exception as e:
                logger.error(f"Error starting workflow: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        # Step execution route
        step_path = f"/agents/{agent_slug}/workflow/{workflow.id}/steps/{{step_id}}"
        logger.debug(f"Registering workflow step path: {step_path}")

        @app.post(step_path, description=f"Execute a step in the {workflow.name} workflow")
        async def execute_step(
            step_id: str,
            data: Dict[str, Any],
            current_workflow: Workflow = workflow
        ):
            try:
                logger.debug(f"Executing step {step_id} with data: {data}")
                
                # Validate session
                session_id = data.get("session_id")
                session = session_manager.get_session(session_id)
                if not session:
                    raise HTTPException(404, "Session not found or expired")
                
                # Get step and handler
                step = next((s for s in current_workflow.steps if s.id == step_id), None)
                if not step:
                    raise HTTPException(404, f"Step {step_id} not found in workflow")
                
                step_info = registry.get_step_handler(current_workflow.id, step_id)
                if not step_info:
                    raise HTTPException(404, f"Handler not found for step {step_id}")
                
                # Update session and execute
                handler, metadata = step_info
                session["current_step"] = step_id
                session_manager.update_session(session_id, session)
                
                result = await handler(data)
                
                # Handle completion
                if step.type == WorkflowStepType.END:
                    session_manager.close_session(session_id)
                    
                logger.info(f"Successfully executed step {step_id}")
                return handle_transitions(result, step)
                
            except Exception as e:
                logger.error(f"Error executing workflow step: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))