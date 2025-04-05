# base_types.py
from enum import Enum
from typing import Type, List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import re
from pydantic import BaseModel, Field

from agentnexus.ui_components import UIComponent

class ActionType(str, Enum):
    """Enumerate the types of actions an agent can perform.

    Defines standard categories of interactions that agents can implement,
    providing a clear taxonomy for agent capabilities.

    Attributes:
        TALK (str): Conversational or interactive actions
        GENERATE (str): Content or data generation actions
        QUESTION (str): Inquiry or information gathering actions
        CUSTOM_UI (str): Custom user interface driven actions
    """
    TALK = "talk"
    GENERATE = "generate"
    QUESTION = "question"
    CUSTOM_UI = "custom_ui"

class Capability(BaseModel):
    """Represents a specific capability or skill of an agent.

    Encapsulates the skills and metadata associated with an agent's
    functional abilities, allowing for detailed capability description
    and introspection.

    Attributes:
        skill_path (List[str]): Hierarchical path describing the skill domain
        metadata (Dict[str, Any]): Additional metadata providing
            detailed information about the capability

    Example:
        >>> Capability(
        ...     skill_path=["Development", "Code", "Generation"],
        ...     metadata={
        ...         "languages": ["Python", "JavaScript"],
        ...         "features": ["Code Generation", "Refactoring"]
        ...     }
        ... )
    """
    skill_path: List[str]
    metadata: Dict[str, Any]

class BaseMetadata(BaseModel):
    """Common metadata fields for agents and actions.

    Provides a base structure for storing fundamental metadata
    information that can be used across different components.

    Attributes:
        name (str): Name of the agent or action
        description (str): Detailed description of the agent or action
        response_template_md (Optional[str]): Path to a markdown response template
    """
    name: str
    description: str
    response_template_md: Optional[str] = None

class UIComponentUpdate(BaseModel):
    """Represents an update to a UI component's state.

    Allows for dynamic updates to user interface elements during
    agent interactions.

    Attributes:
        key (str): Unique identifier for the UI component
        state (Dict[str, Any]): New state to be applied to the component
        meta (Optional[Dict[str, Any]]): Additional metadata for the update
    """
    key: str
    state: Dict[str, Any]
    meta: Optional[Dict[str, Any]] = None

class UIResponse(BaseModel):
    """Represents a response that includes both data and UI updates.

    Allows agents to return both computational results and
    user interface modifications in a single response.

    Attributes:
        data (Dict[str, Any]): The primary data returned by the action
        ui_updates (List[UIComponentUpdate]): List of UI component updates
    """
    data: Dict[str, Any]
    ui_updates: List[UIComponentUpdate]

class WorkflowStepType(str, Enum):
    """Define the types of steps in a workflow.

    Provides a clear categorization of workflow step types,
    helping to structure complex multi-step processes.

    Attributes:
        START (str): Initial step of a workflow
        UI_STEP (str): Interactive user interface step
        END (str): Final step of a workflow
    """
    START = "start"
    UI_STEP = "ui_step"
    END = "end"

class WorkflowDataMapping(BaseModel):
    """Defines how data is mapped between workflow steps.

    Allows for flexible data transformation and transfer
    between different stages of a workflow.

    Attributes:
        source_field (str): The field to be mapped from the source
        target_field (str): The field to be mapped to in the target
        transform (Optional[str]): Optional transformation to apply
            during mapping (e.g., type conversion, formatting)

    Example:
        >>> WorkflowDataMapping(
        ...     source_field="user_input",
        ...     target_field="processed_data",
        ...     transform="uppercase"
        ... )
    """
    source_field: str
    target_field: str
    transform: Optional[str] = None

class WorkflowTransition(BaseModel):
    """Defines transition rules between workflow steps.

    Specifies how and under what conditions a workflow
    can move from one step to another.

    Attributes:
        target (str): The identifier of the next workflow step
        condition (Optional[str]): Conditional logic for the transition
        data_mapping (List[WorkflowDataMapping]): Rules for mapping data
            between steps
    """
    target: str
    condition: Optional[str] = None
    data_mapping: List[WorkflowDataMapping] = Field(default_factory=list)

class WorkflowStep(BaseModel):
    """Represents an individual step in a workflow.

    Defines the characteristics and behavior of a specific
    step within a larger workflow process.

    Attributes:
        id (str): Unique identifier for the step
        type (WorkflowStepType): Type of workflow step
        action (Optional[str]): Action associated with the step
        transitions (List[WorkflowTransition]): Possible transitions
            from this step
    """
    id: str
    type: Optional[WorkflowStepType] = WorkflowStepType.UI_STEP
    action: Optional[str] = None
    transitions: Optional[List[WorkflowTransition]] = None

