# base_types.py additions

from typing import Union, List, Dict, Any, Literal, Optional, Callable, ClassVar
from pydantic import BaseModel, Field, model_validator, validator
from inspect import signature, Parameter
import logging

logger = logging.getLogger(__name__)

class EventHandlerMetadata:
    """Metadata for tracking event handler information."""
    def __init__(self, func: Callable, event_type: str):
        self.func = func
        self.event_type = event_type

class UIComponentBase(BaseModel):
    """Base class for creating dynamic, configurable user interface components.

    Provides a standard structure for defining UI components with
    flexible configuration options. This base class allows for
    dynamic state management and metadata attachment.

    Attributes:
        type (str): Identifies the type of UI component
        key (str): Unique identifier for the component
        title (Optional[str]): Human-readable title for the component
        meta (Dict[str, Any]): Additional metadata for the component
        state (Dict[str, Any]): Current state of the component
    """
    type: str
    key: str = Field(..., min_length=1)
    title: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)
    state: Dict[str, Any] = Field(default_factory=dict)
    # Internal handler storage - not included in serialization
    event_handlers: Dict[str, Callable] = Field(default_factory=dict, exclude=True)
    # Class-level valid events (to be overridden by subclasses)
    valid_events: ClassVar[List[str]] = []

    model_config = {
        "arbitrary_types_allowed": True,
        "validate_assignment": True
    }

    def register_handler(self, event_type: str, handler: Callable) -> None:
        """Register a handler for a specific event type.
        Args:
            event_type: The type of event to handle
            handler: The function to handle the event
        Raises:
            ValueError: If the event type is not valid for this component
        """
        if event_type not in self.valid_events:
            raise ValueError(
                f"Invalid event type '{event_type}' for {self.type} component. "
                f"Valid events are: {', '.join(self.valid_events)}"
            )
        self.event_handlers[event_type] = handler
        logger.debug(f"Registered {event_type} handler for {self.key}")

    def get_handler(self, event_type: str) -> Optional[Callable]:
        """Retrieve a handler for a specific event type.
        Args:
            event_type: The type of event to get handler for
        Returns:
            The handler function or None if not found
        """
        return self.event_handlers.get(event_type)

    @validator('event_handlers', pre=True, always=True)
    def _collect_event_handlers(cls, v, values):
        """Collect event handlers defined as class attributes."""
        handlers = v or {}
        # Collect handlers from class attributes
        for key, value in values.items():
            if key.startswith('on_') and callable(value):
                event_type = key[3:]  # Remove 'on_' prefix
                if event_type in cls.valid_events:
                    handlers[event_type] = value
        
        return handlers

class ActionHandlerMap(BaseModel):
    """Maps action names to handler functions for components with dynamic actions."""
    handlers: Dict[str, Callable] = Field(default_factory=dict)
    default_handler: Optional[Callable] = None
    model_config = {
        "arbitrary_types_allowed": True
    }
    def get_handler(self, action: str) -> Optional[Callable]:
        """Get the appropriate handler for an action."""
        return self.handlers.get(action, self.default_handler)
    def register_handler(self, action: str, handler: Callable) -> None:
        """Add a handler for a specific action."""
        self.handlers[action] = handler

class TableColumn(BaseModel):
    """Defines the configuration for a single column in a table component.

    Allows detailed customization of table columns, including
    sortability and width specifications.

    Attributes:
        field (str): Data field corresponding to the column
        header (str): Display name for the column header
        sortable (bool, optional): Whether the column can be sorted. Defaults to True
        width (Optional[str]): Optional width specification (e.g., '100px', '20%')

    Example:
        >>> column = TableColumn(
        ...     field="username",
        ...     header="User Name",
        ...     sortable=True,
        ...     width="200px"
        ... )
    """
    field: str
    header: str
    sortable: bool = True
    width: Optional[str] = None

class TableComponent(UIComponentBase):
    """Represents a table-based user interface component with advanced features.

    Provides a comprehensive configuration for creating interactive
    tables with support for pagination, sorting, and custom actions.

    Attributes:
        type (Literal["table"]): Fixed type identifier for table components
        columns (List[TableColumn]): Configuration for table columns
        data (List[Dict[str, Any]]): The data to be displayed in the table
        actions (List[str], optional): List of available actions for the table
        pagination (bool, optional): Enable/disable table pagination. Defaults to True
        page_size (int, optional): Number of rows per page. Defaults to 10

    Example:
        >>> table = TableComponent(
        ...     key="user_table",
        ...     title="User Management",
        ...     columns=[
        ...         TableColumn(field="id", header="ID"),
        ...         TableColumn(field="name", header="Name")
        ...     ],
        ...     data=[
        ...         {"id": 1, "name": "John Doe"},
        ...         {"id": 2, "name": "Jane Smith"}
        ...     ],
        ...     actions=["edit", "delete"],
        ...     pagination=True,
        ...     page_size=5
        ... )
    """
    type: Literal["table"] = "table"
    columns: List[TableColumn]
    data: List[Dict[str, Any]]
    actions: List[str] = Field(default_factory=list)
    action_handlers: Optional[ActionHandlerMap] = None
    pagination: bool = True
    page_size: int = 10
    # Event handlers
    valid_events: ClassVar[List[str]] = ["row_action", "sort", "pagination"]
    # Optional action-specific handlers
    on_row_action: Optional[Callable] = None
    on_sort: Optional[Callable] = None
    on_pagination: Optional[Callable] = None
    def __init__(self, **data):
        super().__init__(**data)
        # Ensure action_handlers exists
        if self.action_handlers is None and 'action_handlers' in data:
            self.action_handlers = data['action_handlers']


