---
title: "Project Organization"
description: "Best practices for organizing your AgentNexus projects"
lead: "Learn how to structure your AgentNexus project for maintainability and scalability."
date: 2025-03-25T08:00:00+00:00
lastmod: 2025-03-25T08:00:00+00:00
draft: false
images: []
menu:
  docs:
    parent: "getting-started"
weight: 240
toc: true
---

## Recommended Project Structure

As your AgentNexus projects grow in complexity, a well-organized structure becomes essential. Here's a recommended project structure that follows best practices:

```
my-agent-project/
├── main.py                # Entry point with FastAPI setup
├── config.py              # Configuration settings
├── agents/                # Agent definitions
│   ├── __init__.py
│   ├── travel_agent.py    # Travel agent definition
│   ├── code_agent.py      # Code agent definition
│   └── ...
├── models/                # Data models
│   ├── __init__.py
│   ├── travel_agent.py    # Travel agent models
│   ├── code_agent.py      # Code agent models
│   └── ...
├── ui_components/         # UI component definitions
│   ├── __init__.py
│   ├── travel_agent.py    # Travel agent UI components
│   ├── code_agent.py      # Code agent UI components
│   └── ...
├── ui_handlers/           # UI event handlers
│   ├── __init__.py
│   ├── travel_agent.py    # Travel agent event handlers
│   ├── code_agent.py      # Code agent event handlers
│   └── ...
├── services/              # External service integrations
│   ├── __init__.py
│   ├── llm_client.py      # LLM integration
│   └── ...
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── test_travel_agent.py
│   └── ...
└── requirements.txt       # Dependencies
```

This structure helps maintain separation of concerns and makes your project more maintainable as it grows.

## Main Application File

Your `main.py` file should be focused on application setup and initialization:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agentnexus.manifest_generator import AgentManager

# Import agent definitions
from agents.travel_agent import travel_agent_app
from agents.code_agent import code_agent_app

def create_app():
    """Create and configure the FastAPI application."""
    app = FastAPI(title="My Agent Hub")
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Configure agents
    agent_manager = AgentManager(base_url="http://localhost:8000")
    
    # Add all agents
    agent_manager.add_agent(travel_agent_app)
    agent_manager.add_agent(code_agent_app)
    
    # Set up routes
    agent_manager.setup_agents(app)
    
    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Agent Definition Files

Each agent should be defined in its own file for better organization:

```python
# agents/travel_agent.py
from agentnexus.base_types import AgentConfig, Capability

# Define travel agent
travel_agent_app = AgentConfig(
    name="Travel Assistant",
    version="1.0.0",
    description="Help plan and book travel",
    capabilities=[
        # Agent capabilities
    ]
)

# Import models and UI components
from models.travel_agent import FlightSearchInput, FlightSearchOutput
from ui_components.travel_agent import flight_search_form

# Define agent actions
@agent_action(
    agent_config=travel_agent_app,
    action_type=ActionType.GENERATE,
    name="Search Flights",
    description="Search for available flights"
)
async def search_flights(input_data: FlightSearchInput) -> FlightSearchOutput:
    # Implementation
    pass
```

## Models Directory

Keep your data models separate for better maintenance:

```python
# models/travel_agent.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class FlightDetails(BaseModel):
    """Details of a flight."""
    flight_number: str = Field(..., description="Unique flight identifier")
    price: float = Field(..., description="Flight price in USD")
    origin: str = Field(..., description="Three-letter airport code")
    destination: str = Field(..., description="Three-letter airport code")
    flight_date: date = Field(..., description="Flight date")

class FlightSearchInput(BaseModel):
    """Input for flight search."""
    origin: str = Field(..., description="Origin airport code")
    destination: str = Field(..., description="Destination airport code")
    departure_date: date = Field(..., description="Departure date")
    passengers: int = Field(default=1, ge=1, le=9, description="Number of passengers")

class FlightSearchOutput(BaseModel):
    """Output for flight search results."""
    flights: List[FlightDetails]
    search_time: float
    filters_applied: dict
```

## UI Components Directory

Organize UI components by agent:

```python
# ui_components/travel_agent.py
from agentnexus.ui_components import FormComponent, FormField, TableComponent, TableColumn

# Import handlers
from ui_handlers.travel_agent import handle_form_submit

flight_search_form = FormComponent(
    component_key="flight_search",
    title="Flight Search",
    form_fields=[
        FormField(
            field_name="origin",
            label_text="Origin",
            field_type="text",
            is_required=True
        ),
        FormField(
            field_name="destination",
            label_text="Destination",
            field_type="text",
            is_required=True
        ),
        # Other fields
    ],
    event_handlers={
        "submit": handle_form_submit
    }
)

flight_results_table = TableComponent(
    component_key="flight_results",
    title="Available Flights",
    columns=[
        TableColumn(field_name="flight_number", header_text="Flight"),
        TableColumn(field_name="price", header_text="Price"),
        # Other columns
    ],
    table_data=[]
)
```

