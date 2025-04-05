---
title: "Manifest Generation"
description: "Understanding the agent manifest generation process"
lead: "AgentNexus automatically generates standardized JSON manifests that enable agent discovery, integration, and remote execution across distributed systems."
date: 2025-03-25T08:00:00+00:00
lastmod: 2025-03-25T08:00:00+00:00
draft: false
images: []
menu:
  docs:
    parent: "core-concepts"
weight: 370
toc: true
---

## Introduction to Agent Manifests

Agent manifests are standardized JSON documents that describe all aspects of an agent, including its capabilities, actions, workflows, and UI components. These manifests serve as a comprehensive "contract" that enables:

- **Agent Discovery**: Finding available agents and their capabilities
- **Remote Execution**: Invoking agent actions from external systems
- **UI Integration**: Building interfaces that interact with agent functionality
- **Distributed Systems**: Enabling cross-system agent orchestration
- **Documentation**: Auto-generating API documentation

The manifest generation system in AgentNexus automatically creates these documents by introspecting your agent definitions, eliminating the need to manually maintain API documentation or client libraries.

## Manifest Structure

A complete agent manifest includes these main sections:

```json
{
  "name": "Document Assistant",
  "slug": "document-assistant",
  "version": "1.0.0",
  "type": "external",
  "description": "Processes and analyzes document files",
  "baseUrl": "http://localhost:9000",
  "metaInfo": {},
  "capabilities": [...],
  "actions": [...],
  "workflows": [...]
}
```

### Core Information

The top-level fields provide basic agent information:

| Field | Description |
|-------|-------------|
| `name` | Human-readable agent name |
| `slug` | URL-friendly identifier (derived from name) |
| `version` | Semantic version of the agent |
| `type` | Agent type (usually "external") |
| `description` | Detailed agent description |
| `baseUrl` | Base URL where the agent is hosted |
| `metaInfo` | Additional metadata (optional) |

### Capabilities Section

The `capabilities` section lists the agent's functional domains:

```json
"capabilities": [
  {
    "skill_path": ["Documents", "Processing"],
    "metadata": {
      "formats": ["PDF", "DOCX", "TXT"],
      "features": ["OCR", "Summarization", "Translation"]
    }
  },
  {
    "skill_path": ["Documents", "Analysis"],
    "metadata": {
      "analysis_types": ["Content", "Sentiment", "Structure"],
      "languages": ["English", "Spanish", "French"]
    }
  }
]
```

### Actions Section

The `actions` section describes all available agent actions with detailed schemas:

```json
"actions": [
  {
    "name": "Process Document",
    "slug": "process-document",
    "actionType": "generate",
    "path": "/agents/document-assistant/actions/process-document",
    "method": "POST",
    "inputSchema": {
      "type": "object",
      "properties": {
        "document_url": {
          "type": "string",
          "description": "URL to the document"
        },
        "format": {
          "type": "string",
          "enum": ["PDF", "DOCX", "TXT"]
        },
        "options": {
          "type": "object",
          "properties": {
            "ocr": {"type": "boolean"}
          }
        }
      },
      "required": ["document_url"]
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "processed_text": {"type": "string"},
        "page_count": {"type": "integer"},
        "processing_time": {"type": "number"}
      },
      "required": ["processed_text"]
    },
    "description": "Process a document and extract its content",
    "isMDResponseEnabled": false,
    "examples": {
      "validRequests": [
        {"document_url": "https://example.com/sample.pdf", "format": "PDF"}
      ]
    }
  }
]
```

### Workflows Section

The `workflows` section describes multi-step workflows with their steps and transitions:

```json
"workflows": [
  {
    "id": "document_processing",
    "name": "Document Processing",
    "description": "Process documents through multiple steps",
    "steps": [
      {"id": "upload", "type": "ui_step"},
      {"id": "validate", "type": "ui_step"},
      {"id": "transform", "type": "ui_step"},
      {"id": "review", "type": "ui_step"},
      {"id": "complete", "type": "end"}
    ],
    "initial_step": "upload",
    "endpoints": {
      "start": {
        "path": "/agents/document-assistant/workflows/document_processing/start",
        "method": "POST",
        "description": "Start the Document Processing workflow",
        "input_schema": {...},
        "output_schema": {...},
        "uiComponents": [...]
      },
      "step_upload": {
        "path": "/agents/document-assistant/workflows/document_processing/steps/upload",
        "method": "POST",
        "description": "Execute upload step",
        "input_schema": {...},
        "output_schema": {...},
        "uiComponents": [...]
      },
      // Other steps...
    }
  }
]
```

