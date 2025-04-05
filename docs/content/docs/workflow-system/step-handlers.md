    ---
title: "Step Handlers"
description: "Implementing workflow step behavior with handlers"
lead: "Step handlers define the behavior of each step in a workflow, processing input and determining the next step."
date: 2025-03-25T08:00:00+00:00
lastmod: 2025-03-25T08:00:00+00:00
draft: false
images: []
menu:
  docs:
    parent: "workflow-system"
weight: 520
toc: true
---

## Understanding Step Handlers

Step handlers are asynchronous functions that implement the behavior of workflow steps. They:

- Process user input and form submissions
- Perform business logic and data processing
- Update the UI to reflect the current state
- Update the shared context with relevant data
- Determine the next step in the workflow

Step handlers are connected to workflow steps using the `workflow_step` decorator, which associates the function with a specific step in a workflow.

## Basic Step Handler Structure

A step handler follows this basic structure:

```python
from agentnexus.workflow_manager import workflow_step
from agentnexus.base_types import WorkflowStepResponse, UIComponentUpdate

@workflow_step(
    agent_config=my_agent,
    workflow_id="my_workflow",
    step_id="my_step",
    name="My Step",
    description="This is a sample step",
    ui_components=[my_form, my_display]
)
async def handle_my_step(input_data) -> WorkflowStepResponse:
    """Handle my workflow step."""
    # Extract context and form data
    context = getattr(input_data, 'context', {}) or {}
    form_data = getattr(input_data, 'form_data', None)

    # Check for form submission
    if form_data and form_data.get("action") == "submit":
        # Process form submission
        values = form_data.get("values", {})

        # Return response with next step
        return WorkflowStepResponse(
            data={"status": "complete"},
            ui_updates=[],
            next_step_id="next_step",
            context_updates={
                "field1": values.get("field1", ""),
                "field2": values.get("field2", "")
            }
        )

    # Initial step load
    return WorkflowStepResponse(
        data={"status": "ready"},
        ui_updates=[
            UIComponentUpdate(
                key="my_form",
                state={"values": {
                    "field1": context.get("field1", ""),
                    "field2": context.get("field2", "")
                }}
            )
        ],
        context_updates={}
    )
```

## Step Handler Decorator

The `workflow_step` decorator associates a function with a workflow step:

```python
@workflow_step(
    agent_config=document_agent,
    workflow_id="document_processing",
    step_id="upload",
    name="Document Upload",
    description="Upload a document for processing",
    ui_components=[upload_form, document_preview]
)
async def handle_upload_step(input_data) -> WorkflowStepResponse:
    # Implementation
    # ...
```

### Decorator Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_config` | `AgentConfig` | The agent this workflow belongs to (required) |
| `workflow_id` | `str` | Identifier of the workflow (required) |
| `step_id` | `str` | Identifier of the step within the workflow (required) |
| `name` | `str` | Human-readable name of the step (required) |
| `description` | `str` | Detailed description of the step (required) |
| `ui_components` | `Optional[List[UIComponent]]` | UI components for this step |
| `allow_dynamic_ui` | `bool` | Whether to allow dynamic UI updates (default: True) |

## Input Data Structure

The `input_data` parameter passed to step handlers contains:

```python
class WorkflowStepInput:
    # Session ID for this workflow instance
    session_id: Optional[str]

    # Shared context data
    context: Dict[str, Any]

    # Optional form submission data
    form_data: Optional[Dict[str, Any]]

    # Additional parameters
    params: Optional[Dict[str, Any]]
```

### Extracting Input Data

Since the input structure can vary, it's best to extract data defensively:

```python
def extract_input_data(input_data) -> Dict[str, Any]:
    """Extract data from input safely."""
    result = {
        'context': {},
        'form_data': {},
        'session_id': None
    }

    # Extract context
    if hasattr(input_data, 'context'):
        result['context'] = input_data.context or {}
    elif isinstance(input_data, dict) and 'context' in input_data:
        result['context'] = input_data['context'] or {}

    # Extract form_data
    if hasattr(input_data, 'form_data'):
        result['form_data'] = input_data.form_data or {}
    elif isinstance(input_data, dict) and 'form_data' in input_data:
        result['form_data'] = input_data['form_data'] or {}

    # Extract session_id
    if hasattr(input_data, 'session_id'):
        result['session_id'] = input_data.session_id
    elif isinstance(input_data, dict) and 'session_id' in input_data:
        result['session_id'] = input_data['session_id']

    return result
```

