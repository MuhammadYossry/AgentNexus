from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agents_manifest.manifest_generator import setup_agent_routes

# Import agent functions first to ensure decorators run
from agents.flight_agent import search_flights, book_flight, plan_travel
# Then import the configured apps
from agents.code_agent_v2 import v2_app as code_agent_v2_app
from agents.flight_agent import flight_app

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount agent apps
app.mount("/v1/flight_agent", flight_app, name="flight_agent")
app.mount("/v2/code_agent", code_agent_v2_app, name="code_agent_v2")

setup_agent_routes(app)

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