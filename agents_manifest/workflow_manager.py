# workflow_manager.py
from typing import Dict, Callable, Optional, List, Tuple, Any
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from datetime import datetime
from loguru import logger
from dataclasses import dataclass
from agents_manifest.base_types import WorkflowStepType, BaseMetadata
from agents_manifest.session_manager import SessionManager


class WorkflowDataMapping(BaseModel):
    """Maps data between workflow steps."""
    source_field: str
    target_field: str
    transform: Optional[str] = None

class WorkflowTransition(BaseModel):
    """Defines transition between workflow steps."""
    target: str
    condition: Optional[str] = None
    data_mapping: List[WorkflowDataMapping] = Field(default_factory=list)

class WorkflowStep(BaseModel):
    """Individual workflow step definition."""
    id: str
    type: WorkflowStepType
    action: Optional[str] = None
    transitions: List[WorkflowTransition] = Field(default_factory=list)

class Workflow(BaseModel):
    """Complete workflow definition."""
    id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    initial_step: str

class WorkflowState(BaseModel):
    """Runtime state of a workflow instance."""
    workflow_id: str
    current_step: str
    data: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

@dataclass
class WorkflowHandlerMetadata:
    """Metadata for workflow step handlers."""
    workflow_id: str
    step_id: str
    action_type: str
    name: str
    description: str
    response_template_md: Optional[str] = None

class WorkflowRegistry:
    """Registry for workflow definitions and handlers."""
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.step_handlers: Dict[Tuple[str, str], Callable] = {}
        self.handler_metadata: Dict[Tuple[str, str], WorkflowHandlerMetadata] = {}

    def register_workflow(self, workflow: Workflow):
        """Register a workflow definition."""
        logger.debug(f"Registering workflow: {workflow.id}")
        self.workflows[workflow.id] = workflow

    def register_step_handler(
        self, 
        workflow_id: str, 
        step_id: str, 
        handler: Callable,
        metadata: WorkflowHandlerMetadata
    ):
        """Register a handler function and its metadata for a workflow step."""
        key = (workflow_id, step_id)
        logger.debug(f"Registering step handler: {workflow_id}/{step_id}")
        self.step_handlers[key] = handler
        self.handler_metadata[key] = metadata

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID."""
        return self.workflows.get(workflow_id)

    def get_step_handler(self, workflow_id: str, step_id: str) -> Optional[Tuple[Callable, WorkflowHandlerMetadata]]:
        """Get handler function and metadata for a workflow step."""
        key = (workflow_id, step_id)
        handler = self.step_handlers.get(key)
        metadata = self.handler_metadata.get(key)
        if handler and metadata:
            return handler, metadata
        return None

def workflow_step(
    workflow_id: str,
    step_id: str,
    action_type: str,
    name: str,
    description: str,
    response_template_md: Optional[str] = None
):
    """Decorator to register workflow step handlers."""
    def decorator(func: Callable):
        metadata = WorkflowHandlerMetadata(
            workflow_id=workflow_id,
            step_id=step_id,
            action_type=action_type,
            name=name,
            description=description,
            response_template_md=response_template_md
        )
        # Store the metadata for route generation
        func._workflow_metadata = metadata
        return func
    return decorator

def handle_transitions(result: Any, step: WorkflowStep) -> Dict[str, Any]:
    """Process workflow transitions and data mapping."""
    response = {"result": result}
    if step.transitions:
        transition = step.transitions[0]  # Taking first transition for simplicity
        response["next_step"] = transition.target
        # Map data according to transition rules
        mapped_data = {}
        for mapping in transition.data_mapping:
            if isinstance(result, dict):
                mapped_data[mapping.target_field] = result.get(mapping.source_field)
            elif hasattr(result, mapping.source_field):
                mapped_data[mapping.target_field] = getattr(result, mapping.source_field)
        response["next_data"] = mapped_data
    return response

def configure_workflow_routes(app: FastAPI, registry: WorkflowRegistry, agent_slug: str):
    """Configure workflow routes for a FastAPI application."""
    session_manager = SessionManager()
    for workflow in registry.workflows.values():
        route_path = f"/agents/{agent_slug}/workflows/{workflow.id}/start"
        @app.post(route_path)
        async def start_workflow(
            data: Dict[str, Any],
            workflow_id: str = workflow.id
        ):
            current_workflow = registry.get_workflow(workflow_id)
            step_info = registry.get_step_handler(workflow_id, current_workflow.initial_step)
            if not step_info:
                raise HTTPException(404, "Initial step handler not found")
            session_id = session_manager.create_session()
            handler, metadata = step_info
            session_manager.update_session(session_id, {"workflow_id": workflow_id})
            result = await handler(data)
            initial_step = next(s for s in current_workflow.steps 
                              if s.id == current_workflow.initial_step)
            step_result = handle_transitions(result, initial_step)
            step_result["session_id"] = session_id
            return step_result

        @app.post(f"/agents/{agent_slug}/workflows/{workflow.id}/steps/{{step_id}}")
        async def execute_step(
            step_id: str,
            data: Dict[str, Any],
            workflow_id: str = workflow.id
        ):
            session = session_manager.get_session(data.get("session_id"))
            if not session:
                raise HTTPException(404, "Session not found") 
            current_workflow = registry.get_workflow(workflow_id)
            step = next((s for s in current_workflow.steps if s.id == step_id), None)
            if not step:
                raise HTTPException(404, f"Step {step_id} not found")
                
            step_info = registry.get_step_handler(workflow_id, step_id)
            if not step_info:
                raise HTTPException(404, f"Handler not found for step {step_id}")
            handler, metadata = step_info
            result = await handler(data)
            if step.type == WorkflowStepType.END:
                session_manager.close_session(data["session_id"])
            return handle_transitions(result, step)