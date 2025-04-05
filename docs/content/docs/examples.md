---
title: "Practical LLM Agent Examples"
description: "Real-world examples of LLM-powered agents built with AgentNexus"
lead: "Learn how to build practical LLM agents that solve real-world tasks with interactive interfaces and structured workflows."
date: 2025-03-25T08:00:00+00:00
lastmod: 2025-03-25T08:00:00+00:00
draft: false
images: []
menu:
  docs:
    parent: "examples"
weight: 710
toc: true
---

## Introduction

This guide provides complete, practical examples of LLM-powered agents built with AgentNexus. Each example demonstrates how to combine LLMs with the AgentNexus framework to create intelligent, interactive agents that solve specific tasks.

## Research Assistant Agent

This agent helps users research topics, find information, and generate summaries using LLMs.

### Agent Definition

```python
from agentnexus.base_types import AgentConfig, Capability, ActionType
from agentnexus.action_manager import agent_action
from agentnexus.services.llm_client import create_llm_client
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# Define models
class ResearchQuery(BaseModel):
    topic: str = Field(..., description="The topic to research")
    focus_areas: Optional[List[str]] = Field(None, description="Specific areas to focus on")
    depth: str = Field("medium", description="Research depth (basic, medium, detailed)")

class ResearchResult(BaseModel):
    summary: str
    key_points: List[str]
    sources: List[Dict[str, str]]
    follow_up_questions: List[str]

# Define the agent
research_agent = AgentConfig(
    name="Research Assistant",
    version="1.0.0",
    description="AI-powered research assistant that helps find information and generate summaries",
    capabilities=[
        Capability(
            skill_path=["Research", "Information Retrieval"],
            metadata={
                "topics": ["General", "Academic", "Scientific"],
                "features": ["Topic Research", "Summary Generation", "Source Finding"]
            }
        ),
        Capability(
            skill_path=["Content", "Summarization"],
            metadata={
                "formats": ["Concise", "Detailed", "Bullet Points"],
                "features": ["Key Point Extraction", "Follow-up Generation"]
            }
        )
    ]
)

# Define search action
@agent_action(
    agent_config=research_agent,
    action_type=ActionType.GENERATE,
    name="Research Topic",
    description="Researches a topic and provides a comprehensive summary"
)
async def research_topic(input_data: ResearchQuery) -> ResearchResult:
    """Research a topic and generate a comprehensive summary."""
    # Get LLM client
    llm_client = create_llm_client()

    # Create research prompt
    topic = input_data.topic
    focus_areas = input_data.focus_areas or []
    depth = input_data.depth

    # Create a detailed prompt
    research_prompt = f"""
    Please conduct thorough research on the topic: {topic}

    {f"Focus specifically on these areas: {', '.join(focus_areas)}" if focus_areas else ""}

    Provide a {depth} level of detail in your research.

    Your response should include:
    1. A comprehensive summary of the topic
    2. Key points and important findings
    3. Potential sources where this information might be found
    4. Interesting follow-up questions for further exploration

    Be factual, balanced, and thorough in your research.
    """

    # Call the LLM
    response = await llm_client.complete(
        prompt=research_prompt,
        system_message="""You are an expert research assistant with deep knowledge across many fields.
        You provide balanced, comprehensive, and factual information on topics.""",
        temperature=0.3,
        max_tokens=2000
    )

    # Process the response to extract structured information
    content = response.content

    # Extract key points (simplified implementation)
    key_points_text = extract_section(content, "Key points")
    key_points = [point.strip() for point in key_points_text.split("\n") if point.strip()]

    # Extract sources (simplified implementation)
    sources_text = extract_section(content, "Sources")
    sources = []
    for line in sources_text.split("\n"):
        if not line.strip():
            continue
        source_parts = line.split(":", 1)
        if len(source_parts) == 2:
            source_name, source_url = source_parts
            sources.append({"name": source_name.strip(), "url": source_url.strip()})
        else:
            sources.append({"name": line.strip(), "url": ""})

    # Extract follow-up questions (simplified implementation)
    questions_text = extract_section(content, "Follow-up questions")
    questions = [q.strip() for q in questions_text.split("\n") if q.strip()]

    # Extract summary (simplified implementation)
    summary = extract_section(content, "Summary")

    # If extractions failed, use a more robust approach with another LLM call
    if not summary or not key_points:
        structuring_prompt = f"""
        Please extract the following from this research content:

        CONTENT:
        {content}

        EXTRACT:
        1. A concise summary (2-3 paragraphs)
        2. 5-7 key points as a bullet list
        3. 3-5 sources (name and URL if available)
        4. 3-5 follow-up questions

        Format your response as:
        SUMMARY:
        (summary text)

        KEY POINTS:
        - Point 1
        - Point 2
        ...

        SOURCES:
        - Source 1: URL1
        - Source 2: URL2
        ...

        FOLLOW-UP QUESTIONS:
        - Question 1
        - Question 2
        ...
        """

        structure_response = await llm_client.complete(
            prompt=structuring_prompt,
            system_message="You are a research assistant that extracts and structures information.",
            temperature=0.1
        )

        structured_content = structure_response.content

        # Re-extract with more reliable formatting
        summary = extract_section(structured_content, "SUMMARY")

        key_points_text = extract_section(structured_content, "KEY POINTS")
        key_points = [point.strip().lstrip("- ") for point in key_points_text.split("\n") if point.strip()]

        sources_text = extract_section(structured_content, "SOURCES")
        sources = []
        for line in sources_text.split("\n"):
            if not line.strip():
                continue
            line = line.lstrip("- ")
            if ":" in line:
                source_name, source_url = line.split(":", 1)
                sources.append({"name": source_name.strip(), "url": source_url.strip()})
            else:
                sources.append({"name": line.strip(), "url": ""})

        questions_text = extract_section(structured_content, "FOLLOW-UP QUESTIONS")
        questions = [q.strip().lstrip("- ") for q in questions_text.split("\n") if q.strip()]

    # Return structured research results
    return ResearchResult(
        summary=summary,
        key_points=key_points,
        sources=sources,
        follow_up_questions=questions
    )

# Helper function to extract sections from LLM output
def extract_section(text, section_name):
    """Extract a section from the LLM output text."""
    # Try different section heading formats
    patterns = [
        f"{section_name}:",
        f"{section_name.upper()}:",
        f"## {section_name}",
        f"**{section_name}**",
        f"{section_name}"
    ]

    for pattern in patterns:
        if pattern in text:
            parts = text.split(pattern, 1)
            if len(parts) > 1:
                section_text = parts[1].strip()
                # Try to find the end of the section (next section heading)
                for end_pattern in patterns:
                    if end_pattern != pattern and end_pattern in section_text:
                        section_text = section_text.split(end_pattern, 1)[0].strip()
                return section_text

    # If no section found, return empty string
    return ""
```

