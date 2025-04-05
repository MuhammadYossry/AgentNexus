"""
AgentNexus: Python Library for AI/LLM Agent Development with UI-Driven Workflows.

A declarative approach to building AI agents with interactive UIs and structured workflows.
"""

__version__ = "0.0.1"

# Export key components
from agentnexus.base_types import (
    AgentConfig,
    Capability,
    ActionType,
    Workflow,
    WorkflowStep,
    WorkflowStepType,
    WorkflowStepResponse,
    UIComponentUpdate,
    UIResponse
)

from agentnexus.action_manager import agent_action
from agentnexus.workflow_manager import workflow_step
from agentnexus.manifest_generator import AgentManager

# Make commonly used UI components available at top level
from agentnexus.ui_components import (
    FormComponent,
    TableComponent,
    CodeEditorComponent,
    MarkdownComponent
)