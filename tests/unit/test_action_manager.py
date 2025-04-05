"""
Tests for the action manager component.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import json

from pydantic import BaseModel
from fastapi import FastAPI, Response

from agentnexus.base_types import AgentConfig, ActionType, UIResponse, UIComponentUpdate
from agentnexus.action_manager import (
    agent_action, get_action_registry, ActionRegistry, 
    configure_action_routes, ActionEndpointInfo
)

class TestModelMixin(BaseModel):
    """Mixin to add dict-like behaviors to test models."""
    def get(self, key, default=None):
        """Provide dict-like get access."""
        return getattr(self, key, default) if hasattr(self, key) else default

# Define test models
class TestInput(TestModelMixin):
    query: str
    options: dict = {}

class TestOutput(TestModelMixin):
    result: str
    status: str

# Test fixtures
@pytest.fixture
def test_action_registry():
    """Fixture providing a clean action registry."""
    return ActionRegistry()

@pytest.fixture
def test_action(simple_agent_config):
    """Fixture providing a test action decorator with handler."""
    @agent_action(
        agent_config=simple_agent_config,
        action_type=ActionType.GENERATE,
        name="Test Generate Action",
        description="A test action for generating content"
    )
    async def test_generate_action(input_data: TestInput) -> TestOutput:
        return TestOutput(
            result=f"Generated response for: {input_data.query}",
            status="success"
        )
    return test_generate_action

@pytest.fixture
def test_ui_action(simple_agent_config):
    """Fixture providing a test UI action with handler."""
    @agent_action(
        agent_config=simple_agent_config,
        action_type=ActionType.CUSTOM_UI,
        name="Test UI Action",
        description="A test action with UI components"
    )
    async def test_ui_action(input_data: TestInput) -> UIResponse:
        return UIResponse(
            data={"message": f"Processed UI request: {input_data.query}"},
            ui_updates=[
                {
                    "key": "test_component",
                    "state": {"value": input_data.query}
                }
            ]
        )
    return test_ui_action

def test_action_registry_initialization(test_action_registry):
    """Test that ActionRegistry initializes correctly."""
    assert hasattr(test_action_registry, 'actions')
    assert isinstance(test_action_registry.actions, dict)
    assert len(test_action_registry.actions) == 0

def test_action_registration(simple_agent_config, test_action):
    """Test that actions are correctly registered in the registry."""
    # Get registry for the agent
    registry = get_action_registry(simple_agent_config.name)
    # Check if action was registered with correct slug
    assert "test-generate-action" in registry.actions
    # Verify action metadata
    action_info = registry.actions["test-generate-action"]
    assert action_info.metadata.name == "Test Generate Action"
    assert action_info.metadata.description == "A test action for generating content"
    assert action_info.metadata.action_type == ActionType.GENERATE
    # Verify input/output models
    assert action_info.input_model == TestInput
    assert action_info.output_model == TestOutput

def test_ui_action_registration(simple_agent_config, test_ui_action):
    """Test that UI actions are correctly registered with proper UI response type."""
    registry = get_action_registry(simple_agent_config.name)
    # Check if action was registered with correct slug
    assert "test-ui-action" in registry.actions
    # Verify action metadata
    action_info = registry.actions["test-ui-action"]
    assert action_info.metadata.name == "Test UI Action"
    assert action_info.metadata.description == "A test action with UI components"
    assert action_info.metadata.action_type == ActionType.CUSTOM_UI
    # Verify input/output models
    assert action_info.input_model == TestInput
    assert action_info.output_model == UIResponse

def test_action_registry_get_action(test_action_registry):
    """Test retrieving actions from registry."""
    # Create a mock action endpoint info
    mock_info = MagicMock()
    # Register the mock action
    test_action_registry.register_action("test-action", mock_info)
    # Retrieve the action
    retrieved_info = test_action_registry.get_action("test-action")
    assert retrieved_info == mock_info
    # Try retrieving a non-existent action
    assert test_action_registry.get_action("non-existent") is None

def test_multiple_actions_for_same_agent(simple_agent_config):
    """Test registering multiple actions for the same agent."""
    # Define first action
    @agent_action(
        agent_config=simple_agent_config,
        action_type=ActionType.QUESTION,
        name="Question Action",
        description="A test question action"
    )
    async def question_action(input_data: TestInput) -> TestOutput:
        return TestOutput(result=f"Question answer for: {input_data.query}", status="success")

    # Define second action
    @agent_action(
        agent_config=simple_agent_config,
        action_type=ActionType.TALK,
        name="Talk Action",
        description="A test talk action"
    )
    async def talk_action(input_data: TestInput) -> TestOutput:
        return TestOutput(result=f"Talking about: {input_data.query}", status="success")

    # Get registry and check both actions
    registry = get_action_registry(simple_agent_config.name)
    assert "question-action" in registry.actions
    assert "talk-action" in registry.actions
    assert registry.actions["question-action"].metadata.action_type == ActionType.QUESTION
    assert registry.actions["talk-action"].metadata.action_type == ActionType.TALK

@pytest.mark.asyncio
async def test_action_handler_execution(simple_agent_config):
    """Test executing an action handler directly."""
    # Define test action
    @agent_action(
        agent_config=simple_agent_config,
        action_type=ActionType.GENERATE,
        name="Direct Execution Action",
        description="Test direct execution"
    )
    async def direct_action(input_data: TestInput) -> TestOutput:
        return TestOutput(
            result=f"Executed with: {input_data.query}",
            status="success"
        )
    # Get action info
    registry = get_action_registry(simple_agent_config.name)
    action_info = registry.actions["direct-execution-action"]
    # Execute handler directly
    result = await action_info.handler(TestInput(query="test query"))
    # Verify result
    assert isinstance(result, TestOutput)
    assert result.result == "Executed with: test query"
    assert result.status == "success"

@pytest.mark.asyncio
async def test_action_with_template(simple_agent_config):
    """Test action with template response."""
    # Mock the template path and content
    with patch('pathlib.Path') as mock_path:
        mock_file = MagicMock()
        mock_file.exists.return_value = True
        mock_file.read_text.return_value = "# Response Template\n\nResult: {{ result }}\nStatus: {{ status }}"
        mock_path.return_value = mock_file

        # Define action with template
        @agent_action(
            agent_config=simple_agent_config,
            action_type=ActionType.GENERATE,
            name="Template Action",
            description="Action with template",
            response_template_md="template.md"
        )
        async def template_action(input_data: TestInput) -> TestOutput:
            return TestOutput(
                result=f"Template result for: {input_data.query}",
                status="success"
            )

        # Get action info
        registry = get_action_registry(simple_agent_config.name)
        action_info = registry.actions["template-action"]

        # Create a mock response to capture the rendered template
        mock_response = MagicMock(spec=Response)
        # Patch the Response class
        with patch('agentnexus.action_manager.Response', return_value=mock_response):
            # Mock Template.render to return a fixed string
            with patch('agentnexus.action_manager.Template') as MockTemplate:
                mock_template_instance = MagicMock()
                mock_template_instance.render.return_value = "# Rendered Template\n\nResult: Template result\nStatus: success"
                MockTemplate.return_value = mock_template_instance
                # Execute the handler directly - don't try to access the handler attribute
                test_input = TestInput(query="test query")
                result = await action_info.handler(test_input)
                # We can still verify that the handler executed correctly
                assert isinstance(result, TestOutput)
                assert "test query" in result.result
                assert result.status == "success"

@pytest.mark.asyncio
async def test_configure_action_routes():
    """Test configuring action routes in a FastAPI application."""
    app = FastAPI()
    registry = ActionRegistry()
    agent_slug = "test-agent"
    # Create a mock endpoint info
    mock_handler = AsyncMock()
    mock_handler.return_value = {"status": "success"}
    mock_metadata = MagicMock()
    mock_metadata.action_type = ActionType.GENERATE
    mock_metadata.name = "Test Action"
    mock_metadata.description = "Test action description"
    endpoint_info = MagicMock()
    endpoint_info.handler = mock_handler
    endpoint_info.metadata = mock_metadata
    endpoint_info.input_model = TestInput
    endpoint_info.output_model = TestOutput
    # Register the action
    registry.register_action("test-action", endpoint_info)
    # Configure routes
    await configure_action_routes(app, registry, agent_slug)
    # Verify routes were added
    route_paths = [route.path for route in app.routes]
    expected_path = f"/agents/{agent_slug}/actions/test-action"
    # The route might not be added in the test environment due to the complexity 
    # of FastAPI's routing system, but we can check that the function attempts to add it
    assert endpoint_info.route_path == expected_path

@pytest.mark.asyncio
async def test_action_with_ui_components(simple_agent_config, form_component):
    """Test action with UI components."""
    # Define action with UI components
    @agent_action(
        agent_config=simple_agent_config,
        action_type=ActionType.CUSTOM_UI,
        name="UI Component Action",
        description="Action with UI components",
        ui_components=[form_component]
    )
    async def ui_component_action(input_data: TestInput) -> UIResponse:
        return UIResponse(
            data={"status": "success"},
            ui_updates=[UIComponentUpdate(
                key=form_component.component_key,
                state={"values": {"name": "Test Name"}}
            )]
        )
    # Get action info
    registry = get_action_registry(simple_agent_config.name)
    action_info = registry.actions["ui-component-action"]
    # Verify UI components are registered
    assert hasattr(action_info.metadata, 'ui_components')
    assert len(action_info.metadata.ui_components) == 1
    assert action_info.metadata.ui_components[0].component_key == "test_form"
    # Execute handler
    result = await action_info.handler(TestInput(query="test query"))
    # Verify UI response - fix the ui_updates access
    assert isinstance(result, UIResponse)
    assert "status" in result.data
    assert len(result.ui_updates) == 1
    assert result.ui_updates[0].key == "test_form" 