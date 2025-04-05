from fastapi import HTTPException, BackgroundTasks, Request
from pathlib import Path
import json
import black
import datetime
from typing import List, Any
from loguru import logger
from agentnexus.base_types import AgentConfig, Capability, ActionType
from agentnexus.action_manager import agent_action

from agents.models.code_agent_v1 import (
    ChatInput, ChatOutput, GenerateCodeInput, GenerateCodeOutput,
    ImproveCodeInput, ImproveCodeOutput, TestCodeInput, TestCodeOutput,
    CollectRequirementsInput, CollectRequirementsOutput,
    CodeReviewInput, CodeReviewOutput
)
from agents.ui_components.code_agent_v1 import main_editor, analysis_output
from agents.llm_client import create_llm_client

AGENT_TEMPLATE = Path(__file__).parent / "templates" / "agent.html"
AGENTS_TEMPLATE = Path(__file__).parent / "templates" / "agents.html"

# Initialize LLM client
llm_client = create_llm_client()

CODE_CAPABILITIES = [
    Capability(
        skill_path=["Development", "Code Generation"],
        metadata={
            "expertise": "advanced",
            "features": [
                "Python Code Generation",
                "Code Improvement",
                "Testing",
                "Documentation",
                "Requirements Analysis"
            ],
            "frameworks": ["FastAPI", "Django", "Flask"],
            "code_quality": ["PEP 8", "Type Hints", "Documentation"]
        }
    ),
    Capability(
        skill_path=["Development", "Code Analysis"],
        metadata={
            "expertise": "advanced",
            "features": [
                "Code Review",
                "Performance Analysis",
                "Security Review",
                "Best Practices"
            ]
        }
    )
]

