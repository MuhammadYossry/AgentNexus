# FastAgents: Python Library for AI/LLM Agent Development with UI-Driven Workflows and Actions!
![image](https://github.com/user-attachments/assets/b7e47c80-8741-43b8-b492-591277710997)
![image](https://github.com/user-attachments/assets/0b4297c5-62c2-4df5-8154-39c2c37a277e)

## 🚀 Core Purpose

A Python Library(so you can use it with libs of your choice) that simplifies the creation of LLM and AI agents with UI-interactable APIs with automatic Agent(s) manifest generation, enabling seamless discovery, distributed deployment, and possibly interaction across different agents. 

## 🌟 Key Features

### 🏗️ Advanced Agent Architecture
- **Declarative Development**: Create complex agents using intuitive Python decorators
- **Multi-Action Support**: Define multiple agent actions endpoints within a single agent
- **Workflow-Driven Design**: Build multi-step UI workflows

### 🖥️ Event-Driven UI System
- **Rich Component Library**: Tables, forms, code editors, and markdown displays
- **Automatic Event Handling**: Simplified component event management
- **Context-Aware State**: Preserve state across workflow steps and sessions

### 🔍 Comprehensive Manifest Generation
- **Standard Protocol**: JSON schema for agents, actions, workflows, and UI components
- **Cross-Platform**: Compatible with any platform supporting the manifest spec(WIP)
- **Distributed Architecture**: Enables decentralized agent discovery and execution
## 📋 Examples

For comprehensive examples, explore our [`agents`](/agents) folder which contains several fully-implemented agents. This folder structure demonstrates best practices for organizing agent code, UI components, models, and event handlers:

```
agents
├── __init__.py
├── code_agent_v1.py
├── code_agent_v2.py
├── flight_agent.py
├── llm_client.py
├── models
│   ├── code_agent_v1.py
│   ├── code_agent_v2.py
│   └── flight_agent.py
├── ui_components
│   ├── code_agent_v1.py
│   ├── code_agent_v2.py
│   └── flight_agent.py
└── ui_handlers
    ├── code_agent_v1.py
    ├── code_agent_v2.py
    └── flight_agent.py
```

### Creating a Simple Agent Action

```python
from fast_agents.base_types import AgentConfig, Capability, ActionType
from fast_agents.action_manager import agent_action

# Define your agent configuration
code_agent = AgentConfig(
    name="Code Assistant",
    version="1.0.0",
    description="AI-powered code analysis agent",
    capabilities=[
        Capability(
            skill_path=["Development", "Code", "Analysis"],
            metadata={
                "languages": ["Python", "JavaScript"],
                "features": ["Quality", "Formatting", "Performance"]
            }
        )
    ]
)

# Create a standalone agent action
@agent_action(
    agent_config=code_agent,
    action_type=ActionType.GENERATE,
    name="Format Code",
    description="Format code according to best practices"
)
async def format_code(input_data):
    """Format code according to language-specific style guidelines."""
    code = input_data.code
    language = input_data.language
    
    # Formatting logic would go here
    formatted_code = code  # Placeholder
    
    return {
        "formatted_code": formatted_code,
        "language": language,
        "stats": {
            "original_length": len(code),
            "formatted_length": len(formatted_code)
        }
    }
```
### 📋 A Workflow Example

```python
from fast_agents.base_types import (
    AgentConfig, Capability, Workflow, WorkflowStep, WorkflowStepType,
    WorkflowStepResponse, UIComponentUpdate
)
from fast_agents.workflow_manager import workflow_step
from fast_agents.ui_components import (
    FormComponent, MarkdownComponent, CodeEditorComponent, 
    TableComponent, FormField
)

# Define UI components for document summarization workflow
document_input = CodeEditorComponent(
    component_key="document_input",
    title="Document Text",
    programming_language="markdown",
    editor_content="Paste your document content here..."
)

options_form = FormComponent(
    component_key="options_form",
    title="Summarization Options",
    form_fields=[
        FormField(
            field_name="summary_length",
            label_text="Summary Length",
            field_type="select",
            field_options=[
                {"value": "short", "label": "Short (1-2 paragraphs)"},
                {"value": "medium", "label": "Medium (3-5 paragraphs)"},
                {"value": "long", "label": "Long (5+ paragraphs)"}
            ]
        ),
        FormField(
            field_name="focus_areas",
            label_text="Focus Areas",
            field_type="select",
            field_options=[
                {"value": "main_points", "label": "Main Points"},
                {"value": "technical", "label": "Technical Details"},
                {"value": "implications", "label": "Implications & Takeaways"}
            ]
        )
    ]
)

summary_display = MarkdownComponent(
    component_key="summary_display",
    title="Document Summary",
    markdown_content="Summary will appear here."
)

feedback_form = FormComponent(
    component_key="feedback_form",
    title="Feedback",
    form_fields=[
        FormField(
            field_name="rating",
            label_text="Summary Quality",
            field_type="select",
            field_options=[
                {"value": "excellent", "label": "Excellent"},
                {"value": "good", "label": "Good"},
                {"value": "needs_improvement", "label": "Needs Improvement"}
            ]
        ),
        FormField(
            field_name="comments",
            label_text="Comments",
            field_type="textarea"
        )
    ]
)

continue_button = FormComponent(
    component_key="continue_button",
    title="Navigation",
    form_fields=[
        FormField(
            field_name="action",
            label_text="Continue",
            field_type="select",
            field_options=[
                {"value": "continue", "label": "Continue to Next Step"}
            ]
        )
    ]
)

# Define summarization workflow
SUMMARIZE_WORKFLOW = Workflow(
    id="document_summarization",
    name="Document Summarization",
    description="Create concise summaries of documents with customizable options",
    steps=[
        WorkflowStep(id="upload"),
        WorkflowStep(id="analyze"),
        WorkflowStep(id="summarize"),
        WorkflowStep(id="review"),
        WorkflowStep(id="export", type=WorkflowStepType.END)
    ],
    initial_step="upload"
)

# Create agent config with the workflow
summarization_agent = AgentConfig(
    name="Document Summarizer",
    version="1.0.0",
    description="AI-powered document summarization with customizable options",
    capabilities=[
        Capability(
            skill_path=["Documents", "Summarization"],
            metadata={
                "document_types": ["text", "markdown", "pdf_extract"],
                "features": ["length_control", "focus_areas", "feedback_loop"]
            }
        )
    ],
    workflows=[SUMMARIZE_WORKFLOW]
)

# Define workflow step handlers
@workflow_step(
    agent_config=summarization_agent,
    workflow_id="document_summarization",
    step_id="upload",
    name="Document Upload",
    description="Upload document content for summarization",
    ui_components=[document_input, continue_button]
)
async def handle_upload_step(input_data) -> WorkflowStepResponse:
    """Handle initial document upload."""
    context = input_data.context
    form_data = input_data.form_data if hasattr(input_data, 'form_data') else {}
    
    if form_data and form_data.get("action") == "submit":
        # When continue button is clicked, move to next step
        document_text = context.get("document", document_input.editor_content)
        
        return WorkflowStepResponse(
            data={"status": "document_uploaded"},
            next_step_id="analyze",
            context_updates={
                "document": document_text
            }
        )
    
    # Initial load or other actions
    return WorkflowStepResponse(
        data={"status": "ready"},
        ui_updates=[
            UIComponentUpdate(
                key="document_input",
                state={"editor_content": context.get("document", document_input.editor_content)}
            )
        ],
        context_updates={}
    )

@workflow_step(
    agent_config=summarization_agent,
    workflow_id="document_summarization",
    step_id="analyze",
    name="Analysis Options",
    description="Set options for document summarization",
    ui_components=[options_form, continue_button]
)
async def handle_analyze_step(input_data) -> WorkflowStepResponse:
    """Handle summarization options selection."""
    context = input_data.context
    form_data = input_data.form_data if hasattr(input_data, 'form_data') else {}
    
    if form_data and form_data.get("action") == "submit":
        component_key = form_data.get("component_key")
        
        if component_key == "options_form":
            # Extract options from form
            values = form_data.get("values", {})
            summary_length = values.get("summary_length", "medium")
            focus_areas = values.get("focus_areas", "main_points")
            
            # Store options in context and continue
            return WorkflowStepResponse(
                data={"status": "options_set"},
                ui_updates=[],
                next_step_id="summarize",
                context_updates={
                    "summary_length": summary_length,
                    "focus_areas": focus_areas
                }
            )
        elif component_key == "continue_button":
            # Default values if continue is pressed without setting options
            return WorkflowStepResponse(
                data={"status": "options_set"},
                ui_updates=[],
                next_step_id="summarize",
                context_updates={
                    "summary_length": "medium",
                    "focus_areas": "main_points"
                }
            )
    
    # Initial load
    return WorkflowStepResponse(
        data={"status": "ready"},
        ui_updates=[
            UIComponentUpdate(
                key="options_form",
                state={
                    "values": {
                        "summary_length": context.get("summary_length", "medium"),
                        "focus_areas": context.get("focus_areas", "main_points")
                    }
                }
            )
        ],
        context_updates={}
    )

@workflow_step(
    agent_config=summarization_agent,
    workflow_id="document_summarization",
    step_id="summarize",
    name="Generate Summary",
    description="Generate summary based on document and options",
    ui_components=[summary_display, continue_button]
)
async def handle_summarize_step(input_data) -> WorkflowStepResponse:
    """Generate document summary based on options."""
    context = input_data.context
    form_data = input_data.form_data if hasattr(input_data, 'form_data') else {}
    
    document = context.get("document", "")
    summary_length = context.get("summary_length", "medium")
    focus_areas = context.get("focus_areas", "main_points")
    
    if form_data and form_data.get("action") == "submit":
        # Move to review step when continue is clicked
        return WorkflowStepResponse(
            data={"status": "summary_accepted"},
            next_step_id="review",
            context_updates={}
        )
    
    # If we don't have a summary yet or are regenerating it
    if not context.get("summary") or form_data.get("action") == "regenerate":
        # Generate summary based on document and options
        summary = generate_summary(document, summary_length, focus_areas)
        
        # Store summary in context
        return WorkflowStepResponse(
            data={"status": "summary_generated"},
            ui_updates=[
                UIComponentUpdate(
                    key="summary_display",
                    state={"markdown_content": summary}
                )
            ],
            context_updates={
                "summary": summary
            }
        )
    
    # Load existing summary
    return WorkflowStepResponse(
        data={"status": "summary_loaded"},
        ui_updates=[
            UIComponentUpdate(
                key="summary_display",
                state={"markdown_content": context.get("summary", "")}
            )
        ],
        context_updates={}
    )

@workflow_step(
    agent_config=summarization_agent,
    workflow_id="document_summarization",
    step_id="review",
    name="Review Summary",
    description="Provide feedback on generated summary",
    ui_components=[summary_display, feedback_form, continue_button]
)
async def handle_review_step(input_data) -> WorkflowStepResponse:
    """Handle feedback and summary review."""
    context = input_data.context
    form_data = input_data.form_data if hasattr(input_data, 'form_data') else {}
    
    if form_data and form_data.get("action") == "submit":
        component_key = form_data.get("component_key")
        
        if component_key == "feedback_form":
            # Process feedback
            values = form_data.get("values", {})
            rating = values.get("rating", "")
            comments = values.get("comments", "")
            
            # If needs improvement, go back to summarize step
            if rating == "needs_improvement":
                return WorkflowStepResponse(
                    data={"status": "needs_improvement"},
                    next_step_id="summarize",
                    context_updates={
                        "feedback_rating": rating,
                        "feedback_comments": comments
                    }
                )
            
            # Otherwise, proceed to export
            return WorkflowStepResponse(
                data={"status": "feedback_submitted"},
                next_step_id="export",
                context_updates={
                    "feedback_rating": rating,
                    "feedback_comments": comments
                }
            )
        elif component_key == "continue_button":
            # Go to export with default feedback
            return WorkflowStepResponse(
                data={"status": "review_completed"},
                next_step_id="export",
                context_updates={}
            )
    
    # Initial load
    return WorkflowStepResponse(
        data={"status": "ready_for_review"},
        ui_updates=[
            UIComponentUpdate(
                key="summary_display",
                state={"markdown_content": context.get("summary", "")}
            )
        ],
        context_updates={}
    )

@workflow_step(
    agent_config=summarization_agent,
    workflow_id="document_summarization",
    step_id="export",
    name="Export Summary",
    description="Export final summary",
    ui_components=[summary_display]
)
async def handle_export_step(input_data) -> WorkflowStepResponse:
    """Prepare final summary export."""
    context = input_data.context
    
    # Get final summary and metadata
    summary = context.get("summary", "")
    rating = context.get("feedback_rating", "")
    comments = context.get("feedback_comments", "")
    
    # Add metadata section
    final_summary = f"""# Document Summary

{summary}

---

**Metadata:**
- Length setting: {context.get('summary_length', 'medium')}
- Focus area: {context.get('focus_areas', 'main_points')}
- Quality rating: {rating}
"""
    
    return WorkflowStepResponse(
        data={
            "status": "summary_complete",
            "exportable_content": final_summary
        },
        ui_updates=[
            UIComponentUpdate(
                key="summary_display",
                state={"markdown_content": final_summary}
            )
        ],
        context_updates={
            "final_summary": final_summary
        }
    )

# Placeholder for the actual summarization logic
def generate_summary(document, length, focus):
    """Generate document summary based on options."""
    # In a real implementation, this could use an LLM or other summarization method
    word_count = len(document.split())
    
    if length == "short":
        target_length = "1-2 paragraphs"
    elif length == "medium":
        target_length = "3-5 paragraphs"
    else:
        target_length = "5+ paragraphs"
    
    return f"""## Document Summary

This is a summary of the provided document ({word_count} words) with focus on **{focus}** and target length of **{target_length}**.

The document covers several important topics that have been condensed into this summary...

[Actual summary would be generated here based on document content and options]
"""
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
- **Actions**: Standalone agent capabilities
- **Workflows**: Multi-step processes with state management
- **UI Components**: Interactive UI elements with event handling
- **Context Management**: Preserve state across workflow steps, It's working but can be better
- **Manifest**: Standardized JSON description to enable decentralized agent discovery and execution

## 🛠️ Installation
WIP
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
