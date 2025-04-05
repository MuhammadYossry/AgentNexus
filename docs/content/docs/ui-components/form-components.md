---
title: "Form Components"
description: "Creating interactive forms for data collection"
lead: "Form components provide a structured way to collect user input with built-in validation and event handling."
date: 2025-03-25T08:00:00+00:00
lastmod: 2025-03-25T08:00:00+00:00
draft: false
images: []
menu:
  docs:
    parent: "ui-components"
weight: 410
toc: true
---

## Introduction to Form Components

The `FormComponent` class is a versatile UI component for collecting structured data from users. Forms can include various field types, validation rules, and event handlers.

Key features include:
- Multiple field types (text, number, select, checkbox, etc.)
- Field validation
- Dynamic field visibility
- Event handling for submissions and changes
- Initial value support

## Basic Form Structure

A form component consists of a container and a collection of form fields:

```python
from agentnexus.ui_components import FormComponent, FormField

contact_form = FormComponent(
    component_key="contact_form",
    title="Contact Information",
    form_fields=[
        FormField(
            field_name="name",
            label_text="Full Name",
            field_type="text",
            is_required=True
        ),
        FormField(
            field_name="email",
            label_text="Email Address",
            field_type="email",
            is_required=True
        ),
        FormField(
            field_name="message",
            label_text="Message",
            field_type="textarea"
        )
    ],
    event_handlers={
        "submit": handle_contact_form_submit
    }
)
```

## Form Parameters

The `FormComponent` class accepts these parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `component_key` | `str` | Unique identifier for this component (required) |
| `title` | `str` | Human-readable title for the form |
| `form_fields` | `List[FormField]` | List of form fields (required) |
| `submit_action_name` | `str` | Name of the submit action (default: "submit") |
| `available_actions` | `List[str]` | List of available actions |
| `event_handlers` | `Dict[str, Callable]` | Functions that handle form events |

## Field Types

Form components support several field types:

| Field Type | Description | Example |
|------------|-------------|---------|
| `text` | Single-line text input | Name, title, short answers |
| `textarea` | Multi-line text area | Comments, descriptions, long answers |
| `number` | Numeric input | Age, quantity, price |
| `email` | Email address input | Email addresses |
| `password` | Password input | Passwords (masked input) |
| `date` | Date picker | Birthdate, appointment date |
| `select` | Dropdown selection | Country, category, single choice |
| `checkbox` | Multiple checkboxes | Multiple selections, true/false |
| `radio` | Radio button group | Mutually exclusive options |

## FormField Definition

Form fields define individual input elements:

```python
from agentnexus.ui_components import FormField

FormField(
    field_name="subscription",
    label_text="Subscription Type",
    field_type="select",
    field_options=[
        {"value": "basic", "label": "Basic"},
        {"value": "premium", "label": "Premium"},
        {"value": "enterprise", "label": "Enterprise"}
    ],
    is_required=True,
    placeholder_text="Select a subscription type",
    validation={"min_length": 1}
)
```

### FormField Parameters

The `FormField` class accepts these parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `field_name` | `str` | Unique name for this field (required) |
| `label_text` | `str` | Label displayed to users (required) |
| `field_type` | `str` | Type of field (text, number, select, etc.) |
| `is_required` | `bool` | Whether the field is required (default: False) |
| `placeholder_text` | `Optional[str]` | Placeholder text shown when empty |
| `field_options` | `Optional[List[Dict[str, str]]]` | Options for select, checkbox, radio |
| `validation` | `Optional[Dict[str, Any]]` | Validation rules for the field |

## Field Options

For fields that offer choices (`select`, `checkbox`, `radio`), you define options:

```python
FormField(
    field_name="country",
    label_text="Country",
    field_type="select",
    field_options=[
        {"value": "us", "label": "United States"},
        {"value": "ca", "label": "Canada"},
        {"value": "mx", "label": "Mexico"},
        {"value": "other", "label": "Other"}
    ]
)
```