## UI Handlers Directory

Separate your event handlers for clarity:

```python
# ui_handlers/travel_agent.py
from typing import Dict, Any
from agentnexus.base_types import UIResponse, UIComponentUpdate

async def handle_form_submit(
    action: str,
    data: Dict[str, Any],
    component_key: str,
    **kwargs
) -> UIResponse:
    """Handle form submission event."""
    # Extract values
    values = data.get("values", {})
    origin = values.get("origin", "")
    destination = values.get("destination", "")
    
    # Process form submission
    # ...
    
    return UIResponse(
        data={"search_complete": True},
        ui_updates=[
            UIComponentUpdate(
                key="flight_results",
                state={"data": flight_data}
            )
        ]
    )
```

## Services Directory

Centralize external service integrations:

```python
# services/llm_client.py
from typing import Optional, Dict, List, Any
import httpx
from pydantic import BaseSettings

class LLMSettings(BaseSettings):
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_API_KEY: str = "your-api-key"
    LLM_MODEL: str = "gpt-4"
    
    class Config:
        env_file = ".env"

class LLMClient:
    # LLM client implementation
    # ...
```

## Configuration Management

Use a dedicated config module:

```python
# config.py
from pydantic import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "My Agent Hub"
    
    # LLM Settings
    LLM_PROVIDER: str = "openai"
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4"
    
    # Redis Settings (for session management)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    SESSION_TTL: int = 3600  # 1 hour
    
    class Config:
        env_file = ".env"

@lru_cache
def get_settings():
    return Settings()
```

## Best Practices

### 1. Separation of Concerns

Keep different aspects of your application separate:
- **Agent definitions**: High-level agent configuration
- **Models**: Data structure definitions
- **UI components**: User interface elements
- **UI handlers**: Event handling logic
- **Services**: External integrations

### 2. Agent-Centric Organization

Organize files around agents rather than technical layers:
- Group all files related to a specific agent
- Makes it easier to understand and modify each agent

### 3. Consistent Naming Conventions

Use clear and consistent naming:
- **Files**: Use snake_case (e.g., `travel_agent.py`)
- **Classes**: Use PascalCase (e.g., `FlightSearchInput`)
- **Functions**: Use snake_case (e.g., `search_flights`)
- **Variables**: Use snake_case (e.g., `flight_data`)

### 4. Environment Configuration

Use environment variables for configuration:
- Create a `.env` file for local development
- Use environment variables in production
- Access through a settings class

### 5. Testing Structure

Organize tests to mirror your application structure:
- Create test files that match application files
- Use fixtures for common test data
- Test both normal and edge cases

## Scaling Up

As your project grows, consider these additional organizational patterns:

### Separating Workflows

For complex agents with multiple workflows:

```
agents/
├── travel_agent/
│   ├── __init__.py
│   ├── agent.py           # Agent definition
│   ├── flights.py         # Flight search workflow
│   ├── hotels.py          # Hotel booking workflow
│   └── itineraries.py     # Itinerary planning workflow
```

### Shared Components

For components used across multiple agents:

```
ui_components/
├── __init__.py
├── common/
│   ├── __init__.py
│   ├── forms.py           # Common form components
│   └── displays.py        # Common display components
├── travel_agent.py
└── code_agent.py
```

### Modular Setup

For very large projects, consider a fully modular approach:

```
my-agent-hub/
├── main.py
├── core/
│   ├── __init__.py
│   ├── config.py
│   └── services/
├── agents/
│   ├── __init__.py
│   ├── travel/
│   └── code/
```

## Deployment Considerations

When preparing for deployment, consider:

1. **Environment separation**: Separate development and production settings
2. **Dockerfile**: Create a containerized version of your application
3. **CI/CD setup**: Automate testing and deployment
4. **Health checks**: Add endpoints for monitoring
5. **Logging**: Configure proper logging for production

## Next Steps

Now that you understand how to organize your AgentNexus project:

- Continue to the [Core Concepts](../../core-concepts/) section
- Explore [UI Components](../../ui-components/) in detail
- Learn about the [Workflow System](../../workflow-system/)
- See real-world [Examples](../../examples/) of agent implementations