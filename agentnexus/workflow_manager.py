from typing import Dict, Callable, Optional, List, Tuple, Any
from fastapi import FastAPI, HTTPException
from functools import wraps
from loguru import logger
import inspect
from agentnexus.base_types import (
    AgentConfig, Workflow, WorkflowStepMetadata,
    ActionType, slugify, UIComponentUpdate, WorkflowStepResponse
)
from agentnexus.ui_components import UIComponent
from agentnexus.session_manager import SessionManager, session_manager
from agentnexus.event_dispatcher import global_event_dispatcher, EventDispatchError

# =========================================================================
# DEFAULT EVENT HANDLERS AND REGISTRATION
# =========================================================================
async def handle_default_submit(action: str, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Default handler for form submissions."""
    logger.debug(f"Default submit handler called with data: {data}")
    return data

async def handle_default_format(action: str, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Default handler for code formatting."""
    logger.debug(f"Default format handler called with data: {data}")
    return {
        "content": data.get("code", ""),
        "message": "Code formatting not implemented for this component"
    }

# Register default handlers for components based on event type
def register_default_handlers():
    """Register default event handlers for common components and events."""
    logger.debug("Registering default event handlers for components...")
    # Component event mappings
    known_components = {
        "language_selector": ["submit", "change"],
        "code_input": ["submit", "format", "save"],
        "improved_code": ["format", "save", "add_types", "add_docs"],
        "continue_form": ["submit"],
        "approval_form": ["submit"],
        "quality_metrics": ["row_click"],
        "analysis_result": ["submit"],
        "improvement_notes": ["submit"],
        "code_display": ["format", "save"],
        "final_code": ["format", "save"],
        "scored_code": ["format", "save"],
    }
    # Event handler mapping
    event_handlers = {
        "submit": handle_default_submit,
        "format": handle_default_format,
    }
    # Register handlers for components
    for comp_key, events in known_components.items():
        for event in events:
            handler = event_handlers.get(event, handle_default_submit)
            global_event_dispatcher.register_event_handler(comp_key, event, handler)
    # Register default handlers for workflow step forms
    for step_type in ['upload', 'analyze', 'improve', 'score', 'review', 'complete']:
        comp_key = f"default_form_{step_type}"
        global_event_dispatcher.register_event_handler(comp_key, "submit", handle_default_submit)
    logger.debug(f"Registered event handlers: {global_event_dispatcher.event_handlers}")

# Register all default handlers
register_default_handlers()

# =========================================================================
# WORKFLOW REGISTRY AND HELPERS
# =========================================================================

class WorkflowRegistry:
    """Enhanced registry for workflow definitions and handlers with event system integration."""

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
                self._extract_handler_models(handler, metadata)
            self.step_handlers[key] = handler
            self.handler_metadata[key] = metadata
            logger.info(f"Successfully registered step handler: {workflow_id}/{step_id}")
        except Exception as e:
            logger.error(f"Error registering step handler {workflow_id}/{step_id}: {str(e)}")
            raise

    def _extract_handler_models(self, handler: Callable, metadata: WorkflowStepMetadata):
        """Extract input and output models from handler signature."""
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

# Global registry dictionary
agent_workflow_registries: Dict[str, WorkflowRegistry] = {}

def get_workflow_registry(agent_name: str) -> WorkflowRegistry:
    """Get or create workflow registry for an agent."""
    agent_slug = slugify(agent_name)
    if agent_slug not in agent_workflow_registries:
        agent_workflow_registries[agent_slug] = WorkflowRegistry()
    return agent_workflow_registries[agent_slug]

def prepare_components_with_context(components: List[UIComponent], context: Dict[str, Any]) -> List[Dict]:
    """Prepare UI components with session context data."""
    prepared_components = []
    for component in components:
        # Create a copy of the component data
        component_data = component.dict(exclude={'event_handlers'})
        # Add supported events
        component_data["supported_events"] = get_supported_events(component)
        # Pre-populate component state based on type and context
        populate_component_state(component_data, component, context)
        prepared_components.append(component_data)
    return prepared_components

def get_supported_events(component: UIComponent) -> List[str]:
    """Get supported events for a component based on its type."""
    supported_events = list(component.supported_events) if hasattr(component, 'supported_events') else []
    # Add default events based on component type
    if component.component_type == "form":
        default_events = ["submit"]
    elif component.component_type == "code_editor":
        default_events = ["format", "save"]
        if component.component_key == "improved_code":
            default_events.extend(["add_types", "add_docs"])
    else:
        default_events = []
    # Add default events not already in the list
    for event in default_events:
        if event not in supported_events:
            supported_events.append(event)
    return supported_events

def populate_component_state(component_data: Dict[str, Any], component: UIComponent, context: Dict[str, Any]):
    """Populate component state based on type and context."""
    component_key = component.component_key
    if component.component_type == "code_editor":
        populate_code_editor_state(component_data, component_key, context)
    elif component.component_type == "markdown":
        populate_markdown_state(component_data, component_key, context)
    elif component.component_type == "table":
        populate_table_state(component_data, component_key, context)
    elif component.component_type == "form":
        populate_form_state(component_data, component_key, context)

def populate_code_editor_state(component_data: Dict[str, Any], component_key: str, context: Dict[str, Any]):
    """Populate state for code editor components."""
    content_key = None
    if component_key == "code_input":
        content_key = "original_code"
    elif component_key == "improved_code":
        content_key = "improved_code"
    elif component_key == "final_code" and "improved_code" in context:
        content_key = "improved_code"
    elif component_key == "final_code" and "original_code" in context:
        content_key = "original_code"

    content = context.get(content_key) if content_key and content_key in context else None
    if not content and "code" in context:
        content = context.get("code")
    if content:
        component_data["editor_content"] = content

def populate_markdown_state(component_data: Dict[str, Any], component_key: str, context: Dict[str, Any]):
    """Populate state for markdown components."""
    content_mapping = {
        "analysis_result": "analysis",
        "improvement_notes": "improvement_notes",
        "completion_summary": "summary"
    }
    content_key = content_mapping.get(component_key, "markdown_content")
    if content_key in context:
        component_data["markdown_content"] = context[content_key]

def populate_table_state(component_data: Dict[str, Any], component_key: str, context: Dict[str, Any]):
    """Populate state for table components."""
    if component_key == "quality_metrics" and "metrics_data" in context:
        component_data["table_data"] = context["metrics_data"]
    elif "table_data" in context:
        component_data["table_data"] = context["table_data"]

def populate_form_state(component_data: Dict[str, Any], component_key: str, context: Dict[str, Any]):
    """Populate state for form components."""
    initial_values = {}
    if component_key == "language_selector" and "language" in context:
        initial_values["language"] = context["language"]
    elif component_key == "continue_form" and "proceed" in context:
        initial_values["proceed"] = context["proceed"]
    elif component_key == "approval_form":
        if "approved" in context:
            initial_values["approved"] = "yes" if context["approved"] else "no"
        if "comments" in context:
            initial_values["comments"] = context["comments"]
    elif "form_data" in context:
        initial_values = context["form_data"]

    if initial_values:
        component_data["initial_values"] = initial_values

# =========================================================================
# RESPONSE STANDARDIZATION
# =========================================================================

def ensure_workflow_step_response(result: Any) -> WorkflowStepResponse:
    """Ensure that a function result is a proper WorkflowStepResponse.

    This helper function normalizes any response into a WorkflowStepResponse format,
    extracting fields appropriately and avoiding nested structures.
    """
    if isinstance(result, WorkflowStepResponse):
        return result
    # Handle dict responses
    if isinstance(result, dict):
        data, ui_updates, context_updates, next_step_id = extract_response_fields(result)
        return WorkflowStepResponse(
            data=data,
            ui_updates=ui_updates,
            next_step_id=next_step_id,
            context_updates=context_updates
        )
    # Handle pydantic models
    if hasattr(result, "dict"):
        return WorkflowStepResponse(
            data=result.dict(),
            ui_updates=[],
            context_updates={}
        )
    # Handle any other type
    return WorkflowStepResponse(
        data={"result": result},
        ui_updates=[],
        context_updates={}
    )

def extract_response_fields(data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Any], Dict[str, Any], Optional[str]]:
    """Extract standard fields from a response dictionary."""
    # Create a copy to avoid modifying the original
    data_copy = data.copy()
    # Extract standard fields
    ui_updates = data_copy.pop("ui_updates", []) if "ui_updates" in data_copy else []
    context_updates = data_copy.pop("context_updates", {}) if "context_updates" in data_copy else {}
    next_step_id = data_copy.pop("next_step_id", None) if "next_step_id" in data_copy else None

    # Handle nested response pattern
    if "result" in data_copy and isinstance(data_copy["result"], dict):
        nested = data_copy.pop("result")
        # Extract nested fields if present
        if "data" in nested:
            data_copy = nested["data"]
        if "ui_updates" in nested and not ui_updates:
            ui_updates = nested["ui_updates"]
        if "context_updates" in nested and not context_updates:
            context_updates = nested["context_updates"]
        if "next_step_id" in nested and not next_step_id:
            next_step_id = nested["next_step_id"]
    return data_copy, ui_updates, context_updates, next_step_id