class CodeEditorComponent(UIComponentBase):
    """Monaco-based code editor component with extensive customization options.

    Provides a fully configurable code editing interface with
    support for multiple programming languages, themes, and editing modes.

    Attributes:
        type (Literal["code_editor"]): Fixed type identifier for code editor
        language (str): Programming language for syntax highlighting
        content (str, optional): Initial content of the editor
        theme (Optional[str]): Editor color theme. Defaults to "vs-dark"
        readonly (bool, optional): Whether the editor is read-only. Defaults to False
        height (str, optional): Height of the editor. Defaults to "400px"
        actions (List[str], optional): Available editor actions
        options (Dict[str, Any], optional): Additional Monaco editor options
        on_change (Optional[Callable]): Handler for content change events
        on_format (Optional[Callable]): Handler for code formatting requests
        on_lint (Optional[Callable]): Handler for linting requests

    Example:
        >>> code_editor = CodeEditorComponent(
        ...     key="python_editor",
        ...     title="Python Code Editor",
        ...     language="python",
        ...     content="def hello_world():\n    print('Hello, World!')",
        ...     theme="vs-light",
        ...     actions=["format", "lint"],
        ...     options={
        ...         "minimap": {"enabled": True},
        ...         "lineNumbers": "on"
        ...     }
        ... )
    """
    type: Literal["code_editor"] = "code_editor"
    language: str
    content: str = ""
    theme: Optional[str] = "vs-dark"
    readonly: bool = False
    height: str = "400px"
    actions: List[str] = Field(default_factory=list)
    action_handlers: Optional[ActionHandlerMap] = Field(default=None, exclude=True)
    options: Dict[str, Any] = Field(default_factory=dict)
    # Event handlers
    valid_events: ClassVar[List[str]] = ["content_change", "save", "format", "lint"]
    on_content_change: Optional[Callable] = None
    on_save: Optional[Callable] = None
    on_format: Optional[Callable] = None
    on_lint: Optional[Callable] = None


class MarkdownComponent(UIComponentBase):
    """Markdown rendering component for displaying formatted text.

    Allows rendering of markdown content with optional custom styling.

    Attributes:
        type (Literal["markdown"]): Fixed type identifier for markdown component
        content (str, optional): Markdown-formatted text to display
        style (Dict[str, Any], optional): Custom CSS styles for the component

    Example:
        >>> markdown = MarkdownComponent(
        ...     key="instructions",
        ...     title="User Guide",
        ...     content="# Welcome\n\nThis is a **markdown** guide.",
        ...     style={
        ...         "backgroundColor": "#f4f4f4",
        ...         "padding": "15px"
        ...     }
        ... )
    """
    type: Literal["markdown"] = "markdown"
    content: str = ""
    style: Dict[str, Any] = Field(default_factory=dict)
    # No events for markdown component
    valid_events: ClassVar[List[str]] = []

class FormField(BaseModel):
    """Defines a single field configuration for form-based UI components.

    Provides comprehensive configuration options for form input fields.

    Attributes:
        name (str): Unique identifier for the form field
        label (str): Human-readable label for the field
        type (Literal): Type of input field (text, number, date, select)
        required (bool, optional): Whether the field is mandatory. Defaults to True
        placeholder (Optional[str]): Hint text for the input field
        options (Optional[List[Dict[str, str]]]): Options for select-type fields

    Example:
        >>> text_field = FormField(
        ...     name="username",
        ...     label="Username",
        ...     type="text",
        ...     required=True,
        ...     placeholder="Enter your username"
        ... )
        >>> select_field = FormField(
        ...     name="country",
        ...     label="Country",
        ...     type="select",
        ...     options=[
        ...         {"label": "United States", "value": "US"},
        ...         {"label": "Canada", "value": "CA"}
        ...     ]
        ... )
    """
    name: str
    label: str
    type: Literal["text", "number", "date", "select"]
    required: bool = False
    placeholder: Optional[str] = None
    options: Optional[List[Dict[str, str]]] = None
    validation: Optional[Dict[str, Any]] = None

class FormComponent(UIComponentBase):
    """Represents a form-based UI component with dynamic field configuration.

    Allows creation of complex, multi-field forms with various input types.

    Attributes:
        type (Literal["form"]): Fixed type identifier for form components
        fields (List[FormField]): List of fields in the form
        submit_action (str): Action to be triggered when the form is submitted

    Example:
        >>> form = FormComponent(
        ...     key="user_registration",
        ...     title="User Registration",
        ...     fields=[
        ...         FormField(
        ...             name="username",
        ...             label="Username",
        ...             type="text",
        ...             required=True
        ...         ),
        ...         FormField(
        ...             name="email",
        ...             label="Email",
        ...             type="text",
        ...             required=True
        ...         )
        ...     ],
        ...     submit_action="register_user"
        ... )
    """
    type: Literal["form"] = "form"
    fields: List[FormField]
    submit_action: str
    valid_events: ClassVar[List[str]] = ["submit", "field_change", "validation"]
    on_submit: Optional[Callable] = None
    on_field_change: Optional[Callable] = None
    on_validation: Optional[Callable] = None