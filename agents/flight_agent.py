from fastapi import FastAPI, HTTPException, BackgroundTasks
import datetime
from loguru import logger
from agents_manifest.base_types import ActionType, Capability, AgentConfig, UIComponentUpdate
from agents_manifest.agent_action_integration import enhanced_agent_action

from agents.models.flight_agent import (
    SeatClass, SeatClassChoices, FlightDetails, SeatPreference, FlightSearchInput, FlightSearchOutput,
    BookingInput, BookingOutput, TravelPreferences, TravelPlanRequest, TravelPlanResponse,
    SeatSelectionInput, SeatSelectionOutput
)
from agents.ui_components.flight_agent import flight_info_form, seats_table, status_display
from agents.llm_client import create_llm_client


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
                seat_class=SeatClassChoices.ECONOMY if request.preferences.budget_range == "economy"
                         else SeatClassChoices.BUSINESS if request.preferences.budget_range == "moderate"
                         else SeatClassChoices.FIRST
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
    This function handles the initial state setup. Events like 'select_seat'
    and 'submit' are handled by the component-specific event handlers.

    Args:
        input_data: The input data from the client

    Returns:
        SeatSelectionOutput with the initial state or response
    """
    try:
        # Initial state setup
        flight_number = getattr(input_data, 'flight_number', '')
        passenger_count = getattr(input_data, 'passenger_count', 1)
        # Initial sample seats (just a few to start)
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
                "flight_number": flight_number,
                "passenger_count": passenger_count,
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