Then use it in your handler:

```python
async def handle_my_step(input_data) -> WorkflowStepResponse:
    """Handle my workflow step."""
    # Extract data safely
    extracted = extract_input_data(input_data)
    context = extracted['context']
    form_data = extracted['form_data']
    session_id = extracted['session_id']

    # Rest of handler implementation
    # ...
```

## Step Response Structure

Step handlers return a `WorkflowStepResponse` object that determines:

- What data to return to the client
- Which UI components to update
- What context to preserve for the next step
- Which step to transition to next

```python
return WorkflowStepResponse(
    data={"status": "complete", "message": "Step completed successfully"},
    ui_updates=[
        UIComponentUpdate(
            key="result_display",
            state={"markdown_content": "Step completed successfully!"}
        )
    ],
    next_step_id="next_step",  # Go to this step next
    context_updates={
        "completed_at": datetime.now().isoformat(),
        "result": process_result
    }
)
```

### Response Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `Dict[str, Any]` | Data to return to the client |
| `ui_updates` | `List[UIComponentUpdate]` | UI component updates |
| `next_step_id` | `Optional[str]` | ID of the next step (None to stay on current step) |
| `context_updates` | `Dict[str, Any]` | Updates to the workflow context |

## Component Event Handling

Step handlers can process events from UI components:

```python
async def handle_document_step(input_data) -> WorkflowStepResponse:
    """Handle document processing step."""
    # Extract data
    extracted = extract_input_data(input_data)
    context = extracted['context']
    form_data = extracted['form_data']

    # Check for component events
    if form_data:
        action = form_data.get("action")
        component_key = form_data.get("component_key")

        # Handle file upload event
        if action == "file_uploaded" and component_key == "document_uploader":
            file_data = form_data.get("file_data", {})
            file_name = file_data.get("name", "")
            file_content = file_data.get("content", "")

            # Process the uploaded file
            processed_content = process_file(file_content)

            # Update UI and context
            return WorkflowStepResponse(
                data={"file_processed": True, "file_name": file_name},
                ui_updates=[
                    UIComponentUpdate(
                        key="document_preview",
                        state={"content": processed_content}
                    ),
                    UIComponentUpdate(
                        key="status_message",
                        state={"markdown_content": f"File '{file_name}' uploaded successfully."}
                    )
                ],
                context_updates={
                    "file_name": file_name,
                    "file_content": file_content,
                    "processed_content": processed_content
                }
            )

        # Handle form submission
        elif action == "submit" and component_key == "settings_form":
            # Process form values
            # ...

    # Initial step load
    # ...
```

## Common Step Handler Patterns

### Form Processing Step

A step that collects and processes form data:

```python
@workflow_step(
    agent_config=registration_agent,
    workflow_id="user_registration",
    step_id="contact_info",
    name="Contact Information",
    description="Collect user contact information",
    ui_components=[contact_form, instructions]
)
async def handle_contact_step(input_data) -> WorkflowStepResponse:
    """Handle contact information step."""
    # Extract context and form data
    context = getattr(input_data, 'context', {}) or {}
    form_data = getattr(input_data, 'form_data', None)

    # Process form submission
    if form_data and form_data.get("action") == "submit":
        # Extract form values
        values = form_data.get("values", {})
        email = values.get("email", "")
        phone = values.get("phone", "")
        address = values.get("address", "")

        # Validate email (simplified example)
        if not "@" in email:
            return WorkflowStepResponse(
                data={"status": "validation_error", "field": "email"},
                ui_updates=[
                    UIComponentUpdate(
                        key="contact_form",
                        state={"errors": {"email": "Invalid email address"}}
                    )
                ],
                context_updates={}
            )

        # Move to next step
        return WorkflowStepResponse(
            data={"status": "contact_info_complete"},
            ui_updates=[],
            next_step_id="preferences",
            context_updates={
                "contact_email": email,
                "contact_phone": phone,
                "contact_address": address
            }
        )

    # Initial step load - populate form with existing data
    return WorkflowStepResponse(
        data={"status": "ready"},
        ui_updates=[
            UIComponentUpdate(
                key="contact_form",
                state={"values": {
                    "email": context.get("contact_email", ""),
                    "phone": context.get("contact_phone", ""),
                    "address": context.get("contact_address", "")
                }}
            )
        ],
        context_updates={}
    )
```

### Data Processing Step

A step that processes data without user input:

