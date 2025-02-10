# base_types.py
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ActionType(str, Enum):
    """Types of actions an agent can perform."""
    TALK = "talk"
    GENERATE = "generate"
    QUESTION = "question"

class WorkflowStepType(str, Enum):
    START = "start"
    ACTION = "action"
    END = "end"

class Capability(BaseModel):
    """Simplified capability definition."""
    skill_path: List[str]
    metadata: Dict[str, Any]

class BaseMetadata(BaseModel):
    """Common metadata fields."""
    name: str
    description: str
    response_template_md: Optional[str] = None