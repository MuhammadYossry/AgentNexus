# manifest_generator.py
from typing import List, Optional, Dict, Any, Callable, Type
from pathlib import Path
import inspect
from loguru import logger
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
from jinja2 import Template

from agentnexus.base_types import (
    Capability, ActionType, WorkflowStepType, AgentConfig, slugify,
    Workflow, WorkflowStep, WorkflowTransition, WorkflowDataMapping,
    UIResponse
)
from agentnexus.action_manager import ActionRegistry, get_action_registry, ActionEndpointInfo
from agentnexus.workflow_manager import WorkflowRegistry, configure_workflow_routes, get_workflow_registry
from agentnexus.event_dispatcher import global_event_dispatcher, EventDispatchError

class AgentManager:
    """Manages the lifecycle and configuration of multiple agents within a FastAPI application.

    This class provides a centralized mechanism for adding, configuring,
    and setting up agents with their associated routes and capabilities.
    It simplifies the process of integrating multiple agents into a single
    application by handling their initialization and route configuration.

    Attributes:
        base_url (str): The base URL where agent services are hosted
        agents (List): Collection of agents to be configured

    Example:
        >>> manager = AgentManager(base_url="http://localhost:9200")
        >>> manager.add_agent(flight_agent_app)
        >>> manager.setup_agents(fastapi_app)
    """
    def __init__(self, base_url: str):
        """Initialize the AgentManager with a base URL for agent services.
        Args:
            base_url (str):  The base URL where agent services will be hosted
        """
        self.base_url = base_url
        self.agents = []

    def add_agent(self, agent):
        """Add an agent to the manager for later setup and configuration.

        Args:
            agent: The agent configuration to be added to the manager
        """
        self.agents.append(agent)

    def setup_agents(self, app: FastAPI):
        """Configure and set up all added agents in the provided FastAPI application.
        This method iterates through all added agents, configuring their
        routes, capabilities, and workflows, and then sets up global agent routes.

        Args:
            app (FastAPI): The FastAPI application instance to configure agents for
        """
        for agent in self.agents:
            configure_agent(
                app=app,
                base_url=self.base_url,
                name=agent.name,
                version=agent.version,
                description=agent.description,
                capabilities=agent.capabilities,
                workflows=agent.workflows
            )
        setup_agent_routes(app)