```python
@workflow_step(
    agent_config=data_agent,
    workflow_id="data_analysis",
    step_id="analyze",
    name="Data Analysis",
    description="Analyze the uploaded data",
    ui_components=[analysis_results, progress_indicator]
)
async def handle_analyze_step(input_data) -> WorkflowStepResponse:
    """Handle data analysis step."""
    # Extract context
    context = getattr(input_data, 'context', {}) or {}

    # Get data from context
    data = context.get("uploaded_data")
    if not data:
        return WorkflowStepResponse(
            data={"status": "error", "message": "No data to analyze"},
            ui_updates=[
                UIComponentUpdate(
                    key="analysis_results",
                    state={"markdown_content": "## Error\n\nNo data available for analysis."}
                )
            ],
            context_updates={}
        )

    # Perform analysis (simplified example)
    try:
        import pandas as pd
        import numpy as np
        import json

        # Parse data as CSV
        df = pd.read_csv(io.StringIO(data))

        # Perform basic analysis
        analysis_results = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "numeric_columns": list(df.select_dtypes(include=[np.number]).columns),
            "missing_values": df.isnull().sum().to_dict(),
            "summary": json.loads(df.describe().to_json())
        }

        # Format results as markdown
        markdown_results = f"""
## Analysis Results

**Dataset Overview:**
- Rows: {analysis_results['row_count']}
- Columns: {analysis_results['column_count']}

**Column Types:**
- Numeric columns: {', '.join(analysis_results['numeric_columns'])}

**Missing Values:**
{chr(10).join(['- ' + col + ': ' + str(val) for col, val in analysis_results['missing_values'].items() if val > 0])}

**Basic Statistics:**
```
{df.describe().to_string()}
```
        """

        # Update UI and context
        return WorkflowStepResponse(
            data={"status": "analysis_complete"},
            ui_updates=[
                UIComponentUpdate(
                    key="analysis_results",
                    state={"markdown_content": markdown_results}
                ),
                UIComponentUpdate(
                    key="progress_indicator",
                    state={"progress": 100, "status": "complete"}
                )
            ],
            next_step_id="visualize",
            context_updates={
                "analysis_results": analysis_results,
                "analysis_markdown": markdown_results
            }
        )
    except Exception as e:
        return WorkflowStepResponse(
            data={"status": "error", "message": str(e)},
            ui_updates=[
                UIComponentUpdate(
                    key="analysis_results",
                    state={"markdown_content": f"## Error\n\nAn error occurred during analysis: {str(e)}"}
                ),
                UIComponentUpdate(
                    key="progress_indicator",
                    state={"progress": 0, "status": "error"}
                )
            ],
            context_updates={}
        )
```

### Decision Step

A step with branching based on user choice:

```python
@workflow_step(
    agent_config=support_agent,
    workflow_id="support_request",
    step_id="issue_type",
    name="Issue Type",
    description="Determine the type of support issue",
    ui_components=[issue_type_form, help_text]
)
async def handle_issue_type_step(input_data) -> WorkflowStepResponse:
    """Handle issue type selection step."""
    # Extract context and form data
    context = getattr(input_data, 'context', {}) or {}
    form_data = getattr(input_data, 'form_data', None)

    # Process form submission
    if form_data and form_data.get("action") == "submit":
        # Extract issue type
        values = form_data.get("values", {})
        issue_type = values.get("issue_type", "")

        # Determine next step based on issue type
        next_steps = {
            "technical": "technical_details",
            "billing": "billing_details",
            "account": "account_details",
            "other": "describe_issue"
        }

        next_step = next_steps.get(issue_type, "describe_issue")

        # Move to appropriate next step
        return WorkflowStepResponse(
            data={"status": "issue_type_selected", "issue_type": issue_type},
            ui_updates=[],
            next_step_id=next_step,
            context_updates={
                "issue_type": issue_type
            }
        )

    # Initial step load
    return WorkflowStepResponse(
        data={"status": "ready"},
        ui_updates=[
            UIComponentUpdate(
                key="issue_type_form",
                state={"values": {
                    "issue_type": context.get("issue_type", "")
                }}
            ),
            UIComponentUpdate(
                key="help_text",
                state={"markdown_content": """
## Select Issue Type

Please select the category that best describes your issue:

- **Technical**: Issues with software, hardware, or services
- **Billing**: Questions about invoices, payments, or subscriptions
- **Account**: Problems with login, permissions, or account settings
- **Other**: Any issues that don't fit the categories above
                """}
            )
        ],
        context_updates={}
    )
```

### Final/Summary Step

A step that presents a summary at the end of a workflow:

