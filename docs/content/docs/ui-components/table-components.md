---
title: "Table Components"
description: "Working with tabular data display and interactive tables"
lead: "Table components provide a powerful way to display structured data with sorting, pagination, and interactive features."
date: 2025-03-25T08:00:00+00:00
lastmod: 2025-03-25T08:00:00+00:00
draft: false
images: []
menu:
  docs:
    parent: "ui-components"
weight: 420
toc: true
---

## Introduction to Table Components

The `TableComponent` class in AgentNexus provides an interactive way to display tabular data with features like:

- Column definitions with headers
- Sortable columns
- Row selection and actions
- Pagination
- Dynamic data updates
- Custom styling

Tables are perfect for displaying:
- Search results
- Data listings
- Selection interfaces
- Comparison views
- Dashboards

## Basic Table Structure

A table component consists of column definitions and data rows:

```python
from agentnexus.ui_components import TableComponent, TableColumn

products_table = TableComponent(
    component_key="products_table",
    title="Product Catalog",
    columns=[
        TableColumn(field_name="id", header_text="ID"),
        TableColumn(field_name="name", header_text="Product Name"),
        TableColumn(field_name="price", header_text="Price"),
        TableColumn(field_name="category", header_text="Category"),
        TableColumn(field_name="in_stock", header_text="In Stock")
    ],
    table_data=[
        {"id": 1, "name": "Laptop", "price": 999.99, "category": "Electronics", "in_stock": True},
        {"id": 2, "name": "Desk Chair", "price": 199.99, "category": "Furniture", "in_stock": True},
        {"id": 3, "name": "Coffee Maker", "price": 49.99, "category": "Appliances", "in_stock": False}
    ],
    event_handlers={
        "row_click": handle_product_selection
    }
)
```

## Table Parameters

The `TableComponent` class accepts these parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `component_key` | `str` | Unique identifier for this component (required) |
| `title` | `str` | Human-readable title for the table |
| `columns` | `List[TableColumn]` | Column definitions (required) |
| `table_data` | `List[Dict[str, Any]]` | Data rows for the table |
| `enable_pagination` | `bool` | Whether to enable pagination (default: True) |
| `rows_per_page` | `int` | Number of rows per page (default: 10) |
| `supported_events` | `List[str]` | Events the table can emit |
| `event_handlers` | `Dict[str, Callable]` | Functions that handle table events |

## Column Definitions

Table columns are defined using the `TableColumn` class:

```python
from agentnexus.ui_components import TableColumn

columns = [
    TableColumn(
        field_name="order_id",
        header_text="Order ID",
        sortable=True,
        column_width="100px"
    ),
    TableColumn(
        field_name="customer_name",
        header_text="Customer",
        sortable=True
    ),
    TableColumn(
        field_name="order_date",
        header_text="Date",
        sortable=True,
        column_width="150px"
    ),
    TableColumn(
        field_name="total",
        header_text="Total",
        sortable=True,
        column_width="120px"
    ),
    TableColumn(
        field_name="status",
        header_text="Status",
        sortable=True,
        column_width="120px"
    )
]
```

### TableColumn Parameters

The `TableColumn` class accepts these parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `field_name` | `str` | The field name in the data (required) |
| `header_text` | `str` | The column header text (required) |
| `sortable` | `bool` | Whether the column is sortable (default: True) |
| `column_width` | `Optional[str]` | Fixed width for the column (e.g., "100px") |

## Table Data Format

Table data is provided as a list of dictionaries, where each dictionary represents a row:

```python
table_data = [
    {
        "order_id": "ORD-1001",
        "customer_name": "John Smith",
        "order_date": "2023-05-15",
        "total": 129.99,
        "status": "Shipped"
    },
    {
        "order_id": "ORD-1002",
        "customer_name": "Jane Doe",
        "order_date": "2023-05-16",
        "total": 79.50,
        "status": "Processing"
    },
    {
        "order_id": "ORD-1003",
        "customer_name": "Robert Johnson",
        "order_date": "2023-05-16",
        "total": 249.99,
        "status": "Delivered"
    }
]
```