The `field_options` parameter takes a list of dictionaries, each with:
- `value`: The internal value (stored and submitted)
- `label`: The human-readable label displayed to users

## Field Validation

Forms support validation rules to ensure data quality:

```python
FormField(
    field_name="password",
    label_text="Password",
    field_type="password",
    is_required=True,
    validation={
        "min_length": 8,
        "pattern": "^(?=.*[A-Za-z])(?=.*\\d)[A-Za-z\\d]{8,}$",
        "pattern_message": "Password must contain letters and numbers"
    }
)
```

### Validation Rules

Common validation rules include:

| Rule | Applicable Types | Description |
|------|------------------|-------------|
| `required` | All | Field must have a value |
| `min_length` | text, textarea, password | Minimum text length |
| `max_length` | text, textarea, password | Maximum text length |
| `min` | number | Minimum numeric value |
| `max` | number | Maximum numeric value |
| `pattern` | text, email, password | Regular expression pattern |
| `pattern_message` | text, email, password | Custom error message for pattern failure |
| `email` | email | Validate as email address |

## Event Handling

Forms emit events that can be handled by your agent:

```python
from typing import Dict, Any
from agentnexus.base_types import WorkflowStepResponse, UIComponentUpdate

async def handle_registration_submit(
    action: str,
    data: Dict[str, Any],
    component_key: str,
    **kwargs
) -> WorkflowStepResponse:
    """Handle registration form submission."""
    # Extract form values
    values = data.get("values", {})
    username = values.get("username", "")
    email = values.get("email", "")

    # Process form data (e.g., create user, store in database)
    # ...

    # Return response with UI updates
    return WorkflowStepResponse(
        data={"registration_complete": True},
        ui_updates=[
            UIComponentUpdate(
                key="status_display",
                state={"markdown_content": f"Thank you for registering, {username}!"}
            )
        ],
        context_updates={
            "username": username,
            "email": email
        }
    )
```

### Form Events

Forms support these events:

| Event | Description | Data Provided |
|-------|-------------|---------------|
| `submit` | Form submission | All form values |
| `field_change` | Individual field change | Field name and new value |
| `validation` | Custom validation | Form values to validate |

### Event Handler Registration

Register event handlers when creating the form:

```python
registration_form = FormComponent(
    component_key="registration_form",
    title="Registration",
    form_fields=[
        # Form fields...
    ],
    event_handlers={
        "submit": handle_registration_submit,
        "field_change": handle_field_change,
        "validation": validate_registration_form
    }
)
```

## Initial Values

You can pre-populate forms with initial values:

```python
user_form = FormComponent(
    component_key="user_form",
    title="User Profile",
    form_fields=[
        FormField(
            field_name="name",
            label_text="Name",
            field_type="text"
        ),
        FormField(
            field_name="email",
            label_text="Email",
            field_type="email"
        )
    ],
    component_state={
        "values": {
            "name": "John Doe",
            "email": "john@example.com"
        }
    }
)
```

Alternatively, you can update a form's values dynamically:

```python
return WorkflowStepResponse(
    data={"user_loaded": True},
    ui_updates=[
        UIComponentUpdate(
            key="user_form",
            state={"values": {
                "name": user.name,
                "email": user.email
            }}
        )
    ],
    context_updates={}
)
```

## Form Layout and Organization

### Form Sections

For longer forms, you can create visual sections:

```python
checkout_form = FormComponent(
    component_key="checkout_form",
    title="Checkout",
    form_fields=[
        # Shipping section
        FormField(
            field_name="shipping_section",
            label_text="Shipping Information",
            field_type="section"
        ),
        FormField(
            field_name="shipping_name",
            label_text="Full Name",
            field_type="text",
            is_required=True
        ),
        FormField(
            field_name="shipping_address",
            label_text="Address",
            field_type="textarea",
            is_required=True
        ),

        # Payment section
        FormField(
            field_name="payment_section",
            label_text="Payment Details",
            field_type="section"
        ),
        FormField(
            field_name="payment_method",
            label_text="Payment Method",
            field_type="select",
            field_options=[
                {"value": "credit", "label": "Credit Card"},
                {"value": "paypal", "label": "PayPal"}
            ],
            is_required=True
        )
    ]
)
```

