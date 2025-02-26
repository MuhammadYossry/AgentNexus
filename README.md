# AgentHub: Intelligent Agent Framework with Automatic API Generation

## 🚀 Core Purpose

AgentHub is a revolutionary framework designed to simplify the creation, discovery, and interaction with intelligent agents through automatic API and agents manifest files generation.

## 🌟 Key Features

### 🏗️ Flexible Agent Architecture
- **Declarative Agent Definition**: Create agents with pythonic decorators
- **Multi-Action Support**: Define complex agents with multiple capabilities
- **Workflow-Driven Interactions**: Design sophisticated multi-step processes

### 🖥️ Dynamic UI Components
- **Interactive Workflows**: Build agents with rich, responsive interfaces
- **Customizable UI Elements**: Support for code editors, forms, tables, and more
- **Context-Aware Interactions**: Maintain state across workflow steps

### 🔍 Automatic Manifest Generation
- **Comprehensive Agent Discovery**: Automatically generate machine-readable manifests for each agent
- **OpenAPI Specification**: Instant, standards-compliant API documentation
- **Introspection Support**: Detailed metadata about agent capabilities, actions, and workflows
- **Seamless API Endpoint Creation**: Automatic route generation using FastAPI

## 📦 Manifest Generation in Action

```python
# Automatic manifest generation for your agent
flight_agent_app = AgentConfig(
    name="Flight Assistant",
    version="1.0.0",
    description="Advanced flight search and booking agent",
    capabilities=[
        Capability(
            skill_path=["Travel", "Flight", "Search"],
            metadata={
                "expertise": "advanced",
                "features": ["Real-time Flight Search", "Price Comparison"]
            }
        )
    ]
)

# Define actions
@agent_action(agent_config=flight_agent_app)
async def search_flights(input_data: FlightSearchInput) -> FlightSearchOutput:
    # Implementation
    ...

# Automatically generates:
# - /agents/flight-assistant.json
# - OpenAPI documentation
# - Discoverable API endpoints
```

### 🔬 Manifest Structure
When you create an agent, AgentHub automatically generates a comprehensive manifest:
- **Agent Metadata**: Name, version, description
- **Capabilities**: Skill paths and detailed metadata
- **Actions**: 
  - Input and output schemas
  - Endpoint paths
  - Example requests
- **Workflows**: Step definitions and UI components
- **API Specifications**: OpenAPI/Swagger documentation

## 🚀 Instant API Creation

```python
# Create a fully functional API with minimal code
app = FastAPI()
agent_manager = AgentManager(base_url="http://localhost:9200")
agent_manager.add_agent(flight_agent_app)
agent_manager.setup_agents(app)

# Instantly get:
# - /agents.json (list of all agents)
# - /agents/{agent_slug}.json (agent-specific manifest)
# - Fully documented API endpoints
```

## 🛠️ Installation

```bash
# Using Poetry (recommended)
poetry add agenhub

# Using pip
pip install agenhub
```

## 🌐 Key Endpoints

- `GET /agents.json`: List all available agents
- `GET /agents/{agent_slug}.json`: Get detailed manifest for a specific agent
- `GET /docs`: Interactive API documentation

## 📚 Documentation

🔗 **Full Documentation**: [https://agenhub.ai/docs](https://agenhub.ai/docs)

## 🤝 Contributing

We welcome contributions! Help us make agent discovery and interaction seamless.

## 🌟 Star Us

If you find AgentHub useful, please give us a star on [GitHub](https://github.com/Relax-N-Tax/AgentHub)!