# =========================================================================
# WORKFLOW STEP DECORATOR
# =========================================================================

def workflow_step(
    agent_config: AgentConfig,
    workflow_id: str,
    step_id: str,
    name: str,
    description: str,
    ui_components: Optional[List[UIComponent]] = None,
    allow_dynamic_ui: bool = True
) -> Callable:
    """Decorator for UI-driven workflow steps with integrated event handling."""

    def decorator(func: Callable) -> Callable:
        try:
            # Create and register metadata
            metadata = create_step_metadata(
                workflow_id, step_id, name, description, ui_components, allow_dynamic_ui
            )
            # Register UI components
            register_step_components(ui_components, workflow_id, step_id)
            # Register step handler
            registry = get_workflow_registry(agent_config.name)
            registry.register_step_handler(workflow_id, step_id, func, metadata)

            @wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    logger.debug(f"Workflow step wrapper called: {workflow_id}/{step_id}")
                    # Extract input data and form data
                    input_data, form_data = extract_input_data(*args, **kwargs)
                    # Handle component events if present
                    event_result = await handle_component_event(form_data, input_data, metadata)
                    if event_result:
                        return event_result
                    # Call original function and return result
                    result = await func(*args, **kwargs)
                    return standardize_step_response(result, input_data, metadata)
                except Exception as e:
                    logger.error(f"Error in workflow step {workflow_id}/{step_id}: {str(e)}")
                    raise
            return wrapper
        except Exception as e:
            logger.error(f"Error setting up workflow step {workflow_id}/{step_id}: {str(e)}")
            raise
    return decorator