class AgentRegistry:
    """Comprehensive registry for managing agent configurations, capabilities, and metadata.

    This class provides a centralized mechanism for storing and generating
    detailed manifests for agents, including their actions, workflows,
    and associated metadata. It supports introspection and automatic
    documentation generation for agent capabilities.

    Attributes:
        base_url (str): Base URL for the agent services
        name (str): Name of the agent
        slug (str): URL-friendly version of the agent name
        version (str): Version of the agent
        description (str): Detailed description of the agent
        capabilities (List[Capability]): List of agent capabilities
        workflows (List[Workflow]): List of defined agent workflows
        action_registry (ActionRegistry): Registry for agent actions
        workflow_registry (WorkflowRegistry): Registry for agent workflows
    Example:
        >>> registry = AgentRegistry(
        ...     base_url="http://localhost:9200",
        ...     name="Flight Assistant",
        ...     version="1.0.0",
        ...     description="Advanced flight booking agent",
        ...     capabilities=[...],
        ...     workflows=[...]
        ... )
    """
    def __init__(
        self,
        base_url: str,
        name: str,
        version: str,
        description: str,
        capabilities: List[Capability],
        workflows: Optional[List[Workflow]] = None
    ):
        """Initialize the AgentRegistry with comprehensive agent details.
        Args:
            base_url (str): Base URL for the agent services
            name (str): Name of the agent
            version (str): Version of the agent
            description (str): Detailed description of the agent
            capabilities (List[Capability]): List of agent capabilities
            workflows (Optional[List[Workflow]], optional): List of agent workflows
        """
        self.base_url = base_url.rstrip('/')
        self.name = name
        self.slug = slugify(name)
        self.version = version
        self.description = description
        self.capabilities = capabilities
        self.workflows = workflows or []
        self.action_registry = ActionRegistry()
        self.workflow_registry = WorkflowRegistry()

    def _get_input_model(self, handler: Callable) -> Optional[Type[BaseModel]]:
        """Extract the input model from a handler function's signature.
        Attempts to find a Pydantic model used for input validation
        by inspecting the function's parameter annotations.
        Args:
            handler (Callable): The function to extract the input model from

        Returns:
            Optional[Type[BaseModel]]: The input validation model if found
        """
        sig = inspect.signature(handler)
        for param in sig.parameters.values():
            if hasattr(param.annotation, 'model_json_schema'):
                return param.annotation
        return None

    def _get_output_model(self, handler: Callable) -> Optional[Type[BaseModel]]:
        """Extract the output model from a handler function's return annotation.
        Attempts to find a Pydantic model used for output validation
        by inspecting the function's return type annotation.

        Args:
            handler (Callable): The function to extract the output model from

        Returns:
            Optional[Type[BaseModel]]: The output validation model if found
        """
        return_annotation = handler.__annotations__.get('return')
        if hasattr(return_annotation, '__origin__'):
            return return_annotation.__args__[0]
        return return_annotation if hasattr(return_annotation, 'model_json_schema') else None

    def generate_manifest(self) -> Dict[str, Any]:
        """Generate a comprehensive manifest describing the agent's capabilities.

        Creates a detailed JSON representation of the agent, including:
        - Agent metadata (name, version, description)
        - Capabilities
        - Actions with input/output schemas
        - Workflow definitions
        - Endpoint information

        Returns:
            Dict[str, Any]: A comprehensive manifest describing the agent

        Notes:
            - Automatically generates schemas for actions and workflows
            - Includes UI component information
            - Supports dynamic template loading
        """
        logger.debug(f"Generating manifest for agent: {self.name}")
        logger.debug(f"Action registry contents: {self.action_registry.actions if self.action_registry else None}")
        # Process actions
        actions = []
        if self.action_registry:
            for action_slug, endpoint_info in self.action_registry.actions.items():
                logger.debug(f"Processing action: {action_slug}")
                logger.debug(f"Endpoint info: {endpoint_info.metadata}")
                template_content = None
                if endpoint_info.metadata.response_template_md:
                    try:
                        template_path = Path(endpoint_info.metadata.response_template_md)
                        if not template_path.is_absolute():
                            # Try relative to project root first
                            project_root = Path(__file__).parent.parent
                            template_path = Path(project_root, "agents_manifest", "templates", template_path.name)

                        if template_path.exists():
                            template_content = template_path.read_text()
                            logger.debug(f"Loaded template from {template_path}")
                        else:
                            logger.warning(f"Template not found at {template_path}")
                    except Exception as e:
                        logger.error(f"Error loading template: {str(e)}")
                action_data = {
                    "name": endpoint_info.metadata.name,
                    "slug": action_slug,
                    "actionType": endpoint_info.metadata.action_type.value,
                    "path": f"/agents/{self.slug}/actions/{action_slug}",
                    "method": "POST",
                    "inputSchema": endpoint_info.input_model.model_json_schema(),
                    "outputSchema": endpoint_info.output_model.model_json_schema(),
                    "description": endpoint_info.metadata.description,
                    "isMDResponseEnabled": template_content is not None,
                    "examples": endpoint_info.examples or {"validRequests": []}
                }
                if template_content:
                    action_data["responseTemplateMD"] = template_content
                if hasattr(endpoint_info.metadata, 'ui_components') and endpoint_info.metadata.ui_components:
                    action_data["uiComponents"] = []
                    for comp in endpoint_info.metadata.ui_components:
                        component_data = comp.dict(exclude_none=True)
                        # Add supported events to the manifest
                        if hasattr(comp, 'supported_events'):
                            component_data["supported_events"] = list(comp.event_handlers.keys())
                        if hasattr(comp, 'event_handlers'):
                            component_data["availableEvents"] = list(comp.event_handlers.keys())
                        action_data["uiComponents"].append(component_data)
                actions.append(action_data)
        logger.debug(f"Generated {len(actions)} actions for manifest")
        workflows_data = []
        logger.debug(f"self.workflow_registry: {self.workflow_registry}")
        # First check the workflow registry
        if self.workflow_registry and hasattr(self.workflow_registry, 'workflows') and self.workflow_registry.workflows:
            logger.debug(f"Using workflow_registry.workflows: {list(self.workflow_registry.workflows.keys())}")
            for workflow_id, workflow in self.workflow_registry.workflows.items():
                logger.debug(f"Processing workflow from registry: {workflow_id}")
                workflow_data = workflow.model_dump()
                workflow_data["endpoints"] = {}
                # Process each step in the workflow
                for step in workflow.steps:
                    logger.debug(f"Processing step: {step.id}")
                    step_handler_info = self.workflow_registry.get_step_handler(workflow.id, step.id)
                    if step_handler_info:
                        # Process step endpoint data
                        handler, step_metadata = step_handler_info
                        endpoint_path = f"/agents/{self.slug}/workflows/{workflow.id}/steps/{step.id}"
                        step_endpoint = {
                            "path": endpoint_path,
                            "method": "POST",
                            "description": step_metadata.description or f"Execute step {step.id}"
                        }
                        # Add input/output schemas
                        input_model = self._get_input_model(handler)
                        if input_model:
                            step_endpoint["input_schema"] = input_model.model_json_schema()
                        output_model = self._get_output_model(handler)
                        if output_model:
                            step_endpoint["output_schema"] = output_model.model_json_schema()
                        # Add UI components
                        if hasattr(step_metadata, 'ui_components') and step_metadata.ui_components:
                            step_endpoint["uiComponents"] = []
                            for comp in step_metadata.ui_components:
                                component_data = comp.dict(exclude_none=True)
                                # Add supported events to the manifest
                                if hasattr(comp, 'supported_events'):
                                    component_data["supported_events"] = list(comp.event_handlers.keys())
                                step_endpoint["uiComponents"].append(component_data)
                        workflow_data["endpoints"][f"step_{step.id}"] = step_endpoint
                        # Add start endpoint if this is the initial step
                        if step.id == workflow.initial_step:
                            start_endpoint = {
                                "path": f"/agents/{self.slug}/workflows/{workflow.id}/start",
                                "method": "POST",
                                "description": f"Start the {workflow.name} workflow"
                            }
                            # Copy the same schema and UI components
                            if 'input_schema' in step_endpoint:
                                start_endpoint["input_schema"] = step_endpoint["input_schema"]
                            if 'output_schema' in step_endpoint:
                                start_endpoint["output_schema"] = step_endpoint["output_schema"]
                            if 'uiComponents' in step_endpoint:
                                start_endpoint["uiComponents"] = step_endpoint["uiComponents"]

                            workflow_data["endpoints"]["start"] = start_endpoint
                    else:
                        logger.warning(f"No handler found for step {step.id} in workflow {workflow.id}")
                workflows_data.append(workflow_data)
                logger.debug(f"Added workflow data for {workflow_id}")
        # Fall back to self.workflows if the registry didn't have workflows
        elif self.workflows:
            logger.debug(f"Falling back to self.workflows: {[w.id for w in self.workflows]}")
            for workflow in self.workflows:
                logger.debug(f"Processing fallback workflow: {workflow.id}")
                workflow_data = workflow.model_dump()
                workflow_data["endpoints"] = {}  # Basic endpoints
                workflows_data.append(workflow_data)
        # Generate the final manifest
        manifest = {
            "name": self.name,
            "slug": self.slug,
            "version": self.version,
            "type": "external",
            "description": self.description,
            "baseUrl": self.base_url,
            "metaInfo": {},
            "capabilities": [cap.model_dump() for cap in self.capabilities],
            "actions": actions,
            "workflows": workflows_data
        }
        logger.debug(f"Generated manifest with {len(workflows_data)} workflows")
        return manifest

