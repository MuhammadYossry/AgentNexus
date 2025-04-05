---
title: "Creating Workflows"
description: "Define multi-step processes with transitions and state management"
lead: "Learn how to define workflows, create steps, and configure transitions to build complex multi-step processes."
date: 2025-03-25T08:00:00+00:00
lastmod: 2025-03-25T08:00:00+00:00
draft: false
images: []
menu:
  docs:
    parent: "workflow-system"
weight: 510
toc: true
---

## Workflow Fundamentals

A workflow in AgentNexus is a structured process comprising multiple steps, where each step represents a specific stage in the overall process. Workflows provide a way to organize complex interactions into manageable pieces, with managed state transitions and UI integration.

### Key Workflow Concepts

- **Workflow**: The overall process definition, including steps and initial state
- **Workflow Steps**: Individual stages or tasks within the workflow
- **Transitions**: Movement between steps, possibly with conditions
- **Context**: Shared state that persists throughout the workflow
- **Step Handlers**: Functions that implement step behavior

## Defining Workflows

Workflows are defined using the `Workflow` class:

```python
from agentnexus.base_types import Workflow, WorkflowStep, WorkflowStepType

DOCUMENT_WORKFLOW = Workflow(
    id="document_processing",
    name="Document Processing",
    description="Process documents through multiple steps",
    steps=[
        WorkflowStep(id="upload"),
        WorkflowStep(id="validate"),
        WorkflowStep(id="transform"),
        WorkflowStep(id="review"),
        WorkflowStep(id="complete", type=WorkflowStepType.END)
    ],
    initial_step="upload"
)
```

### Workflow Parameters

The `Workflow` class accepts these parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | `str` | Unique identifier for the workflow (required) |
| `name` | `str` | Human-readable name of the workflow (required) |
| `description` | `str` | Detailed description of the workflow (required) |
| `steps` | `List[WorkflowStep]` | List of steps in the workflow (required) |
| `initial_step` | `str` | ID of the first step (required) |

## Defining Workflow Steps

Steps are defined using the `WorkflowStep` class:

```python
from agentnexus.base_types import WorkflowStep, WorkflowStepType

steps = [
    WorkflowStep(
        id="upload",
        type=WorkflowStepType.START  # Optional, defaults to UI_STEP
    ),
    WorkflowStep(
        id="validate",
        type=WorkflowStepType.UI_STEP  # This is the default
    ),
    WorkflowStep(
        id="complete",
        type=WorkflowStepType.END  # Marks the end of the workflow
    )
]
```

### Step Parameters

The `WorkflowStep` class accepts these parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | `str` | Unique identifier for the step (required) |
| `type` | `WorkflowStepType` | Type of workflow step (default: UI_STEP) |
| `action` | `Optional[str]` | Optional action associated with the step |
| `transitions` | `Optional[List[WorkflowTransition]]` | Optional explicit transitions |

### Step Types

AgentNexus supports several step types:

| Step Type | Description | Use Case |
|-----------|-------------|----------|
| `WorkflowStepType.START` | Initial workflow step | Entry point for workflows |
| `WorkflowStepType.UI_STEP` | Interactive step with UI | User input collection |
| `WorkflowStepType.END` | Final workflow step | Completion and summary |

## Registering Workflows with Agents

Workflows need to be registered with an agent:

```python
from agentnexus.base_types import AgentConfig, Capability

document_agent = AgentConfig(
    name="Document Processor",
    version="1.0.0",
    description="Process and transform documents",
    capabilities=[
        Capability(
            skill_path=["Documents", "Processing"],
            metadata={"formats": ["Text", "CSV", "JSON"]}
        )
    ],
    workflows=[DOCUMENT_WORKFLOW]  # Register workflow here
)
```

## Workflow Patterns

### Linear Workflow

A simple sequence of steps:

```python
CHECKOUT_WORKFLOW = Workflow(
    id="checkout",
    name="Checkout Process",
    description="Complete purchase checkout process",
    steps=[
        WorkflowStep(id="cart"),
        WorkflowStep(id="shipping"),
        WorkflowStep(id="payment"),
        WorkflowStep(id="review"),
        WorkflowStep(id="confirmation", type=WorkflowStepType.END)
    ],
    initial_step="cart"
)
```

### Branching Workflow

A workflow with conditional branches:

```python
SUPPORT_WORKFLOW = Workflow(
    id="support_ticket",
    name="Support Ticket Process",
    description="Handle support ticket from creation to resolution",
    steps=[
        WorkflowStep(id="create_ticket"),
        WorkflowStep(id="categorize"),
        WorkflowStep(id="technical_support"),
        WorkflowStep(id="billing_support"),
        WorkflowStep(id="account_support"),
        WorkflowStep(id="verification"),
        WorkflowStep(id="resolution", type=WorkflowStepType.END)
    ],
    initial_step="create_ticket"
)
```

In this example, after the "categorize" step, the workflow branches to one of three support paths based on the ticket category.

### Cyclic Workflow

A workflow that can loop back to previous steps:

```python
CODE_REVIEW_WORKFLOW = Workflow(
    id="code_review",
    name="Code Review Process",
    description="Review and improve code with feedback cycles",
    steps=[
        WorkflowStep(id="upload"),
        WorkflowStep(id="analyze"),
        WorkflowStep(id="improve"),
        WorkflowStep(id="review"),
        WorkflowStep(id="approval"),
        WorkflowStep(id="complete", type=WorkflowStepType.END)
    ],
    initial_step="upload"
)
```

In this example, the workflow can loop back from "review" to "improve" until the code meets quality standards.

## Advanced Workflow Features

### Explicit Transitions

You can define explicit transitions between steps:

```python
from agentnexus.base_types import WorkflowTransition, WorkflowDataMapping

approval_step = WorkflowStep(
    id="approval",
    transitions=[
        WorkflowTransition(
            target="complete",
            condition="approved == true",
            data_mapping=[
                WorkflowDataMapping(
                    source_field="approval_data",
                    target_field="final_approval_details"
                )
            ]
        ),
        WorkflowTransition(
            target="improve",
            condition="approved == false",
            data_mapping=[
                WorkflowDataMapping(
                    source_field="feedback",
                    target_field="improvement_notes"
                )
            ]
        )
    ]
)
```

### Conditional Transitions

In the step handlers, you can implement conditional logic to determine the next step:

```python
@workflow_step(
    agent_config=support_agent,
    workflow_id="support_ticket",
    step_id="categorize",
    name="Categorize Ticket",
    ui_components=[category_form]
)
async def handle_categorize_step(input_data) -> WorkflowStepResponse:
    """Handle ticket categorization."""
    # Extract context and form data
    context = getattr(input_data, 'context', {}) or {}
    form_data = getattr(input_data, 'form_data', None)

    # Process form submission
    if form_data and form_data.get("action") == "submit":
        values = form_data.get("values", {})
        category = values.get("category", "")

        # Determine next step based on category
        next_step = {
            "technical": "technical_support",
            "billing": "billing_support",
            "account": "account_support"
        }.get(category, "technical_support")

        # Move to appropriate support step
        return WorkflowStepResponse(
            data={"status": "categorized", "category": category},
            ui_updates=[],
            next_step_id=next_step,  # Dynamic next step based on category
            context_updates={
                "ticket_category": category,
                "categorized_at": datetime.now().isoformat()
            }
        )

    # Initial step load
    return WorkflowStepResponse(
        data={"status": "ready"},
        ui_updates=[],
        context_updates={}
    )
```

### Data Mapping

You can map data between steps:

```python
@workflow_step(
    agent_config=code_agent,
    workflow_id="code_review",
    step_id="review",
    name="Code Review",
    ui_components=[review_form, improved_code]
)
async def handle_review_step(input_data) -> WorkflowStepResponse:
    """Handle code review step."""
    # Extract context and form data
    context = getattr(input_data, 'context', {}) or {}
    form_data = getattr(input_data, 'form_data', None)

    # Process form submission
    if form_data and form_data.get("action") == "submit":
        values = form_data.get("values", {})
        approved = values.get("approved", "no") == "yes"
        feedback = values.get("feedback", "")

        # Determine next step based on approval
        next_step = "complete" if approved else "improve"

        # Map data differently based on the next step
        if approved:
            context_updates = {
                "approved": True,
                "final_code": context.get("improved_code", ""),
                "approval_time": datetime.now().isoformat()
            }
        else:
            context_updates = {
                "approved": False,
                "feedback": feedback,
                "review_iteration": context.get("review_iteration", 0) + 1
            }

        # Move to next step with appropriate data mapping
        return WorkflowStepResponse(
            data={"status": "reviewed", "approved": approved},
            ui_updates=[],
            next_step_id=next_step,
            context_updates=context_updates
        )

    # Initial step load
    return WorkflowStepResponse(
        data={"status": "ready"},
        ui_updates=[
            UIComponentUpdate(
                key="improved_code",
                state={"editor_content": context.get("improved_code", "")}
            )
        ],
        context_updates={}
    )
```

