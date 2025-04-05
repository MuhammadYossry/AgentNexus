---
title: "Agents"
description: "Understanding agent definition, configuration, and capabilities in AgentNexus"
lead: "Agents are the central entities in AgentNexus, representing AI assistants with defined capabilities and behaviors."
date: 2025-03-25T08:00:00+00:00
lastmod: 2025-03-25T08:00:00+00:00
draft: false
images: []
menu:
  docs:
    parent: "core-concepts"
weight: 310
toc: true
---

## What is an Agent?

In the AgentNexus framework, an **agent** represents an AI assistant with specific capabilities, actions, and workflows. Agents are the primary entities that users interact with, and they provide structure for organizing related functionality.

Think of an agent as a virtual assistant specialized for certain tasks, like a travel agent, a code assistant, or a document analyzer. Each agent has:

- A unique identity (name, version, description)
- A set of capabilities defining what it can do
- Actions that implement specific functionalities
- Optional workflows for multi-step processes
- Associated UI components for interaction

## Agent Configuration

Agents are defined using the `AgentConfig` class, which provides a declarative way to specify all aspects of an agent.

### Basic Configuration

Here's a simple agent configuration:

```python
from agentnexus.base_types import AgentConfig, Capability

travel_agent = AgentConfig(
    name="Travel Assistant",
    version="1.0.0",
    description="Helps plan and book travel arrangements",
    capabilities=[
        Capability(
            skill_path=["Travel", "Booking"],
            metadata={
                "modes": ["Flight", "Hotel", "Car"],
                "regions": ["Global"]
            }
        )
    ]
)
```

### Configuration Parameters

The `AgentConfig` class accepts several parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | The name of the agent (required) |
| `version` | `str` | The version of the agent (default: "1.0.0") |
| `description` | `str` | A detailed description of the agent |
| `capabilities` | `List[Capability]` | A list of agent capabilities |
| `workflows` | `Optional[List[Workflow]]` | Optional workflows for multi-step processes |
| `base_path` | `str` | Custom base path for agent endpoints (default: derived from name) |
| `metadata` | `Dict[str, Any]` | Additional metadata for the agent |

### Name and Slugification

The agent's name is important as it's used to generate:

- A slug for API endpoints (e.g., "Travel Assistant" → "travel-assistant")
- Display names in the auto-generated docs
- Identifiers for the agent in the manifest

The conversion from name to slug happens automatically using the `slugify` function:

```python
from agentnexus.base_types import slugify

agent_name = "AI Code Assistant"
agent_slug = slugify(agent_name)  # "ai-code-assistant"
```

## Agent Capabilities

Capabilities define what an agent can do and its areas of expertise. They're organized as a list of `Capability` objects, each with a skill path and metadata.

### Defining Capabilities

Capabilities use a hierarchical skill path and flexible metadata:

```python
from agentnexus.base_types import Capability

code_capabilities = [
    Capability(
        skill_path=["Development", "Code", "Generation"],
        metadata={
            "languages": ["Python", "JavaScript", "TypeScript"],
            "frameworks": ["FastAPI", "React", "Django"],
            "features": ["Refactoring", "Documentation", "Testing"]
        }
    ),
    Capability(
        skill_path=["Development", "Code", "Analysis"],
        metadata={
            "analysis_types": ["Performance", "Security", "Quality"],
            "tools": ["Static Analysis", "Complexity Metrics"]
        }
    )
]
```

### Skill Paths

Skill paths are lists of strings that create a hierarchy of capabilities. They help organize and discover agents based on their skills. For example:

- `["Travel", "Flight", "Search"]`
- `["Development", "Code", "Generation"]`
- `["Finance", "Budget", "Analysis"]`

### Capability Metadata

Metadata provides additional details about a capability as a flexible dictionary. Common metadata fields include:

- Supported languages, frameworks, or tools
- Feature lists and supported operations
- Expertise levels and specializations
- Domain-specific attributes

## Registering Agents

After defining an agent, you need to register it with the `AgentManager` to set up API endpoints:

```python
from fastapi import FastAPI
from agentnexus.manifest_generator import AgentManager

app = FastAPI()
agent_manager = AgentManager(base_url="http://localhost:8000")

# Register multiple agents
agent_manager.add_agent(travel_agent)
agent_manager.add_agent(code_agent)

# Set up routes
agent_manager.setup_agents(app)
```

