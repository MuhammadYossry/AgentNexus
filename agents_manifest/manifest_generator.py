# manifest_generator.py
from typing import List, Optional, Dict, Any, Callable, Type
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
from jinja2 import Environment, FileSystemLoader, Template
from pathlib import Path
import sys
import inspect 
from loguru import logger
from agents_manifest.base_types import (
    Capability, ActionType, WorkflowStepType, AgentConfig, slugify,
    Workflow, WorkflowStep, WorkflowTransition, WorkflowDataMapping
)
from agents_manifest.action_manager import ActionRegistry, agent_action, get_action_registry, ActionEndpointInfo
from agents_manifest.workflow_manager import WorkflowRegistry, configure_workflow_routes, workflow_step, get_workflow_registry


class AgentManager:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.agents = []

    def add_agent(self, agent):
        self.agents.append(agent)

    def setup_agents(self, app: FastAPI):
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
    """Registry for agents and their capabilities."""
    def __init__(
        self, 
        base_url: str,
        name: str,
        version: str,
        description: str,
        capabilities: List[Capability],
        workflows: Optional[List[Workflow]] = None
    ):
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
        """Extract input model from handler signature."""
        sig = inspect.signature(handler)
        for param in sig.parameters.values():
            if hasattr(param.annotation, 'model_json_schema'):
                return param.annotation
        return None

    def _get_output_model(self, handler: Callable) -> Optional[Type[BaseModel]]:
        """Extract output model from handler return annotation."""
        return_annotation = handler.__annotations__.get('return')
        if hasattr(return_annotation, '__origin__'):
            return return_annotation.__args__[0]
        return return_annotation if hasattr(return_annotation, 'model_json_schema') else None

    def generate_manifest(self) -> Dict[str, Any]:
        """Generate complete agent manifest."""
        logger.debug(f"Generating manifest for agent: {self.name}")
        logger.debug(f"Action registry contents: {self.action_registry.actions}")
        actions = []
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
                        template_path = project_root / "agents_manifest" / "templates" / template_path.name
                    
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
            actions.append(action_data)
        logger.debug(f"Generated {len(actions)} actions for manifest")
        workflows_data = []
        for workflow in self.workflows:
            workflow_data = workflow.model_dump()
            workflow_data["endpoints"] = {}
            # Get workflow handlers and metadata
            for step in workflow.steps:
                step_handler = self.workflow_registry.get_step_handler(workflow.id, step.id)
                if step_handler:
                    handler, metadata = step_handler
                    if step.id == workflow.initial_step:
                        # Extract schemas from decorated function signature
                        input_model = self._get_input_model(handler)
                        output_model = self._get_output_model(handler)
                        workflow_data["endpoints"]["start"] = {
                            "path": f"/agents/{self.slug}/workflows/{workflow.id}/start",
                            "method": "POST",
                            "input_schema": input_model.model_json_schema() if input_model else {},
                            "output_schema": output_model.model_json_schema() if output_model else {},
                            "description": f"Start the {workflow.name} workflow"
                        }
                    else:
                        input_model = self._get_input_model(handler)
                        output_model = self._get_output_model(handler)
                        workflow_data["endpoints"][f"step_{step.id}"] = {
                            "path": f"/agents/{self.slug}/workflows/{workflow.id}/steps/{step.id}",
                            "method": "POST",
                            "input_schema": input_model.model_json_schema() if input_model else {},
                            "output_schema": output_model.model_json_schema() if output_model else {},
                            "description": metadata.description
                        }
            workflows_data.append(workflow_data)

        return {
            "name": self.name,
            "slug": self.slug,
            "version": self.version,
            "type": "external",
            "description": self.description,
            "baseUrl": self.base_url,
            "metaInfo": {},
            "capabilities": [cap.model_dump() for cap in self.capabilities],
            "actions": actions,
            "workflows": workflows_data if workflows_data else []
        }

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
           try:
               result = await ei.handler(request_data)
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
    # Create agent registry
    registry = AgentRegistry(base_url, name, version, description, capabilities, workflows)
    agent_slug = registry.slug

    # Get registries
    action_registry = get_action_registry(name)
    registry.action_registry = action_registry
    workflow_registry = get_workflow_registry(name) if workflows else None
    configure_agent_routes(app, agent_slug, action_registry, workflow_registry)
    if workflow_registry and workflows:
        for workflow in workflows:
            workflow_registry.register_workflow(workflow)
            logger.debug(f"Registering workflow: {workflow.id}")

        configure_workflow_routes(app, workflow_registry, agent_slug)
        registry.workflow_registry = workflow_registry

    agent_registries[agent_slug] = registry
    # action_registry.actions.clear()
    
    logger.debug(f"Registered routes: {[route.path for route in app.routes]}")
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