### Interactive Research Workflow

Here's a complete workflow for interactive research:

```python
from agentnexus.base_types import Workflow, WorkflowStep, WorkflowStepResponse, UIComponentUpdate
from agentnexus.workflow_manager import workflow_step
from agentnexus.ui_components import FormComponent, FormField, MarkdownComponent

# Define the workflow
RESEARCH_WORKFLOW = Workflow(
    id="interactive_research",
    name="Interactive Research",
    description="Interactive research with topic refinement and exploration",
    steps=[
        WorkflowStep(id="query"),
        WorkflowStep(id="refine"),
        WorkflowStep(id="results"),
        WorkflowStep(id="explore")
    ],
    initial_step="query"
)

# Update agent with workflow
research_agent.workflows = [RESEARCH_WORKFLOW]

# Define UI components
query_form = FormComponent(
    component_key="query_form",
    title="Research Query",
    form_fields=[
        FormField(
            field_name="topic",
            label_text="Topic",
            field_type="text",
            is_required=True,
            placeholder_text="Enter the topic you want to research"
        ),
        FormField(
            field_name="focus_areas",
            label_text="Focus Areas (optional)",
            field_type="textarea",
            placeholder_text="Enter specific areas to focus on, one per line"
        ),
        FormField(
            field_name="depth",
            label_text="Research Depth",
            field_type="select",
            field_options=[
                {"value": "basic", "label": "Basic (quick overview)"},
                {"value": "medium", "label": "Medium (standard depth)"},
                {"value": "detailed", "label": "Detailed (comprehensive)"}
            ]
        )
    ]
)

instructions = MarkdownComponent(
    component_key="instructions",
    title="Instructions",
    markdown_content="""
    # Research Assistant

    Use this tool to research any topic of interest. The AI will:

    1. Analyze your topic
    2. Suggest refinements to improve results
    3. Conduct thorough research
    4. Present findings with sources
    5. Offer follow-up areas to explore

    Enter your initial topic and any specific focus areas you're interested in.
    """
)

results_display = MarkdownComponent(
    component_key="results_display",
    title="Research Results",
    markdown_content="Your research results will appear here after processing."
)

refinement_form = FormComponent(
    component_key="refinement_form",
    title="Refine Your Research",
    form_fields=[
        FormField(
            field_name="refined_topic",
            label_text="Refined Topic",
            field_type="text",
            is_required=True
        ),
        FormField(
            field_name="suggested_focus",
            label_text="Suggested Focus Areas",
            field_type="checkbox",
            field_options=[]  # Will be populated dynamically
        ),
        FormField(
            field_name="additional_focus",
            label_text="Additional Focus Areas",
            field_type="textarea",
            placeholder_text="Add any other areas of interest"
        )
    ]
)

explore_form = FormComponent(
    component_key="explore_form",
    title="Explore Further",
    form_fields=[
        FormField(
            field_name="follow_up",
            label_text="Follow-up Question",
            field_type="select",
            field_options=[]  # Will be populated dynamically
        ),
        FormField(
            field_name="custom_question",
            label_text="Or ask your own question",
            field_type="text",
            placeholder_text="Enter a custom follow-up question"
        )
    ]
)

# Step 1: Query
@workflow_step(
    agent_config=research_agent,
    workflow_id="interactive_research",
    step_id="query",
    name="Research Query",
    ui_components=[instructions, query_form]
)
async def handle_query_step(input_data) -> WorkflowStepResponse:
    """Handle initial research query input."""
    # Extract context and form data
    context = getattr(input_data, 'context', {}) or {}
    form_data = getattr(input_data, 'form_data', None)

    # Handle form submission
    if form_data and form_data.get("action") == "submit":
        # Extract values
        values = form_data.get("values", {})
        topic = values.get("topic", "")
        focus_areas_text = values.get("focus_areas", "")
        depth = values.get("depth", "medium")

        # Process focus areas
        focus_areas = [area.strip() for area in focus_areas_text.split("\n") if area.strip()]

        # Get LLM client for refinement suggestions
        llm_client = create_llm_client()

        # Create prompt for topic refinement
        refinement_prompt = f"""
        I want to research this topic: "{topic}"

        Focus areas: {', '.join(focus_areas) if focus_areas else 'None specified'}

        Please suggest:
        1. A refined, more specific version of this topic
        2. 5-7 potential focus areas that would make the research more effective
        3. Any clarifying questions that would help narrow the scope

        Format your response as:
        REFINED TOPIC:
        (suggested refined topic)

        FOCUS AREAS:
        - Focus area 1
        - Focus area 2
        ...

        CLARIFYING QUESTIONS:
        - Question 1
        - Question 2
        ...
        """

        # Get refinement suggestions
        refinement = await llm_client.complete(
            prompt=refinement_prompt,
            system_message="You are a research expert who helps refine topics for more effective research.",
            temperature=0.4
        )

        # Parse the refinement suggestions
        refinement_text = refinement.content

        # Extract refined topic
        refined_topic = extract_section(refinement_text, "REFINED TOPIC")

        # Extract suggested focus areas
        focus_areas_text = extract_section(refinement_text, "FOCUS AREAS")
        suggested_focus = [area.strip().lstrip("- ") for area in focus_areas_text.split("\n") if area.strip()]

        # Extract clarifying questions
        questions_text = extract_section(refinement_text, "CLARIFYING QUESTIONS")
        clarifying_questions = [q.strip().lstrip("- ") for q in questions_text.split("\n") if q.strip()]

        # Prepare focus area options for the refinement form
        focus_options = []
        for area in suggested_focus:
            focus_options.append({"value": area, "label": area})

        # Move to refinement step
        return WorkflowStepResponse(
            data={"status": "query_received"},
            ui_updates=[
                UIComponentUpdate(
                    key="refinement_form",
                    state={
                        "values": {"refined_topic": refined_topic},
                        "field_updates": [
                            {
                                "field_name": "suggested_focus",
                                "field_options": focus_options
                            }
                        ]
                    }
                ),
                UIComponentUpdate(
                    key="instructions",
                    state={
                        "markdown_content": f"""
                        # Refine Your Research

                        Initial topic: "{topic}"

                        Based on your topic, I've suggested some refinements to make your research more effective.
                        You can use the suggested refinements or modify them as needed.

                        ### Clarifying Questions to Consider:

                        {chr(10).join(['- ' + q for q in clarifying_questions])}
                        """
                    }
                )
            ],
            next_step_id="refine",
            context_updates={
                "original_topic": topic,
                "original_focus_areas": focus_areas,
                "depth": depth,
                "refined_topic": refined_topic,
                "suggested_focus": suggested_focus,
                "clarifying_questions": clarifying_questions
            }
        )

    # Initial step load
    return WorkflowStepResponse(
        data={"status": "ready"},
        ui_updates=[],
        context_updates={}
    )

# Step 2: Refine
@workflow_step(
    agent_config=research_agent,
    workflow_id="interactive_research",
    step_id="refine",
    name="Refine Research",
    ui_components=[instructions, refinement_form]
)
async def handle_refine_step(input_data) -> WorkflowStepResponse:
    """Handle research refinement."""
    # Extract context and form data
    context = getattr(input_data, 'context', {}) or {}
    form_data = getattr(input_data, 'form_data', None)

    # Handle form submission
    if form_data and form_data.get("action") == "submit":
        # Extract values
        values = form_data.get("values", {})
        refined_topic = values.get("refined_topic", "")
        additional_focus = values.get("additional_focus", "")
        selected_focus = values.get("suggested_focus", [])

        # Process additional focus areas
        additional_focus_areas = [area.strip() for area in additional_focus.split("\n") if area.strip()]

        # Combine selected and additional focus areas
        if not isinstance(selected_focus, list):
            selected_focus = [selected_focus]

        combined_focus = selected_focus + additional_focus_areas

        # Get research depth from context
        depth = context.get("depth", "medium")

        # Create research input
        research_input = ResearchQuery(
            topic=refined_topic,
            focus_areas=combined_focus,
            depth=depth
        )

        # Call the research action
        research_result = await research_topic(research_input)

        # Format results as markdown
        results_markdown = f"""
        # Research Results: {refined_topic}

        ## Summary

        {research_result.summary}

        ## Key Points

        {chr(10).join(['- ' + point for point in research_result.key_points])}

        ## Sources

        {chr(10).join(['- ' + source["name"] + (f": {source['url']}" if source["url"] else "") for source in research_result.sources])}

        ## Follow-up Questions

        {chr(10).join(['- ' + question for question in research_result.follow_up_questions])}
        """

        # Prepare follow-up options for the explore form
        follow_up_options = []
        for question in research_result.follow_up_questions:
            follow_up_options.append({"value": question, "label": question})

        # Move to results step
        return WorkflowStepResponse(
            data={"status": "research_complete"},
            ui_updates=[
                UIComponentUpdate(
                    key="results_display",
                    state={"markdown_content": results_markdown}
                ),
                UIComponentUpdate(
                    key="explore_form",
                    state={
                        "field_updates": [
                            {
                                "field_name": "follow_up",
                                "field_options": follow_up_options
                            }
                        ]
                    }
                )
            ],
            next_step_id="results",
            context_updates={
                "refined_topic": refined_topic,
                "focus_areas": combined_focus,
                "research_results": {
                    "summary": research_result.summary,
                    "key_points": research_result.key_points,
                    "sources": research_result.sources,
                    "follow_up_questions": research_result.follow_up_questions
                }
            }
        )

    # Initial step load - should never happen directly
    return WorkflowStepResponse(
        data={"status": "refine_ready"},
        ui_updates=[],
        context_updates={}
    )

# Step 3: Results
@workflow_step(
    agent_config=research_agent,
    workflow_id="interactive_research",
    step_id="results",
    name="Research Results",
    ui_components=[results_display, explore_form]
)
async def handle_results_step(input_data) -> WorkflowStepResponse:
    """Handle research results display and follow-up."""
    # Extract context and form data
    context = getattr(input_data, 'context', {}) or {}
    form_data = getattr(input_data, 'form_data', None)

    # Handle form submission
    if form_data and form_data.get("action") == "submit":
        # Extract values
        values = form_data.get("values", {})
        follow_up = values.get("follow_up", "")
        custom_question = values.get("custom_question", "")

        # Use custom question if provided, otherwise use selected follow-up
        question = custom_question if custom_question else follow_up

        # Get original research context
        refined_topic = context.get("refined_topic", "")
        research_results = context.get("research_results", {})
        summary = research_results.get("summary", "")

        # Create research input for the follow-up
        llm_client = create_llm_client()

        # Create prompt for follow-up exploration
        explore_prompt = f"""
        Original Research Topic: {refined_topic}

        Topic Summary:
        {summary}

        Follow-up Question: {question}

        Please provide a detailed answer to this follow-up question based on the research topic.
        Include additional sources or references if relevant.
        """

        # Get exploration results
        exploration = await llm_client.complete(
            prompt=explore_prompt,
            system_message="You are a research assistant providing detailed answers to follow-up questions.",
            temperature=0.3,
            max_tokens=1000
        )

        # Format exploration as markdown
        exploration_markdown = f"""
        # Follow-up Exploration

        ## Question

        {question}

        ## Answer

        {exploration.content}
        """

        # Move to explore step
        return WorkflowStepResponse(
            data={"status": "exploration_complete"},
            ui_updates=[
                UIComponentUpdate(
                    key="results_display",
                    state={"markdown_content": exploration_markdown}
                )
            ],
            next_step_id="explore",
            context_updates={
                "follow_up_question": question,
                "exploration_result": exploration.content
            }
        )

    # Initial step load - should never happen directly
    return WorkflowStepResponse(
        data={"status": "results_ready"},
        ui_updates=[],
        context_updates={}
    )

# Step 4: Explore
@workflow_step(
    agent_config=research_agent,
    workflow_id="interactive_research",
    step_id="explore",
    name="Explore Further",
    ui_components=[results_display, explore_form]
)
async def handle_explore_step(input_data) -> WorkflowStepResponse:
    """Handle further exploration."""
    # Almost identical to results step - allows for multiple follow-ups
    return await handle_results_step(input_data)
```