```python
@workflow_step(
    agent_config=order_agent,
    workflow_id="order_placement",
    step_id="confirmation",
    name="Order Confirmation",
    description="Confirm order details and complete the order",
    ui_components=[order_summary, confirmation_message]
)
async def handle_confirmation_step(input_data) -> WorkflowStepResponse:
    """Handle order confirmation step."""
    # Extract context
    context = getattr(input_data, 'context', {}) or {}

    # Get order details from context
    order_items = context.get("order_items", [])
    shipping_address = context.get("shipping_address", {})
    payment_method = context.get("payment_method", {})

    # Calculate order total
    order_total = sum(item.get("price", 0) * item.get("quantity", 0) for item in order_items)

    # Generate order ID
    import uuid
    order_id = str(uuid.uuid4())[:8].upper()

    # Format order summary
    items_list = "\n".join([
        f"- {item.get('quantity')}x {item.get('name')} - ${item.get('price'):.2f} each"
        for item in order_items
    ])

    address_formatted = f"{shipping_address.get('street')}, {shipping_address.get('city')}, {shipping_address.get('state')} {shipping_address.get('zip')}"

    summary_markdown = f"""
## Order Confirmation

**Order ID:** {order_id}

### Items:
{items_list}

**Total:** ${order_total:.2f}

### Shipping Address:
{address_formatted}

### Payment Method:
{payment_method.get('type')} ending in {payment_method.get('last4')}

Your order has been placed successfully and will be processed shortly.
You will receive a confirmation email at {context.get('email')}.

Thank you for your order!
    """

    # Create confirmation message
    confirmation_text = f"""
# Thank You for Your Order!

Your order #{order_id} has been successfully placed.

## Next Steps

1. You'll receive a confirmation email shortly
2. You can track your order status on your account page
3. Expected delivery: 3-5 business days

[View Order Status](#) | [Continue Shopping](#)
    """

    # Return final step
    return WorkflowStepResponse(
        data={
            "status": "order_complete",
            "order_id": order_id,
            "order_total": order_total
        },
        ui_updates=[
            UIComponentUpdate(
                key="order_summary",
                state={"markdown_content": summary_markdown}
            ),
            UIComponentUpdate(
                key="confirmation_message",
                state={"markdown_content": confirmation_text}
            )
        ],
        next_step_id=None,  # No next step (end of workflow)
        context_updates={
            "order_id": order_id,
            "order_total": order_total,
            "order_date": datetime.now().isoformat(),
            "order_status": "placed"
        }
    )
```

## Integration with LLM Agents

Step handlers can integrate with LLM-powered agents:

```python
@workflow_step(
    agent_config=content_agent,
    workflow_id="content_creation",
    step_id="generate",
    name="Content Generation",
    description="Generate content based on requirements",
    ui_components=[requirements_form, content_editor, generation_options]
)
async def handle_generate_step(input_data) -> WorkflowStepResponse:
    """Handle content generation step with LLM integration."""
    # Extract context and form data
    context = getattr(input_data, 'context', {}) or {}
    form_data = getattr(input_data, 'form_data', None)

    # Get generation parameters
    if form_data and form_data.get("action") == "submit":
        values = form_data.get("values", {})

        # Topic or title
        topic = values.get("topic", "")

        # Content type
        content_type = values.get("content_type", "blog_post")

        # Content parameters
        tone = values.get("tone", "informative")
        length = values.get("length", "medium")

        # Additional requirements
        keywords = values.get("keywords", "").split(",")
        target_audience = values.get("target_audience", "general")

        # Create prompt for LLM
        prompt = f"""
        Create a {content_type} about "{topic}".

        Tone: {tone}
        Length: {length}
        Target audience: {target_audience}
        Keywords to include: {', '.join(keywords)}

        The content should be well-structured, engaging, and formatted with Markdown.
        """

        try:
            # Initialize LLM client
            from agents.llm_client import create_llm_client
            llm_client = create_llm_client()

            # Generate content with LLM
            response = await llm_client.complete(
                prompt=prompt,
                system_message="You are an expert content creator specializing in producing high-quality, engaging content.",
                temperature=0.7
            )

            generated_content = response.content

            # Return generated content
            return WorkflowStepResponse(
                data={"status": "content_generated", "content_type": content_type},
                ui_updates=[
                    UIComponentUpdate(
                        key="content_editor",
                        state={"editor_content": generated_content}
                    )
                ],
                context_updates={
                    "generated_content": generated_content,
                    "content_type": content_type,
                    "topic": topic,
                    "generation_parameters": {
                        "tone": tone,
                        "length": length,
                        "keywords": keywords,
                        "target_audience": target_audience
                    }
                }
            )
        except Exception as e:
            return WorkflowStepResponse(
                data={"status": "error", "message": str(e)},
                ui_updates=[
                    UIComponentUpdate(
                        key="error_message",
                        state={"markdown_content": f"## Error\n\nAn error occurred during content generation: {str(e)}"}
                    )
                ],
                context_updates={}
            )

    # Initial step load
    return WorkflowStepResponse(
        data={"status": "ready"},
        ui_updates=[
            UIComponentUpdate(
                key="requirements_form",
                state={"values": {
                    "topic": context.get("topic", ""),
                    "content_type": context.get("content_type", "blog_post"),
                    "tone": context.get("tone", "informative"),
                    "length": context.get("length", "medium"),
                    "keywords": ",".join(context.get("keywords", [])),
                    "target_audience": context.get("target_audience", "general")
                }}
            )
        ],
        context_updates={}
    )
```

