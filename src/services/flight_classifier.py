"""
Flight classifier service.
Classifies flights and ATCs by country."""

from ..models import Pilot, ATC
from ..config import Settings

class FlightClassifier:
    """Classifies flights and ATCs based on country prefix."""
    
    def __init__(self):
        """Initialize classifier."""
        self.settings = Settings()
    
    @property
    def prefixes(self):
        """Get current country prefixes from settings."""
        # Ensure we have a tuple for startswith
        return tuple(self.settings.country_prefixes)
    
    def is_domestic(self, pilot: Pilot) -> bool:
        """Check if flight is domestic (both departure and arrival in country)."""
        dep = pilot.flight_plan.departure_id
        arr = pilot.flight_plan.arrival_id
        return dep.startswith(self.prefixes) and arr.startswith(self.prefixes)
    
    def is_international_departure(self, pilot: Pilot) -> bool:
        """Check if flight is international departure (departs from country)."""
        dep = pilot.flight_plan.departure_id
        arr = pilot.flight_plan.arrival_id
        return dep.startswith(self.prefixes) and not arr.startswith(self.prefixes)
    
    def is_international_arrival(self, pilot: Pilot) -> bool:
        """Check if flight is international arrival (arrives to country)."""
        dep = pilot.flight_plan.departure_id
        arr = pilot.flight_plan.arrival_id
        return not dep.startswith(self.prefixes) and arr.startswith(self.prefixes)
    
    def involves_country(self, pilot: Pilot) -> bool:
        """Check if flight involves the country (departure or arrival)."""
        dep = pilot.flight_plan.departure_id
        arr = pilot.flight_plan.arrival_id
        return dep.startswith(self.prefixes) or arr.startswith(self.prefixes)
    
    def is_country_atc(self, atc: ATC) -> bool:
        """Check if ATC is for the country."""
        return atc.callsign.startswith(self.prefixes)