## AI Code Assistant

This example creates a complete code assistant agent that helps generate, review, and improve code.

### Agent Setup

```python
from agentnexus.base_types import AgentConfig, Capability, ActionType, Workflow, WorkflowStep
from agentnexus.action_manager import agent_action
from agentnexus.services.llm_client import create_llm_client
from agentnexus.ui_components import CodeEditorComponent, FormComponent, FormField, MarkdownComponent
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# Define input/output models
class CodeGenInput(BaseModel):
    description: str = Field(..., description="Description of what the code should do")
    language: str = Field(..., description="Programming language")
    include_tests: bool = Field(False, description="Whether to include tests")
    frameworks: Optional[List[str]] = Field(None, description="Frameworks to use")

class CodeGenOutput(BaseModel):
    code: str
    language: str
    explanation: str
    tests: Optional[str] = None
    next_steps: List[str]

class CodeReviewInput(BaseModel):
    code: str
    language: str = Field("python", description="Programming language")
    review_focus: Optional[List[str]] = Field(None, description="Focus areas for review")

class CodeReviewOutput(BaseModel):
    issues: List[Dict[str, Any]]
    improvements: List[Dict[str, str]]
    code_quality: Dict[str, float]
    suggested_fixes: str
    explanation: str

# Define agent
code_agent = AgentConfig(
    name="AI Code Assistant",
    version="1.0.0",
    description="AI-powered assistant for code generation, review, and improvement",
    capabilities=[
        Capability(
            skill_path=["Development", "Code Generation"],
            metadata={
                "languages": ["Python", "JavaScript", "TypeScript", "Java", "C#", "Go"],
                "frameworks": ["React", "FastAPI", "Django", "Flask", "Express"],
                "features": ["Generation", "Tests", "Documentation"]
            }
        ),
        Capability(
            skill_path=["Development", "Code Review"],
            metadata={
                "review_types": ["Security", "Performance", "Style", "Logic"],
                "features": ["Issue Detection", "Improvement Suggestions", "Code Metrics"]
            }
        ),
        Capability(
            skill_path=["Development", "Code Improvement"],
            metadata={
                "improvement_types": ["Refactoring", "Optimization", "Bug Fixing"],
                "features": ["Code Transformation", "Algorithm Improvement", "Type Hints"]
            }
        )
    ]
)

# Define code generation action
@agent_action(
    agent_config=code_agent,
    action_type=ActionType.GENERATE,
    name="Generate Code",
    description="Generates code based on a description"
)
async def generate_code(input_data: CodeGenInput) -> CodeGenOutput:
    """Generate code based on a description."""
    # Create LLM client
    llm_client = create_llm_client()

    # Extract parameters
    description = input_data.description
    language = input_data.language
    include_tests = input_data.include_tests
    frameworks = input_data.frameworks or []

    # Create prompt for code generation
    frameworks_text = f"using {', '.join(frameworks)}" if frameworks else ""
    tests_text = "Include comprehensive tests for the code." if include_tests else ""

    prompt = f"""
    Generate {language} code {frameworks_text} that accomplishes the following:

    {description}

    Your response should include:
    1. Well-structured, production-quality code
    2. Clear comments explaining key sections
    3. A brief explanation of how the code works
    4. Next steps for extending or improving the code
    {tests_text}

    Make the code as robust, readable, and maintainable as possible.
    """

    # Call the LLM
    response = await llm_client.complete(
        prompt=prompt,
        system_message="""You are an expert software developer who writes clean, efficient, well-documented code.
        Follow best practices for the requested language and frameworks.""",
        temperature=0.2,
        max_tokens=2000
    )

    # Process the response
    content = response.content

    # Extract code (find code blocks)
    import re
    code_pattern = r"```(?:\w+)?\n([\s\S]*?)```"
    code_matches = re.findall(code_pattern, content)

    if code_matches:
        # Use the first code block as the main code
        main_code = code_matches[0].strip()

        # Check if there are additional code blocks (possibly tests)
        tests = None
        if len(code_matches) > 1 and include_tests:
            tests = code_matches[1].strip()
    else:
        # If no code blocks found, make a best guess
        if "```" in content:
            parts = content.split("```")
            if len(parts) > 2:
                main_code = parts[1].strip()
                if include_tests and len(parts) > 4:
                    tests = parts[3].strip()
            else:
                main_code = content  # Fallback to using entire content
        else:
            main_code = content

    # Extract explanation (text before or after code block)
    explanation_pattern = r".*?(?:```(?:\w+)?\n[\s\S]*?```)([\s\S]*)"
    explanation_matches = re.findall(explanation_pattern, content)

    if explanation_matches:
        explanation = explanation_matches[0].strip()
    else:
        # Try to find an "Explanation" section
        if "Explanation:" in content:
            explanation = content.split("Explanation:", 1)[1].strip()
            if "```" in explanation:
                explanation = explanation.split("```", 1)[0].strip()
        elif "How it works:" in content:
            explanation = content.split("How it works:", 1)[1].strip()
            if "```" in explanation:
                explanation = explanation.split("```", 1)[0].strip()
        else:
            # Fallback: use everything except code blocks
            explanation = re.sub(code_pattern, "", content).strip()

    # Extract next steps
    next_steps = []
    if "Next steps:" in content or "Next Steps:" in content:
        next_section = content.split("Next steps:", 1)[1] if "Next steps:" in content else content.split("Next Steps:", 1)[1]
        next_section = next_section.strip()
        next_lines = next_section.split("\n")
        for line in next_lines:
            if line.strip().startswith("- ") or line.strip().startswith("* "):
                next_steps.append(line.strip()[2:])
            elif line.strip().startswith("#") or line.strip().startswith("1. "):
                break

    # If we couldn't extract next steps, ask the LLM specifically
    if not next_steps:
        next_steps_prompt = f"""
        Based on this code:

        ```{language}
        {main_code}
        ```

        Provide 3-5 specific next steps for extending or improving this code.
        """

        next_steps_response = await llm_client.complete(
            prompt=next_steps_prompt,
            system_message="You are a software developer suggesting improvements to code.",
            temperature=0.3,
            max_tokens=500
        )

        next_steps_content = next_steps_response.content
        for line in next_steps_content.split("\n"):
            if line.strip().startswith("- ") or line.strip().startswith("* "):
                next_steps.append(line.strip()[2:])
            elif line.strip().startswith("#") or ":" in line:
                continue
            elif line.strip():
                next_steps.append(line.strip())

    # Ensure we have at least some next steps
    if not next_steps:
        next_steps = [
            "Add error handling",
            "Improve documentation",
            "Add more tests",
            "Optimize performance"
        ]

    # Return the code generation output
    return CodeGenOutput(
        code=main_code,
        language=language,
        explanation=explanation,
        tests=tests,
        next_steps=next_steps
    )

