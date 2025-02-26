# base_types.py additions

from typing import Union, List, Dict, Any, Literal, Optional
from pydantic import BaseModel, Field

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
    pagination: bool = True
    page_size: int = 10

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
    options: Dict[str, Any] = Field(default_factory=dict)

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
    required: bool = True
    placeholder: Optional[str] = None
    options: Optional[List[Dict[str, str]]] = None

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