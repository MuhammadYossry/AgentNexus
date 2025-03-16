from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fast_agents.manifest_generator import AgentManager, configure_agent

# Import agent functions first to ensure decorators run
from agents.flight_agent import flight_agent_app
from agents.code_agent_v1 import code_agent_v1_app
from agents.code_agent_v2 import code_agent_v2_app

def add_cors_middleware(app: FastAPI):
    app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def create_app():
    app = FastAPI()
    add_cors_middleware(app)
    agent_manager = AgentManager(base_url="http://localhost:9200")
    agent_manager.add_agent(flight_agent_app)
    agent_manager.add_agent(code_agent_v1_app)
    agent_manager.add_agent(code_agent_v2_app)
    agent_manager.setup_agents(app)
    return app

app = create_app()

@app.get("/debug/routes", include_in_schema=False)
async def list_routes():
    routes = []
    for route in app.routes:
        route_info = {
            "path": route.path,
            "name": route.name,
            "methods": list(route.methods) if hasattr(route, "methods") else None,
        }
        routes.append(route_info)
    return {"routes": routes}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9200)