code_agent_v1_app = AgentConfig(
    name="Python Code Assistant V1",
    version="1.0.0",
    description="Advanced code generation with dynamic forms",
    base_path="/v1/code_agent",
    capabilities=CODE_CAPABILITIES
)
@agent_action(
    agent_config=code_agent_v1_app,
    action_type=ActionType.TALK,
    name="Chat with Python Assistant",
    description="Engage in a conversation with the Python code agent",
    response_template_md="templates/chat_response.md",
    schema_definitions={
        "ChatInput": ChatInput,
        "ChatOutput": ChatOutput
    }
)
async def chat_with_agent(input_data: ChatInput) -> ChatOutput:
    """Handle chat interactions with the agent."""
    try:
        response = await llm_client.complete(
            prompt=input_data.message,
            system_message="You are a helpful Python programming assistant.",
            temperature=0.7
        )

        return ChatOutput(
            response=response.content,
            confidence=0.95,
            suggested_actions=["Share your code", "Specify requirements", "Run analysis"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@agent_action(
    agent_config=code_agent_v1_app,
    action_type=ActionType.GENERATE,
    name="Generate Python Code",
    description="Generates Python code based on requirements",
    response_template_md="templates/generate_response.md",
    schema_definitions={
        "GenerateCodeInput": GenerateCodeInput,
        "GenerateCodeOutput": GenerateCodeOutput
    }
)
async def generate_code(input_data: GenerateCodeInput) -> GenerateCodeOutput:
    """Generate Python code based on specified requirements."""
    try:
        generated_code = await _generate_code_from_requirements(input_data.code_requirements)
        test_cases = []
        if input_data.include_tests:
            test_code = await _generate_tests(generated_code, [])
            test_cases = [test_code] if test_code else []
        documentation = await _generate_documentation(generated_code, input_data.documentation_level)

        return GenerateCodeOutput(
            generated_code=generated_code,
            description="Generated code based on requirements",
            test_cases=test_cases,
            documentation=documentation
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@agent_action(
    agent_config=code_agent_v1_app,
    action_type=ActionType.GENERATE,
    name="Improve Python Code",
    description="Improves and formats existing Python code",
    schema_definitions={
        "ImproveCodeInput": ImproveCodeInput,
        "ImproveCodeOutput": ImproveCodeOutput
    }
)
async def improve_code(input_data: ImproveCodeInput) -> ImproveCodeOutput:
    """Improve and format Python code."""
    try:
        code_changes = []
        for change in input_data.changes_list:
            improved_code = await _apply_code_changes(change)

            if input_data.apply_black_formatting:
                improved_code = black.format_str(improved_code, mode=black.FileMode())

            code_changes.append({
                "type": change.type,
                "description": change.description,
                "before": change.target or "",
                "after": improved_code,
                "impact": "Code structure improved and formatted"
            })

        return ImproveCodeOutput(
            code_changes=code_changes,
            changes_description="Applied code improvements successfully",
            quality_metrics={
                "complexity": 75.0,
                "maintainability": 85.0,
                "test_coverage": 90.0
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def _generate_code_from_requirements(code_requirements: Any) -> str:
    """Generate code based on requirements using LLM."""
    prompt = f"Generate Python/{code_requirements.framework} code for: {code_requirements.description}. Functions: {', '.join(code_requirements.required_functions)}"

    response = await llm_client.complete(
        prompt=prompt,
        system_message="You are an expert Python developer. Generate clean, efficient code following PEP 8 standards.",
        temperature=0.3
    )
    return response.content

async def _generate_tests(code: str, test_instructions: List[Any]) -> str:
    """Generate test cases using LLM."""
    prompt = f"""
    Generate Python test cases for the following code:
    {code}

    Test requirements:
    {[instr.description for instr in test_instructions]}
    """

    response = await llm_client.complete(
        prompt=prompt,
        system_message="You are an expert in Python testing. Generate comprehensive test cases.",
        temperature=0.2
    )
    return response.content

async def _generate_documentation(code: str, level: str) -> str:
    """Generate documentation using LLM."""
    prompt = f"""
    Generate {level} documentation for the following Python code:
    {code}
    """

    response = await llm_client.complete(
        prompt=prompt,
        system_message="You are a technical documentation expert. Generate clear and comprehensive documentation.",
        temperature=0.3
    )
    return response.content

async def _apply_code_changes(change: Any) -> str:
    """Apply code improvements using LLM."""
    prompt = f"""
    Improve the following Python code according to these requirements:
    Change type: {change.type}
    Description: {change.description}
    Priority: {change.priority}

    Code to improve:
    {change.target or "No code provided"}
    """

    response = await llm_client.complete(
        prompt=prompt,
        system_message="You are an expert Python developer. Improve the code while maintaining its functionality.",
        temperature=0.2
    )
    return response.content


def parse_questionnaire_response(response: str) -> dict:
    """Clean and extract JSON from various response formats."""
    try:
        # Split response into questionnaire and JSON parts
        content = response.content
        #  Extract JSON from response
        content = response.content
        # If response is wrapped in markdown code blocks, extract just the JSON
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            json_str = content.split("```")[1].strip()
        else:
            json_str = content.strip()
        # Parse the JSON
        form_structure = json.loads(json_str)
        # Validate expected structure
        if not isinstance(form_structure, dict):
            raise ValueError("Response is not a JSON object")
        if "questionnaire_form" not in form_structure:
            raise ValueError("Response missing questionnaire_form key")
        if "steps" not in form_structure["questionnaire_form"]:
            raise ValueError("Response missing steps in questionnaire_form")
        # Return just the form structure
        return form_structure["questionnaire_form"]
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        logger.error(f"Raw response: {content}")
        logger.error(f"Extracted JSON: {json_str}")
        raise HTTPException(
            status_code=400,
            detail="Failed to generate valid form structure. Please try again."
        )
    except Exception as e:
        logger.error(f"Error processing form: {str(e)}")
        logger.error(f"Raw response: {content}")
        raise HTTPException(
            status_code=400,
            detail="Failed to process the requirements form. Please try again."
        )

async def _generate_requirements_form(message: str) -> dict:
    """Generate both questionnaire and JSON form using Chain of Thought in a single prompt."""
    # Define the JSON template separately
    json_template = """
    {
      "questionnaire_form": {
        "steps": [
          {
            "title": "Section Title",
            "fields": [
              {
                "type": "text|textarea|select|checkbox|radio|number",
                "name": "field_name",
                "label": "Question text",
                "placeholder": "Helper text for user",
                "validation": { "required": true|false },
                "options": [{ "label": "Option text", "value": "option_value" }]
              }
            ]
          }
        ]
      }
    }
    """
    # Define the prompt without deeply nested f-strings
    prompt = f"""You are a requirements gathering expert. Analyze this project description and generate a detailed requirements questionnaire:

Project: {message}

Generate a JSON form with 5 key sections:
1. Core Purpose and Goals (focus on objectives, target users, key features)
2. Content and Features (specific functionalities, user interactions)
3. Design and User Experience (UI/UX preferences, responsive design)
4. Technical Requirements (platform, integrations, infrastructure)
5. Timeline and Budget (development timeline, budget constraints)

Required JSON format:
{json_template}

Field type guidelines:
- Use textarea: For detailed explanations (goals, requirements)
- Use select: For single-choice predefined options (platforms, design themes)
- Use checkbox: For multiple-choice selections (features, integrations)
- Use radio: For mutually exclusive choices (yes/no, priority levels)
- Use number: For budgets, timelines, quantities

Example 1:
Query: "I want to build a website for collecting user reviews on tech books, It should be similar to social book club"
Response:
{{
  "questionnaire_form": {{
    "steps": [
      {{
        "title": "Core Purpose and Goals",
        "fields": [
          {{
            "type": "textarea",
            "name": "primary_goals",
            "label": "Primary goals and objectives",
            "placeholder": "Describe the primary goals and objectives...",
            "validation": {{ "required": true }}
          }},
          {{
            "type": "textarea",
            "name": "target_audience",
            "label": "Target audience",
            "placeholder": "Describe the target audience...",
            "validation": {{ "required": true }}
          }},
          {{
            "type": "checkbox",
            "name": "key_features",
            "label": "Key features needed",
            "placeholder": "",
            "validation": {{ "required": true }},
            "options": [
              {{
                "label": "User profiles with review history",
                "value": "user_profiles"
              }},
              {{
                "label": "Book discussion forums or comment sections",
                "value": "discussion_forums"
              }},
              {{
                "label": "Book rating and review system",
                "value": "rating_system"
              }}
            ]
          }}
        ]
      }},
      {{
        "title": "Content and Features",
        "fields": [
          {{
            "type": "textarea",
            "name": "content_description",
            "label": "Describe the content and features",
            "placeholder": "Provide details about the content and features...",
            "validation": {{ "required": true }}
          }}
        ]
      }}
    ]
  }}
}}

Example shortened response:
Query: "I want to build a recipe sharing and meal planning app"
Response:
{{
  "questionnaire_form": {{
    "steps": [
      {{
        "title": "Core Purpose and Goals",
        "fields": [
          {{
            "type": "textarea",
            "name": "primary_goals",
            "label": "What are the main goals of your recipe app?",
            "placeholder": "e.g., help users discover recipes, plan meals, share cooking experiences",
            "validation": {{ "required": true }}
          }},
          {{
            "type": "checkbox",
            "name": "key_features",
            "label": "Essential features needed",
            "options": [
              {{
                "label": "Recipe creation and sharing",
                "value": "recipe_sharing"
              }},
              {{
                "label": "Meal planning calendar",
                "value": "meal_planning"
              }},
              {{
                "label": "Shopping list generation",
                "value": "shopping_list"
              }},
              {{
                "label": "Nutritional information tracking",
                "value": "nutrition_tracking"
              }}
            ]
          }}
        ]
      }},
      {{
        "title": "Content and Features",
        "fields": [
          {{
            "type": "textarea",
            "name": "content_description",
            "label": "Describe the content and features",
            "placeholder": "Provide details about the content and features...",
            "validation": {{ "required": true }}
          }}
        ]
      }}
    ]
  }}
}}

Make questions:
1. Specific to the project type (website, mobile app, platform)
2. Progressive (basic → advanced requirements)
3. Include relevant options based on industry standards
4. All critical fields should have "required": true
5. Add helpful placeholder text

Output only the valid JSON questionnaire form without any additional text.
"""

    response = await llm_client.complete(
        prompt=prompt,
        system_message="""You are a requirements analysis expert who creates structured forms.
Follow the chain of thought process carefully.
First output a markdown questionnaire, then output a strict JSON form structure.""",
        temperature=0.3
    )
    return parse_questionnaire_response(response)

async def _generate_phase2_form(initial_query: str, phase1_answers: dict) -> dict:
    prompt = f"""Given the initial project query and phase 1 answers, create a detailed technical questionnaire.

Initial Query: {initial_query}
Phase 1 Answers: {json.dumps(phase1_answers, indent=2)}

Generate *focused* and *crafted* questions based on the selected features and requirements. Include:
- Specific technical implementation details
- Detailed UX/UI requirements
- Integration specifications
- Performance requirements
- Security considerations
- Testing requirements
- Deployment preferences

Required JSON format:
{json_template}

Example 1:
shortened Response, build a new one from the first princples based on the previous questionare answers:
{{
  "questionnaire_form": {{
    "steps": [
      {{
        "title": "Core Purpose and Goals",
        "fields": [
          {{
            "type": "textarea",
            "name": "primary_goals",
            "label": "What are the main goals of your recipe app?",
            "placeholder": "e.g., help users discover recipes, plan meals, share cooking experiences",
            "validation": {{ "required": true }}
          }},
          {{
            "type": "checkbox",
            "name": "key_features",
            "label": "Essential features needed",
            "options": [
              {{
                "label": "Recipe creation and sharing",
                "value": "recipe_sharing"
              }},
              {{
                "label": "Meal planning calendar",
                "value": "meal_planning"
              }},
              {{
                "label": "Shopping list generation",
                "value": "shopping_list"
              }},
              {{
                "label": "Nutritional information tracking",
                "value": "nutrition_tracking"
              }}
            ]
          }}
        ]
      }},
      {{
        "title": "Content and Features",
        "fields": [
          {{
            "type": "textarea",
            "name": "content_description",
            "label": "Describe the content and features",
            "placeholder": "Provide details about the content and features...",
            "validation": {{ "required": true }}
          }}
        ]
      }}
    ]
  }}
}}

Output only JSON following the questionnaire_form format."""

    response = await llm_client.complete(
        prompt=prompt,
        system_message="You are a technical requirements analyst. Generate detailed follow-up questions based on initial requirements.",
        temperature=0.3
    )

    # Same response parsing as before
    return parse_questionnaire_response(response)

@agent_action(
    agent_config=code_agent_v1_app,
    action_type=ActionType.QUESTION,
    name="Collect Requirements",
    description="Generates a requirements questionnaire form based on user input",
    schema_definitions={
        "CollectRequirementsInput": CollectRequirementsInput,
        "CollectRequirementsOutput": CollectRequirementsOutput
    }
)
async def collect_requirements(input_data: CollectRequirementsInput) -> CollectRequirementsOutput:
    """Generate a structured requirements form based on the user's project description."""
    try:
        if not input_data.history:
            # questionnaire_form = await _generate_requirements_form(input_data.message)
            questionnaire_form = {
                "steps": [
                    {
                        "title": "Code Specifications",
                        "fields": [
                            {
                                "type": "select",
                                "name": "framework",
                                "label": "Primary Framework",
                                "validation": {"required": True},
                                "options": [
                                    {"label": "React", "value": "react"},
                                    {"label": "Vue.js", "value": "vue"},
                                    {"label": "Angular", "value": "angular"},
                                    {"label": "Svelte", "value": "svelte"}
                                ]
                            },
                            {
                                "type": "textarea",
                                "name": "architecture_requirements",
                                "label": "Architecture Requirements",
                                "placeholder": "Describe your architectural needs (e.g., single-page application, server-side rendering, static site generation)",
                                "validation": {"required": True}
                            },
                            {
                                "type": "checkbox",
                                "name": "key_functionalities",
                                "label": "Key Functionalities Needed",
                                "options": [
                                    {"label": "User Authentication", "value": "auth"},
                                    {"label": "Prompt Sharing", "value": "prompt_sharing"},
                                    {"label": "Prompt Rating System", "value": "rating"},
                                    {"label": "Search and Filter Prompts", "value": "search_filter"},
                                    {"label": "User Profiles", "value": "profiles"}
                                ]
                            }
                        ]
                    },
                    {
                        "title": "Technical Requirements",
                        "fields": [
                            {
                                "type": "number",
                                "name": "response_time",
                                "label": "Maximum Response Time (ms)",
                                "placeholder": "e.g., 200",
                                "validation": {"required": True}
                            },
                            {
                                "type": "checkbox",
                                "name": "security_needs",
                                "label": "Security Requirements",
                                "options": [
                                    {"label": "HTTPS Enforcement", "value": "https"},
                                    {"label": "Content Security Policy (CSP)", "value": "csp"},
                                    {"label": "Cross-Origin Resource Sharing (CORS)", "value": "cors"},
                                    {"label": "Data Encryption at Rest", "value": "encryption"}
                                ]
                            },
                            {
                                "type": "textarea",
                                "name": "integration_points",
                                "label": "Integration Points",
                                "placeholder": "Describe any third-party integrations (e.g., OpenAI API, payment gateways, analytics)",
                                "validation": {"required": False}
                            }
                        ]
                    },
                    {
                        "title": "Development Preferences",
                        "fields": [
                            {
                                "type": "select",
                                "name": "code_style",
                                "label": "Code Style Preferences",
                                "options": [
                                    {"label": "Prettier", "value": "prettier"},
                                    {"label": "ESLint", "value": "eslint"},
                                    {"label": "StandardJS", "value": "standardjs"}
                                ]
                            },
                            {
                                "type": "radio",
                                "name": "documentation_level",
                                "label": "Documentation Level",
                                "options": [
                                    {"label": "Minimal", "value": "minimal"},
                                    {"label": "Moderate", "value": "moderate"},
                                    {"label": "Comprehensive", "value": "comprehensive"}
                                ]
                            },
                            {
                                "type": "checkbox",
                                "name": "testing_requirements",
                                "label": "Testing Requirements",
                                "options": [
                                    {"label": "Unit Testing", "value": "unit"},
                                    {"label": "Integration Testing", "value": "integration"},
                                    {"label": "End-to-End Testing", "value": "e2e"}
                                ]
                            }
                        ]
                    },
                    {
                        "title": "Implementation Details",
                        "fields": [
                            {
                                "type": "textarea",
                                "name": "specific_features",
                                "label": "Specific Features",
                                "placeholder": "Describe any specific features (e.g., real-time updates, dark mode, offline support)",
                                "validation": {"required": True}
                            },
                            {
                                "type": "textarea",
                                "name": "data_structures",
                                "label": "Data Structures",
                                "placeholder": "Describe the data structures needed (e.g., user schema, prompt schema, rating schema)",
                                "validation": {"required": True}
                            },
                            {
                                "type": "textarea",
                                "name": "api_endpoints",
                                "label": "API Endpoints",
                                "placeholder": "List any required API endpoints (e.g., GET /prompts, POST /prompts, PUT /prompts/{id})",
                                "validation": {"required": False}
                            }
                        ]
                    }
                ]
            }
            return CollectRequirementsOutput(questionnaire_form=questionnaire_form)
        last_phase = input_data.history[-1]
        questionnaire_form = await _generate_phase2_form(input_data.message, last_phase.answers)
        return CollectRequirementsOutput(questionnaire_form=questionnaire_form)
    except Exception as e:
        logger.error(f"Error in collect_requirements: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@agent_action(
    agent_config=code_agent_v1_app,
    action_type=ActionType.CUSTOM_UI,
    name="Interactive Code Review",
    description="Interactive interface for code review and analysis",
    ui_components=[
        main_editor,
        analysis_output
    ]
)
async def code_review_interface(input_data: CodeReviewInput) -> CodeReviewOutput:
    """Handle interactive code review interface."""
    return CodeReviewOutput(
        data={
            "initialized": True,
            "timestamp": datetime.now().isoformat()
        },
        ui_updates=[]
    )