The keys in each dictionary should match the `field_name` values in your column definitions.

## Event Handling

Tables emit events that can be handled by your agent:

```python
from typing import Dict, Any
from agentnexus.base_types import WorkflowStepResponse, UIComponentUpdate

async def handle_product_selection(
    action: str,
    data: Dict[str, Any],
    component_key: str,
    **kwargs
) -> WorkflowStepResponse:
    """Handle product row selection."""
    # Extract row data
    row_data = data.get("data", {})
    product_id = row_data.get("id")
    product_name = row_data.get("name")

    # Process selection
    # ...

    # Return response with UI updates
    return WorkflowStepResponse(
        data={"product_selected": True, "product_id": product_id},
        ui_updates=[
            UIComponentUpdate(
                key="product_details",
                state={"markdown_content": f"## Selected Product\n\n**{product_name}**\n\nPrice: ${row_data.get('price')}\nCategory: {row_data.get('category')}\nIn Stock: {row_data.get('in_stock')}"}
            )
        ],
        context_updates={
            "selected_product": row_data
        }
    )
```

### Table Events

Tables support these events:

| Event | Description | Data Provided |
|-------|-------------|---------------|
| `row_click` | Row selection | Complete row data |
| `sort` | Column sorting | Column field name and direction |
| `pagination` | Page change | Page number and rows per page |

### Event Handler Registration

Register event handlers when creating the table:

```python
orders_table = TableComponent(
    component_key="orders_table",
    title="Recent Orders",
    columns=[...],
    table_data=[...],
    event_handlers={
        "row_click": handle_order_selection,
        "sort": handle_order_sort,
        "pagination": handle_order_pagination
    }
)
```

## Table Updates

You can update tables dynamically:

```python
# Update entire table data
return WorkflowStepResponse(
    data={"search_complete": True},
    ui_updates=[
        UIComponentUpdate(
            key="results_table",
            state={"table_data": search_results}
        )
    ],
    context_updates={}
)

# Update specific rows
return WorkflowStepResponse(
    data={"status_updated": True},
    ui_updates=[
        UIComponentUpdate(
            key="orders_table",
            state={"data_updates": [
                {"row_match": {"order_id": "ORD-1001"}, "field": "status", "value": "Delivered"}
            ]}
        )
    ],
    context_updates={}
)
```

### Update Types

Tables support several types of updates:

| Update Type | Description | Example |
|-------------|-------------|---------|
| `table_data` | Replace all data | `{"table_data": new_data}` |
| `data_updates` | Update specific fields | `{"data_updates": [{"row_match": {...}, "field": "...", "value": "..."}]}` |
| `add_rows` | Add new rows | `{"add_rows": [new_row1, new_row2]}` |
| `remove_rows` | Remove rows | `{"remove_rows": [{"field": "id", "value": 123}]}` |

## Pagination

Tables support automatic pagination:

```python
large_table = TableComponent(
    component_key="large_table",
    title="Large Dataset",
    columns=[...],
    table_data=[...],  # Many rows
    enable_pagination=True,
    rows_per_page=20,
    event_handlers={
        "pagination": handle_page_change
    }
)
```

### Handling Pagination

You can handle pagination events to load data for specific pages:

```python
async def handle_page_change(
    action: str,
    data: Dict[str, Any],
    component_key: str,
    **kwargs
) -> WorkflowStepResponse:
    """Handle pagination events."""
    page = data.get("page", 1)
    rows_per_page = data.get("rows_per_page", 10)

    # Calculate offset for database query
    offset = (page - 1) * rows_per_page

    # Fetch data for the requested page
    page_data = await fetch_data_page(offset, rows_per_page)

    # Return updated table data
    return WorkflowStepResponse(
        data={"page_loaded": True, "page": page},
        ui_updates=[
            UIComponentUpdate(
                key=component_key,
                state={"table_data": page_data}
            )
        ],
        context_updates={}
    )
```