def configure_agent_routes(
   app: FastAPI,
   agent_slug: str,
   action_registry: ActionRegistry,
   workflow_registry: Optional[WorkflowRegistry] = None
):
    """Configure both action and workflow routes."""
    logger.debug(f"Configuring routes for agent: {agent_slug}")

    # Action routes
    for action_slug, endpoint_info in action_registry.actions.items():
        route_path = f"/agents/{agent_slug}/actions/{action_slug}"
        endpoint_info.route_path = route_path
        logger.debug(f"Setting up action route: {route_path}")

        async def action_handler(
            request_data: endpoint_info.input_model,
            ei: ActionEndpointInfo = endpoint_info
        ):
            """Handle component actions with both new event system and legacy action system."""
            try:
                # Check for component actions/events
                if ei.metadata.ui_components and hasattr(request_data, 'action') and request_data.action:
                    # Get the target component key
                    target_key = getattr(request_data, 'component_key', 'main_editor')
                    logger.debug(f"Handling component action: {request_data.action} for {target_key}")
                    # Prepare data for dispatching
                    data_dict = request_data.model_dump() if hasattr(request_data, 'dict') else {}
                    try:
                        logger.debug(f"Attempting to dispatch component event via global_dispatcher")
                        event_handlers = global_event_dispatcher.event_handlers.get(target_key, {})
                        logger.debug(f"Available event handlers: {event_handlers.keys()}")
                        # First, try to handle as an event (new style)
                        try:
                            # Map common action names to event names
                            event_name = request_data.action
                            if request_data.action == 'select_seat':
                                event_name = 'row_click'
                            elif request_data.action == 'search_seats':
                                event_name = 'submit'
                            result = await global_event_dispatcher.dispatch_event(
                                component_key=target_key,
                                event_name=event_name,
                                event_data=data_dict
                            )
                            logger.debug(f"Event dispatch result: {result}")
                            # Convert to UIResponse if needed
                            if result and not isinstance(result, UIResponse):
                                if hasattr(result, 'dict'):
                                    result = UIResponse(data=result.dict(), ui_updates=[])
                                else:
                                    result = UIResponse(data=result, ui_updates=[])
                            return result
                        except EventDispatchError as e:
                            # Fall back to old action dispatch if event dispatch fails
                            logger.debug(f"Event dispatch failed, trying action dispatch: {str(e)}")
                            # Only try action dispatch if we have the attribute
                            if hasattr(global_event_dispatcher, 'dispatch_action'):
                                try:
                                    result = await global_event_dispatcher.dispatch_action(
                                        component_key=target_key,
                                        action_name=request_data.action,
                                        action_data=data_dict
                                    )
                                    logger.debug(f"Action dispatch result: {result}")
                                    # Convert to UIResponse if needed
                                    if result and not isinstance(result, UIResponse):
                                        if hasattr(result, 'dict'):
                                            result = UIResponse(data=result.dict(), ui_updates=[])
                                        else:
                                            result = UIResponse(data=result, ui_updates=[])
                                    return result
                                except Exception as e2:
                                    logger.warning(f"Action dispatch also failed: {str(e2)}")
                            else:
                                logger.warning(f"No action dispatch method available")
                    except EventDispatchError as e:
                        # Fall back to original handler if dispatching fails
                        logger.warning(f"Event dispatch failed: {str(e)}")
                # Fall back to original handler
                logger.debug(f"Falling back to original handler")
                result = await ei.handler(request_data)
                # Handle response template
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

        app.add_api_route(
            route_path,
            action_handler,
            methods=["POST"],
            response_model=endpoint_info.output_model
        )

    # Workflow routes
    if workflow_registry and workflow_registry.workflows:
        for workflow in workflow_registry.workflows.values():
            workflow_registry.register_workflow(workflow)
            logger.debug(f"Registered workflow in registry: {workflow.id}")
            logger.debug(f"Setting up workflow: {workflow.id}")

            # Start route
            start_path = f"/agents/{agent_slug}/workflow/{workflow.id}/start"
            logger.debug(f"Registering workflow start: {start_path}")

            async def workflow_start_handler(data: Dict[str, Any]):
                try:
                    handler_info = workflow_registry.get_step_handler(workflow.id, workflow.initial_step)
                    if not handler_info:
                        msg = f"Initial step handler not found for workflow {workflow.id}"
                        logger.error(msg)
                        raise HTTPException(404, msg)
                    handler, _ = handler_info
                    return await handler(data)
                except Exception as e:
                    logger.error(f"Error in workflow start: {str(e)}")
                    raise HTTPException(status_code=500, detail=str(e))
            app.add_api_route(
                start_path,
                workflow_start_handler,
                methods=["POST"]
            )
           # Step routes
            for step in workflow.steps:
                if step.type != WorkflowStepType.END:
                    step_path = f"/agents/{agent_slug}/workflow/{workflow.id}/steps/{step.id}"
                    logger.debug(f"Registering step route: {step_path}")
                    async def step_handler(
                        data: Dict[str, Any],
                        step_id: str = step.id,
                        wf_id: str = workflow.id
                    ):
                        try:
                            handler_info = workflow_registry.get_step_handler(wf_id, step_id)
                            if not handler_info:
                                msg = f"Handler not found for step {step_id}"
                                logger.error(msg)
                                raise HTTPException(404, msg)
                            handler, _ = handler_info
                            return await handler(data)
                        except Exception as e:
                            logger.error(f"Error in step handler: {str(e)}")
                            raise HTTPException(status_code=500, detail=str(e))

                    app.add_api_route(
                        step_path,
                        step_handler,
                        methods=["POST"]
                    )
