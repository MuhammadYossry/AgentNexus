---
title: "Markdown Components"
description: "Working with formatted text display components"
lead: "Markdown components provide a simple way to display formatted text, documentation, and rich content in agent interfaces."
date: 2025-03-25T08:00:00+00:00
lastmod: 2025-03-25T08:00:00+00:00
draft: false
images: []
menu:
  docs:
    parent: "ui-components"
weight: 440
toc: true
---

## Introduction to Markdown Components

The `MarkdownComponent` provides a way to display formatted text using Markdown syntax. These components are perfect for:

- Displaying instructions and documentation
- Showing results and analysis
- Presenting structured information
- Providing feedback to users
- Rendering rich text content

Markdown components are typically used to complement interactive components like forms, tables, and code editors by providing context, instructions, or results.

## Basic Markdown Component Structure

A markdown component is straightforward to define:

```python
from agentnexus.ui_components import MarkdownComponent

welcome_message = MarkdownComponent(
    component_key="welcome_message",
    title="Welcome",
    markdown_content="""
# Welcome to the Application

This interface helps you accomplish the following tasks:

1. Search for information
2. Analyze data
3. Generate reports

## Getting Started

Start by entering your query in the search form below.
    """
)
```

## Markdown Component Parameters

The `MarkdownComponent` class accepts these parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `component_key` | `str` | Unique identifier for this component (required) |
| `title` | `str` | Human-readable title for the component |
| `markdown_content` | `str` | Markdown-formatted content to display |
| `content_style` | `Dict[str, Any]` | Custom styling for the content |

## Markdown Syntax

Markdown components support standard Markdown syntax:

### Headings

```markdown
# Heading 1
## Heading 2
### Heading 3
#### Heading 4
##### Heading 5
###### Heading 6
```

### Text Formatting

```markdown
**Bold text**
*Italic text*
~~Strikethrough~~
`Inline code`
```

### Lists

```markdown
* Unordered list item
* Another item
  * Nested item

1. Ordered list item
2. Another item
   1. Nested item
```

### Links and Images

```markdown
[Link text](https://example.com)

![Image alt text](/image.jpg)
```

### Code Blocks

````markdown
```python
def hello_world():
    print("Hello, world!")
```
````

### Tables

```markdown
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |
```

### Blockquotes

```markdown
> This is a blockquote.
> It can span multiple lines.
```

### Horizontal Rules

```markdown
---
```

## Updating Markdown Components

You can update markdown components dynamically:

```python
from agentnexus.base_types import WorkflowStepResponse, UIComponentUpdate

# Update markdown content
return WorkflowStepResponse(
    data={"analysis_complete": True},
    ui_updates=[
        UIComponentUpdate(
            key="analysis_results",
            state={"markdown_content": analysis_text}
        )
    ],
    context_updates={
        "analysis": analysis_text
    }
)
```

## Dynamic Content Generation

Markdown components are often used to display dynamically generated content:

```python
async def handle_analyze_step(input_data) -> WorkflowStepResponse:
    """Handle the analysis step."""
    # Extract data from input
    text = input_data.context.get("text", "")

    # Perform analysis
    word_count = len(text.split())
    sentence_count = len([s for s in text.split(".") if s.strip()])
    avg_word_length = sum(len(word) for word in text.split()) / max(1, word_count)

    # Generate markdown content
    analysis_md = f"""
## Text Analysis Results

| Metric | Value |
|--------|-------|
| Word Count | {word_count} |
| Sentence Count | {sentence_count} |
| Average Word Length | {avg_word_length:.2f} |

### Key Findings

* {'Long' if word_count > 500 else 'Short'} document
* {'Complex' if avg_word_length > 6 else 'Simple'} vocabulary
* {'Many' if sentence_count > 20 else 'Few'} sentences

### Recommendations

* ${{'Simplify language' if avg_word_length > 6 else 'Add more details'}}
* ${{'Break into sections' if sentence_count > 20 else 'Expand content'}}
    """

    # Return response with markdown update
    return WorkflowStepResponse(
        data={"status": "analysis_complete"},
        ui_updates=[
            UIComponentUpdate(
                key="analysis_results",
                state={"markdown_content": analysis_md}
            )
        ],
        context_updates={
            "analysis": {
                "word_count": word_count,
                "sentence_count": sentence_count,
                "avg_word_length": avg_word_length
            }
        }
    )
```

## Template-Based Content

You can use template strings to generate markdown content:

```python
def generate_report_markdown(data):
    """Generate a markdown report from data."""
    report_template = """
# {title}

## Summary
{summary}

## Details

| Metric | Value |
|--------|-------|
{metrics_table}

## Conclusion
{conclusion}
    """

    # Generate metrics table rows
    metrics_rows = "\n".join([
        f"| {metric} | {value} |"
        for metric, value in data["metrics"].items()
    ])

    # Fill in the template
    return report_template.format(
        title=data["title"],
        summary=data["summary"],
        metrics_table=metrics_rows,
        conclusion=data["conclusion"]
    )

# Later, in a workflow step or action handler:
report_data = {
    "title": "Monthly Sales Report",
    "summary": "Sales increased by 15% compared to last month.",
    "metrics": {
        "Total Sales": "$125,000",
        "Units Sold": "1,250",
        "Average Order Value": "$100",
        "Return Rate": "2.3%"
    },
    "conclusion": "The new marketing campaign has been successful in driving higher sales."
}

report_md = generate_report_markdown(report_data)

return WorkflowStepResponse(
    data={"report_generated": True},
    ui_updates=[
        UIComponentUpdate(
            key="report_display",
            state={"markdown_content": report_md}
        )
    ],
    context_updates={
        "report": report_data,
        "report_markdown": report_md
    }
)
```