## Sorting

Tables support column sorting:

```python
sortable_table = TableComponent(
    component_key="sortable_table",
    title="Sortable Data",
    columns=[
        TableColumn(field_name="name", header_text="Name", sortable=True),
        TableColumn(field_name="age", header_text="Age", sortable=True),
        TableColumn(field_name="city", header_text="City", sortable=True)
    ],
    table_data=[...],
    event_handlers={
        "sort": handle_table_sort
    }
)
```

### Handling Sort Events

You can handle sort events to reorder table data:

```python
async def handle_table_sort(
    action: str,
    data: Dict[str, Any],
    component_key: str,
    **kwargs
) -> WorkflowStepResponse:
    """Handle table sort events."""
    sort_field = data.get("field", "")
    sort_direction = data.get("direction", "asc")

    # Get current table data from context
    context = kwargs.get("context", {})
    current_data = context.get("table_data", [])

    # Sort the data
    sorted_data = sorted(
        current_data,
        key=lambda x: x.get(sort_field, ""),
        reverse=(sort_direction == "desc")
    )

    # Return sorted data
    return WorkflowStepResponse(
        data={"sorted": True, "field": sort_field, "direction": sort_direction},
        ui_updates=[
            UIComponentUpdate(
                key=component_key,
                state={"table_data": sorted_data}
            )
        ],
        context_updates={
            "table_data": sorted_data,
            "sort_field": sort_field,
            "sort_direction": sort_direction
        }
    )
```

## Advanced Table Features

### Row Actions

Tables can include row-specific actions:

```python
user_table = TableComponent(
    component_key="user_table",
    title="User Management",
    columns=[
        TableColumn(field_name="id", header_text="ID"),
        TableColumn(field_name="name", header_text="Name"),
        TableColumn(field_name="email", header_text="Email"),
        TableColumn(field_name="actions", header_text="Actions")
    ],
    table_data=[
        {"id": 1, "name": "John Doe", "email": "john@example.com", "actions": ["edit", "delete"]},
        {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "actions": ["edit", "delete"]}
    ],
    supported_events=["row_action"],
    event_handlers={
        "row_action": handle_user_action
    }
)

async def handle_user_action(
    action: str,
    data: Dict[str, Any],
    component_key: str,
    **kwargs
) -> WorkflowStepResponse:
    """Handle user table actions."""
    row_data = data.get("row_data", {})
    action_name = data.get("action_name", "")
    user_id = row_data.get("id")

    if action_name == "edit":
        # Handle edit action
        return WorkflowStepResponse(
            data={"action": "edit", "user_id": user_id},
            ui_updates=[
                UIComponentUpdate(
                    key="user_form",
                    state={"values": row_data}
                )
            ],
            context_updates={
                "editing_user": row_data
            }
        )
    elif action_name == "delete":
        # Handle delete action
        # ...
```

### Selectable Rows

You can implement row selection with checkboxes:

```python
selection_table = TableComponent(
    component_key="selection_table",
    title="Select Items",
    columns=[
        TableColumn(field_name="selected", header_text=""),
        TableColumn(field_name="name", header_text="Name"),
        TableColumn(field_name="description", header_text="Description")
    ],
    table_data=[
        {"id": 1, "selected": False, "name": "Item 1", "description": "Description 1"},
        {"id": 2, "selected": False, "name": "Item 2", "description": "Description 2"},
        {"id": 3, "selected": False, "name": "Item 3", "description": "Description 3"}
    ],
    event_handlers={
        "row_click": handle_row_selection
    }
)

async def handle_row_selection(
    action: str,
    data: Dict[str, Any],
    component_key: str,
    **kwargs
) -> WorkflowStepResponse:
    """Handle row selection."""
    row_data = data.get("data", {})
    row_id = row_data.get("id")
    current_selection = row_data.get("selected", False)

    # Toggle selection
    new_selection = not current_selection

    # Update the table
    return WorkflowStepResponse(
        data={"row_selected": new_selection, "row_id": row_id},
        ui_updates=[
            UIComponentUpdate(
                key=component_key,
                state={"data_updates": [
                    {"row_match": {"id": row_id}, "field": "selected", "value": new_selection}
                ]}
            )
        ],
        context_updates={}
    )
```

