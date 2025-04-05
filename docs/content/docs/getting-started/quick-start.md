---
title: "Quick Start"
description: "Build your first agent with AgentNexus in 5 minutes"
lead: "Learn how to create a simple but functional agent with AgentNexus in just a few minutes."
date: 2025-03-25T08:00:00+00:00
lastmod: 2025-03-25T08:00:00+00:00
draft: false
images: []
menu:
  docs:
    parent: "getting-started"
weight: 230
toc: true
---

## Overview

This quick start guide will walk you through creating a simple text analysis agent with AgentNexus. Your agent will:

1. Accept text input
2. Perform basic analysis (word count, sentiment, etc.)
3. Return formatted results

Let's get started!

## Step 1: Installation

First, make sure you have AgentNexus installed:

```bash
pip install fast-agents
```

## Step 2: Create a New Project

Create a directory for your project and set up a basic structure:

```bash
mkdir text-analyzer
cd text-analyzer
touch main.py
```

## Step 3: Define Your Agent

Open `main.py` in your editor and start by defining your agent:

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field
from agentnexus.base_types import AgentConfig, Capability, ActionType
from agentnexus.action_manager import agent_action
from agentnexus.manifest_generator import AgentManager

# Define input/output models
class TextAnalysisInput(BaseModel):
    text: str = Field(..., description="Text to analyze")
    include_sentiment: bool = Field(True, description="Include sentiment analysis")

class TextAnalysisOutput(BaseModel):
    word_count: int
    character_count: int
    sentence_count: int
    sentiment: str = None
    summary: str = None

# Define agent configuration
text_analyzer = AgentConfig(
    name="Text Analyzer",
    version="1.0.0",
    description="Analyzes text and provides statistical insights",
    capabilities=[
        Capability(
            skill_path=["Text", "Analysis"],
            metadata={
                "features": ["Word Count", "Character Count", "Sentiment Analysis"],
                "languages": ["English"]
            }
        )
    ]
)
```

## Step 4: Implement Agent Actions

Now, add an action to your agent:

```python
@agent_action(
    agent_config=text_analyzer,
    action_type=ActionType.GENERATE,
    name="Analyze Text",
    description="Provides statistical analysis of input text"
)
async def analyze_text(input_data: TextAnalysisInput) -> TextAnalysisOutput:
    """Analyze text and provide statistics."""
    text = input_data.text
    
    # Basic analysis
    words = text.split()
    word_count = len(words)
    character_count = len(text)
    sentences = text.split('.')
    sentence_count = len([s for s in sentences if s.strip()])
    
    # Simple sentiment analysis (very basic example)
    positive_words = ['good', 'great', 'excellent', 'happy', 'positive']
    negative_words = ['bad', 'terrible', 'unhappy', 'negative', 'sad']
    
    positive_count = sum(1 for word in words if word.lower() in positive_words)
    negative_count = sum(1 for word in words if word.lower() in negative_words)
    
    sentiment = "neutral"
    if positive_count > negative_count:
        sentiment = "positive"
    elif negative_count > positive_count:
        sentiment = "negative"
    
    # Generate a basic summary (first 50 characters + ellipsis)
    summary = text[:50] + "..." if len(text) > 50 else text
    
    return TextAnalysisOutput(
        word_count=word_count,
        character_count=character_count,
        sentence_count=sentence_count,
        sentiment=sentiment if input_data.include_sentiment else None,
        summary=summary
    )
```

## Step 5: Set Up FastAPI Integration

Complete your application by setting up FastAPI:

```python
app = FastAPI(title="Text Analysis Agent")

