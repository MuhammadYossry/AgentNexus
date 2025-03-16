from typing import Any, Dict, List, Literal, Optional
from enum import Enum
import datetime
from pydantic import BaseModel, Field
from fast_agents.base_types import UIResponse, UIComponentUpdate

class SeatClassChoices(str, Enum):
    """Available seat classes."""
    ECONOMY = "economy"
    BUSINESS = "business"
    FIRST = "first"

# Create a wrapper class that extends BaseModel
class SeatClass(BaseModel):
    """Pydantic model wrapper for SeatClass enum."""
    value: SeatClassChoices

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
    seat_class: SeatClass = Field(default=SeatClassChoices.ECONOMY)

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