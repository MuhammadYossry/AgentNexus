"""
Common test fixtures and utilities for FastAgents tests.
"""
import asyncio
import os
import json
import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pathlib import Path

from fast_agents.base_types import (
    AgentConfig, Capability, Workflow, WorkflowStep, WorkflowStepType
)
from fast_agents.ui_components import (
    FormComponent, MarkdownComponent, CodeEditorComponent, 
    TableComponent, FormField, TableColumn
)
from fast_agents.manifest_generator import AgentManager
from fast_agents.session_manager import SessionManager

# ============================================================================
# Core Fixtures
# ============================================================================

@pytest.fixture
def test_app():
    """Fixture providing a clean FastAPI application for testing."""
    return FastAPI()

@pytest.fixture
def test_client(test_app):
    """Fixture providing a TestClient for API testing."""
    return TestClient(test_app)

# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture(scope="function", autouse=True)
def mock_redis():
    """Mock Redis for all tests to prevent actual Redis connections."""
    redis_mock = MagicMock()
    redis_mock.ping.return_value = True
    redis_mock.get.return_value = json.dumps({
        "created_at": datetime.now().isoformat(),
        "context": {"test_key": "test_value"}
    })
    redis_mock.set.return_value = True
    redis_mock.delete.return_value = 1
    redis_mock.exists.return_value = True
    with patch('redis.Redis', return_value=redis_mock):
        yield redis_mock

@pytest.fixture
def mock_uuid():
    """Mock uuid4 to return predictable values for testing."""
    with patch('uuid.uuid4') as mock:
        mock.return_value = "00000000-0000-0000-0000-000000000000"
        yield mock

@pytest.fixture(autouse=True)
def reset_registries():
    """Reset all registries between tests to prevent test pollution."""
    from fast_agents.action_manager import agent_registries
    from fast_agents.workflow_manager import agent_workflow_registries
    from fast_agents.manifest_generator import agent_registries as manifest_registries

    # Store original values
    original_action_registries = dict(agent_registries)
    original_workflow_registries = dict(agent_workflow_registries)
    original_manifest_registries = dict(manifest_registries)
    # Clear registries
    agent_registries.clear()
    agent_workflow_registries.clear()
    manifest_registries.clear()
    yield
    # Restore original values
    agent_registries.update(original_action_registries)
    agent_workflow_registries.update(original_workflow_registries)
    manifest_registries.update(original_manifest_registries)

@pytest.fixture(autouse=True)
def reset_event_dispatcher():
    """Reset the event dispatcher between tests."""
    from fast_agents.event_dispatcher import global_event_dispatcher
    # Store original registered components and handlers
    original_components = dict(global_event_dispatcher.registered_components)
    original_handlers = dict(global_event_dispatcher.event_handlers)
    # Clear dispatcher
    global_event_dispatcher.registered_components.clear()
    global_event_dispatcher.event_handlers.clear()
    yield
    # Restore original values
    global_event_dispatcher.registered_components.update(original_components)
    global_event_dispatcher.event_handlers.update(original_handlers)

# ============================================================================
# Agent Configuration Fixtures
# ============================================================================
@pytest.fixture
def simple_capability():
    """Fixture providing a simple capability."""
    return Capability(
        skill_path=["Testing", "Simple"],
        metadata={"feature": "testing"}
    )

@pytest.fixture
def advanced_capability():
    """Fixture providing a more advanced capability."""
    return Capability(
        skill_path=["Testing", "Advanced"],
        metadata={
            "features": ["advanced testing", "complex scenarios"],
            "languages": ["python", "javascript"]
        }
    )

@pytest.fixture
def simple_agent_config(simple_capability):
    """Fixture providing a basic agent configuration."""
    return AgentConfig(
        name="Simple Test Agent",
        version="1.0.0",
        description="A simple test agent for unit testing",
        capabilities=[simple_capability]
    )

@pytest.fixture
def workflow_agent_config(advanced_capability):
    """Fixture providing an agent config with workflows."""
    workflow = Workflow(
        id="test_workflow",
        name="Test Workflow",
        description="A test workflow for testing",
        steps=[
            WorkflowStep(id="step1", type=WorkflowStepType.UI_STEP),
            WorkflowStep(id="step2", type=WorkflowStepType.UI_STEP),
            WorkflowStep(id="step3", type=WorkflowStepType.END)
        ],
        initial_step="step1"
    )
    
    return AgentConfig(
        name="Workflow Test Agent",
        version="1.0.0",
        description="An agent with workflows for testing",
        capabilities=[advanced_capability],
        workflows=[workflow]
    )

# ============================================================================
# UI Component Fixtures
# ============================================================================
@pytest.fixture
def markdown_component():
    """Fixture providing a markdown component."""
    return MarkdownComponent(
        component_key="test_markdown",
        title="Test Markdown",
        markdown_content="# Test Heading\nThis is a test markdown content."
    )

@pytest.fixture
def form_component():
    """Fixture providing a form component."""
    return FormComponent(
        component_key="test_form",
        title="Test Form",
        form_fields=[
            FormField(
                field_name="name",
                label_text="Name",
                field_type="text",
                is_required=True
            ),
            FormField(
                field_name="email",
                label_text="Email",
                field_type="text",
                is_required=True,
                validation_rules={"pattern": r"^[\w.-]+@[\w.-]+\.\w+$"}
            )
        ]
    )

@pytest.fixture
def code_editor_component():
    """Fixture providing a code editor component."""
    return CodeEditorComponent(
        component_key="test_editor",
        title="Test Editor",
        programming_language="python",
        editor_content="def test_function():\n    return 'Hello, World!'"
    )

@pytest.fixture
def table_component():
    """Fixture providing a table component."""
    return TableComponent(
        component_key="test_table",
        title="Test Table",
        columns=[
            TableColumn(field_name="id", header_text="ID"),
            TableColumn(field_name="name", header_text="Name"),
            TableColumn(field_name="value", header_text="Value")
        ],
        table_data=[
            {"id": 1, "name": "Item 1", "value": 100},
            {"id": 2, "name": "Item 2", "value": 200},
            {"id": 3, "name": "Item 3", "value": 300}
        ]
    )

# ============================================================================
# Test Model Fixtures
# ============================================================================

@pytest.fixture
def pydantic_models():
    """Fixture providing common pydantic models for testing."""
    from pydantic import BaseModel

    class TestInput(BaseModel):
        query: str
        options: dict = {}

    class TestOutput(BaseModel):
        result: str
        status: str

    class WorkflowStepInput(BaseModel):
        session_id: str
        context: dict = {}
        form_data: dict = {}

    return {
        "TestInput": TestInput,
        "TestOutput": TestOutput,
        "WorkflowStepInput": WorkflowStepInput
    }

# ============================================================================
# Session Management Fixtures
# ============================================================================

@pytest.fixture
def session_manager(mock_redis):
    """Fixture providing a session manager with mocked Redis."""
    manager = SessionManager()
    manager.redis = mock_redis
    manager.session_ttl = 3600
    return manager

@pytest.fixture
def sample_session_data():
    """Fixture providing sample session data."""
    return {
        "created_at": datetime.now().isoformat(),
        "workflow_id": "test_workflow",
        "current_step": "step1",
        "step_history": ["step1"],
        "context": {
            "test_key": "test_value",
            "code": "def test():\n    pass",
            "language": "python"
        },
        "last_updated": datetime.now().isoformat()
    }

# ============================================================================
# Utility Functions
# ============================================================================

def async_return(value):
    """Helper function to create an async function that returns a value."""
    async def _async_return(*args, **kwargs):
        return value
    return _async_return