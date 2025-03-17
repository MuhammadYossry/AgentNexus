"""
Tests for UI components and event handling system.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import inspect

from fast_agents.ui_components import (
    UIComponent, TableComponent, FormComponent, CodeEditorComponent,
    MarkdownComponent, TableColumn, FormField, ComponentEventType,
    EventContext
)
from fast_agents.event_dispatcher import (
    ComponentEventDispatcher, global_event_dispatcher, EventDispatchError
)

def test_ui_component_base_class():
    """Test the base UIComponent class."""
    # Create a minimal UIComponent
    component = UIComponent(
        component_type="test_type",
        component_key="test_key",
        title="Test Title"
    )
    # Check basic properties
    assert component.component_type == "test_type"
    assert component.component_key == "test_key"
    assert component.title == "Test Title"
    assert hasattr(component, "metadata")
    assert hasattr(component, "component_state")
    assert hasattr(component, "supported_events")
    assert hasattr(component, "event_handlers")
    # Check empty collections
    assert component.metadata == {}
    assert component.component_state == {}
    assert component.supported_events == []
    assert component.event_handlers == {}

def test_markdown_component(markdown_component):
    """Test the MarkdownComponent."""
    assert markdown_component.component_type == "markdown"
    assert markdown_component.component_key == "test_markdown"
    assert markdown_component.title == "Test Markdown"
    assert markdown_component.markdown_content == "# Test Heading\nThis is a test markdown content."

def test_form_component(form_component):
    """Test the FormComponent."""
    assert form_component.component_type == "form"
    assert form_component.component_key == "test_form"
    assert form_component.title == "Test Form"
    assert len(form_component.form_fields) == 2
    # Check first field
    field1 = form_component.form_fields[0]
    assert field1.field_name == "name"
    assert field1.label_text == "Name"
    assert field1.field_type == "text"
    assert field1.is_required is True
    # Check second field with validation
    field2 = form_component.form_fields[1]
    assert field2.field_name == "email"
    assert field2.validation_rules is not None
    assert "pattern" in field2.validation_rules

def test_code_editor_component(code_editor_component):
    """Test the CodeEditorComponent."""
    assert code_editor_component.component_type == "code_editor"
    assert code_editor_component.component_key == "test_editor"
    assert code_editor_component.title == "Test Editor"
    assert code_editor_component.programming_language == "python"
    assert "def test_function()" in code_editor_component.editor_content
    assert code_editor_component.is_readonly is False

def test_table_component(table_component):
    """Test the TableComponent."""
    assert table_component.component_type == "table"
    assert table_component.component_key == "test_table"
    assert table_component.title == "Test Table"
    assert len(table_component.columns) == 3
    assert len(table_component.table_data) == 3
    # Check columns
    assert table_component.columns[0].field_name == "id"
    assert table_component.columns[0].header_text == "ID"
    # Check data
    assert table_component.table_data[0]["id"] == 1
    assert table_component.table_data[0]["name"] == "Item 1"
    assert table_component.table_data[0]["value"] == 100

def test_component_serialization(form_component):
    """Test component serialization to dict excludes event handlers."""
    # Convert to dict
    component_dict = form_component.model_dump()
    # Check basic fields
    assert component_dict["component_type"] == "form"
    assert component_dict["component_key"] == "test_form"
    assert len(component_dict["form_fields"]) == 2
    # Check event handlers are excluded
    assert "event_handlers" not in component_dict
    # Check JSON serialization works
    import json
    json_str = json.dumps(component_dict)
    assert isinstance(json_str, str)
    assert "test_form" in json_str

def test_component_event_handler_registration(form_component):
    """Test registering event handlers for components."""
    # Define a test handler
    async def test_submit_handler(**kwargs):
        return {"status": "success", "data": data}
    # Set valid event types for the component
    FormComponent.valid_event_types = ["submit", "validation"]
    # Register handler
    form_component.register_event_handler("submit", test_submit_handler)
    # Check handler registration
    assert "submit" in form_component.event_handlers
    assert form_component.event_handlers["submit"] == test_submit_handler
    assert "submit" in form_component.supported_events

def test_component_invalid_event_type(form_component):
    """Test that registering an invalid event type raises ValueError."""
    # Define a test handler
    async def test_handler(action, data, **kwargs):
        return {"status": "success", "data": data}
    # Set valid event types for the component
    FormComponent.valid_event_types = ["submit", "validation"]
    # Check that invalid event raises ValueError
    with pytest.raises(ValueError):
        form_component.register_event_handler("invalid_event_type", test_handler)

@pytest.mark.asyncio
async def test_component_event_handling(form_component):
    """Test handling events directly on components."""
    # Define a test handler
    async def test_submit_handler(**kwargs):
        print(kwargs)
        return {"status": "success", "form_data": kwargs}
    # Set valid event types and register handler
    FormComponent.valid_event_types = ["submit"]
    form_component.register_event_handler("submit", test_submit_handler)
    # Trigger event
    event_data = {
        "values": {"name": "Test User", "email": "test@example.com"}
    }
    result = await form_component.handle_event("submit", **event_data)
    assert result["status"] == "success"


def test_event_context():
    """Test the EventContext class."""
    # Create a simple event context
    context = EventContext(
        context_type="row",
        data={"id": 1, "name": "Test Item"}
    )
    # Check properties
    assert context.context_type == "row"
    assert context.data["id"] == 1
    assert context.data["name"] == "Test Item"

def test_event_dispatcher_initialization():
    """Test initialization of ComponentEventDispatcher."""
    # Create dispatcher
    dispatcher = ComponentEventDispatcher()
    # Check initialization
    assert hasattr(dispatcher, "registered_components")
    assert hasattr(dispatcher, "event_handlers")
    assert isinstance(dispatcher.registered_components, dict)
    assert isinstance(dispatcher.event_handlers, dict)

def test_event_dispatcher_singleton():
    """Test that ComponentEventDispatcher is a singleton."""
    # Create two dispatcher instances
    dispatcher1 = ComponentEventDispatcher()
    dispatcher2 = ComponentEventDispatcher()
    # Check they are the same instance
    assert dispatcher1 is dispatcher2
    # Check the global instance
    assert global_event_dispatcher is dispatcher1

def test_component_registration_in_dispatcher(form_component):
    """Test registering components with the event dispatcher."""
    # Create dispatcher
    dispatcher = ComponentEventDispatcher()
    # Register component
    dispatcher.register_component(form_component)
    # Check registration
    assert form_component.component_key in dispatcher.registered_components
    assert dispatcher.registered_components[form_component.component_key] == form_component

def test_event_handler_registration_in_dispatcher():
    """Test registering event handlers in the dispatcher."""
    # Create dispatcher
    dispatcher = ComponentEventDispatcher()
    # Define a test handler
    async def test_submit_handler(action, data, **kwargs):
        return {"status": "success", "data": data}
    # Register handler directly in dispatcher
    dispatcher.register_event_handler(
        component_key="test_component",
        event_name="submit",
        handler=test_submit_handler
    )
    # Check registration
    assert "test_component" in dispatcher.event_handlers
    assert "submit" in dispatcher.event_handlers["test_component"]
    assert dispatcher.event_handlers["test_component"]["submit"] == test_submit_handler

@pytest.mark.asyncio
async def test_event_dispatching(form_component):
    """Test dispatching events through the dispatcher."""
    # Create dispatcher
    dispatcher = ComponentEventDispatcher()

    # Define a test handler
    async def test_submit_handler(**kwargs):
        return {"status": "success", "form_data": kwargs}

    # Set valid event types and register handler
    FormComponent.valid_event_types = ["submit"]
    form_component.register_event_handler("submit", test_submit_handler)
    # Register component
    dispatcher.register_component(form_component)
    # Dispatch event
    event_data = {
        "action": "submit",
        "component_key": form_component.component_key,
        "values": {"name": "Test User", "email": "test@example.com"}
    }
    result = await dispatcher.dispatch_event(
        component_key=form_component.component_key,
        event_name="submit",
        event_data=event_data
    )
    # Check result
    assert result["status"] == "success"

@pytest.mark.asyncio
async def test_event_dispatch_error_handling():
    """Test error handling in event dispatching."""
    pass

@pytest.mark.asyncio
async def test_component_event_parameter_filtering():
    """Test that event handlers only receive parameters they accept."""
    # Create a form component
    form = FormComponent(
        component_key="test_filter_form",
        title="Test Form",
        form_fields=[
            FormField(
                field_name="name",
                label_text="Name",
                field_type="text"
            )
        ]
    )
    # Define a handler with specific parameters
    async def specific_handler(action, values, component_key):
        return {
            "action": action,
            "component": component_key,
            "values_received": values
        }

    # Set valid event types and register handler
    FormComponent.valid_event_types = ["submit"]
    form.register_event_handler("submit", specific_handler)
    # Create event context with extra parameters
    event_data = {
        "action": "submit",
        "component_key": form.component_key,
        "values": {"name": "Test User"},
        "extra_param1": "value1",
        "extra_param2": "value2"
    }
    # Handle event
    result = await form.handle_event("submit", **event_data)
    # Check that only specified parameters were passed
    assert result["action"] == "submit"
    assert result["component"] == form.component_key
    assert result["values_received"] == {"name": "Test User"}
    # Extra params should not be in the result
    assert not any(key in result for key in ["extra_param1", "extra_param2"])

@pytest.mark.asyncio
async def test_table_row_click_event(table_component):
    """Test table row click event handling."""
    pass

@pytest.mark.asyncio
async def test_code_editor_format_event(code_editor_component):
    """Test code editor format event."""
    pass

def test_component_event_type_enum():
    """Test the ComponentEventType enum for standardized event types."""
    # Check common event types
    assert ComponentEventType.SUBMIT == "submit"
    assert ComponentEventType.ROW_CLICK == "row_click"
    assert ComponentEventType.CLICK == "click"
    assert ComponentEventType.FORMAT == "format"
    assert ComponentEventType.SAVE == "save"