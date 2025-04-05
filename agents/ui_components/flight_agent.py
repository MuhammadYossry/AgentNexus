from typing import Dict, Any
from agentnexus.ui_components import FormComponent, FormField, TableComponent, TableColumn, MarkdownComponent

from agents.ui_handlers.flight_agent import handle_form_submit, handle_seat_selection

flight_info_form = FormComponent(
    component_key="flight_info",
    component_type="form",
    title="Flight Information",
    form_fields=[
        FormField(
            field_name="flight_number",
            label_text="Flight Number",
            field_type="text",
            is_required=True
        ),
        FormField(
            field_name="selected_class",
            label_text="Class",
            field_type="select",
            field_options=[
                {"value": "economy", "label": "Economy"},
                {"value": "business", "label": "Business"},
                {"value": "first", "label": "First Class"}
            ]
        )
    ],
    supported_events=["submit"],
    event_handlers={  # Add event handlers directly here
        "submit": handle_form_submit
    }
)

# Create the table component with event handlers directly
seats_table = TableComponent(
    component_key="seats_table",
    component_type="table",
    title="Available Seats",
    columns=[
        TableColumn(field_name="seat_number", header_text="Seat"),
        TableColumn(field_name="class", header_text="Class"),
        TableColumn(field_name="price", header_text="Price"),
        TableColumn(field_name="available", header_text="Available")
    ],
    table_data=[],
    # Allow naming the event handlers labels to use names like `select_seat` instead of `row_click`
    supported_events=["row_click"],
    event_handlers={
        "row_click": handle_seat_selection,
    }
)

# Status display component remains the same
status_display = MarkdownComponent(
    component_key="status_display",
    component_type="markdown",
    title="Reservation Status",
    markdown_content="Select a seat to complete your reservation.",
    content_style={"padding": "1rem", "backgroundColor": "#f5f5f5"}
)