# AgentHub: AI Agent Development Framework with UI-Driven Workflows and Actions!

## 🚀 Core Purpose

AgentHub is a powerful Python framework that simplifies the creation of intelligent agents with rich, interactive user interfaces and automatic API generation. Build sophisticated multi-step workflows with declarative syntax and seamless state management.

## 🌟 Key Features

### 🏗️ Advanced Agent Architecture
- **Declarative Development**: Create complex agents using intuitive Python decorators
- **Multi-Action Support**: Define multiple capabilities within a single agent
- **Workflow-Driven Design**: Build sophisticated multi-step processes with proper state transitions

### 🖥️ Event-Driven UI System
- **Rich Component Library**: Pre-built components for tables, forms, code editors, and markdown displays
- **Automatic Event Handling**: Built-in handlers for common events with standardized responses
- **Context-Aware State Management**: Maintain and pass state across workflow steps

### 🔄 Powerful Workflow Capabilities
- **Step Transitions**: Define workflows with conditional transitions between steps
- **Session Management**: Maintain context across multiple interactions
- **Response Standardization**: Consistent WorkflowStepResponse objects for reliable operation

### 🔍 API and Documentation Generation
- **Automatic Manifest Files**: Generate comprehensive machine-readable agent manifests
- **OpenAPI Integration**: Instant, standards-compliant API documentation
- **Self-Documenting Endpoints**: Complete metadata about capabilities, actions, and workflows

## 📋 Example: Creating a Code Review Agent

```python
from agents_manifest.base_types import AgentConfig, Capability, WorkflowStepResponse
from agents_manifest.workflow_manager import workflow_step

# Define your agent configuration
code_agent = AgentConfig(
    name="Code Assistant",
    version="1.0.0",
    description="AI-powered code review and improvement agent",
    capabilities=[
        Capability(
            skill_path=["Development", "Code", "Quality"],
            metadata={
                "languages": ["Python", "JavaScript"],
                "features": ["Documentation", "Type Annotations", "Performance"]
            }
        )
    ],
    workflows=[code_review_workflow]  # Define your workflow structure
)

# Create a workflow step with UI components
@workflow_step(
    agent_config=code_agent,
    workflow_id="code_review",
    step_id="analyze",
    name="Code Analysis",
    description="Analyze code and provide improvement suggestions",
    ui_components=[code_display, analysis_result]
)
async def handle_analyze_step(input_data) -> WorkflowStepResponse:
    """Handle the analysis step of the workflow."""
    # Extract data from input
    context = input_data.context
    code = context.get("original_code", "")

    # Perform analysis
    analysis_text = analyze_code(code)

    # Return standardized response with UI updates
    return WorkflowStepResponse(
        data={"status": "analysis_complete"},
        ui_updates=[
            UIComponentUpdate(
                key="analysis_result",
                state={"markdown_content": analysis_text}
            )
        ],
        next_step_id="improve",  # Define where to go next
        context_updates={"analysis": analysis_text}
    )
```

## 🌐 Automatic Endpoint Generation

```python
# Set up your FastAPI application with AgentHub
app = FastAPI()
agent_manager = AgentManager(base_url="http://localhost:9000")
agent_manager.add_agent(code_agent)
agent_manager.setup_agents(app)

# Run your application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
```

## 📚 Key Concepts

- **Agent Config**: Define your agent's metadata and capabilities
- **Workflow Steps**: Build multi-step processes with proper transitions
- **UI Components**: Pre-built interactive elements for your agent's interface
- **Event Handling**: Standardized response system for consistent behavior
- **Context Management**: Preserve state across workflow steps

## 🛠️ Installation

```bash
# Using pip
pip install agenthub

# Using Poetry
poetry add agenthub
```

## 🌐 Auto-Generated Endpoints

- `GET /agents.json` - List all available agents
- `GET /agents/{agent_slug}.json` - Get detailed manifest for a specific agent
- `POST /agents/{agent_slug}/actions/{action_name}` - Trigger agent actions
- `POST /agents/{agent_slug}/workflows/{workflow_id}/steps/{step_id}` - Execute workflow steps

## 📖 Documentation

For full documentation and examples [TBD]

## 🤝 Contributing

Contributions are welcome! Help us improve AgentHub and make intelligent agent development even more accessible.

## 🌟 Star Us

If you find AgentHub useful, please give us a star on [GitHub](https://github.com/Relax-N-Tax/AgentHub)!