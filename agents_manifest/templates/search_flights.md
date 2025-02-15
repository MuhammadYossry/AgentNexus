# ✈️ Flight Search Results

Here are the flights we found based on your search criteria:

---

## 🔍 Search Filters
| Filter        | Value          |
|---------------|----------------|
| **Origin**     | {{ filters_applied.origin }} |
| **Destination**| {{ filters_applied.destination }} |
| **Date**       | {{ filters_applied.date }} |
| **Passengers** | {{ filters_applied.passengers }} |
| **Seat Class** | {{ filters_applied.seat_class }} |

---

## 🛫 Available Flights
{% if flights %}
{% for flight in flights %}
### 🛩️ Flight {{ flight.flight_number }}
- **Price**: ${{ flight.price | round(2) }}
- **Origin**: {{ flight.origin }}
- **Destination**: {{ flight.destination }}
- **Date**: {{ flight.flight_date }}

{% endfor %}
{% else %}
No flights found matching your criteria. 😢
{% endif %}

---

## 📊 Search Metrics
- **Search Time**: {{ search_time | round(6) }} seconds
- **Total Flights Found**: {{ flights | length }}

---

*🔍 Search performed at {{ now | default("current time") }}*