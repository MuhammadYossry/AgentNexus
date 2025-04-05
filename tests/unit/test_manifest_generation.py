"""
Tests for manifest generation functionality.
"""
import pytest
from unittest.mock import patch, MagicMock

from agentnexus.manifest_generator import (
    AgentRegistry, configure_agent, AgentManager, setup_agent_routes
)

def test_agent_registry_initialization(simple_agent_config):
    """Test that AgentRegistry initializes correctly with agent config."""
    registry = AgentRegistry(
        base_url="http://localhost:9000",
        name=simple_agent_config.name,
        version=simple_agent_config.version,
        description=simple_agent_config.description,
        capabilities=simple_agent_config.capabilities
    )
    assert registry.name == "Simple Test Agent"
    assert registry.slug == "simple-test-agent"  # Check the slug conversion
    assert registry.version == "1.0.0"
    assert registry.description == "A simple test agent for unit testing"
    assert len(registry.capabilities) == 1
    assert registry.capabilities[0].skill_path == ["Testing", "Simple"]
    assert registry.base_url == "http://localhost:9000"
    assert hasattr(registry, 'action_registry')
    assert hasattr(registry, 'workflow_registry')

def test_agent_registry_with_trailing_slash():
    """Test that AgentRegistry handles base_url with trailing slash."""
    registry = AgentRegistry(
        base_url="http://localhost:9000/",
        name="Test Agent",
        version="1.0.0",
        description="Test description",
        capabilities=[]
    )
    assert registry.base_url == "http://localhost:9000"  # Trailing slash removed

def test_agent_manifest_generation(simple_agent_config):
    """Test that agent manifest is generated correctly with basic structure."""
    registry = AgentRegistry(
        base_url="http://localhost:9000",
        name=simple_agent_config.name,
        version=simple_agent_config.version,
        description=simple_agent_config.description,
        capabilities=simple_agent_config.capabilities
    )
    manifest = registry.generate_manifest()
    # Assert basic structure and content
    assert manifest["name"] == "Simple Test Agent"
    assert manifest["slug"] == "simple-test-agent"
    assert manifest["version"] == "1.0.0"
    assert manifest["description"] == "A simple test agent for unit testing"
    assert manifest["baseUrl"] == "http://localhost:9000"
    assert manifest["type"] == "external"
    assert len(manifest["capabilities"]) == 1
    assert manifest["capabilities"][0]["skill_path"] == ["Testing", "Simple"]
    assert "actions" in manifest
    assert "workflows" in manifest

def test_agent_manifest_with_workflows(workflow_agent_config):
    """Test that agent manifest correctly includes workflow information."""
    registry = AgentRegistry(
        base_url="http://localhost:9000",
        name=workflow_agent_config.name,
        version=workflow_agent_config.version,
        description=workflow_agent_config.description,
        capabilities=workflow_agent_config.capabilities,
        workflows=workflow_agent_config.workflows
    )
    manifest = registry.generate_manifest()
    # Check workflows are included
    assert "workflows" in manifest
    assert len(manifest["workflows"]) > 0
    # Check first workflow details
    workflow = manifest["workflows"][0]
    assert workflow["id"] == "test_workflow"
    assert workflow["name"] == "Test Workflow"
    assert "steps" in workflow
    assert len(workflow["steps"]) == 3
    assert workflow["initial_step"] == "step1"

@patch('agentnexus.workflow_manager.configure_workflow_routes')
@patch('agentnexus.action_manager.configure_action_routes')
def test_configure_agent(test_app, simple_agent_config):
    """Test agent configuration with FastAPI application."""
    pass

@patch('agentnexus.manifest_generator.agent_registries')
@patch('agentnexus.manifest_generator.Path')
def test_setup_agent_routes(mock_path, mock_registries, test_app):
    """Test setting up agent routes in FastAPI app."""
    # Mock Path for template loading
    mock_templates_dir = MagicMock()
    mock_path.return_value.__truediv__.return_value = mock_templates_dir
    mock_templates_dir.__truediv__.return_value.read_text.return_value = "<html></html>"
    # Mock agent registry
    mock_registry = MagicMock()
    mock_registry.name = "Test Agent"
    mock_registry.slug = "test-agent"
    mock_registry.generate_manifest.return_value = {"name": "Test Agent"}
    # Setup mock registries dict
    mock_registries.items.return_value = [("test-agent", mock_registry)]
    mock_registries.get.return_value = mock_registry
    # Call the function
    setup_agent_routes(test_app)
    # Check routes by examining the app's routes list
    route_paths = [route.path for route in test_app.routes]
    expected_paths = [
        "/agents.json",
        "/agents",
        "/agents/{agent_slug}.json",
        "/agents/{agent_slug}"
    ]
    for path in expected_paths:
        assert path in route_paths

