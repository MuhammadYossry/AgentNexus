from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
import datetime
from enum import Enum

from agents_manifest.base_types import ActionType, Capability, AgentConfig, UIResponse, UIComponentUpdate
from agents_manifest.action_manager import agent_action
from agents_manifest.manifest_generator import configure_agent
from agents_manifest.ui_components import FormComponent, FormField, TableComponent, TableColumn
from agents.llm_client import create_llm_client

class SeatClass(str, Enum):
    """Available seat classes."""
    ECONOMY = "economy"
    BUSINESS = "business"
    FIRST = "first"

# Models
class FlightDetails(BaseModel):
    """Details of a flight."""
    flight_number: str = Field(..., description="Unique flight identifier")
    price: float = Field(..., description="Flight price in USD")
    origin: str = Field(..., description="Three-letter airport code for origin")
    destination: str = Field(..., description="Three-letter airport code for destination")
    flight_date: datetime.date = Field(..., description="Flight date")

class NoFlightFound(BaseModel):
    """Response when no valid flight is found."""
    reason: str = Field(..., description="Reason why no flight was found")

class SeatPreference(BaseModel):
    """Seat preference details."""
    row: int = Field(..., ge=1, le=30, description="Row number")
    seat: Literal["A", "B", "C", "D", "E", "F"] = Field(..., description="Seat letter")
    seat_class: SeatClass = Field(default=SeatClass.ECONOMY)

class FlightSearchInput(BaseModel):
    """Input for flight search."""
    origin: str = Field(..., description="Three-letter airport code")
    destination: str = Field(..., description="Three-letter airport code")
    departure_date: datetime.date = Field(..., description="Desired flight date")
    passengers: int = Field(default=1, ge=1, le=9, description="Number of passengers")
    seat_class: Optional[SeatClass] = None

class FlightSearchOutput(BaseModel):
    """Output for flight search results."""
    flights: List[FlightDetails]
    search_time: float
    filters_applied: Dict[str, Any]

class BookingInput(BaseModel):
    """Input for flight booking."""
    flight_number: str
    passengers: List[Dict[str, str]]
    seat_preferences: List[SeatPreference]

class BookingOutput(BaseModel):
    """Output for booking confirmation."""
    booking_reference: str
    flight_details: FlightDetails
    seats: List[SeatPreference]
    total_price: float
    booking_time: datetime.datetime

class TravelPreferences(BaseModel):
    """Travel preferences for planning."""
    budget_range: str = Field(..., description="Budget range (e.g., 'economy', 'moderate', 'luxury')")
    interests: List[str] = Field(..., description="List of travel interests")
    accommodation_type: Optional[str] = Field(None, description="Preferred accommodation type")
    transportation_mode: Optional[str] = Field(None, description="Preferred mode of transportation")
    meal_preferences: Optional[str] = Field(None, description="Dietary preferences")

class TravelPlanRequest(BaseModel):
    """Input for travel plan generation."""
    origin: str = Field(..., description="Three-letter airport code for origin")
    destination: str = Field(..., description="Three-letter airport code for destination")
    start_date: datetime.date = Field(..., description="Start date of travel")
    end_date: datetime.date = Field(..., description="End date of travel")
    travelers: int = Field(default=1, ge=1, le=9, description="Number of travelers")
    preferences: TravelPreferences = Field(..., description="Travel preferences")
    max_budget: float = Field(..., description="Maximum budget in USD")

class DailyItinerary(BaseModel):
    """Daily itinerary details."""
    date: datetime.date
    activities: List[str]
    accommodation: str
    meals: List[str]
    transportation: str
    estimated_costs: Dict[str, float]

class TravelPlanResponse(BaseModel):
    """Output for travel plan generation."""
    itinerary: List[DailyItinerary]
    total_cost: float
    flight_details: FlightDetails
    recommendations: List[str]
    weather_notes: Optional[str]
    local_tips: List[str]
    emergency_contacts: Dict[str, str]

class SeatSelectionInput(BaseModel):
    """Input for seat selection interface."""
    flight_number: str
    passenger_count: int = Field(default=1, ge=1, le=9)

class SeatSelectionOutput(UIResponse):
    """Output for seat selection interface with UI updates."""
    pass


# Define rich capabilities for the flight agent
FLIGHT_CAPABILITIES = [
    Capability(
        skill_path=["Travel", "Flight", "Search"],
        metadata={
            "expertise": "advanced",
            "features": ["Real-time Flight Search", "Price Comparison", "Seat Selection", "Multi-city Routing"],
            "supported_classes": ["Economy", "Business", "First"],
            "route_coverage": "Global",
            "booking_features": ["Instant Confirmation", "Seat Selection", "Special Requests"]
        }
    ),
    Capability(
        skill_path=["Travel", "Flight", "Booking"],
        metadata={
            "expertise": "advanced",
            "features": ["Real-time Booking", "Seat Allocation", "Fare Rules", "Cancellation Policies"],
            "payment_methods": ["Credit Card", "Digital Wallet"],
            "booking_window": "1-365 days",
            "passenger_types": ["Adult", "Child", "Infant"]
        }
    )
]