## Complex Workflow Example

Here's a complete example of a multi-step onboarding workflow:

```python
from agentnexus.base_types import Workflow, WorkflowStep, WorkflowStepType

# Define a comprehensive onboarding workflow
USER_ONBOARDING = Workflow(
    id="user_onboarding",
    name="User Onboarding",
    description="Complete user onboarding process with profile setup and preferences",
    steps=[
        # Phase 1: Account creation
        WorkflowStep(id="create_account"),

        # Phase 2: Profile setup
        WorkflowStep(id="basic_profile"),
        WorkflowStep(id="contact_info"),
        WorkflowStep(id="profile_picture"),

        # Phase 3: Preferences
        WorkflowStep(id="notification_preferences"),
        WorkflowStep(id="privacy_settings"),
        WorkflowStep(id="theme_selection"),

        # Phase 4: Verification and completion
        WorkflowStep(id="email_verification"),
        WorkflowStep(id="review_profile"),
        WorkflowStep(id="welcome", type=WorkflowStepType.END)
    ],
    initial_step="create_account"
)

# Register workflow with agent
user_agent = AgentConfig(
    name="User Management Agent",
    version="1.0.0",
    description="Handles user account management and onboarding",
    capabilities=[
        Capability(
            skill_path=["Users", "Onboarding"],
            metadata={"processes": ["Registration", "Profile Management"]}
        )
    ],
    workflows=[USER_ONBOARDING]
)
```

## Workflow Visual Representation

When designing complex workflows, it can be helpful to create a visual representation:

```
┌─────────────────┐
│ create_account  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌────────────────┐
│  basic_profile  │────▶│  contact_info  │
└────────┬────────┘     └───────┬────────┘
         │                      │
         │                      ▼
         │              ┌────────────────┐
         └─────────────▶│profile_picture │
                        └───────┬────────┘
                                │
                                ▼
┌─────────────────┐     ┌────────────────────────┐
│theme_selection  │◀────│notification_preferences│
└────────┬────────┘     └───────────┬────────────┘
         │                          │
         │                          │
         ▼                          ▼
┌─────────────────┐     ┌────────────────┐
│privacy_settings │◀────│email_verification
└────────┬────────┘     └───────┬────────┘
         │                      │
         │                      ▼
         │              ┌────────────────┐
         └─────────────▶│review_profile  │
                        └───────┬────────┘
                                │
                                ▼
                        ┌────────────────┐
                        │    welcome     │
                        └────────────────┘
```

You can create these diagrams using tools like Mermaid or draw.io, which can help visualize the flow and transitions in complex workflows.

## Best Practices

### Workflow Design

1. **Clear Step Names**: Use descriptive names for steps
2. **Logical Flow**: Arrange steps in a logical sequence
3. **Appropriate Granularity**: Neither too many nor too few steps
4. **Context Sharing**: Ensure proper data flow between steps
5. **Error Handling**: Plan for error cases in each step

### Implementation Tips

1. **Step Independence**: Design steps to be as independent as possible
2. **Context Documentation**: Document the expected context structure
3. **Conditional Transitions**: Use clear conditions for branching
4. **Progress Tracking**: Include progress information in the context
5. **Validate Inputs**: Validate inputs before proceeding to the next step

### Testing Workflows

1. **Step Testing**: Test each step independently
2. **Path Testing**: Test all possible paths through the workflow
3. **Error Testing**: Test error handling in each step
4. **Context Validation**: Verify context is preserved correctly
5. **Edge Cases**: Test boundary conditions and unusual scenarios

## Next Steps

- Learn about [Step Handlers](../step-handlers) to implement step behavior
- Understand [State Management](../state-management) for workflows
- Explore [UI Integration](../ui-integration) for interactive workflows
- See how [Session Management](../session-management) works with workflows