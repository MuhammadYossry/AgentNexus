---
title: "Custom Components"
description: "Creating your own UI components for specialized interactions"
lead: "Learn how to create custom UI components to extend AgentNexus with specialized interactive elements."
date: 2025-03-25T08:00:00+00:00
lastmod: 2025-03-25T08:00:00+00:00
draft: false
images: []
menu:
  docs:
    parent: "ui-components"
weight: 450
toc: true
---

## Introduction to Custom Components

While AgentNexus provides several built-in component types, you may need specialized components for unique interactions. The framework allows you to create custom components by extending the base `UIComponent` class.

Custom components can be useful for:
- Domain-specific visualizations
- Specialized input methods
- Interactive visualizations
- Custom editors and viewers
- Composite components combining multiple interactions

## Component Inheritance Hierarchy

All UI components in AgentNexus inherit from the base `UIComponent` class:

```
UIComponent
├── FormComponent
├── TableComponent
├── CodeEditorComponent
├── MarkdownComponent
└── YourCustomComponent
```

## Creating a Basic Custom Component

To create a custom component, extend the `UIComponent` class:

```python
from agentnexus.ui_components import UIComponent
from typing import Dict, Any, Callable, List, Optional, ClassVar

class RatingComponent(UIComponent):
    """Custom component for collecting star ratings."""
    component_type: str = "rating"
    max_stars: int = 5
    initial_rating: int = 0
    star_size: str = "medium"  # small, medium, large
    allow_half_stars: bool = False
    valid_event_types: ClassVar[List[str]] = ["rate", "hover", "reset"]

    def __init__(
        self,
        component_key: str,
        title: Optional[str] = None,
        max_stars: int = 5,
        initial_rating: int = 0,
        star_size: str = "medium",
        allow_half_stars: bool = False,
        event_handlers: Optional[Dict[str, Callable]] = None,
        **kwargs
    ):
        """Initialize the rating component."""
        super().__init__(
            component_type="rating",
            component_key=component_key,
            title=title,
            component_state={
                "max_stars": max_stars,
                "current_rating": initial_rating,
                "star_size": star_size,
                "allow_half_stars": allow_half_stars
            },
            supported_events=["rate", "hover", "reset"],
            event_handlers=event_handlers or {},
            **kwargs
        )
        self.max_stars = max_stars
        self.initial_rating = initial_rating
        self.star_size = star_size
        self.allow_half_stars = allow_half_stars
```

## Component Properties and Methods

Custom components should define:

1. **Properties**: Class attributes that define the component's structure
2. **Initialization**: Constructor that sets up the component
3. **Event Handling**: Methods for processing user interactions
4. **State Management**: Logic for managing component state

### Required Properties

| Property | Type | Description |
|----------|------|-------------|
| `component_type` | `str` | The type identifier for the component |
| `valid_event_types` | `ClassVar[List[str]]` | List of valid event types |

### Optional Properties

| Property | Type | Description |
|----------|------|-------------|
| `metadata` | `Dict[str, Any]` | Additional component metadata |
| `component_state` | `Dict[str, Any]` | Initial state of the component |
| `supported_events` | `List[str]` | Events this component instance supports |

## Event Handling in Custom Components

Custom components can define event handlers for specific interactions:

```python
# Create a rating component with event handlers
product_rating = RatingComponent(
    component_key="product_rating",
    title="Rate this Product",
    max_stars=5,
    initial_rating=0,
    star_size="large",
    allow_half_stars=True,
    event_handlers={
        "rate": handle_rating_submit,
        "reset": handle_rating_reset
    }
)

# Event handler implementation
async def handle_rating_submit(
    action: str,
    data: Dict[str, Any],
    component_key: str,
    **kwargs
) -> WorkflowStepResponse:
    """Handle rating submission."""
    rating = data.get("rating", 0)

    return WorkflowStepResponse(
        data={"rating_submitted": True, "rating": rating},
        ui_updates=[
            UIComponentUpdate(
                key="rating_feedback",
                state={"markdown_content": f"Thank you for your rating of {rating} stars!"}
            )
        ],
        context_updates={
            "product_rating": rating
        }
    )
```

