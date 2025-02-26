# base_types.py
from enum import Enum
from typing import Type, List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import re
from pydantic import BaseModel, Field

from agents_manifest.ui_components import UIComponentBase

class ActionType(str, Enum):
    """Types of actions an agent can perform."""
    TALK = "talk"
    GENERATE = "generate"
    QUESTION = "question"
    CUSTOM_UI = "custom_ui"

class Capability(BaseModel):
    """Simplified capability definition."""
    skill_path: List[str]
    metadata: Dict[str, Any]

class BaseMetadata(BaseModel):
    """Common metadata fields."""
    name: str
    description: str
    response_template_md: Optional[str] = None

# Models

# Response model for UI updates
class UIComponentUpdate(BaseModel):
    key: str
    state: Dict[str, Any]
    meta: Optional[Dict[str, Any]] = None

class UIResponse(BaseModel):
    data: Dict[str, Any]
    ui_updates: List[UIComponentUpdate]

class WorkflowStepType(str, Enum):
    START = "start"
    UI_STEP = "ui_step"
    END = "end"

class WorkflowDataMapping(BaseModel):
    """Maps data between workflow steps."""
    source_field: str
    target_field: str
    transform: Optional[str] = None

class WorkflowTransition(BaseModel):
    """Defines transition between workflow steps."""
    target: str
    condition: Optional[str] = None
    data_mapping: List[WorkflowDataMapping] = Field(default_factory=list)

class WorkflowStep(BaseModel):
    """Individual workflow step definition."""
    id: str
    type: WorkflowStepType
    action: Optional[str] = None
    transitions: List[WorkflowTransition] = Field(default_factory=list)

class Workflow(BaseModel):
    """Complete workflow definition."""
    id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    initial_step: str

class WorkflowState(BaseModel):
    """Runtime state of a workflow instance."""
    workflow_id: str
    current_step: str
    data: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class WorkflowStepResponse(BaseModel):
    """Response structure for workflow steps with UI support."""
    data: Dict[str, Any]
    ui_updates: List[UIComponentUpdate] = []
    next_step_id: Optional[str] = None  # Dynamic next step
    context_updates: Dict[str, Any] = {}  # Updates to workflow context

@dataclass
class WorkflowStepMetadata:
    """Enhanced metadata for workflow step handlers."""
    workflow_id: str
    step_id: str
    action_type: str
    name: str
    description: str
    ui_components: List[UIComponentBase] = field(default_factory=list)
    allow_dynamic_ui: bool = True
    input_model: Optional[Type[BaseModel]] = None
    output_model: Optional[Type[BaseModel]] = None

@dataclass
class AgentConfig:
    name: str
    version: str = "1.0.0"
    description: str = ""
    capabilities: List[Capability] = field(default_factory=list)
    workflows: Optional[List[Workflow]] = None
    base_path: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.base_path:
            self.base_path = f"/v1/{self.name.lower().replace(' ', '-')}"

def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')