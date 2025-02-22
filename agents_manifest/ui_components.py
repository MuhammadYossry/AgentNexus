# base_types.py additions

from typing import Union, List, Dict, Any, Literal, Optional
from pydantic import BaseModel, Field

class UIComponentBase(BaseModel):
    """Base model for all UI components with dynamic state support."""
    type: str
    key: str = Field(..., min_length=1)
    title: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)
    state: Dict[str, Any] = Field(default_factory=dict)

class TableColumn(BaseModel):
    field: str
    header: str
    sortable: bool = True
    width: Optional[str] = None

class TableComponent(UIComponentBase):
    type: Literal["table"] = "table"
    columns: List[TableColumn]
    data: List[Dict[str, Any]]
    actions: List[str] = Field(default_factory=list)
    pagination: bool = True
    page_size: int = 10

class FormField(BaseModel):
    name: str
    label: str
    type: Literal["text", "number", "date", "select"]
    required: bool = True
    placeholder: Optional[str] = None
    options: Optional[List[Dict[str, str]]] = None

class FormComponent(UIComponentBase):
    type: Literal["form"] = "form"
    fields: List[FormField]
    submit_action: str
