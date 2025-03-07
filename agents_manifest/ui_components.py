"""
UI component system with integrated event handlers for improved developer experience.
"""
from typing import Dict, Any, Callable, Optional, List, ClassVar, Type, Union
from pydantic import BaseModel, Field, model_validator
import inspect
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ComponentEventType(str, Enum):
    """Standard event types for UI components with descriptive naming."""
    CONTENT_CHANGE = "content_change"
    SUBMIT = "submit"
    ROW_ACTION = "row_action"
    SORT = "sort"
    PAGINATION = "pagination" 
    ACTION = "action"
    VALIDATION = "validation"
    FIELD_CHANGE = "field_change"
    FORMAT = "format"
    LINT = "lint"
    SAVE = "save"


class UIComponent(BaseModel):
    """
    Base class for UI components with integrated event handling.
    Provides a foundation for creating UI components with self-contained
    event handling logic, improving code organization and readability.
    """
    component_type: str
    component_key: str = Field(..., min_length=1)
    title: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    component_state: Dict[str, Any] = Field(default_factory=dict)
    # Dictionary of event handlers, excluded from serialization
    event_handlers: Dict[str, Callable] = Field(default_factory=dict, exclude=True)
    # Class variable defining valid event types for component subclasses
    valid_event_types: ClassVar[List[str]] = []

    model_config = {
        "arbitrary_types_allowed": True
    }

    def register_event_handler(self, event_type: str, handler_function: Callable) -> None:
        """
        Register an event handler for this component.

        Args:
            event_type: The type of event to handle
            handler_function: The function to call when the event occurs

        Raises:
            ValueError: If the event type is not valid for this component
        """
        if event_type not in self.valid_event_types:
            valid_events = ", ".join(self.valid_event_types)
            raise ValueError(
                f"Invalid event type '{event_type}' for {self.component_type} component. "
                f"Valid events are: {valid_events}"
            )
        self.event_handlers[event_type] = handler_function
        logger.debug(f"Registered handler for {self.component_key}.{event_type}")

    def get_event_handler(self, event_type: str) -> Optional[Callable]:
        """
        Get the handler function for a specific event type.

        Args:
            event_type: The type of event to get handler for
  
        Returns:
            The handler function or None if not registered
        """
        return self.event_handlers.get(event_type)
    
    @model_validator(mode='after')
    def setup_event_handlers(self) -> 'UIComponent':
        """
        Set up handlers from component attributes after initialization.

        This method should be overridden by subclasses to collect handlers
        from specific attributes like on_submit, on_content_change, etc.
        """
        return self


class ActionHandlerRegistry(BaseModel):
    """
    Registry for mapping action names to handler functions.

    Provides a central registry for components that support dynamic
    action-based events, allowing handlers to be registered by name.
    """
    handler_functions: Dict[str, Callable] = Field(default_factory=dict)
    default_handler_function: Optional[Callable] = None
    
    model_config = {
        "arbitrary_types_allowed": True
    }
    
    def get_handler_for_action(self, action_name: str) -> Optional[Callable]:
        """
        Get the appropriate handler for an action.

        Args:
            action_name: The name of the action to handle

        Returns:
            The handler function, or the default handler if not found
        """
        return self.handler_functions.get(action_name, self.default_handler_function)
    
    def register_action_handler(self, action_name: str, handler_function: Callable) -> None:
        """
        Register a handler for a specific action.

        Args:
            action_name: The name of the action to handle
            handler_function: The function to handle the action
        """
        self.handler_functions[action_name] = handler_function


class ActionHandlerMap:
    """
    Map of action names to handler functions.
    
    This class provides a simpler alternative to ActionHandlerRegistry
    for defining action handlers directly when creating a component.
    """
    def __init__(self, handlers: Dict[str, Callable], default_handler: Optional[Callable] = None):
        """
        Initialize the action handler map.
        
        Args:
            handlers: Dictionary mapping action names to handler functions
            default_handler: Optional default handler for actions not in handlers
        """
        self.handlers = handlers
        self.default_handler = default_handler


class TableColumn(BaseModel):
    """
    Configuration for a column in a table component.
    
    Provides detailed customization options for table columns,
    including data binding, display properties, and sorting.
    """
    field_name: str
    header_text: str
    sortable: bool = True
    column_width: Optional[str] = None


class TableComponent(UIComponent):
    """
    Table component with integrated event handling.
    
    Displays tabular data with support for sorting, pagination,
    and row actions. Handlers can be attached directly to the component.
    """
    component_type: str = "table"
    columns: List[TableColumn]
    table_data: List[Dict[str, Any]]
    available_actions: List[str] = Field(default_factory=list)
    enable_pagination: bool = True
    rows_per_page: int = 10
    # Event handlers as component attributes
    on_row_action: Optional[Callable] = Field(default=None, exclude=True)
    on_sort: Optional[Callable] = Field(default=None, exclude=True)
    on_pagination: Optional[Callable] = Field(default=None, exclude=True)
    # Define valid event types for table components
    valid_event_types: ClassVar[List[str]] = [
        ComponentEventType.ROW_ACTION, 
        ComponentEventType.SORT, 
        ComponentEventType.PAGINATION
    ]

    @model_validator(mode='after')
    def setup_event_handlers(self) -> 'TableComponent':
        """Set up handlers from component attributes."""
        # Initialize handlers dictionary if needed
        if not hasattr(self, 'event_handlers'):
            self.event_handlers = {}
        # Register handlers from attributes
        if self.on_row_action:
            self.event_handlers[ComponentEventType.ROW_ACTION] = self.on_row_action
        if self.on_sort:
            self.event_handlers[ComponentEventType.SORT] = self.on_sort
        if self.on_pagination:
            self.event_handlers[ComponentEventType.PAGINATION] = self.on_pagination
        return self