# Define code review action
@agent_action(
    agent_config=code_agent,
    action_type=ActionType.GENERATE,
    name="Review Code",
    description="Reviews code and provides improvement suggestions"
)
async def review_code(input_data: CodeReviewInput) -> CodeReviewOutput:
    """Review code and provide improvement suggestions."""
    # Create LLM client
    llm_client = create_llm_client()

    # Extract parameters
    code = input_data.code
    language = input_data.language
    review_focus = input_data.review_focus or ["bugs", "performance", "style", "security"]

    # Create prompt for code review
    focus_text = ", ".join(review_focus)

    prompt = f"""
    Review this {language} code, focusing on {focus_text}:

    ```{language}
    {code}
    ```

    Provide a thorough code review including:
    1. Issues found (bugs, security concerns, etc.)
    2. Improvements for readability and maintainability
    3. Performance optimizations
    4. Code quality metrics
    5. Suggested fixes with code examples

    Format your response as:

    ISSUES:
    - [Category] Issue description
    - ...

    IMPROVEMENTS:
    - [Area] Improvement suggestion
    - ...

    CODE QUALITY:
    - Structure: X/10
    - Readability: X/10
    - Maintainability: X/10
    - Performance: X/10

    SUGGESTED FIXES:
    ```{language}
    // Code with suggested fixes
    ```

    EXPLANATION:
    Detailed explanation of the review and recommendations.
    """

    # Call the LLM
    response = await llm_client.complete(
        prompt=prompt,
        system_message="""You are an expert code reviewer with deep knowledge of best practices, security, and performance optimization.
        Provide constructive, specific feedback that will help improve the code.""",
        temperature=0.2,
        max_tokens=2000
    )

    # Process the response
    content = response.content

    # Extract issues
    issues_text = extract_section(content, "ISSUES")
    issues = []
    for line in issues_text.split("\n"):
        if line.strip() and (line.strip().startswith("- ") or line.strip().startswith("* ")):
            issue_text = line.strip()[2:]
            if "[" in issue_text and "]" in issue_text:
                category = issue_text.split("[", 1)[1].split("]", 1)[0]
                description = issue_text.split("]", 1)[1].strip()
                issues.append({"category": category, "description": description})
            else:
                issues.append({"category": "General", "description": issue_text})

    # Extract improvements
    improvements_text = extract_section(content, "IMPROVEMENTS")
    improvements = []
    for line in improvements_text.split("\n"):
        if line.strip() and (line.strip().startswith("- ") or line.strip().startswith("* ")):
            improvement_text = line.strip()[2:]
            if "[" in improvement_text and "]" in improvement_text:
                area = improvement_text.split("[", 1)[1].split("]", 1)[0]
                suggestion = improvement_text.split("]", 1)[1].strip()
                improvements.append({"area": area, "suggestion": suggestion})
            else:
                improvements.append({"area": "General", "suggestion": improvement_text})

    # Extract code quality
    quality_text = extract_section(content, "CODE QUALITY")
    code_quality = {}
    for line in quality_text.split("\n"):
        if ":" in line and "/" in line:
            metric, score_text = line.strip().split(":", 1)
            metric = metric.strip().lstrip("- ").lstrip("* ")
            score_text = score_text.strip()
            if "/" in score_text:
                try:
                    score = float(score_text.split("/")[0])
                    code_quality[metric.lower()] = score
                except ValueError:
                    pass

    # If we couldn't parse code quality, provide defaults
    if not code_quality:
        code_quality = {
            "structure": 7.0,
            "readability": 7.0,
            "maintainability": 7.0,
            "performance": 7.0
        }

    # Extract suggested fixes
    import re
    fixes_pattern = r"```(?:\w+)?\n([\s\S]*?)```"
    fixes_match = re.search(fixes_pattern, content[content.find("SUGGESTED FIXES:"):] if "SUGGESTED FIXES:" in content else content)

    if fixes_match:
        suggested_fixes = fixes_match.group(1).strip()
    else:
        suggested_fixes = "# No specific code fixes suggested"

    # Extract explanation
    explanation = extract_section(content, "EXPLANATION")
    if not explanation:
        explanation = "Review complete. See the issues and improvements sections for details."

    # Return the code review output
    return CodeReviewOutput(
        issues=issues,
        improvements=improvements,
        code_quality=code_quality,
        suggested_fixes=suggested_fixes,
        explanation=explanation
    )