flight_agent_app = AgentConfig(
    name="Flight Assistant",
    version="1.0.0",
    description="Advanced flight search and booking agent",
    base_path="/v1/flight_agent",
    capabilities=FLIGHT_CAPABILITIES
)

@agent_action(
    agent_config=flight_agent_app,
    action_type=ActionType.GENERATE,
    name="Search Flights",
    description="Search for available flights based on criteria",
    response_template_md="search_flights.md",
    schema_definitions={
        "FlightDetails": FlightDetails,
        "SeatClass": SeatClass
    },
    examples={
        "validRequests": [
            {
                "origin": "SFO",
                "destination": "JFK",
                "departure_date": "2025-01-15",
                "passengers": 2,
                "seat_class": "economy"
            }
        ]
    }
)
async def search_flights(input_data: FlightSearchInput) -> FlightSearchOutput:
    """Search for available flights based on search criteria."""
    try:
        # Simulate flight search from a database or external API
        # In a real implementation, this would connect to actual flight data sources
        start_time = datetime.datetime.now()

        # Sample flight data (would come from real data source)
        sample_flights = [
            FlightDetails(
                flight_number=f"{input_data.origin}{input_data.destination}123",
                price=299.99,
                origin=input_data.origin,
                destination=input_data.destination,
                flight_date=input_data.departure_date
            ),
            FlightDetails(
                flight_number=f"{input_data.origin}{input_data.destination}456",
                price=349.99,
                origin=input_data.origin,
                destination=input_data.destination,
                flight_date=input_data.departure_date
            )
        ]

        search_time = (datetime.datetime.now() - start_time).total_seconds()

        return FlightSearchOutput(
            flights=sample_flights,
            search_time=search_time,
            filters_applied={
                "origin": input_data.origin,
                "destination": input_data.destination,
                "date": input_data.departure_date,
                "passengers": input_data.passengers,
                "seat_class": input_data.seat_class
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
  
@agent_action(
    agent_config=flight_agent_app,
    action_type=ActionType.GENERATE,
    name="Book Flight",
    description="Book a flight with specified details and seat preferences",
    schema_definitions={
        "BookingInput": BookingInput,
        "BookingOutput": BookingOutput,
        "SeatPreference": SeatPreference,
        "FlightDetails": FlightDetails
    },
    examples={
        "validRequests": [
            {
                "flight_number": "SFO-JFK123",
                "passengers": [{"first_name": "John", "last_name": "Doe"}],
                "seat_preferences": [{"row": 12, "seat": "A", "seat_class": "economy"}]
            }
        ]
    }
)
async def book_flight(
    input_data: BookingInput,
    background_tasks: BackgroundTasks
) -> BookingOutput:
    """Book a flight with the specified details."""
    try:
        # Simulate flight booking process
        # In real implementation, this would interact with airline booking systems
        booking_reference = f"BK{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Simulate flight details retrieval
        flight_details = FlightDetails(
            flight_number=input_data.flight_number,
            price=299.99,  # Would be actual price from database
            origin="SFO",  # Would be retrieved based on flight number
            destination="JFK",
            flight_date=datetime.date(2025, 1, 15)
        )

        # Calculate total price (would include actual pricing logic)
        total_price = flight_details.price * len(input_data.passengers)

        # Add background task for confirmation email (simulated)
        background_tasks.add_task(
            lambda: print(f"Sending booking confirmation for {booking_reference}")
        )

        return BookingOutput(
            booking_reference=booking_reference,
            flight_details=flight_details,
            seats=input_data.seat_preferences,
            total_price=total_price,
            booking_time=datetime.datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @flight_app.post("/flight_agent/plan_travel", response_model=TravelPlanResponse)
@agent_action(
    agent_config=flight_agent_app,
    action_type=ActionType.GENERATE,
    name="Plan Travel",
    description="Generate a comprehensive travel plan",
    response_template_md="templates/travel_plan.md",
    examples={
        "validRequests": [
            {
                "origin": "SFO",
                "destination": "TYO",
                "start_date": "2024-06-15",
                "end_date": "2024-06-22",
                "travelers": 2,
                "preferences": {
                    "budget_range": "moderate",
                    "interests": ["culture", "food", "history"],
                    "accommodation_type": "hotel",
                    "transportation_mode": "public_transport",
                    "meal_preferences": "local_cuisine"
                },
                "max_budget": 5000.0
            }
        ]
    }
)
async def plan_travel(
    request: TravelPlanRequest,
    background_tasks: BackgroundTasks
) -> TravelPlanResponse:
    """Generate a comprehensive travel plan based on user preferences."""
    try:
        # Initialize LLM client
        llm_client = create_llm_client()

        # Calculate trip duration
        duration = (request.end_date - request.start_date).days

        # First, get flight details using existing functionality
        flight_search = await search_flights(
            FlightSearchInput(
                origin=request.origin,
                destination=request.destination,
                departure_date=request.start_date,
                passengers=request.travelers,
                seat_class=SeatClass.ECONOMY if request.preferences.budget_range == "economy"
                         else SeatClass.BUSINESS if request.preferences.budget_range == "moderate"
                         else SeatClass.FIRST
            )
        )

        # Prepare prompt for LLM to generate detailed itinerary
        prompt = f"""
        Create a detailed {duration}-day travel itinerary for {request.travelers} traveler(s):

        Destination: {request.destination}
        Duration: {duration} days
        Budget Range: {request.preferences.budget_range}
        Total Budget: ${request.max_budget}
        Interests: {', '.join(request.preferences.interests)}
        Accommodation Preference: {request.preferences.accommodation_type}
        Transportation Preference: {request.preferences.transportation_mode}
        Dietary Preferences: {request.preferences.meal_preferences}

        Flight Budget: ${flight_search.flights[0].price if flight_search.flights else 0}

        Please provide:
        1. Daily itinerary with activities
        2. Accommodation recommendations
        3. Local transportation options
        4. Meal recommendations
        5. Estimated costs for each day
        6. Local tips and cultural considerations
        7. Emergency contact information

        Format the response as a structured JSON matching the TravelPlanResponse schema.
        """

        # Get travel plan from LLM
        llm_response = await llm_client.complete(
            prompt=prompt,
            system_message="You are an experienced travel planner with extensive knowledge of global destinations. Provide detailed, practical travel plans within budget constraints.",
            temperature=0.7
        )

        # Parse LLM response into TravelPlanResponse
        try:
            plan_data = json.loads(llm_response.content)

            # Convert dates from strings to date objects
            for day in plan_data["itinerary"]:
                day["date"] = datetime.strptime(day["date"], "%Y-%m-%d").date()

            # Create response
            travel_plan = TravelPlanResponse(
                itinerary=plan_data["itinerary"],
                total_cost=plan_data["total_cost"],
                flight_details=flight_search.flights[0],
                recommendations=plan_data["recommendations"],
                weather_notes=plan_data.get("weather_notes"),
                local_tips=plan_data["local_tips"],
                emergency_contacts=plan_data["emergency_contacts"]
            )

            # Add background task for confirmation email
            background_tasks.add_task(
                lambda: print(f"Sending travel plan confirmation for {request.destination}")
            )

            return travel_plan

        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error parsing LLM response: {str(e)}"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@agent_action(
    agent_config=flight_agent_app,
    action_type=ActionType.CUSTOM_UI,
    name="Interactive Seat Selection",
    description="Interactive interface for selecting seats on a flight",
    ui_components=[
        FormComponent(
            key="flight_info",
            title="Flight Information",
            fields=[
                FormField(
                    name="flight_number",
                    label="Flight Number",
                    type="text",
                    required=True
                ),
                FormField(
                    name="class",
                    label="Class",
                    type="select",
                    options=[
                        {"value": "economy", "label": "Economy"},
                        {"value": "business", "label": "Business"},
                        {"value": "first", "label": "First Class"}
                    ]
                )
            ],
            submit_action="search_seats"
        ),
        TableComponent(
            key="seats_table",
            title="Available Seats",
            columns=[
                TableColumn(field="seat_number", header="Seat"),
                TableColumn(field="class", header="Class"),
                TableColumn(field="price", header="Price"),
                TableColumn(field="available", header="Available")
            ],
            data=[],  # Initially empty
            actions=["select_seat"]
        )
    ]
)
async def seat_selection_interface(input_data: SeatSelectionInput) -> SeatSelectionOutput:
    """Handle the seat selection interface."""
    # Simulate fetching seat data
    sample_seats = [
        {"seat_number": f"{row}{letter}",
         "class": "Economy" if row > 3 else "Business",
         "price": 150.00 if row > 3 else 450.00,
         "available": True}
        for row in range(1, 20)
        for letter in ['A', 'B', 'C', 'D', 'E', 'F']
    ]

    return SeatSelectionOutput(
        data={
            "flight_number": input_data.flight_number,
            "total_seats": len(sample_seats),
            "available_seats": len([s for s in sample_seats if s["available"]])
        },
        ui_updates=[
            UIComponentUpdate(
                key="seats_table",
                state={"data": sample_seats[:input_data.passenger_count * 10]}  # Show limited seats
            ),
            UIComponentUpdate(
                key="flight_info",
                state={
                    "flight_number": input_data.flight_number,
                    "readonly": True
                }
            )
        ]
    )