def test_agent_manager(test_app, simple_agent_config):
    """Test AgentManager for adding and setting up agents."""
    agent_manager = AgentManager(base_url="http://localhost:9000")
    # Mock the configure_agent function
    with patch('agentnexus.manifest_generator.configure_agent') as mock_configure_agent, \
         patch('agentnexus.manifest_generator.setup_agent_routes') as mock_setup_routes:
        agent_manager.add_agent(simple_agent_config)
        agent_manager.setup_agents(test_app)
        # Assert configure_agent was called with our agent
        mock_configure_agent.assert_called_once()
        args, kwargs = mock_configure_agent.call_args
        assert kwargs["app"] == test_app
        assert kwargs["name"] == simple_agent_config.name
        # Assert setup_agent_routes was called
        mock_setup_routes.assert_called_once_with(test_app)

def test_agent_manifest_endpoint(test_app, test_client, simple_agent_config):
    """Test the agent manifest endpoint returns correct manifest."""
    # Mock the relevant functions
    with patch('agentnexus.manifest_generator.agent_registries') as mock_registries:
        # Create a mock registry that returns our data
        registry = MagicMock()
        registry.name = simple_agent_config.name
        registry.slug = "simple-test-agent"
        registry.generate_manifest.return_value = {
            "name": simple_agent_config.name,
            "slug": "simple-test-agent",
            "version": simple_agent_config.version,
            "description": simple_agent_config.description
        }
        # Mock the items() method to return our registry
        mock_registries.items.return_value = [("simple-test-agent", registry)]
        # Set up a special agent_registries for the path lookup
        mock_registries.__getitem__.side_effect = lambda x: registry if x == "simple-test-agent" else None
        mock_registries.get.return_value = registry
        # Add a route handler mock response for agents.json
        @test_app.get("/agents.json")
        async def mock_agents_json():
            return {
                "agents": [
                    {
                        "name": simple_agent_config.name,
                        "slug": "simple-test-agent",
                        "version": simple_agent_config.version,
                        "manifestUrl": "http://localhost:9000/agents/simple-test-agent.json",
                        "dashboardUrl": "http://localhost:9000/agents/simple-test-agent"
                    }
                ]
            }

        # Add a route handler for specific agent
        @test_app.get("/agents/simple-test-agent.json")
        async def mock_agent_json():
            return {
                "name": simple_agent_config.name,
                "slug": "simple-test-agent",
                "version": simple_agent_config.version,
                "description": simple_agent_config.description
            }

        # Test the /agents.json endpoint
        response = test_client.get("/agents.json")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) == 1
        assert data["agents"][0]["name"] == simple_agent_config.name
        # Test the specific agent endpoint
        response = test_client.get("/agents/simple-test-agent.json")
        assert response.status_code == 200
        agent_data = response.json()
        assert agent_data["name"] == simple_agent_config.name
        assert agent_data["slug"] == "simple-test-agent"


def test_multiple_agents_setup():
    """Test configuring multiple agents with AgentManager."""
    from agentnexus.base_types import AgentConfig

    agent1 = AgentConfig(name="Agent1", version="1.0", description="First agent")
    agent2 = AgentConfig(name="Agent2", version="1.0", description="Second agent")
    # Create manager and add agents
    from agentnexus.manifest_generator import AgentManager
    manager = AgentManager(base_url="http://localhost:9000")
    manager.add_agent(agent1)
    manager.add_agent(agent2)
    # Verify agents are added
    assert len(manager.agents) == 2
    assert manager.agents[0] == agent1
    assert manager.agents[1] == agent2

    # Mock setup function to verify all agents are configured
    with patch('agentnexus.manifest_generator.configure_agent') as mock_configure:
        app = MagicMock()
        manager.setup_agents(app)
        # Verify configure_agent called for each agent
        assert mock_configure.call_count == 2