def create_step_metadata(
    workflow_id: str,
    step_id: str,
    name: str,
    description: str,
    ui_components: Optional[List[UIComponent]],
    allow_dynamic_ui: bool
) -> WorkflowStepMetadata:
    """Create workflow step metadata."""
    return WorkflowStepMetadata(
        workflow_id=workflow_id,
        action_type=ActionType.CUSTOM_UI,
        step_id=step_id,
        name=name,
        description=description,
        ui_components=ui_components or [],
        allow_dynamic_ui=allow_dynamic_ui
    )

def register_step_components(
    ui_components: Optional[List[UIComponent]],
    workflow_id: str,
    step_id: str
):
    """Register step UI components with the global dispatcher."""
    if not ui_components:
        return
    for component in ui_components:
        # Register component with dispatcher
        global_event_dispatcher.register_component(component)
        # Register default handlers based on component type
        if component.component_type == "form":
            if not global_event_dispatcher.event_handlers.get(component.component_key, {}).get("submit"):
                global_event_dispatcher.register_event_handler(
                    component.component_key, "submit", handle_default_submit
                )
        elif component.component_type == "code_editor":
            if not global_event_dispatcher.event_handlers.get(component.component_key, {}).get("format"):
                global_event_dispatcher.register_event_handler(
                    component.component_key, "format", handle_default_format
                )
        logger.debug(f"Registered component {component.component_key} from workflow step {workflow_id}/{step_id}")

def extract_input_data(*args, **kwargs) -> Tuple[Any, Optional[Dict[str, Any]]]:
    """Extract input data and form data from function arguments."""
    input_data = args[0] if args else next(iter(kwargs.values()), None)
    form_data = None
    if input_data:
        if hasattr(input_data, 'form_data'):
            form_data = input_data.form_data
        elif isinstance(input_data, dict) and 'form_data' in input_data:
            form_data = input_data['form_data']
    return input_data, form_data