# Define interactive code review UI action
@agent_action(
    agent_config=code_agent,
    action_type=ActionType.CUSTOM_UI,
    name="Interactive Code Editor",
    description="Interactive code editor with generation and review capabilities",
    ui_components=[
        CodeEditorComponent(
            component_key="code_editor",
            title="Code Editor",
            programming_language="python",
            editor_content="# Enter your code here\n\ndef example():\n    pass\n",
            editor_theme="vs-dark",
            editor_height="400px",
            event_handlers={}  # Will be set up in action function
        ),
        FormComponent(
            component_key="code_actions",
            title="Code Actions",
            form_fields=[
                FormField(
                    field_name="language",
                    label_text="Language",
                    field_type="select",
                    field_options=[
                        {"value": "python", "label": "Python"},
                        {"value": "javascript", "label": "JavaScript"},
                        {"value": "typescript", "label": "TypeScript"},
                        {"value": "java", "label": "Java"},
                        {"value": "csharp", "label": "C#"},
                        {"value": "go", "label": "Go"}
                    ]
                ),
                FormField(
                    field_name="action",
                    label_text="Action",
                    field_type="select",
                    field_options=[
                        {"value": "generate", "label": "Generate New Code"},
                        {"value": "review", "label": "Review Code"},
                        {"value": "refactor", "label": "Refactor Code"},
                        {"value": "document", "label": "Add Documentation"},
                        {"value": "test", "label": "Generate Tests"}
                    ]
                ),
                FormField(
                    field_name="description",
                    label_text="Description / Instructions",
                    field_type="textarea",
                    placeholder_text="Describe what you want to do with the code"
                )
            ],
            event_handlers={}  # Will be set up in action function
        ),
        MarkdownComponent(
            component_key="results_display",
            title="Results",
            markdown_content="Select an action and provide a description to get started."
        )
    ]
)
async def interactive_code_editor(input_data) -> Dict[str, Any]:
    """Handle interactive code editor with LLM integration."""
    # Extract form data
    form_data = getattr(input_data, 'form_data', None)

    # If we don't have form data, return initial state
    if not form_data:
        return {
            "status": "ready",
            "ui_updates": []
        }

    # Process based on action
    action = form_data.get("action", "")
    component_key = form_data.get("component_key", "")

    # Handle form submission
    if component_key == "code_actions" and form_data.get("values"):
        values = form_data.get("values", {})
        language = values.get("language", "python")
        action_type = values.get("action", "review")
        description = values.get("description", "")

        # Get current code from context
        context = getattr(input_data, 'context', {}) or {}
        code = context.get("current_code", "# No code provided")

        # Create LLM client
        llm_client = create_llm_client()

        # Different handling based on action type
        if action_type == "generate":
            # Generate new code
            gen_input = CodeGenInput(
                description=description,
                language=language,
                include_tests=False
            )

            gen_result = await generate_code(gen_input)

            # Format the result
            result_md = f"""
            # Generated Code

            ## Code

            ```{language}
            {gen_result.code}
            ```

            ## Explanation

            {gen_result.explanation}

            ## Next Steps

            {chr(10).join(['- ' + step for step in gen_result.next_steps])}
            """

            return {
                "status": "code_generated",
                "ui_updates": [
                    {
                        "key": "code_editor",
                        "state": {
                            "editor_content": gen_result.code,
                            "programming_language": language
                        }
                    },
                    {
                        "key": "results_display",
                        "state": {
                            "markdown_content": result_md
                        }
                    }
                ]
            }

        elif action_type == "review":
            # Review existing code
            review_input = CodeReviewInput(
                code=code,
                language=language
            )

            review_result = await review_code(review_input)

            # Format the issues
            issues_md = "\n".join([f"- **[{issue['category']}]** {issue['description']}" for issue in review_result.issues])

            # Format the improvements
            improvements_md = "\n".join([f"- **[{imp['area']}]** {imp['suggestion']}" for imp in review_result.improvements])

            # Format code quality metrics
            quality_md = "\n".join([f"- **{key.capitalize()}**: {value}/10" for key, value in review_result.code_quality.items()])

            # Format the result
            result_md = f"""
            # Code Review Results

            ## Issues Found

            {issues_md if issues_md else "No significant issues found."}

            ## Suggested Improvements

            {improvements_md if improvements_md else "No specific improvements suggested."}

            ## Code Quality Metrics

            {quality_md}

            ## Suggested Code Changes

            ```{language}
            {review_result.suggested_fixes}
            ```

            ## Explanation

            {review_result.explanation}
            """

            return {
                "status": "code_reviewed",
                "ui_updates": [
                    {
                        "key": "results_display",
                        "state": {
                            "markdown_content": result_md
                        }
                    }
                ]
            }

        elif action_type == "refactor":
            # Refactor the code
            refactor_prompt = f"""
            Refactor this {language} code according to these instructions:

            {description}

            Original Code:
            ```{language}
            {code}
            ```

            Provide a refactored version with better structure, readability, and performance.
            Explain the key changes made and why they improve the code.
            """

            refactor_response = await llm_client.complete(
                prompt=refactor_prompt,
                system_message="You are an expert software developer specializing in code refactoring.",
                temperature=0.2
            )

            # Extract refactored code
            import re
            code_pattern = r"```(?:\w+)?\n([\s\S]*?)```"
            code_matches = re.findall(code_pattern, refactor_response.content)

            refactored_code = code_matches[0] if code_matches else "# No refactored code generated"

            # Remove the code block from the explanation
            explanation = re.sub(code_pattern, "", refactor_response.content).strip()

            # Format the result
            result_md = f"""
            # Refactored Code

            ## Code

            ```{language}
            {refactored_code}
            ```

            ## Explanation

            {explanation}
            """

            return {
                "status": "code_refactored",
                "ui_updates": [
                    {
                        "key": "code_editor",
                        "state": {
                            "editor_content": refactored_code,
                            "programming_language": language
                        }
                    },
                    {
                        "key": "results_display",
                        "state": {
                            "markdown_content": result_md
                        }
                    }
                ]
            }

        elif action_type == "document":
            # Add documentation to the code
            document_prompt = f"""
            Add comprehensive documentation to this {language} code:

            ```{language}
            {code}
            ```

            Add:
            1. File-level docstring/comments
            2. Function/class documentation
            3. Parameter descriptions
            4. Return value descriptions
            5. Example usage where appropriate

            Follow best practices for {language} documentation formats.
            """

            document_response = await llm_client.complete(
                prompt=document_prompt,
                system_message="You are an expert software developer specializing in code documentation.",
                temperature=0.2
            )

            # Extract documented code
            import re
            code_pattern = r"```(?:\w+)?\n([\s\S]*?)```"
            code_matches = re.findall(code_pattern, document_response.content)

            documented_code = code_matches[0] if code_matches else "# No documented code generated"

            # Format the result
            result_md = f"""
            # Documented Code

            ```{language}
            {documented_code}
            ```

            ## Documentation Standards

            This code follows {language} documentation best practices:

            - File-level documentation explaining purpose
            - Function/method documentation describing behavior
            - Parameter and return value descriptions
            - Type annotations where applicable
            - Example usage where helpful
            """

            return {
                "status": "code_documented",
                "ui_updates": [
                    {
                        "key": "code_editor",
                        "state": {
                            "editor_content": documented_code,
                            "programming_language": language
                        }
                    },
                    {
                        "key": "results_display",
                        "state": {
                            "markdown_content": result_md
                        }
                    }
                ]
            }

        elif action_type == "test":
            # Generate tests for the code
            test_prompt = f"""
            Generate comprehensive tests for this {language} code:

            ```{language}
            {code}
            ```

            Create tests that:
            1. Cover all functions and methods
            2. Test normal cases, edge cases and error cases
            3. Achieve high code coverage
            4. Follow best practices for {language} testing

            Use the appropriate testing framework for {language}.
            """

            test_response = await llm_client.complete(
                prompt=test_prompt,
                system_message="You are an expert software developer specializing in test development.",
                temperature=0.2
            )

            # Extract test code
            import re
            code_pattern = r"```(?:\w+)?\n([\s\S]*?)```"
            code_matches = re.findall(code_pattern, test_response.content)

            test_code = code_matches[0] if code_matches else "# No test code generated"

            # Format the result
            result_md = f"""
            # Generated Tests

            ```{language}
            {test_code}
            ```

            ## Testing Approach

            These tests are designed to:

            - Validate core functionality
            - Check edge cases and error handling
            - Ensure code behaves as expected
            - Document expected behavior through tests

            To run these tests, save them to a file and execute with the appropriate test runner for {language}.
            """

            return {
                "status": "tests_generated",
                "ui_updates": [
                    {
                        "key": "results_display",
                        "state": {
                            "markdown_content": result_md
                        }
                    }
                ]
            }

        # Default response
        return {
            "status": "unknown_action",
            "ui_updates": [
                {
                    "key": "results_display",
                    "state": {
                        "markdown_content": "Unknown action selected."
                    }
                }
            ]
        }

    # Handle code editor updates
    elif component_key == "code_editor" and "content" in form_data:
        code_content = form_data.get("content", "")

        # Store the current code in context for future actions
        return {
            "status": "code_updated",
            "context_updates": {
                "current_code": code_content
            }
        }

    # Default response for unhandled events
    return {
        "status": "unhandled_event",
        "ui_updates": []
    }