# Global registry storage
agent_registries: Dict[str, AgentRegistry] = {}
def configure_agent(
    app: FastAPI,
    base_url: str,
    name: str,
    version: str,
    description: str,
    capabilities: List[Capability],
    workflows: Optional[List[Workflow]] = None,
) -> FastAPI:
    """Configure an agent with both action and workflow routes."""
    logger.debug(f"=== Configuring agent: {name} ===")
    # Get registries FIRST before creating the AgentRegistry
    action_registry = get_action_registry(name)
    workflow_registry = get_workflow_registry(name)  # Always get the registry, not conditionally
    # Create agent registry
    registry = AgentRegistry(base_url, name, version, description, capabilities, workflows)
    agent_slug = registry.slug
    # Get action registry first
    action_registry = get_action_registry(name)
    registry.action_registry = action_registry
    # Get workflow registry and explicitly register workflows
    workflow_registry = get_workflow_registry(name)
    registry.workflow_registry = workflow_registry
    # First, register workflows if they exist
    if workflows:
        for workflow in workflows:
            logger.debug(f"Registering workflow: {workflow.id}")
            workflow_registry.register_workflow(workflow)
            # Look for steps that might be already registered
            for step in workflow.steps:
                step_handler = workflow_registry.get_step_handler(workflow.id, step.id)
                if step_handler:
                    handler, metadata = step_handler
                    if hasattr(metadata, 'ui_components') and metadata.ui_components:
                        for component in metadata.ui_components:
                            logger.debug(f"Registering workflow component {component.component_key} from step {step.id}")
                            # Register the component with the global dispatcher
                            global_event_dispatcher.register_component(component)
                            # Register event handlers if present
                            if hasattr(component, 'event_handlers'):
                                for event_name, handler in component.event_handlers.items():
                                    logger.debug(f"Registering event handler {event_name} for {component.component_key}")
                                    global_event_dispatcher.register_event_handler(
                                        component_key=component.component_key,
                                        event_name=event_name,
                                        handler=handler
                                    )
    # Register UI components from actions
    for action_slug, endpoint_info in action_registry.actions.items():
        if hasattr(endpoint_info.metadata, 'ui_components'):
            for component in endpoint_info.metadata.ui_components:
                logger.debug(f"Registering action component {component.component_key} from {action_slug}")
                # Register the component with the global dispatcher
                global_event_dispatcher.register_component(component)
                # Register event handlers if present
                if hasattr(component, 'event_handlers'):
                    for event_name, handler in component.event_handlers.items():
                        logger.debug(f"Registering event handler {event_name} for {component.component_key}")
                        global_event_dispatcher.register_event_handler(
                            component_key=component.component_key,
                            event_name=event_name,
                            handler=handler
                        )
    # Configure routes
    configure_agent_routes(app, agent_slug, action_registry, workflow_registry)
    if workflow_registry and workflow_registry.workflows:
        configure_workflow_routes(app, workflow_registry, agent_slug)
    # Store the registry
    agent_registries[agent_slug] = registry
    logger.debug(f"Registered routes: {[route.path for route in app.routes]}")
    logger.debug(f"Registered event handlers: {global_event_dispatcher.event_handlers}")
    return app