async def handle_component_event(
    form_data: Optional[Dict[str, Any]],
    input_data: Any,
    metadata: WorkflowStepMetadata
) -> Optional[Dict[str, Any]]:
    """Handle component events and return a response if an event was processed."""
    if not form_data or not isinstance(form_data, dict):
        return None
    component_key = form_data.get('component_key')
    event_name = form_data.get('event_name') or form_data.get('action')
    if not (component_key and event_name):
        return None

    try:
        logger.debug(f"Attempting to dispatch event {event_name} for component {component_key}")
        event_result = await global_event_dispatcher.dispatch_event(
            component_key=component_key,
            event_name=event_name,
            event_data=form_data
        )
        if not event_result:
            return None
        logger.debug(f"Event handler succeeded with result: {event_result}")
        # Create UI updates from result
        ui_updates = create_ui_updates_from_event(component_key, event_result)
        # Standardize and normalize result
        normalized_result = ensure_workflow_step_response(event_result)
        # Return standardized response
        return {
            "session_id": input_data.get("session_id") if input_data else None,
            "metadata": {
                "name": metadata.name,
                "description": metadata.description
            },
            "data": normalized_result.data,
            "ui_updates": ui_updates or normalized_result.ui_updates,
            "next_step_id": normalized_result.next_step_id,
            "context_updates": normalized_result.context_updates
        }
    except EventDispatchError as e:
        logger.warning(f"Event dispatch failed: {str(e)}")
        return None

def create_ui_updates_from_event(component_key: str, event_result: Any) -> List[UIComponentUpdate]:
    """Create UI component updates from event result."""
    ui_updates = []
    if isinstance(event_result, dict):
        # Extract content if present
        content = event_result.get("content")
        if content is not None:
            ui_updates.append(
                UIComponentUpdate(
                    key=component_key,
                    state={"content": content}
                )
            )
        # Add other state updates
        for key, value in event_result.items():
            if key not in ["content", "message"]:
                ui_updates.append(
                    UIComponentUpdate(
                        key=component_key,
                        state={key: value}
                    )
                )
    elif event_result is not None:
        # For non-dict results, create a basic update
        ui_updates.append(
            UIComponentUpdate(
                key=component_key,
                state={"content": str(event_result)}
            )
        )
    return ui_updates

def standardize_step_response(result: Any, input_data: Any, metadata: WorkflowStepMetadata) -> Dict[str, Any]:
    """Standardize a step response to ensure consistent structure."""
    normalized_result = ensure_workflow_step_response(result)

    return {
        "session_id": input_data.get("session_id") if input_data else None,
        "metadata": {
            "name": metadata.name,
            "description": metadata.description
        },
        "data": normalized_result.data,
        "ui_updates": normalized_result.ui_updates,
        "next_step_id": normalized_result.next_step_id,
        "context_updates": normalized_result.context_updates
    }

# =========================================================================
# WORKFLOW EXECUTION MANAGER
# =========================================================================