```

## Document Analysis Agent

This example creates a document analysis agent that can process, analyze, and extract information from documents.

```python
from agentnexus.base_types import AgentConfig, Capability, ActionType
from agentnexus.action_manager import agent_action
from agentnexus.services.llm_client import create_llm_client
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# Define models
class DocumentInput(BaseModel):
    content: str = Field(..., description="Document content to analyze")
    document_type: str = Field("text", description="Document type (text, pdf, code, etc.)")
    analysis_type: List[str] = Field(["summary", "key_points"], description="Types of analysis to perform")

class DocumentAnalysisOutput(BaseModel):
    summary: Optional[str] = None
    key_points: Optional[List[str]] = None
    entities: Optional[List[Dict[str, str]]] = None
    topics: Optional[List[Dict[str, float]]] = None
    sentiment: Optional[Dict[str, float]] = None
    structure: Optional[Dict[str, Any]] = None

# Define agent
document_agent = AgentConfig(
    name="Document Analyzer",
    version="1.0.0",
    description="AI-powered document analysis and information extraction",
    capabilities=[
        Capability(
            skill_path=["Documents", "Analysis"],
            metadata={
                "document_types": ["Text", "PDF", "Code", "Email"],
                "analysis_types": ["Summary", "Key Points", "Entities", "Topics", "Sentiment", "Structure"]
            }
        ),
        Capability(
            skill_path=["Documents", "Information Extraction"],
            metadata={
                "extraction_types": ["Entities", "Dates", "Statistics", "Citations", "Contacts"]
            }
        )
    ]
)