### Conditional Fields

You can show or hide fields conditionally based on other field values:

```python
contact_form = FormComponent(
    component_key="contact_form",
    title="Contact Preferences",
    form_fields=[
        FormField(
            field_name="contact_method",
            label_text="Preferred Contact Method",
            field_type="select",
            field_options=[
                {"value": "email", "label": "Email"},
                {"value": "phone", "label": "Phone"},
                {"value": "mail", "label": "Postal Mail"}
            ]
        ),
        FormField(
            field_name="email",
            label_text="Email Address",
            field_type="email",
            is_required=True,
            visibility={"field": "contact_method", "value": "email"}
        ),
        FormField(
            field_name="phone",
            label_text="Phone Number",
            field_type="text",
            is_required=True,
            visibility={"field": "contact_method", "value": "phone"}
        ),
        FormField(
            field_name="address",
            label_text="Mailing Address",
            field_type="textarea",
            is_required=True,
            visibility={"field": "contact_method", "value": "mail"}
        )
    ]
)
```

## Advanced Form Features

### Custom Validation

You can implement complex validation logic:

```python
async def validate_registration_form(
    action: str,
    data: Dict[str, Any],
    component_key: str,
    **kwargs
) -> Dict[str, Any]:
    """Custom validation for registration form."""
    values = data.get("values", {})
    password = values.get("password", "")
    confirm_password = values.get("confirm_password", "")

    errors = {}

    # Check password match
    if password and confirm_password and password != confirm_password:
        errors["confirm_password"] = "Passwords do not match"

    # Check username availability
    username = values.get("username", "")
    if username and await is_username_taken(username):
        errors["username"] = "Username is already taken"

    # Return validation result
    if errors:
        return {
            "valid": False,
            "errors": errors
        }

    return {"valid": True}
```

### Field Dependencies

You can create fields that depend on other fields:

```python
product_form = FormComponent(
    component_key="product_form",
    title="Product Configuration",
    form_fields=[
        FormField(
            field_name="product_type",
            label_text="Product Type",
            field_type="select",
            field_options=[
                {"value": "hardware", "label": "Hardware"},
                {"value": "software", "label": "Software"},
                {"value": "service", "label": "Service"}
            ]
        ),
        # Dynamic options based on product type
        FormField(
            field_name="product_subtype",
            label_text="Product Subtype",
            field_type="select",
            field_options_source={"field": "product_type", "values": {
                "hardware": [
                    {"value": "computer", "label": "Computer"},
                    {"value": "peripheral", "label": "Peripheral"}
                ],
                "software": [
                    {"value": "app", "label": "Application"},
                    {"value": "os", "label": "Operating System"}
                ],
                "service": [
                    {"value": "installation", "label": "Installation"},
                    {"value": "support", "label": "Support"}
                ]
            }}
        )
    ]
)
```

### Field Change Handling

You can handle individual field changes:

```python
async def handle_field_change(
    action: str,
    data: Dict[str, Any],
    component_key: str,
    **kwargs
) -> WorkflowStepResponse:
    """Handle form field changes."""
    field_name = data.get("field_name", "")
    field_value = data.get("value", "")

    # Process specific field changes
    if field_name == "zip_code" and field_value:
        # Look up city and state from zip code
        city, state = await lookup_zip_code(field_value)

        # Update other fields
        return WorkflowStepResponse(
            data={"zip_lookup_complete": True},
            ui_updates=[
                UIComponentUpdate(
                    key="address_form",
                    state={"field_updates": [
                        {"field": "city", "value": city},
                        {"field": "state", "value": state}
                    ]}
                )
            ],
            context_updates={}
        )

    # Return empty response for other fields
    return WorkflowStepResponse(
        data={},
        ui_updates=[],
        context_updates={}
    )
```