class WorkflowExecutionManager:
    """Manages workflow execution and state transitions with enhanced context handling."""

    def __init__(self, registry: WorkflowRegistry, session_manager: SessionManager):
        self.registry = registry
        self.session_manager = session_manager
        self.event_dispatcher = global_event_dispatcher

    async def preview_workflow_step(
        self,
        workflow_id: str,
        step_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Preview a workflow step with populated UI components."""
        try:
            # Validate session and handler
            session = self._validate_session(session_id)
            handler_info = self._validate_handler(workflow_id, step_id)
            _, metadata = handler_info
            # Prepare UI components
            ui_components = []
            if metadata.ui_components:
                ui_components = prepare_components_with_context(
                    metadata.ui_components,
                    session["context"]
                )
            return {
                "session_id": session_id,
                "metadata": {
                    "name": metadata.name,
                    "description": metadata.description,
                },
                "ui_components": ui_components,
                "context_data": session["context"]
            }
        except Exception as e:
            logger.error(f"Error previewing step: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def process_workflow_step(
        self,
        workflow_id: str,
        step_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a workflow step with enhanced context handling and UI updates."""
        try:
            # Validate session and handler
            session_id = data.get("session_id")
            if not session_id:
                raise HTTPException(400, "session_id required in request body")
            session = self._validate_session(session_id)
            handler_info = self._validate_handler(workflow_id, step_id)
            handler, metadata = handler_info
            # Handle component events or execute step handler
            response = await self._handle_step_execution(data, session, handler)
            # Update session with context updates
            if response.context_updates:
                # Ensure context exists
                if "context" not in session:
                    session["context"] = {}
                session["context"].update(response.context_updates)
                logger.debug(f"Updated session context: {session['context']}")
            # Handle step transition if needed
            if response.next_step_id:
                return await self._handle_step_transition(
                    workflow_id, response, session, session_id
                )
            self.session_manager.update_session(session_id, session)
            logger.debug(f"Session update successful.")
            return {
                "session_id": session_id,
                "metadata": {
                    "name": metadata.name,
                    "description": metadata.description,
                },
                "data": response.data,  # Direct data, not nested
                "ui_updates": response.ui_updates  # Direct UI updates
            }
        except Exception as e:
            logger.error(f"Error executing step: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def _validate_session(self, session_id: str) -> Dict[str, Any]:
        """Validate and return a session."""
        session = self.session_manager.get_session(session_id)
        if not session:
            raise HTTPException(404, "Session expired or invalid")
        return session

    def _validate_handler(self, workflow_id: str, step_id: str) -> Tuple[Callable, WorkflowStepMetadata]:
        """Validate and return a step handler with metadata."""
        handler_info = self.registry.get_step_handler(workflow_id, step_id)
        if not handler_info:
            raise HTTPException(404, "Step handler not found")
        return handler_info

    async def _handle_step_execution(
        self,
        data: Dict[str, Any],
        session: Dict[str, Any],
        handler: Callable
    ) -> WorkflowStepResponse:
        """Handle step execution or component event dispatching."""
        form_data = data.get("form_data", {})
        # Try to handle component event
        context = session.get("context", {})
        logger.debug(f"Session context being passed to handler: {context}")
        response = await self._try_handle_component_event(form_data)
        # Fall back to step handler if no event was handled
        if not response:
            # Execute step with context
            merged_data = {**data, "context": session.get("context", {})}
            result = await handler(merged_data)
            response = ensure_workflow_step_response(result)
        return response

    async def _try_handle_component_event(self, form_data: Dict[str, Any]) -> Optional[WorkflowStepResponse]:
        """Try to handle a component event and return a response if successful."""
        if not form_data or not isinstance(form_data, dict):
            return None
        component_key = form_data.get("component_key")
        event_name = form_data.get("event_name") or form_data.get("action")
        if not (event_name and component_key):
            return None

        try:
            logger.debug(f"Attempting to dispatch event {event_name} for component {component_key}")
            event_result = await self.event_dispatcher.dispatch_event(
                component_key=component_key,
                event_name=event_name,
                event_data=form_data
            )
            if not event_result:
                return None
            logger.debug(f"Event handler succeeded, result: {event_result}")
            return ensure_workflow_step_response(event_result)
        except EventDispatchError as e:
            logger.warning(f"Event dispatch failed, falling back to step handler: {str(e)}")
            return None

    async def _handle_step_transition(
        self,
        workflow_id: str,
        response: WorkflowStepResponse,
        session: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """Handle transition to next step."""
        session["current_step"] = response.next_step_id
        next_handler_info = self.registry.get_step_handler(workflow_id, response.next_step_id)
        if not next_handler_info:
            logger.warning(f"Next step handler not found: {response.next_step_id}")
            self.session_manager.update_session(session_id, session)
            return {
                "session_id": session_id,
                "data": response.data,
                "ui_updates": response.ui_updates,
                "next_step_id": response.next_step_id
            }
        # Prepare next step
        _, next_metadata = next_handler_info
        next_components = prepare_components_with_context(
            next_metadata.ui_components,
            session["context"]
        )
        # Update session
        self.session_manager.update_session(session_id, session)
        # Return response with next step info
        return {
            "session_id": session_id,
            "metadata": {
                "name": next_metadata.name,
                "description": next_metadata.description,
            },
            "data": response.data,
            "ui_updates": response.ui_updates,
            "next_step_id": response.next_step_id,
            "next_step": {
                "metadata": {
                    "name": next_metadata.name,
                    "description": next_metadata.description,
                },
                "ui_components": next_components
            }
        }

# =========================================================================
# ROUTE CONFIGURATION
# =========================================================================

def configure_workflow_routes(app: FastAPI, registry: WorkflowRegistry, agent_slug: str):
    """Configure workflow routes with enhanced state management."""
    workflow_manager = WorkflowExecutionManager(registry, session_manager)
    logger.debug(f"Configuring workflow routes for agent: {agent_slug}")
    for workflow_id, workflow in registry.workflows.items():
        logger.debug(f"Setting up routes for workflow: {workflow_id}")
        # Register workflow start endpoint
        register_workflow_start_endpoint(
            app, workflow_id, workflow, registry, agent_slug
        )
        # Register step execution endpoints
        register_workflow_step_endpoints(
            app, workflow_id, workflow_manager, agent_slug
        )
        # Register preview endpoint
        register_workflow_preview_endpoint(
            app, workflow_id, workflow_manager, agent_slug
        )

def register_workflow_start_endpoint(
    app: FastAPI,
    workflow_id: str,
    workflow: Workflow,
    registry: WorkflowRegistry,
    agent_slug: str
):
    """Register the workflow start endpoint."""
    @app.post(f"/agents/{agent_slug}/workflows/{workflow_id}/start",
             description=f"Start the {workflow.name} workflow")
    async def start_workflow(
        workflow_id: str = workflow_id,
        data: Dict[str, Any] = None
    ):
        try:
            if data is None:
                data = {}
            # Validate workflow
            workflow = registry.get_workflow(workflow_id)
            if not workflow:
                raise HTTPException(404, "Workflow not found")

            # Create session
            session_id = session_manager.create_session()
            session = {
                "workflow_id": workflow_id,
                "current_step": workflow.initial_step,
                "context": data.get("context", {})
            }
            # Get initial step handler
            handler_info = registry.get_step_handler(workflow_id, workflow.initial_step)
            if not handler_info:
                raise HTTPException(404, "Initial step handler not found")
            handler, metadata = handler_info
            # Execute initial step
            response = await handler(data)
            normalized_response = ensure_workflow_step_response(response)
            # Update session
            session["context"].update(normalized_response.context_updates)
            session_manager.update_session(session_id, session)
            # Prepare UI components
            ui_components_data = []
            if metadata.ui_components:
                ui_components_data = prepare_components_with_context(
                    metadata.ui_components,
                    session["context"]
                )
            # Return response
            return {
                "session_id": session_id,
                "metadata": {
                    "name": metadata.name,
                    "description": metadata.description,
                    "ui_components": ui_components_data
                },
                "data": normalized_response.data,
                "ui_updates": normalized_response.ui_updates,
                "next_step_id": normalized_response.next_step_id
            }
        except Exception as e:
            logger.error(f"Error starting workflow: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

def register_workflow_step_endpoints(
    app: FastAPI,
    workflow_id: str,
    workflow_manager: WorkflowExecutionManager,
    agent_slug: str
):
    """Register step execution endpoints."""
    @app.post(f"/agents/{agent_slug}/workflows/{workflow_id}/steps/{{step_id}}")
    async def execute_step(
        step_id: str,
        data: Dict[str, Any],
        curr_workflow_id: str = workflow_id
    ):
        return await workflow_manager.process_workflow_step(curr_workflow_id, step_id, data)

def register_workflow_preview_endpoint(
    app: FastAPI,
    workflow_id: str,
    workflow_manager: WorkflowExecutionManager,
    agent_slug: str
):
    """Register preview endpoint."""
    from pydantic import BaseModel
    class PreviewRequest(BaseModel):
        session_id: str

    @app.post(
        f"/agents/{agent_slug}/workflows/{workflow_id}/steps/{{step_id}}/preview",
        description="Preview a workflow step's UI components"
    )
    async def preview_workflow_step(
        step_id: str,
        request: PreviewRequest,
        current_workflow_id: str = workflow_id
    ):
        """Preview a workflow step's UI components with session context."""
        logger.debug(f"Preview request for {current_workflow_id}/{step_id} with session {request.session_id}")
        return await workflow_manager.preview_workflow_step(
            workflow_id=current_workflow_id,
            step_id=step_id,
            session_id=request.session_id
        )

async def preview_step(workflow_id: str, step_id: str, session_id: str):
    """Helper function to preview a workflow step."""
    # Extract agent name from workflow ID
    parts = workflow_id.split("_")
    agent_name = parts[0] if len(parts) > 0 else workflow_id
    # Try to get the registry
    registry = get_workflow_registry(agent_name)
    if not registry:
        # Try any registry with this workflow
        for name, reg in agent_workflow_registries.items():
            if workflow_id in reg.workflows:
                registry = reg
                break
    if not registry:
        raise HTTPException(404, f"No registry found for workflow {workflow_id}")
    workflow_manager = WorkflowExecutionManager(registry, session_manager)
    return await workflow_manager.preview_workflow_step(workflow_id, step_id, session_id)