# Define document analysis action
@agent_action(
    agent_config=document_agent,
    action_type=ActionType.GENERATE,
    name="Analyze Document",
    description="Analyzes documents and extracts information"
)
async def analyze_document(input_data: DocumentInput) -> DocumentAnalysisOutput:
    """Analyze a document and extract information."""
    # Create LLM client
    llm_client = create_llm_client()

    # Extract parameters
    content = input_data.content
    document_type = input_data.document_type
    analysis_types = input_data.analysis_type

    # Initialize result
    result = DocumentAnalysisOutput()

    # Generate summary if requested
    if "summary" in analysis_types:
        summary_prompt = f"""
        Provide a concise summary of this {document_type} document:

        {content[:6000]}  # Limit content to avoid token limits

        The summary should capture the main points and purpose of the document in 2-3 paragraphs.
        """

        summary_response = await llm_client.complete(
            prompt=summary_prompt,
            system_message="You are an expert document analyst specializing in creating concise, accurate summaries.",
            temperature=0.3
        )

        result.summary = summary_response.content.strip()

    # Extract key points if requested
    if "key_points" in analysis_types:
        key_points_prompt = f"""
        Extract the key points from this {document_type} document:

        {content[:6000]}  # Limit content to avoid token limits

        Provide 5-10 key points that capture the most important information.
        Format each point as a single, concise statement.
        """

        key_points_response = await llm_client.complete(
            prompt=key_points_prompt,
            system_message="You are an expert document analyst specializing in identifying key information.",
            temperature=0.3
        )

        # Extract key points from response
        key_points_text = key_points_response.content
        key_points = []

        for line in key_points_text.split("\n"):
            if line.strip().startswith("- ") or line.strip().startswith("* "):
                key_points.append(line.strip()[2:])
            elif line.strip().startswith("1. ") or line.strip().startswith("1) "):
                # Handle numbered lists - extract the number and points
                point_text = re.sub(r"^\d+[\.\)]\s*", "", line.strip())
                key_points.append(point_text)
            elif line.strip() and not line.strip().startswith("#") and ":" not in line:
                # Catch other non-empty, non-header, non-label lines
                key_points.append(line.strip())

        result.key_points = key_points

    # Extract entities if requested
    if "entities" in analysis_types:
        entities_prompt = f"""
        Extract the named entities from this {document_type} document:

        {content[:6000]}  # Limit content to avoid token limits

        Identify people, organizations, locations, dates, and other significant entities.
        Format the output as:

        PEOPLE:
        - Name 1
        - Name 2

        ORGANIZATIONS:
        - Organization 1
        - Organization 2

        LOCATIONS:
        - Location 1
        - Location 2

        DATES:
        - Date 1
        - Date 2

        OTHER:
        - Entity 1 (Type)
        - Entity 2 (Type)
        """

        entities_response = await llm_client.complete(
            prompt=entities_prompt,
            system_message="You are an expert document analyst specializing in named entity recognition.",
            temperature=0.2
        )

        # Extract entities from response
        entities_text = entities_response.content
        entities = []

        current_type = None
        for line in entities_text.split("\n"):
            if ":" in line and not line.strip().startswith("-"):
                current_type = line.split(":", 1)[0].strip()
            elif line.strip().startswith("- "):
                entity_text = line.strip()[2:]
                entity_type = current_type
                # Handle "Entity (Type)" format
                if "(" in entity_text and ")" in entity_text:
                    entity_name, entity_type_extra = entity_text.rsplit("(", 1)
                    entity_name = entity_name.strip()
                    entity_type_extra = entity_type_extra.rstrip(")").strip()
                    if entity_type_extra:
                        entity_type = entity_type_extra
                else:
                    entity_name = entity_text

                entities.append({"name": entity_name, "type": entity_type})

        result.entities = entities

    # Extract topics if requested
    if "topics" in analysis_types:
        topics_prompt = f"""
        Identify the main topics in this {document_type} document, with confidence scores:

        {content[:6000]}  # Limit content to avoid token limits

        List the top 5-7 topics with a confidence score (0-1) for each.
        Format your response as:

        TOPICS:
        - Topic 1: 0.95
        - Topic 2: 0.82
        - Topic 3: 0.75
        ...
        """

        topics_response = await llm_client.complete(
            prompt=topics_prompt,
            system_message="You are an expert document analyst specializing in topic identification.",
            temperature=0.2
        )

        # Extract topics from response
        topics_text = topics_response.content
        topics = []

        for line in topics_text.split("\n"):
            if ":" in line and (line.strip().startswith("- ") or line.strip().startswith("* ")):
                line = line.strip()[2:]  # Remove list marker
                if ":" in line:
                    topic, score_text = line.split(":", 1)
                    try:
                        score = float(score_text.strip())
                        topics.append({"topic": topic.strip(), "confidence": score})
                    except ValueError:
                        topics.append({"topic": topic.strip(), "confidence": 0.5})  # Default if parsing fails

        result.topics = topics

    # Extract sentiment if requested
    if "sentiment" in analysis_types:
        sentiment_prompt = f"""
        Analyze the sentiment in this {document_type} document:

        {content[:6000]}  # Limit content to avoid token limits

        Provide scores for:
        - Overall sentiment (positive/negative) from -1 to 1
        - Confidence in the sentiment analysis from 0 to 1
        - Emotional tone scores (0-1) for: joy, sadness, anger, fear, surprise
        """

        sentiment_response = await llm_client.complete(
            prompt=sentiment_prompt,
            system_message="You are an expert document analyst specializing in sentiment analysis.",
            temperature=0.2
        )

        # Extract sentiment from response
        sentiment_text = sentiment_response.content
        sentiment = {}

        for line in sentiment_text.split("\n"):
            if ":" in line:
                key, value_text = line.split(":", 1)
                key = key.strip().lstrip("- ").lstrip("* ").lower()
                value_text = value_text.strip()
                try:
                    value = float(value_text)
                    sentiment[key] = value
                except ValueError:
                    pass

        # Ensure we have some values
        if not sentiment:
            sentiment = {
                "overall": 0.0,
                "confidence": 0.5,
                "joy": 0.0,
                "sadness": 0.0,
                "anger": 0.0,
                "fear": 0.0,
                "surprise": 0.0
            }

        result.sentiment = sentiment

    # Extract document structure if requested
    if "structure" in analysis_types:
        structure_prompt = f"""
        Analyze the structure of this {document_type} document:

        {content[:6000]}  # Limit content to avoid token limits

        Identify:
        - Document sections and their hierarchy
        - Approximate section lengths
        - Document organization pattern
        - Formatting elements (lists, tables, etc.)
        """

        structure_response = await llm_client.complete(
            prompt=structure_prompt,
            system_message="You are an expert document analyst specializing in document structure and organization.",
            temperature=0.2
        )

        # Extract structure - this is more complex, so we'll use the LLM to format it
        formatting_prompt = f"""
        Convert this document structure analysis into a JSON format:

        {structure_response.content}

        Create a JSON object with these properties:
        - sections: array of section objects with title, level, and length
        - pattern: the document organization pattern
        - elements: array of formatting elements found

        Format carefully as valid JSON.
        """

        format_response = await llm_client.complete(
            prompt=formatting_prompt,
            system_message="You convert text descriptions into valid JSON structures.",
            temperature=0.1
        )

        # Extract the JSON
        json_text = format_response.content

        # Find JSON in the response (it might be in a code block)
        import json
        import re

        json_pattern = r"```(?:json)?\n([\s\S]*?)```"
        json_match = re.search(json_pattern, json_text)

        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON without code blocks
            json_str = json_text
            # Remove any text before { and after }
            start_idx = json_str.find("{")
            end_idx = json_str.rfind("}")
            if start_idx != -1 and end_idx != -1:
                json_str = json_str[start_idx:end_idx+1]

        try:
            structure = json.loads(json_str)
            result.structure = structure
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            result.structure = {
                "sections": [],
                "pattern": "unknown",
                "elements": []
            }

    # Return the analysis result
    return result