The `AgentManager` handles:

1. Registering agents and their actions
2. Setting up FastAPI routes
3. Generating agent manifests
4. Creating auto-documentation

## Agent Manifests

Every agent automatically generates a JSON manifest describing its capabilities, actions, and workflows. This manifest is accessible at:

```
/agents/{agent_slug}.json
```

Here's a simplified example of what an agent manifest looks like:

```json
{
  "name": "Travel Assistant",
  "slug": "travel-assistant",
  "version": "1.0.0",
  "type": "external",
  "description": "Helps plan and book travel arrangements",
  "baseUrl": "http://localhost:8000",
  "capabilities": [
    {
      "skill_path": ["Travel", "Booking"],
      "metadata": {
        "modes": ["Flight", "Hotel", "Car"],
        "regions": ["Global"]
      }
    }
  ],
  "actions": [
    {
      "name": "Search Flights",
      "slug": "search-flights",
      "actionType": "generate",
      "path": "/agents/travel-assistant/actions/search-flights",
      "method": "POST",
      "inputSchema": {...},
      "outputSchema": {...},
      "description": "Search for available flights"
    }
  ],
  "workflows": [...]
}
```

These manifests enable:

- Agent discovery and integration
- Consistent API documentation
- Client generation
- Cross-agent communication

## Practical Examples

### Simple Information Agent

```python
from agentnexus.base_types import AgentConfig, Capability, ActionType
from agentnexus.action_manager import agent_action

info_agent = AgentConfig(
    name="Information Assistant",
    version="1.0.0",
    description="Provides answers to general information questions",
    capabilities=[
        Capability(
            skill_path=["Information", "General"],
            metadata={"topics": ["Science", "History", "Geography"]}
        )
    ]
)

@agent_action(
    agent_config=info_agent,
    action_type=ActionType.TALK,
    name="Answer Question",
    description="Answers general knowledge questions"
)
async def answer_question(input_data):
    question = input_data.question
    # Implementation logic here
    return {"answer": "Sample answer to: " + question}
```

### Complex Agent with Multiple Capabilities

```python
from agentnexus.base_types import AgentConfig, Capability, ActionType

content_agent = AgentConfig(
    name="Content Creation Assistant",
    version="2.1.0",
    description="Helps create, edit, and improve various types of content",
    capabilities=[
        Capability(
            skill_path=["Content", "Writing", "Creative"],
            metadata={
                "content_types": ["Stories", "Blog Posts", "Marketing Copy"],
                "tones": ["Professional", "Casual", "Persuasive"]
            }
        ),
        Capability(
            skill_path=["Content", "Editing", "Grammar"],
            metadata={
                "checks": ["Grammar", "Style", "Readability"],
                "styles": ["APA", "MLA", "Chicago"]
            }
        ),
        Capability(
            skill_path=["Content", "Analysis", "SEO"],
            metadata={
                "features": ["Keyword Analysis", "Readability Scores"]
            }
        )
    ],
    metadata={
        "recommended_use_cases": ["Blog Writing", "Academic Papers", "Marketing"],
        "limitations": ["Does not generate images", "English language only"]
    }
)
```

## Best Practices

### Agent Design

1. **Focused Purpose**: Design agents with a clear, focused purpose
2. **Descriptive Names**: Use clear, descriptive names for agents
3. **Detailed Descriptions**: Provide comprehensive descriptions
4. **Granular Capabilities**: Break capabilities into logical groups
5. **Consistent Versioning**: Use semantic versioning (MAJOR.MINOR.PATCH)

### Agent Organization

1. **Related Functionality**: Group related functionality within a single agent
2. **Capability Hierarchy**: Use skill paths to create a logical hierarchy
3. **Comprehensive Metadata**: Include detailed metadata for discovery
4. **Clear Boundaries**: Maintain clear boundaries between different agents

## Next Steps

- Learn about [Actions](../actions) to implement agent functionality
- Explore [Workflows](../workflows) for multi-step processes
- Understand [UI Components](../ui-components) for interactive interfaces
- See how to use [Event Handling](../event-handling) with agents