## Best Practices

### Error Handling

Implement proper error handling in step handlers:

```python
try:
    # Main logic
    result = process_data(data)
    return WorkflowStepResponse(
        data={"status": "success"},
        ui_updates=[...],
        context_updates={...}
    )
except ValidationError as e:
    # Handle validation errors
    return WorkflowStepResponse(
        data={"status": "validation_error", "errors": e.errors()},
        ui_updates=[
            UIComponentUpdate(
                key="error_message",
                state={"markdown_content": f"## Validation Error\n\n{str(e)}"}
            ),
            UIComponentUpdate(
                key="form",
                state={"errors": e.errors()}
            )
        ],
        context_updates={}
    )
except Exception as e:
    # Handle unexpected errors
    logger.error(f"Error in step handler: {str(e)}")
    return WorkflowStepResponse(
        data={"status": "error", "message": str(e)},
        ui_updates=[
            UIComponentUpdate(
                key="error_message",
                state={"markdown_content": f"## Error\n\nAn unexpected error occurred: {str(e)}"}
            )
        ],
        context_updates={}
    )
```

### Context Management

Use consistent context keys and provide fallbacks:

```python
# Consistently defined context keys
CONTEXT_KEYS = {
    "USER_PROFILE": "user_profile",
    "PREFERENCES": "preferences",
    "SUBMISSION_DATA": "submission_data"
}

# Access context with fallbacks
user_profile = context.get(CONTEXT_KEYS["USER_PROFILE"], {})
name = user_profile.get("name", "Guest")
```

### Step Independence

Design steps to be as independent as possible:

```python
# Each step should validate its inputs
def validate_inputs(context):
    """Validate required context data for this step."""
    errors = []
    if "user_id" not in context:
        errors.append("User ID is required")
    if "document_id" not in context:
        errors.append("Document ID is required")
    return errors

# Check for input issues
input_errors = validate_inputs(context)
if input_errors:
    return WorkflowStepResponse(
        data={"status": "input_error", "errors": input_errors},
        ui_updates=[
            UIComponentUpdate(
                key="error_message",
                state={"markdown_content": f"## Input Errors\n\n- {chr(10).join(input_errors)}"}
            )
        ],
        context_updates={}
    )
```

### Progress Tracking

Include progress information in responses:

```python
# Calculate workflow progress
total_steps = 5
current_step_index = 2  # 0-based index
progress_percentage = int((current_step_index / (total_steps - 1)) * 100)

# Include progress in the response
return WorkflowStepResponse(
    data={
        "status": "step_complete",
        "progress": {
            "current_step": current_step_index + 1,
            "total_steps": total_steps,
            "percentage": progress_percentage
        }
    },
    ui_updates=[
        UIComponentUpdate(
            key="progress_bar",
            state={"progress": progress_percentage}
        ),
        UIComponentUpdate(
            key="progress_text",
            state={"markdown_content": f"Step {current_step_index + 1} of {total_steps}"}
        )
    ],
    context_updates={
        "workflow_progress": {
            "current_step": current_step_index + 1,
            "total_steps": total_steps,
            "percentage": progress_percentage
        }
    }
)
```

## Next Steps

- Learn about [State Management](../state-management) for preserving context
- Explore [UI Integration](../ui-integration) for interactive workflows
- Understand [Session Management](../session-management) for persistence
- See the [Workflow Examples](../../examples/workflows) for complete implementations