## Common Form Patterns

### Login Form

```python
login_form = FormComponent(
    component_key="login_form",
    title="Log In",
    form_fields=[
        FormField(
            field_name="username",
            label_text="Username or Email",
            field_type="text",
            is_required=True
        ),
        FormField(
            field_name="password",
            label_text="Password",
            field_type="password",
            is_required=True
        ),
        FormField(
            field_name="remember_me",
            label_text="Remember Me",
            field_type="checkbox",
            field_options=[
                {"value": "true", "label": "Keep me logged in"}
            ]
        )
    ],
    event_handlers={
        "submit": handle_login_submit
    }
)
```

### Search Form

```python
search_form = FormComponent(
    component_key="search_form",
    title="Search Products",
    form_fields=[
        FormField(
            field_name="query",
            label_text="Search Query",
            field_type="text",
            placeholder_text="Enter keywords...",
            is_required=True
        ),
        FormField(
            field_name="category",
            label_text="Category",
            field_type="select",
            field_options=[
                {"value": "", "label": "All Categories"},
                {"value": "electronics", "label": "Electronics"},
                {"value": "clothing", "label": "Clothing"},
                {"value": "books", "label": "Books"}
            ]
        ),
        FormField(
            field_name="price_range",
            label_text="Price Range",
            field_type="select",
            field_options=[
                {"value": "", "label": "Any Price"},
                {"value": "0-25", "label": "Under $25"},
                {"value": "25-100", "label": "$25 to $100"},
                {"value": "100+", "label": "Over $100"}
            ]
        )
    ],
    event_handlers={
        "submit": handle_search_submit
    }
)
```

### Multi-Page Form

For complex forms, you can split them across multiple workflow steps:

```python
# Step 1: Basic Information
basic_info_form = FormComponent(
    component_key="basic_info_form",
    title="Basic Information",
    form_fields=[
        FormField(
            field_name="name",
            label_text="Full Name",
            field_type="text",
            is_required=True
        ),
        FormField(
            field_name="email",
            label_text="Email Address",
            field_type="email",
            is_required=True
        )
    ],
    event_handlers={
        "submit": handle_basic_info_submit
    }
)

# Step 2: Address Information
address_form = FormComponent(
    component_key="address_form",
    title="Address Information",
    form_fields=[
        FormField(
            field_name="street",
            label_text="Street Address",
            field_type="text",
            is_required=True
        ),
        FormField(
            field_name="city",
            label_text="City",
            field_type="text",
            is_required=True
        ),
        FormField(
            field_name="state",
            label_text="State/Province",
            field_type="text",
            is_required=True
        ),
        FormField(
            field_name="zip",
            label_text="ZIP/Postal Code",
            field_type="text",
            is_required=True
        )
    ],
    event_handlers={
        "submit": handle_address_submit
    }
)
```

## Best Practices

### Form Design

1. **Clear Labels**: Use clear, concise labels for all fields
2. **Logical Grouping**: Group related fields together
3. **Field Order**: Place fields in a logical order
4. **Required Fields**: Clearly indicate which fields are required
5. **Field Types**: Use appropriate field types for different data
6. **Validation**: Implement appropriate validation rules
7. **Error Messages**: Provide helpful error messages

### Performance and UX

1. **Minimal Fields**: Include only necessary fields
2. **Initial Focus**: Set initial focus on the first field
3. **Tabbing Order**: Ensure a logical tab order
4. **Validation Timing**: Validate fields at appropriate times (on change, on blur, on submit)
5. **Disable Submit**: Disable submit button until form is valid
6. **Loading States**: Show loading indicators during processing

## Next Steps

- Explore [Table Components](../table-components) for displaying data
- Learn about [Code Editor Components](../code-editor-components) for code input
- Understand [Event Handling](../../core-concepts/event-handling) in depth
- See how forms fit into [Workflows](../../core-concepts/workflows)