def setup_agent_routes(app: FastAPI):
    """Set up agent-related routes."""
    templates_dir = Path(__file__).parent / "templates"

    @app.get("/agents.json")
    async def get_agents_manifest():
        agents = []
        for registry in agent_registries.values():
            agents.append({
                "name": registry.name,
                "slug": registry.slug,
                "version": registry.version,
                "manifestUrl": f"{registry.base_url}/agents/{registry.slug}.json",
                "dashboardUrl": f"{registry.base_url}/agents/{registry.slug}"
            })
        return {"agents": agents}

    @app.get("/agents", response_class=HTMLResponse)
    async def get_agents_dashboard():
        try:
            return (templates_dir / "agents.html").read_text()
        except Exception as e:
            raise HTTPException(404, "Agents dashboard template not found")

    @app.get("/agents/{agent_slug}.json")
    async def get_agent_manifest(agent_slug: str):
        if agent_slug not in agent_registries:
            raise HTTPException(404, "Agent not found")
        return agent_registries[agent_slug].generate_manifest()

    @app.get("/agents/{agent_slug}", response_class=HTMLResponse)
    async def get_agent_dashboard(agent_slug: str):
        try:
            return (templates_dir / "agent.html").read_text()
        except Exception as e:
            raise HTTPException(404, "Agent dashboard template not found")