## Implementing Validation

Custom components can implement their own validation logic:

```python
class DateRangeComponent(UIComponent):
    """Custom component for selecting date ranges."""
    component_type: str = "date_range"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    min_date: Optional[str] = None
    max_date: Optional[str] = None
    valid_event_types: ClassVar[List[str]] = ["select", "clear", "validate"]

    def __init__(
        self,
        component_key: str,
        title: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_date: Optional[str] = None,
        max_date: Optional[str] = None,
        event_handlers: Optional[Dict[str, Callable]] = None,
        **kwargs
    ):
        """Initialize the date range component."""
        super().__init__(
            component_type="date_range",
            component_key=component_key,
            title=title,
            component_state={
                "start_date": start_date,
                "end_date": end_date,
                "min_date": min_date,
                "max_date": max_date
            },
            supported_events=["select", "clear", "validate"],
            event_handlers=event_handlers or {},
            **kwargs
        )
        self.start_date = start_date
        self.end_date = end_date
        self.min_date = min_date
        self.max_date = max_date

    async def validate(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Validate the date range."""
        from datetime import datetime

        errors = {}

        # Parse dates
        try:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

            # Check that end date is after start date
            if end <= start:
                errors["end_date"] = "End date must be after start date"

            # Check min date constraint
            if self.min_date:
                min_date = datetime.fromisoformat(self.min_date.replace('Z', '+00:00'))
                if start < min_date:
                    errors["start_date"] = f"Start date must be on or after {self.min_date}"

            # Check max date constraint
            if self.max_date:
                max_date = datetime.fromisoformat(self.max_date.replace('Z', '+00:00'))
                if end > max_date:
                    errors["end_date"] = f"End date must be on or before {self.max_date}"

        except ValueError:
            errors["format"] = "Invalid date format"

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
```

## Using Custom Actions

Custom components can define specialized actions:

```python
class ImageAnnotationComponent(UIComponent):
    """Custom component for annotating images."""
    component_type: str = "image_annotation"
    image_url: str
    annotations: List[Dict[str, Any]] = []
    valid_event_types: ClassVar[List[str]] = [
        "add_annotation", "update_annotation", "delete_annotation",
        "zoom", "pan", "reset_view"
    ]

    def __init__(
        self,
        component_key: str,
        title: Optional[str] = None,
        image_url: str = "",
        annotations: Optional[List[Dict[str, Any]]] = None,
        event_handlers: Optional[Dict[str, Callable]] = None,
        **kwargs
    ):
        """Initialize the image annotation component."""
        super().__init__(
            component_type="image_annotation",
            component_key=component_key,
            title=title,
            component_state={
                "image_url": image_url,
                "annotations": annotations or [],
                "zoom_level": 1.0,
                "pan_x": 0,
                "pan_y": 0
            },
            supported_events=[
                "add_annotation", "update_annotation", "delete_annotation",
                "zoom", "pan", "reset_view"
            ],
            event_handlers=event_handlers or {},
            **kwargs
        )
        self.image_url = image_url
        self.annotations = annotations or []
```

## Component Rendering Hints

While AgentNexus handles the actual rendering of components in the client interface, you can provide hints about how your component should be rendered:

```python
class GaugeComponent(UIComponent):
    """Custom component for displaying gauge/meter visualizations."""
    component_type: str = "gauge"
    min_value: float = 0.0
    max_value: float = 100.0
    current_value: float = 0.0
    thresholds: Dict[str, float] = Field(default_factory=dict)
    rendering_hints: Dict[str, Any] = {
        "display_type": "radial",  # radial, semi-circle, horizontal, vertical
        "color_scheme": "default",  # default, traffic-light, custom
        "animation_speed": "medium",  # slow, medium, fast
        "show_labels": True
    }
    valid_event_types: ClassVar[List[str]] = ["value_change", "threshold_reached"]

    def __init__(
        self,
        component_key: str,
        title: Optional[str] = None,
        min_value: float = 0.0,
        max_value: float = 100.0,
        current_value: float = 0.0,
        thresholds: Optional[Dict[str, float]] = None,
        rendering_hints: Optional[Dict[str, Any]] = None,
        event_handlers: Optional[Dict[str, Callable]] = None,
        **kwargs
    ):
        """Initialize the gauge component."""
        merged_hints = {
            "display_type": "radial",
            "color_scheme": "default",
            "animation_speed": "medium",
            "show_labels": True
        }
        if rendering_hints:
            merged_hints.update(rendering_hints)

        super().__init__(
            component_type="gauge",
            component_key=component_key,
            title=title,
            component_state={
                "min_value": min_value,
                "max_value": max_value,
                "current_value": current_value,
                "thresholds": thresholds or {},
                "rendering_hints": merged_hints
            },
            supported_events=["value_change", "threshold_reached"],
            event_handlers=event_handlers or {},
            metadata={"rendering_hints": merged_hints},
            **kwargs
        )
        self.min_value = min_value
        self.max_value = max_value
        self.current_value = current_value
        self.thresholds = thresholds or {}
        self.rendering_hints = merged_hints
```

## Complex Component Examples

### Interactive Chart Component

```python
class ChartComponent(UIComponent):
    """Interactive chart component."""
    component_type: str = "chart"
    chart_type: str = "line"  # line, bar, pie, scatter, etc.
    data: Dict[str, Any] = {}
    options: Dict[str, Any] = {}
    valid_event_types: ClassVar[List[str]] = ["data_point_click", "legend_click", "zoom", "download"]

    def __init__(
        self,
        component_key: str,
        title: Optional[str] = None,
        chart_type: str = "line",
        data: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None,
        event_handlers: Optional[Dict[str, Callable]] = None,
        **kwargs
    ):
        """Initialize the chart component."""
        super().__init__(
            component_type="chart",
            component_key=component_key,
            title=title,
            component_state={
                "chart_type": chart_type,
                "data": data or {},
                "options": options or {}
            },
            supported_events=["data_point_click", "legend_click", "zoom", "download"],
            event_handlers=event_handlers or {},
            **kwargs
        )
        self.chart_type = chart_type
        self.data = data or {}
        self.options = options or {}

# Usage example
sales_chart = ChartComponent(
    component_key="sales_chart",
    title="Monthly Sales",
    chart_type="bar",
    data={
        "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "datasets": [
            {
                "label": "2024 Sales",
                "data": [12, 19, 3, 5, 2, 3],
                "backgroundColor": "rgba(54, 162, 235, 0.2)"
            },
            {
                "label": "2023 Sales",
                "data": [7, 11, 5, 8, 3, 7],
                "backgroundColor": "rgba(255, 99, 132, 0.2)"
            }
        ]
    },
    options={
        "responsive": True,
        "title": {
            "display": True,
            "text": "Monthly Sales Comparison"
        }
    },
    event_handlers={
        "data_point_click": handle_data_point_click
    }
)
```

### File Upload Component