# Helper function to extract sections from LLM output
def extract_section(text, section_name):
    """Extract a section from the LLM output text."""
    # Try different section heading formats
    patterns = [
        f"{section_name}:",
        f"{section_name.upper()}:",
        f"## {section_name}",
        f"**{section_name}**",
        f"{section_name}"
    ]

    for pattern in patterns:
        if pattern in text:
            parts = text.split(pattern, 1)
            if len(parts) > 1:
                section_text = parts[1].strip()
                # Try to find the end of the section (next section heading)
                for end_pattern in patterns:
                    if end_pattern != pattern and end_pattern in section_text:
                        section_text = section_text.split(end_pattern, 1)[0].strip()
                return section_text

    # If no section found, return empty string
    return ""
```

## Best Practices for LLM Agent Development

When building practical LLM agents:

1. **Task-Oriented Design**
   - Focus on solving specific user problems
   - Design the agent around clear use cases
   - Break complex tasks into manageable steps

2. **LLM Integration**
   - Use system messages to define agent personality and expertise
   - Create detailed, specific prompts with clear instructions
   - Structure LLM outputs for easier extraction
   - Include fallback mechanisms for extraction failures

3. **Interactive Workflows**
   - Guide users through multi-step processes
   - Provide feedback at each step
   - Maintain context throughout interactions
   - Allow for iteration and refinement

4. **UI Considerations**
   - Use appropriate components for each interaction type
   - Provide clear instructions and feedback
   - Design for progressive disclosure of complexity
   - Support both novice and expert users

5. **Error Handling**
   - Validate inputs before sending to LLMs
   - Wrap LLM calls in try/except blocks
   - Provide helpful error messages
   - Include fallback options for LLM failures