### Row Styling

You can apply custom styling to rows based on data:

```python
styled_table = TableComponent(
    component_key="status_table",
    title="Order Status",
    columns=[
        TableColumn(field_name="order_id", header_text="Order ID"),
        TableColumn(field_name="customer", header_text="Customer"),
        TableColumn(field_name="status", header_text="Status"),
        TableColumn(field_name="amount", header_text="Amount")
    ],
    table_data=[
        {"order_id": "ORD-1001", "customer": "John Smith", "status": "Completed", "amount": 129.99, "_row_class": "success"},
        {"order_id": "ORD-1002", "customer": "Jane Doe", "status": "Processing", "amount": 79.50, "_row_class": "info"},
        {"order_id": "ORD-1003", "customer": "Robert Johnson", "status": "Failed", "amount": 249.99, "_row_class": "danger"}
    ]
)
```

The special field `_row_class` can be used to apply CSS classes to rows.

### Aggregation Rows

You can include summary rows at the bottom of tables:

```python
financial_table = TableComponent(
    component_key="financial_table",
    title="Financial Summary",
    columns=[
        TableColumn(field_name="category", header_text="Category"),
        TableColumn(field_name="q1", header_text="Q1"),
        TableColumn(field_name="q2", header_text="Q2"),
        TableColumn(field_name="q3", header_text="Q3"),
        TableColumn(field_name="q4", header_text="Q4"),
        TableColumn(field_name="total", header_text="Total")
    ],
    table_data=[
        {"category": "Revenue", "q1": 150000, "q2": 175000, "q3": 200000, "q4": 225000, "total": 750000},
        {"category": "Expenses", "q1": 120000, "q2": 130000, "q3": 140000, "q4": 150000, "total": 540000},
        {"category": "Profit", "q1": 30000, "q2": 45000, "q3": 60000, "q4": 75000, "total": 210000, "_row_class": "summary"}
    ]
)
```

## Common Table Patterns

### Data Listing

```python
product_table = TableComponent(
    component_key="product_table",
    title="Product Catalog",
    columns=[
        TableColumn(field_name="id", header_text="ID"),
        TableColumn(field_name="name", header_text="Product Name"),
        TableColumn(field_name="category", header_text="Category"),
        TableColumn(field_name="price", header_text="Price"),
        TableColumn(field_name="stock", header_text="In Stock")
    ],
    table_data=products,
    enable_pagination=True,
    rows_per_page=10,
    event_handlers={
        "row_click": handle_product_selection,
        "pagination": handle_product_pagination,
        "sort": handle_product_sort
    }
)
```

### Selection Table

```python
selection_table = TableComponent(
    component_key="selection_table",
    title="Select Attendees",
    columns=[
        TableColumn(field_name="selected", header_text=""),
        TableColumn(field_name="name", header_text="Name"),
        TableColumn(field_name="email", header_text="Email"),
        TableColumn(field_name="department", header_text="Department")
    ],
    table_data=[
        {"id": 1, "selected": False, "name": "John Doe", "email": "john@example.com", "department": "Engineering"},
        {"id": 2, "selected": False, "name": "Jane Smith", "email": "jane@example.com", "department": "Marketing"},
        {"id": 3, "selected": False, "name": "Robert Johnson", "email": "robert@example.com", "department": "Finance"}
    ],
    event_handlers={
        "row_click": handle_attendee_selection
    }
)
```