## Custom Styling

You can customize the appearance of markdown components:

```python
warning_message = MarkdownComponent(
    component_key="warning_message",
    title="Important Notice",
    markdown_content="""
## ⚠️ Warning

This action cannot be undone. Please review your changes before proceeding.
    """,
    content_style={
        "backgroundColor": "#fff3cd",
        "padding": "1rem",
        "borderRadius": "0.25rem",
        "border": "1px solid #ffeeba"
    }
)
```

## Combining with Other Components

Markdown components work well with other component types:

```python
# Form plus instructions
registration_instructions = MarkdownComponent(
    component_key="registration_instructions",
    title="Registration Instructions",
    markdown_content="""
## How to Register

1. Fill out all required fields (marked with *)
2. Choose a strong password (at least 8 characters)
3. Verify your email after submission
    """
)

registration_form = FormComponent(
    component_key="registration_form",
    title="Registration Form",
    form_fields=[
        # Form fields...
    ],
    event_handlers={
        "submit": handle_registration_submit
    }
)

# Table plus explanation
data_explanation = MarkdownComponent(
    component_key="data_explanation",
    title="Understanding the Data",
    markdown_content="""
## Sales Data Guide

This table shows monthly sales figures across different regions:

* **Region**: Geographic sales region
* **Q1-Q4**: Quarterly sales figures in thousands ($K)
* **Total**: Annual total sales
* **Growth**: Year-over-year growth percentage

Click on any row to see detailed statistics for that region.
    """
)

sales_table = TableComponent(
    component_key="sales_table",
    title="Annual Sales by Region",
    columns=[
        # Table columns...
    ],
    table_data=[
        # Table data...
    ],
    event_handlers={
        "row_click": handle_region_selection
    }
)
```

## Common Markdown Component Patterns

### Instructions and Guidelines

```python
task_instructions = MarkdownComponent(
    component_key="task_instructions",
    title="Task Guidelines",
    markdown_content="""
# Code Review Guidelines

When reviewing the code, please consider the following:

## Style and Formatting
- Is the code following PEP 8 conventions?
- Are variable names descriptive and consistent?
- Is there appropriate whitespace and indentation?

## Functionality
- Does the code work as expected?
- Are there any edge cases not handled?
- Could the algorithm be optimized?

## Best Practices
- Are there redundant or duplicate code sections?
- Is error handling implemented properly?
- Are there appropriate comments and documentation?
    """
)
```

### Results and Analysis

```python
analysis_results = MarkdownComponent(
    component_key="analysis_results",
    title="Analysis Results",
    markdown_content="""
# Code Analysis

## Overview
- **Lines of Code**: 245
- **Functions**: 12
- **Classes**: 3
- **Complexity Score**: Medium

## Issues Found
1. **Redundant Code** (Lines 34-42)
   The same calculation is performed twice.

2. **Inefficient Algorithm** (Lines 78-95)
   The current approach is O(n²), could be improved to O(n).

3. **Missing Error Handling** (Line 112)
   No exception handling for potential file access errors.

## Recommendations
- Extract duplicate code into a helper function
- Replace nested loops with a more efficient algorithm
- Add proper try/except blocks around file operations
    """
)
```

### Step-by-Step Guidance

```python
workflow_guidance = MarkdownComponent(
    component_key="workflow_guidance",
    title="Current Step: Data Upload",
    markdown_content="""
# Data Upload

## Step 1 of 4: Upload your data file

In this step, you need to:

1. Select the CSV file containing your data
2. Choose the appropriate delimiter (comma, tab, etc.)
3. Indicate whether the file has a header row
4. Click 'Upload' to proceed

### Supported Formats
- CSV (Comma-Separated Values)
- TSV (Tab-Separated Values)
- Custom-delimited text files

### Size Limits
Files must be under 10MB. For larger files, please contact support.
    """
)
```

### Status and Feedback

```python
status_display = MarkdownComponent(
    component_key="status_display",
    title="Processing Status",
    markdown_content="""
# Processing Complete ✅

Your request has been successfully processed.

## Summary
- **Files Processed**: 12
- **Records Created**: 543
- **Processing Time**: 2.4 seconds

## Next Steps
You can now view the results or download the processed data.

[View Results](#) | [Download Data](#)
    """
)
```

## Best Practices

### Content Structure

1. **Clear Hierarchy**: Use heading levels (H1, H2, H3) meaningfully
2. **Consistent Formatting**: Maintain consistent style throughout
3. **Chunking**: Break content into digestible sections
4. **Visual Cues**: Use lists, tables, and formatting to highlight information
5. **Progressive Disclosure**: Present the most important information first

### Readability

1. **Concise Language**: Keep text clear and to the point
2. **Appropriate Length**: Avoid excessively long content
3. **Scannable Format**: Use headings, lists, and emphasis for scanability
4. **Visual Spacing**: Include whitespace for readability
5. **Consistent Terminology**: Use consistent terms throughout

### Visual Design

1. **Appropriate Styling**: Use styling that matches content purpose
2. **Color for Meaning**: Use color to enhance, not replace, meaning
3. **Responsive Design**: Ensure content works on different screen sizes
4. **Accessible Contrast**: Maintain sufficient text/background contrast
5. **Focus on Content**: Avoid overly decorative elements

## Next Steps

- Explore [Custom Components](../custom-components) for specialized needs
- Learn how markdown components work with [Forms](../form-components) and [Tables](../table-components)
- Understand [Event Handling](../../core-concepts/event-handling) for interactive components
- See how all components fit into [Workflows](../../core-concepts/workflows)