class CodeEditorComponent(UIComponent):
    """
    Code editor component with integrated event handling.
    
    Provides a rich code editing experience with syntax highlighting,
    formatting, and other development features. Handlers can be attached
    directly to the component.
    """
    component_type: str = "code_editor"
    programming_language: str
    editor_content: str = ""
    editor_theme: Optional[str] = "vs-dark"
    is_readonly: bool = False
    editor_height: str = "400px"
    available_actions: List[str] = Field(default_factory=list)
    editor_options: Dict[str, Any] = Field(default_factory=dict)
    # Action handlers for dynamic actions
    action_handler_registry: Optional[ActionHandlerRegistry] = Field(default=None, exclude=True)
    # Event handlers as component attributes
    on_content_change: Optional[Callable] = Field(default=None, exclude=True)
    on_format: Optional[Callable] = Field(default=None, exclude=True)
    on_lint: Optional[Callable] = Field(default=None, exclude=True)
    on_save: Optional[Callable] = Field(default=None, exclude=True)
    # Define valid event types for code editor components
    valid_event_types: ClassVar[List[str]] = [
        ComponentEventType.CONTENT_CHANGE,
        ComponentEventType.FORMAT,
        ComponentEventType.LINT,
        ComponentEventType.SAVE,
        ComponentEventType.ACTION
    ]

    def __init__(self, **data):
        """Initialize with proper handling of action_handlers parameter."""
        # Check if action_handlers is in data and convert it to action_handler_registry
        if 'action_handlers' in data and isinstance(data['action_handlers'], ActionHandlerMap):
            action_map = data.pop('action_handlers')
            # Create a registry from the map
            registry = ActionHandlerRegistry()
            registry.handler_functions = action_map.handlers
            registry.default_handler_function = action_map.default_handler
            data['action_handler_registry'] = registry
            
        # Continue with standard initialization
        super().__init__(**data)

    @model_validator(mode='after')
    def setup_event_handlers(self) -> 'CodeEditorComponent':
        """Set up handlers from component attributes."""
        # Initialize handlers dictionary if needed
        if not hasattr(self, 'event_handlers'):
            self.event_handlers = {}
        # Register handlers from attributes
        if self.on_content_change:
            self.event_handlers[ComponentEventType.CONTENT_CHANGE] = self.on_content_change
        if self.on_format:
            self.event_handlers[ComponentEventType.FORMAT] = self.on_format
        if self.on_lint:
            self.event_handlers[ComponentEventType.LINT] = self.on_lint
        if self.on_save:
            self.event_handlers[ComponentEventType.SAVE] = self.on_save

        return self

    async def handle_action(self, action_name: str, **kwargs) -> Any:
        """
        Handle a dynamic action with the appropriate handler.

        Args:
            action_name: The name of the action to handle
            **kwargs: Additional parameters to pass to the handler

        Returns:
            The result of the handler function
        """
        if self.action_handler_registry:
            handler = self.action_handler_registry.get_handler_for_action(action_name)
            if handler:
                return await handler(action=action_name, **kwargs)
        # If we have a generic action handler registered
        if ComponentEventType.ACTION in self.event_handlers:
            return await self.event_handlers[ComponentEventType.ACTION](action=action_name, **kwargs)
        return None


class FormField(BaseModel):
    """
    Configuration for a field in a form component.
    
    Provides detailed configuration for form fields, including
    data binding, validation, and display properties.
    """
    field_name: str
    label_text: str
    field_type: str  # text, number, date, select, checkbox, radio, textarea
    is_required: bool = False
    placeholder_text: Optional[str] = None
    field_options: Optional[List[Dict[str, str]]] = None
    validation_rules: Optional[Dict[str, Any]] = None


class FormComponent(UIComponent):
    """
    Form component with integrated event handling.
    
    Provides a structured way to collect and validate user input.
    Handlers can be attached directly to the component.
    """
    component_type: str = "form"
    form_fields: List[FormField]
    submit_action_name: str = "submit"
    available_actions: List[str] = Field(default_factory=list)
    # Event handlers as component attributes
    on_submit: Optional[Callable] = Field(default=None, exclude=True)
    on_field_change: Optional[Callable] = Field(default=None, exclude=True)
    on_validation: Optional[Callable] = Field(default=None, exclude=True)
    # Define valid event types for form components
    valid_event_types: ClassVar[List[str]] = [
        ComponentEventType.SUBMIT,
        ComponentEventType.FIELD_CHANGE,
        ComponentEventType.VALIDATION
    ]

    @model_validator(mode='after')
    def setup_event_handlers(self) -> 'FormComponent':
        """Set up handlers from component attributes."""
        # Initialize handlers dictionary if needed
        if not hasattr(self, 'event_handlers'):
            self.event_handlers = {}
        # Register handlers from attributes
        if self.on_submit:
            self.event_handlers[ComponentEventType.SUBMIT] = self.on_submit
        if self.on_field_change:
            self.event_handlers[ComponentEventType.FIELD_CHANGE] = self.on_field_change
        if self.on_validation:
            self.event_handlers[ComponentEventType.VALIDATION] = self.on_validation
            
        return self


class MarkdownComponent(UIComponent):
    """
    Markdown component for displaying formatted text.

    Renders markdown content with optional styling.
    This component typically doesn't have event handlers.
    """
    component_type: str = "markdown"
    markdown_content: str = ""
    content_style: Dict[str, Any] = Field(default_factory=dict)

    # Markdown components typically don't have event handlers
    valid_event_types: ClassVar[List[str]] = []