### Dashboard Table

```python
dashboard_table = TableComponent(
    component_key="dashboard_table",
    title="System Status",
    columns=[
        TableColumn(field_name="service", header_text="Service"),
        TableColumn(field_name="status", header_text="Status"),
        TableColumn(field_name="uptime", header_text="Uptime"),
        TableColumn(field_name="load", header_text="Load"),
        TableColumn(field_name="actions", header_text="Actions")
    ],
    table_data=[
        {"service": "Web Server", "status": "Online", "uptime": "10d 4h", "load": "32%", "actions": ["restart", "logs"], "_row_class": "success"},
        {"service": "Database", "status": "Warning", "uptime": "5d 12h", "load": "78%", "actions": ["restart", "logs"], "_row_class": "warning"},
        {"service": "Cache", "status": "Online", "uptime": "10d 2h", "load": "45%", "actions": ["restart", "logs"], "_row_class": "success"}
    ],
    event_handlers={
        "row_action": handle_service_action
    }
)
```

## Integration with Search Forms

Tables often work together with search forms:

```python
# Search form
search_form = FormComponent(
    component_key="search_form",
    title="Search Products",
    form_fields=[
        FormField(
            field_name="query",
            label_text="Search Query",
            field_type="text",
            placeholder_text="Enter keywords..."
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
        )
    ],
    event_handlers={
        "submit": handle_search_submit
    }
)

# Results table
results_table = TableComponent(
    component_key="results_table",
    title="Search Results",
    columns=[
        TableColumn(field_name="id", header_text="ID"),
        TableColumn(field_name="name", header_text="Product Name"),
        TableColumn(field_name="category", header_text="Category"),
        TableColumn(field_name="price", header_text="Price")
    ],
    table_data=[],  # Initially empty
    event_handlers={
        "row_click": handle_product_selection
    }
)

# Search form handler
async def handle_search_submit(
    action: str,
    data: Dict[str, Any],
    component_key: str,
    **kwargs
) -> WorkflowStepResponse:
    """Handle search form submission."""
    # Extract search parameters
    values = data.get("values", {})
    query = values.get("query", "")
    category = values.get("category", "")

    # Perform search
    search_results = await search_products(query, category)

    # Update results table
    return WorkflowStepResponse(
        data={"search_complete": True, "results_count": len(search_results)},
        ui_updates=[
            UIComponentUpdate(
                key="results_table",
                state={"table_data": search_results}
            )
        ],
        context_updates={
            "search_query": query,
            "search_category": category,
            "search_results": search_results
        }
    )
```

## Best Practices

### Table Design

1. **Clear Headers**: Use clear, concise column headers
2. **Appropriate Widths**: Set appropriate column widths
3. **Sortable Columns**: Make relevant columns sortable
4. **Row Density**: Balance between compactness and readability
5. **Visual Hierarchy**: Use styling to emphasize important data
6. **Consistent Actions**: Use consistent actions across tables

### Performance

1. **Pagination**: Use pagination for large datasets
2. **Progressive Loading**: Load data as needed
3. **Incremental Updates**: Update only changed rows when possible
4. **Limit Columns**: Include only necessary columns
5. **Optimize Data Format**: Structure data efficiently

### Interactivity

1. **Clear Selection**: Make selectable rows visually distinct
2. **Action Feedback**: Provide feedback for row actions
3. **Loading States**: Show loading indicators during data retrieval
4. **Empty States**: Handle empty tables gracefully
5. **Error States**: Display error messages appropriately

## Next Steps

- Learn about [Code Editor Components](../code-editor-components) for code input
- Explore [Markdown Components](../markdown-components) for formatted display
- Understand [Event Handling](../../core-concepts/event-handling) in depth
- See how tables fit into [Workflows](../../core-concepts/workflows)