### UI Components Section

UI components are included within actions or workflow steps:

```json
"uiComponents": [
  {
    "component_type": "form",
    "component_key": "document_form",
    "title": "Document Upload",
    "component_state": {},
    "supported_events": ["submit", "field_change"],
    "form_fields": [
      {
        "field_name": "document_type",
        "label_text": "Document Type",
        "field_type": "select",
        "is_required": true,
        "field_options": [
          {"value": "pdf", "label": "PDF"},
          {"value": "docx", "label": "Word Document"},
          {"value": "txt", "label": "Text File"}
        ]
      },
      {
        "field_name": "ocr_enabled",
        "label_text": "Enable OCR",
        "field_type": "checkbox",
        "is_required": false
      }
    ]
  },
  {
    "component_type": "markdown",
    "component_key": "instructions",
    "title": "Instructions",
    "component_state": {},
    "markdown_content": "# Document Upload\n\nSelect the document type and upload your file.",
    "content_style": {"padding": "1rem"}
  }
]
```

## The Manifest Generation Process

AgentNexus generates manifests through careful introspection of your agent code:

### 1. Agent Configuration

The process begins with your `AgentConfig` definition:

```python
document_agent = AgentConfig(
    name="Document Assistant",
    version="1.0.0",
    description="Processes and analyzes document files",
    capabilities=[
        Capability(
            skill_path=["Documents", "Processing"],
            metadata={"formats": ["PDF", "DOCX", "TXT"]}
        )
    ]
)
```

### 2. Action Registration

Actions are registered with the `agent_action` decorator, which collects metadata:

```python
@agent_action(
    agent_config=document_agent,
    action_type=ActionType.GENERATE,
    name="Process Document",
    description="Process a document and extract its content"
)
async def process_document(input_data: ProcessInput) -> ProcessOutput:
    # Implementation...
```

### 3. Schema Extraction

The manifest generator extracts schemas from Pydantic models:

```python
class ProcessInput(BaseModel):
    document_url: str = Field(..., description="URL to the document")
    format: Optional[str] = Field(None, description="Document format")
    options: Optional[Dict[str, Any]] = Field(None, description="Processing options")

class ProcessOutput(BaseModel):
    processed_text: str
    page_count: int
    processing_time: float
```

These models automatically become JSON schema in the manifest.

### 4. Workflow Registration

Workflows are registered with the agent and their steps are collected:

```python
DOCUMENT_WORKFLOW = Workflow(
    id="document_processing",
    name="Document Processing",
    description="Process documents through multiple steps",
    steps=[
        WorkflowStep(id="upload"),
        WorkflowStep(id="validate"),
        # More steps...
    ],
    initial_step="upload"
)

document_agent = AgentConfig(
    # Other configuration...
    workflows=[DOCUMENT_WORKFLOW]
)
```

### 5. Step Handler Introspection

Step handlers provide additional metadata through their decorator:

```python
@workflow_step(
    agent_config=document_agent,
    workflow_id="document_processing",
    step_id="upload",
    name="Document Upload",
    ui_components=[upload_form, instructions]
)
async def handle_upload_step(input_data) -> WorkflowStepResponse:
    # Step implementation...
```

### 6. Component Collection

UI components included in actions or workflow steps are collected:

```python
upload_form = FormComponent(
    component_key="document_form",
    title="Document Upload",
    form_fields=[...]
)

instructions = MarkdownComponent(
    component_key="instructions",
    title="Instructions",
    markdown_content="# Document Upload\n\nSelect the document type and upload your file."
)
```

### 7. Endpoint Generation

The manifest includes information about the endpoints for each action and workflow step:

```json
"path": "/agents/document-assistant/actions/process-document",
"method": "POST"
```

### 8. Example Collection

Examples provided in the decorator are included in the manifest:

```python
@agent_action(
    # Other parameters...
    examples={
        "validRequests": [
            {"document_url": "https://example.com/sample.pdf", "format": "PDF"}
        ]
    }
)
```

## The AgentManager and Registry

The manifest generation system uses two key classes:

### 1. AgentRegistry

The `AgentRegistry` class maintains information about a specific agent and generates its manifest:

```python
registry = AgentRegistry(
    base_url="http://localhost:9000",
    name="Document Assistant",
    version="1.0.0",
    description="Processes and analyzes document files",
    capabilities=[...],
    workflows=[...]
)

# Generate manifest
manifest = registry.generate_manifest()
```