class Workflow(BaseModel):
    """Represents a complete workflow definition.

    Provides a comprehensive description of a multi-step
    process, including its steps and initial entry point.

    Attributes:
        id (str): Unique identifier for the workflow
        name (str): Human-readable name of the workflow
        description (str): Detailed description of the workflow
        steps (List[WorkflowStep]): All steps in the workflow
        initial_step (str): Identifier of the first step in the workflow
    """
    id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    initial_step: str

class WorkflowState(BaseModel):
    """Represents the runtime state of a workflow instance.

    Tracks the current progress, data, and metadata of an
    ongoing workflow execution.

    Attributes:
        workflow_id (str): Identifier of the workflow
        current_step (str): Current step in the workflow
        data (Dict[str, Any]): Workflow-specific data
        created_at (datetime): Timestamp of workflow creation
        updated_at (datetime): Timestamp of last workflow update
    """
    workflow_id: str
    current_step: str
    data: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class WorkflowStepResponse(BaseModel):
    """Response structure for workflow steps with UI support.

    Provides a comprehensive response mechanism for workflow
    steps, including data, UI updates, and context management.

    Attributes:
        data (Dict[str, Any]): Step-specific data
        ui_updates (List[UIComponentUpdate]): UI component updates
        next_step_id (Optional[str]): Identifier of the next workflow step
        context_updates (Dict[str, Any]): Updates to the workflow context
    """
    data: Dict[str, Any]
    ui_updates: List[UIComponentUpdate] = []
    next_step_id: Optional[str] = None
    context_updates: Dict[str, Any] = {}

@dataclass
class WorkflowStepMetadata:
    """Enhanced metadata for workflow step handlers.

    Provides additional context and configuration for
    individual workflow step implementations.

    Attributes:
        workflow_id (str): Identifier of the parent workflow
        step_id (str): Unique identifier for the step
        action_type (str): Type of action for the step
        name (str): Human-readable name of the step
        description (str): Detailed description of the step
        ui_components (List[UIComponent]): UI components for the step
        allow_dynamic_ui (bool): Flag to enable dynamic UI generation
        input_model (Optional[Type[BaseModel]]): Input validation model
        output_model (Optional[Type[BaseModel]]): Output validation model
    """
    workflow_id: str
    step_id: str
    action_type: str
    name: str
    description: str
    ui_components: List[UIComponent] = field(default_factory=list)
    allow_dynamic_ui: bool = True
    input_model: Optional[Type[BaseModel]] = None
    output_model: Optional[Type[BaseModel]] = None

@dataclass
class AgentConfig:
    """Configuration and metadata for an AI agent.

    Provides a comprehensive configuration mechanism for defining
    an agent's core characteristics, capabilities, and operational parameters.

    Attributes:
        name (str): The unique name of the agent
        version (str): Version of the agent
        description (str): Detailed description of the agent's purpose
        capabilities (List[Capability]): List of agent capabilities
        workflows (Optional[List[Workflow]]): Defined workflows for the agent
        base_path (str): Base URL path for the agent's endpoints
        metadata (Dict[str, Any]): Additional metadata about the agent

    Example:
        >>> agent_config = AgentConfig(
        ...     name="Code Assistant",
        ...     version="2.0.0",
        ...     description="AI-powered code generation and review agent",
        ...     capabilities=[
        ...         Capability(
        ...             skill_path=["Development", "Code Generation"],
        ...             metadata={"languages": ["Python", "JavaScript"]}
        ...         )
        ...     ]
        ... )
    """
    name: str
    version: str = "1.0.0"
    description: str = ""
    capabilities: List[Capability] = field(default_factory=list)
    workflows: Optional[List[Workflow]] = None
    base_path: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Post-initialization hook to ensure base_path is set correctly.

        Automatically generates a base path using the agent's name if
        no explicit path is provided.
        """
        if not self.base_path:
            self.base_path = f"/v1/{slugify(self.name)}"

def slugify(text: str) -> str:
    """Convert a string to a URL-friendly slug.
    Transforms an input string into a lowercase,
    hyphen-separated version suitable for use in URLs.

    Args:
        text (str): The input string to be converted

    Returns:
        str: A URL-friendly version of the input string

    Examples:
        >>> slugify("Hello World!")
        'hello-world'
        >>> slugify("AgentHub Framework")
        'agentHub-framework'
    """
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')