```python
class FileUploadComponent(UIComponent):
    """Custom file upload component."""
    component_type: str = "file_upload"
    accept: str = "*/*"  # File types to accept
    multiple: bool = False  # Allow multiple files
    max_size: int = 10485760  # 10MB default
    upload_url: Optional[str] = None  # Custom upload endpoint
    valid_event_types: ClassVar[List[str]] = ["file_selected", "upload_start", "upload_progress", "upload_complete", "upload_error"]

    def __init__(
        self,
        component_key: str,
        title: Optional[str] = None,
        accept: str = "*/*",
        multiple: bool = False,
        max_size: int = 10485760,
        upload_url: Optional[str] = None,
        event_handlers: Optional[Dict[str, Callable]] = None,
        **kwargs
    ):
        """Initialize the file upload component."""
        super().__init__(
            component_type="file_upload",
            component_key=component_key,
            title=title,
            component_state={
                "accept": accept,
                "multiple": multiple,
                "max_size": max_size,
                "upload_url": upload_url,
                "files": [],
                "upload_status": "idle"  # idle, selecting, uploading, complete, error
            },
            supported_events=["file_selected", "upload_start", "upload_progress", "upload_complete", "upload_error"],
            event_handlers=event_handlers or {},
            **kwargs
        )
        self.accept = accept
        self.multiple = multiple
        self.max_size = max_size
        self.upload_url = upload_url

# Usage example
document_uploader = FileUploadComponent(
    component_key="document_uploader",
    title="Upload Documents",
    accept=".pdf,.doc,.docx",
    multiple=True,
    max_size=20971520,  # 20MB
    event_handlers={
        "file_selected": handle_file_selected,
        "upload_complete": handle_upload_complete
    }
)
```

## Registering Custom Components

Custom components need to be registered with the event dispatcher:

```python
from agentnexus.event_dispatcher import global_event_dispatcher

# Create the component
map_component = MapComponent(
    component_key="location_map",
    title="Location Selection",
    initial_latitude=37.7749,
    initial_longitude=-122.4194,
    zoom_level=12,
    map_type="roadmap",
    event_handlers={
        "marker_added": handle_marker_added,
        "map_clicked": handle_map_clicked
    }
)

# Register the component with the global dispatcher
global_event_dispatcher.register_component(map_component)
```

## Using Custom Components in Workflows

Custom components can be used in workflow steps just like built-in components:

```python
from agentnexus.workflow_manager import workflow_step
from agentnexus.base_types import WorkflowStepResponse

@workflow_step(
    agent_config=location_agent,
    workflow_id="location_selection",
    step_id="select_location",
    name="Location Selection",
    description="Select a location on the map",
    ui_components=[location_instructions, map_component, location_form]
)
async def handle_location_step(input_data) -> WorkflowStepResponse:
    """Handle location selection step."""
    # Implementation
    # ...
```

## Integration with LLM-based Agents

Custom components can be used with LLM agents for specialized interactions:

```python
@agent_action(
    agent_config=visualization_agent,
    action_type=ActionType.CUSTOM_UI,
    name="Data Visualization",
    description="Visualize data with interactive charts",
    ui_components=[data_form, chart_component, chart_controls]
)
async def data_visualization(input_data) -> UIResponse:
    """Handle data visualization with custom chart component."""
    # Implementation
    # ...
```

## Best Practices

### Component Design

1. **Clear Purpose**: Each component should have a single, well-defined purpose
2. **Standard Patterns**: Follow established UI patterns when possible
3. **Focused Events**: Define specific, meaningful events
4. **Comprehensive State**: Ensure state includes all necessary properties
5. **Clear Documentation**: Document component behavior and events

### Implementation

1. **Type Hints**: Use proper type hints for all properties and methods
2. **Default Values**: Provide sensible defaults for optional properties
3. **Error Handling**: Handle invalid inputs and states gracefully
4. **State Validation**: Validate state updates before applying them
5. **Event Consistency**: Make event data structure consistent

### Integration

1. **Global Registration**: Register components with the global dispatcher
2. **Context Management**: Preserve component state in workflow context
3. **Clear Updates**: Make UI updates specific and targeted
4. **Browser Compatibility**: Consider cross-browser compatibility
5. **Accessibility**: Make components accessible to all users

## Next Steps

- Learn how to [Extend AgentNexus](../../advanced-topics/extending-fastagents) with custom features
- Understand [Component Events](../../core-concepts/event-handling) in depth
- Explore how to use custom components in [Workflows](../../core-concepts/workflows)
- See the [Custom Component Example](../../examples/custom-component) for a complete implementation