### 2. AgentManager

The `AgentManager` class coordinates multiple agents and sets up their routes:

```python
# Initialize the manager
agent_manager = AgentManager(base_url="http://localhost:9000")

# Add agents
agent_manager.add_agent(document_agent)
agent_manager.add_agent(translation_agent)

# Set up routes in FastAPI app
agent_manager.setup_agents(app)
```

## Manifest Endpoints

AgentNexus automatically creates several manifest-related endpoints:

| Endpoint | Description |
|----------|-------------|
| `/agents.json` | Lists all available agents |
| `/agents/{agent_slug}.json` | Complete manifest for a specific agent |
| `/agents` | HTML dashboard listing all agents |
| `/agents/{agent_slug}` | HTML dashboard for a specific agent |

## Remote API Integration

Remote systems can use the manifest to integrate with your agents:

1. **Discovery**: Fetch `/agents.json` to discover available agents
2. **Exploration**: Fetch `/agents/{agent_slug}.json` to learn capabilities
3. **Integration**: Use schema information to build API clients
4. **Execution**: Call action and workflow endpoints with the proper data
5. **UI Building**: Use component information to build dynamic interfaces

## Integration Example

Here's how a client might use the manifest to integrate with your agent:

```python
# Client-side integration using the manifest
import requests
import json

# 1. Discover agents
response = requests.get("http://localhost:9000/agents.json")
agents = response.json()["agents"]

# 2. Get manifest for a specific agent
agent_slug = agents[0]["slug"]
response = requests.get(f"http://localhost:9000/agents/{agent_slug}.json")
manifest = response.json()

# 3. Find an action
process_action = next(
    (a for a in manifest["actions"] if a["slug"] == "process-document"),
    None
)

# 4. Extract endpoint and schema information
endpoint = process_action["path"]
input_schema = process_action["inputSchema"]
output_schema = process_action["outputSchema"]

# 5. Call the action with appropriate data
action_data = {
    "document_url": "https://example.com/sample.pdf",
    "format": "PDF",
    "options": {"ocr": True}
}
response = requests.post(
    f"{manifest['baseUrl']}{endpoint}",
    json=action_data
)
result = response.json()

# 6. Process the result
if response.status_code == 200:
    print(f"Document processed successfully: {result['processed_text'][:100]}...")
else:
    print(f"Error: {result.get('detail', 'Unknown error')}")
```

## UI Integration Example

Remote UI systems can build dynamic interfaces using component information:

```javascript
// Client-side UI building based on manifest
async function buildUIFromManifest() {
  // Fetch manifest
  const response = await fetch('http://localhost:9000/agents/document-assistant.json');
  const manifest = await response.json();

  // Find a workflow
  const workflow = manifest.workflows.find(w => w.id === 'document_processing');

  // Get start endpoint
  const startEndpoint = workflow.endpoints.start;

  // Get UI components
  const components = startEndpoint.uiComponents || [];

  // Build UI dynamically
  const container = document.getElementById('workflow-container');

  for (const component of components) {
    switch (component.component_type) {
      case 'form':
        buildForm(container, component);
        break;
      case 'markdown':
        buildMarkdown(container, component);
        break;
      // Handle other component types...
    }
  }

  // Set up form submission handler
  setupFormSubmission(workflow.endpoints.start.path);
}

// Function to build a form component
function buildForm(container, formComponent) {
  const form = document.createElement('form');
  form.id = formComponent.component_key;
  form.innerHTML = `<h3>${formComponent.title || 'Form'}</h3>`;

  // Build fields
  for (const field of formComponent.form_fields) {
    const fieldContainer = document.createElement('div');
    fieldContainer.className = 'form-field';

    // Label
    const label = document.createElement('label');
    label.textContent = field.label_text;
    if (field.is_required) {
      label.innerHTML += ' <span class="required">*</span>';
    }
    label.htmlFor = field.field_name;
    fieldContainer.appendChild(label);

    // Input field
    let input;
    switch (field.field_type) {
      case 'text':
      case 'email':
      case 'number':
        input = document.createElement('input');
        input.type = field.field_type;
        input.name = field.field_name;
        input.id = field.field_name;
        input.required = field.is_required;
        if (field.placeholder_text) {
          input.placeholder = field.placeholder_text;
        }
        break;
      case 'select':
        input = document.createElement('select');
        input.name = field.field_name;
        input.id = field.field_name;
        input.required = field.is_required;

        // Add options
        if (field.field_options) {
          for (const option of field.field_options) {
            const optionEl = document.createElement('option');
            optionEl.value = option.value;
            optionEl.textContent = option.label;
            input.appendChild(optionEl);
          }
        }
        break;
      // Handle other field types...
    }

    fieldContainer.appendChild(input);
    form.appendChild(fieldContainer);
  }

  // Submit button
  const submitBtn = document.createElement('button');
  submitBtn.type = 'submit';
  submitBtn.textContent = 'Submit';
  form.appendChild(submitBtn);

  container.appendChild(form);
}

// Function to build a markdown component
function buildMarkdown(container, markdownComponent) {
  const div = document.createElement('div');
  div.id = markdownComponent.component_key;
  div.className = 'markdown-content';
  if (markdownComponent.title) {
    div.innerHTML = `<h3>${markdownComponent.title}</h3>`;
  }

  // Convert markdown to HTML (using a library like marked.js)
  // const html = marked(markdownComponent.markdown_content);
  // div.innerHTML += html;

  // Or for simplicity
  div.innerHTML += `<div class="markdown">${markdownComponent.markdown_content}</div>`;

  // Apply custom styles
  if (markdownComponent.content_style) {
    Object.assign(div.style, markdownComponent.content_style);
  }

  container.appendChild(div);
}

// Set up form submission
function setupFormSubmission(endpoint) {
  document.querySelector('form').addEventListener('submit', async (event) => {
    event.preventDefault();

    // Collect form data
    const formData = new FormData(event.target);
    const values = {};
    for (const [key, value] of formData.entries()) {
      values[key] = value;
    }

    // Prepare submission data
    const submissionData = {
      form_data: {
        action: 'submit',
        component_key: event.target.id,
        values: values
      }
    };

    // Submit to agent
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(submissionData)
      });

      const result = await response.json();

      // Process UI updates
      if (result.ui_updates) {
        for (const update of result.ui_updates) {
          updateComponent(update.key, update.state);
        }
      }

      // Handle next step
      if (result.next_step_id) {
        loadStep(result.next_step_id, result.context_updates || {});
      }
    } catch (error) {
      console.error('Error submitting form:', error);
    }
  });
}

// Call function to build UI
buildUIFromManifest();
```

## Template Support

The manifest system supports custom response templates:

```python
@agent_action(
    agent_config=report_agent,
    action_type=ActionType.GENERATE,
    name="Generate Report",
    description="Creates a formatted report",
    response_template_md="templates/report_template.md"
)
async def generate_report(input_data: ReportInput) -> ReportOutput:
    # Implementation...
```

The template path is included in the manifest:

```json
"isMDResponseEnabled": true,
"responseTemplateMD": "# Report: {{title}}\n\n*Generated: {{generated_at}}*\n\n..."
```

## Dynamic Component Discovery

The manifest includes information about component events:

```json
"uiComponents": [
  {
    "component_type": "code_editor",
    "component_key": "code_input",
    "title": "Source Code",
    "supported_events": ["format", "save"],
    "programming_language": "python",
    "editor_content": "# Enter Python code here",
    "availableEvents": ["format", "save"]
  }
]
```

This allows clients to dynamically wire up event handlers.

## Security Considerations

When working with agent manifests, consider these security aspects:

1. **Exposure Control**: Be mindful of what information is exposed in the manifest
2. **Authentication**: Add authentication to restrict access to manifest endpoints
3. **CORS Configuration**: Configure appropriate CORS settings for cross-origin access
4. **Input Validation**: Ensure proper validation of all inputs based on schema
5. **Output Filtering**: Be careful not to expose sensitive data in outputs

## Best Practices

### Manifest Design

1. **Complete Descriptions**: Provide thorough descriptions for actions and parameters
2. **Meaningful Examples**: Include clear examples for all actions
3. **Consistent Naming**: Use consistent naming patterns across the manifest
4. **Version Management**: Update versions when making breaking changes
5. **Documentation Links**: Include links to additional documentation

### Integration Support

1. **Base URL Configuration**: Ensure base_url is correctly configured
2. **Cross-Origin Support**: Configure CORS for web clients
3. **Error Handling**: Return standardized error responses
4. **Rate Limiting**: Implement rate limiting for production APIs
5. **Health Endpoints**: Add health check endpoints for monitoring

## Next Steps

- Learn about [Agent Configuration](../agents) in detail
- Explore [Actions](../actions) for implementing agent functionality
- Understand how [Workflows](../workflows) fit into the manifest
- See how [UI Components](../ui-components) are represented in the manifest