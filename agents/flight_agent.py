from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
import datetime
import random
import json
import logging
from enum import Enum

from agents_manifest.base_types import ActionType, Capability, AgentConfig, UIResponse, UIComponentUpdate
from agents_manifest.agent_action_integration import enhanced_agent_action
from agents_manifest.ui_components import (
    ActionHandlerRegistry, FormComponent, FormField, TableComponent, TableColumn, MarkdownComponent
)
from agents_manifest.component_decorator import component_action_handler
from agents.llm_client import create_llm_client

logger = logging.getLogger(__name__)

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
    passenger_count: Optional[int] = Field(default=1, ge=1, le=9)
    action: Optional[str] = None
    component_key: Optional[str] = None
    seat_number: Optional[str] = None
    selected_class: Optional[str] = None

class SeatSelectionOutput(UIResponse):
    """Output for seat selection interface with UI updates."""
    data: Dict[str, Any]
    ui_updates: List[UIComponentUpdate]


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

@enhanced_agent_action(
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
  
@enhanced_agent_action(
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

@enhanced_agent_action(
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

        # For testing purposes return sample data instead of parsing LLM response
        sample_data = {
            "itinerary": [
                {
                    "date": request.start_date,
                    "activities": ["Airport arrival", "Hotel check-in", "Local neighborhood exploration"],
                    "accommodation": "Sample Hotel",
                    "meals": ["Welcome dinner at hotel restaurant"],
                    "transportation": "Airport shuttle",
                    "estimated_costs": {"accommodation": 150.0, "meals": 80.0, "activities": 20.0, "transportation": 30.0}
                },
                {
                    "date": request.start_date + datetime.timedelta(days=1),
                    "activities": ["City tour", "Museum visit", "Shopping district"],
                    "accommodation": "Sample Hotel",
                    "meals": ["Breakfast at hotel", "Lunch at local cafe", "Dinner at traditional restaurant"],
                    "transportation": "Public transit",
                    "estimated_costs": {"accommodation": 150.0, "meals": 100.0, "activities": 50.0, "transportation": 15.0}
                }
            ],
            "total_cost": flight_search.flights[0].price * request.travelers + 595.0,
            "recommendations": ["Visit during weekdays to avoid crowds", "Book museum tickets in advance"],
            "weather_notes": "Expect mild temperatures with occasional rain",
            "local_tips": ["Tipping is not customary", "Most places accept credit cards"],
            "emergency_contacts": {"police": "911", "hospital": "+1-555-123-4567", "embassy": "+1-555-987-6543"}
        }

        # Create response with sample data
        travel_plan = TravelPlanResponse(
            itinerary=sample_data["itinerary"],
            total_cost=sample_data["total_cost"],
            flight_details=flight_search.flights[0],
            recommendations=sample_data["recommendations"],
            weather_notes=sample_data["weather_notes"],
            local_tips=sample_data["local_tips"],
            emergency_contacts=sample_data["emergency_contacts"]
        )

        # Add background task for confirmation email
        background_tasks.add_task(
            lambda: print(f"Sending travel plan confirmation for {request.destination}")
        )

        return travel_plan

    except Exception as e:
        logger.error(f"Error in plan_travel: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@component_action_handler(action_name="search_seats", component_key="flight_info")
async def handle_search_seats(
    flight_number: str,
    selected_class: Optional[str] = None,
    **kwargs
) -> UIResponse:
    """Handle seat search action from the form."""
    try:
        # Generate sample seat data
        seat_class = selected_class if selected_class else "economy"
        
        if seat_class == "economy":
            rows = range(10, 30)
            price_base = 150.00
        elif seat_class == "business":
            rows = range(4, 10)
            price_base = 450.00
        else:  # First class
            rows = range(1, 4)
            price_base = 950.00
        
        sample_seats = [
            {
                "seat_number": f"{row}{letter}",
                "class": seat_class.capitalize(),
                "price": price_base + random.randint(-20, 50),
                "available": random.random() > 0.3
            }
            for row in rows
            for letter in ['A', 'B', 'C', 'D', 'E', 'F']
        ]

        return UIResponse(
            data={
                "flight_number": flight_number,
                "class": seat_class,
                "total_seats": len(sample_seats),
                "available_seats": len([s for s in sample_seats if s["available"]])
            },
            ui_updates=[
                UIComponentUpdate(
                    key="seats_table",
                    state={"data": sample_seats}
                )
            ]
        )
    except Exception as e:
        logger.error(f"Error in search seats handler: {str(e)}", exc_info=True)
        return UIResponse(
            data={"error": str(e)},
            ui_updates=[
                UIComponentUpdate(
                    key="status_display",
                    state={"content": f"## Error\n\nAn error occurred: {str(e)}"}
                )
            ]
        )

@component_action_handler(action_name="select_seat", component_key="seats_table")
async def handle_select_seat(
    seat_number: str,
    flight_number: str = "",
    **kwargs
) -> UIResponse:
    """Handle seat selection action from the table."""
    try:
        confirmation_code = f"SEAT{random.randint(10000, 99999)}"
        return UIResponse(
            data={
                "seat_selected": seat_number,
                "flight_number": flight_number,
                "selection_time": datetime.datetime.now().isoformat(),
                "confirmation_code": confirmation_code
            },
            ui_updates=[
                UIComponentUpdate(
                    key="status_display",
                    state={
                        "content": f"## Seat Selected\n\nYou have selected seat {seat_number} on flight {flight_number}.\n\nConfirmation code: {confirmation_code}"
                    }
                ),
                UIComponentUpdate(
                    key="seats_table",
                    state={
                        "data_updates": [
                            {"row_match": {"seat_number": seat_number}, "field": "available", "value": False}
                        ]
                    }
                )
            ]
        )
    except Exception as e:
        logger.error(f"Error in select seat handler: {str(e)}", exc_info=True)
        return UIResponse(
            data={"error": str(e)},
            ui_updates=[
                UIComponentUpdate(
                    key="status_display",
                    state={"content": f"## Error\n\nAn error occurred: {str(e)}"}
                )
            ]
        )


# Create the components directly using the component factories for cleaner code
flight_info_form = FormComponent(
    component_key="flight_info",
    component_type="form",
    title="Flight Information",
    form_fields=[
        FormField(
            field_name="flight_number",
            label_text="Flight Number",
            field_type="text",
            is_required=True
        ),
        FormField(
            field_name="selected_class",
            label_text="Class",
            field_type="select",
            field_options=[
                {"value": "economy", "label": "Economy"},
                {"value": "business", "label": "Business"},
                {"value": "first", "label": "First Class"}
            ]
        )
    ],
    available_actions=["search_seats"],
    submit_action_name="search_seats"
)

seats_table = TableComponent(
    component_key="seats_table",
    component_type="table",
    title="Available Seats",
    columns=[
        TableColumn(field_name="seat_number", header_text="Seat"),
        TableColumn(field_name="class", header_text="Class"),
        TableColumn(field_name="price", header_text="Price"),
        TableColumn(field_name="available", header_text="Available")
    ],
    table_data=[],  # Will be populated by the action handler
    available_actions=["select_seat"]
)

status_display = MarkdownComponent(
    component_key="status_display",
    component_type="markdown",
    title="Reservation Status",
    markdown_content="Select a seat to complete your reservation.",
    content_style={"padding": "1rem", "backgroundColor": "#f5f5f5"}
)

@enhanced_agent_action(
    agent_config=flight_agent_app,
    action_type=ActionType.CUSTOM_UI,
    name="Interactive Seat Selection",
    description="Interactive interface for selecting seats on a flight",
    ui_components=[
        flight_info_form,
        seats_table,
        status_display
    ]
)
async def seat_selection_interface(input_data: SeatSelectionInput) -> SeatSelectionOutput:
    """
    Handle interactive seat selection interface.
    
    Args:
        input_data: The input data from the client
        
    Returns:
        SeatSelectionOutput with the initial state or response
    """
    try:
        # Initial state setup
        sample_seats = [
            {"seat_number": f"{row}{letter}",
             "class": "Economy" if row > 3 else "Business",
             "price": 150.00 if row > 3 else 450.00,
             "available": True}
            for row in range(1, 5)  # Just show a few rows initially
            for letter in ['A', 'B', 'C', 'D', 'E', 'F']
        ]

        return SeatSelectionOutput(
            data={
                "flight_number": getattr(input_data, 'flight_number', ''),
                "passenger_count": getattr(input_data, 'passenger_count', 1),
                "total_seats": len(sample_seats),
                "available_seats": len([s for s in sample_seats if s["available"]])
            },
            ui_updates=[
                UIComponentUpdate(
                    key="seats_table",
                    state={"data": sample_seats}
                )
            ]
        )
    except Exception as e:
        logger.error(f"Error in seat selection interface: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))