from typing import Any, Dict, Optional
import random
import datetime
from loguru import logger
from agentnexus.base_types import UIResponse, UIComponentUpdate

async def handle_form_submit(
    action: str,  # Will receive 'search_seats'
    flight_number: str,
    selected_class: Optional[str] = None,
    **kwargs
) -> UIResponse:
    """Handle form submission event from the flight info form."""
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
                ),
                UIComponentUpdate(
                    key="status_display",
                    state={"content": f"## Flight {flight_number}\n\nShowing available seats for {seat_class} class. Click on a seat to select it."}
                )
            ]
        )
    except Exception as e:
        logger.error(f"Error in form submit handler: {str(e)}", exc_info=True)
        return UIResponse(
            data={"error": str(e)},
            ui_updates=[
                UIComponentUpdate(
                    key="status_display",
                    state={"content": f"## Error\n\nAn error occurred: {str(e)}"}
                )
            ]
        )


async def handle_seat_selection(
    action: str,
    data: Dict[str, Any],
    flight_number: str = "",
    **kwargs
) -> UIResponse:
    """Handle seat selection event from the table."""
    try:
       # Handle both direct data and nested data cases
        row_data = data.get('data', data) if isinstance(data, dict) else data
        seat_number = row_data.get("seat_number", "")
        seat_class = row_data.get("class", "")
        seat_price = row_data.get("price", 0.0)
        print(f"row_data: {row_data}")
        # Only allow selection if seat is available
        if not row_data.get("available", True):
            return UIResponse(
                data={"error": "Seat not available"},
                ui_updates=[
                    UIComponentUpdate(
                        key="status_display",
                        state={
                            "content": f"""## Seat Not Available
⚠️ Seat **{seat_number}** is not available for selection.
Please choose another seat from the available options in the table.
*Available seats are marked as 'true' in the table.*"""
                        }
                    )
                ]
            )

        confirmation_code = f"SEAT{random.randint(10000, 99999)}"
        return UIResponse(
            data={
                "seat_selected": seat_number,
                "seat_class": seat_class,
                "seat_price": seat_price,
                "flight_number": flight_number,
                "selection_time": datetime.datetime.now().isoformat(),
                "confirmation_code": confirmation_code
            },
            ui_updates=[
                UIComponentUpdate(
                    key="status_display",
                    state={
                        "content": f"""## Seat Selection Confirmed ✅

**Flight Details:**
- Flight Number: `{flight_number}`
- Seat: **{seat_number}**
- Class: {seat_class}
- Price: ${seat_price:.2f}

**Confirmation Code:** `{confirmation_code}`

### Next Steps
1. Your seat has been temporarily reserved
2. Please proceed to checkout within 10 minutes
3. Complete payment to finalize your booking

*Note: Seat reservations expire after 10 minutes if not completed*"""
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
        logger.error(f"Error in seat selection handler: {str(e)}", exc_info=True)
        return UIResponse(
            data={"error": str(e)},
            ui_updates=[
                UIComponentUpdate(
                    key="status_display",
                    state={
                        "content": f"""## Error Occurred ❌

An error occurred while processing your seat selection:

{str(e)}"""
                    }
                )
            ]
        )
