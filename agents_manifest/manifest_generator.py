# manifest_generator.py
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import re
from loguru import logger
from agents_manifest.base_types import Capability, ActionType, WorkflowStepType
from agents_manifest.action_manager import ActionRegistry, configure_action_routes, agent_action, get_action_registry
from agents_manifest.workflow_manager import (
    WorkflowRegistry, configure_workflow_routes, workflow_step,
    Workflow, WorkflowStep, WorkflowTransition, WorkflowDataMapping
)

def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

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

    def generate_manifest(self) -> Dict[str, Any]:
        """Generate complete agent manifest."""
        logger.debug(f"Generating manifest for agent: {self.name}")
        logger.debug(f"Action registry contents: {self.action_registry.actions}")
        actions = []
        for action_slug, endpoint_info in self.action_registry.actions.items():
            logger.debug(f"Processing action: {action_slug}")
            logger.debug(f"Endpoint info: {endpoint_info.metadata}")
            action_data = {
                "name": endpoint_info.metadata.name,
                "slug": action_slug,
                "actionType": endpoint_info.metadata.action_type.value,
                "path": f"/agents/{self.slug}/actions/{action_slug}",
                "method": "POST",
                "inputSchema": endpoint_info.input_model.model_json_schema(),
                "outputSchema": endpoint_info.output_model.model_json_schema(),
                "description": endpoint_info.metadata.description,
                "isMDResponseEnabled": endpoint_info.metadata.response_template_md is not None,
                "examples": endpoint_info.examples or {"validRequests": []}
            }
            
            if endpoint_info.metadata.response_template_md:
                action_data["responseTemplateMD"] = endpoint_info.metadata.response_template_md
                
            actions.append(action_data)
        logger.debug(f"Generated {len(actions)} actions for manifest")

        workflows_data = []
        for workflow in self.workflows:
            workflow_data = workflow.model_dump()
            workflow_data["endpoints"] = {
                "start": {
                    "path": f"/agents/{self.slug}/workflows/{workflow.id}/start",
                    "method": "POST",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"},
                            "context": {"type": "object"}
                        },
                        "required": ["message"]
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string"},
                            "step_data": {"type": "object"}
                        },
                        "required": ["session_id"]
                    },
                    "description": f"Start the {workflow.name} workflow"
                },
                "step": {
                    "path": f"/agents/{self.slug}/workflows/{workflow.id}/steps/{{step_id}}",
                    "method": "POST"
                }
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
    """Configure a FastAPI app as an agent."""
    logger.debug(f"=== Configuring agent: {name} ===")
    # Create agent registry
    registry = AgentRegistry(
        base_url=base_url,
        name=name,
        version=version,
        description=description,
        capabilities=capabilities,
        workflows=workflows or []
    )

    # Transfer actions from global registry to agent-specific registry
    _action_registry = get_action_registry()
    logger.debug(f"Global registry actions: {len(_action_registry.actions)}")
    for action_slug, endpoint_info in _action_registry.actions.items():
        logger.debug(f"Transferring action {action_slug} to agent registry")
        registry.action_registry.register_action(action_slug, endpoint_info)
    
    # Clear global registry for next agent
    logger.debug(f"Agent registry actions after transfer: {len(registry.action_registry.actions)}")
    
    # Store in global registry
    agent_registries[registry.slug] = registry
    
    # Add registry to app state
    if not hasattr(app, 'state'):
        setattr(app, 'state', type('State', (), {}))
    app.state.agent_registry = registry

    # Configure routes
    logger.debug(f"Configuring routes for {len(registry.action_registry.actions)} actions")
    configure_workflow_routes(app, registry.workflow_registry, registry.slug)
    configure_action_routes(app, registry.action_registry, registry.slug)
    _action_registry.actions.clear()
    
    return app

def setup_agent_routes(app: FastAPI):
    """Set up agent-related routes."""
    templates_dir = Path(__file__).parent / "templates"
    print(templates_dir)

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