# Set up agent manager
agent_manager = AgentManager(base_url="http://localhost:8000")
agent_manager.add_agent(text_analyzer)
agent_manager.setup_agents(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Step 6: Run Your Agent

Save the file and run your agent:

```bash
uvicorn main:app --reload
```

Your agent is now running on `http://localhost:8000`!

## Step 7: Explore Your Agent

Once your agent is running, you can:

1. Visit the auto-generated API docs at `http://localhost:8000/docs`
2. View the agent manifest at `http://localhost:8000/agents/text-analyzer.json`
3. Test the agent by sending a POST request to `http://localhost:8000/agents/text-analyzer/actions/analyze-text`

Here's a sample request using curl:

```bash
curl -X 'POST' \
  'http://localhost:8000/agents/text-analyzer/actions/analyze-text' \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "This is a great example of a AgentNexus application. It analyzes text and provides useful insights.",
    "include_sentiment": true
  }'
```

You should receive a response like:

```json
{
  "word_count": 16,
  "character_count": 95,
  "sentence_count": 2,
  "sentiment": "positive",
  "summary": "This is a great example of a AgentNexus applicatio..."
}
```

## Adding UI Components (Optional)

To make your agent more interactive, you can add UI components. Let's enhance our agent with a text input form and results display:

```python
from agentnexus.ui_components import FormComponent, FormField, MarkdownComponent
from agentnexus.base_types import UIComponentUpdate, UIResponse

# Define UI components
text_input_form = FormComponent(
    component_key="text_input",
    title="Text Analysis Input",
    form_fields=[
        FormField(
            field_name="text",
            label_text="Text to Analyze",
            field_type="textarea",
            is_required=True
        ),
        FormField(
            field_name="include_sentiment",
            label_text="Include Sentiment Analysis",
            field_type="checkbox"
        )
    ]
)

analysis_result = MarkdownComponent(
    component_key="analysis_result",
    title="Analysis Results",
    markdown_content="Submit text to see analysis results."
)

# Create a UI-driven action
@agent_action(
    agent_config=text_analyzer,
    action_type=ActionType.CUSTOM_UI,
    name="Interactive Text Analysis",
    description="Analyze text with an interactive UI",
    ui_components=[text_input_form, analysis_result]
)
async def interactive_text_analysis(input_data) -> UIResponse:
    """Handle interactive text analysis with UI components."""
    # Check if we have form data
    if hasattr(input_data, 'form_data') and input_data.form_data:
        # Extract values from form
        form_data = input_data.form_data
        if form_data.get("action") == "submit" and form_data.get("component_key") == "text_input":
            values = form_data.get("values", {})
            text = values.get("text", "")
            include_sentiment = values.get("include_sentiment", True)
            
            # Perform analysis (reusing our existing function)
            analysis = await analyze_text(TextAnalysisInput(
                text=text,
                include_sentiment=include_sentiment
            ))
            
            # Format results for markdown display
            result_text = f"""
## Analysis Results

- **Word Count:** {analysis.word_count}
- **Character Count:** {analysis.character_count}
- **Sentence Count:** {analysis.sentence_count}

{f"**Sentiment:** {analysis.sentiment}" if include_sentiment else ""}

### Summary
{analysis.summary}
"""
            
            # Return UI response with updated components
            return UIResponse(
                data={"analysis_complete": True},
                ui_updates=[
                    UIComponentUpdate(
                        key="analysis_result",
                        state={"markdown_content": result_text}
                    )
                ]
            )
    
    # Default initial state
    return UIResponse(
        data={"ready": True},
        ui_updates=[]
    )
```

Now you have an interactive UI for your text analysis agent!

## Next Steps

Congratulations! You've built your first agent with AgentNexus. Here are some ways to expand on this:

1. Add more sophisticated text analysis features
2. Implement a multi-step workflow for document processing
3. Integrate with an LLM for more advanced language capabilities
4. Add visualization components for analysis results

For more advanced topics, check out:

- [Project Organization](../project-organization) for best practices
- [Core Concepts](../../core-concepts/) for detailed documentation
- [Workflow System](../../workflow-system/) for multi-step processes
- [Examples](../../examples/) for more complex agent implementations