"""
Pilot data model.
Represents a pilot with flight plan information."""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from ..utils.text_utils import clean_route

@dataclass(slots=True)
class FlightPlan:
    """Flight plan information."""
    departure_id: str
    arrival_id: str
    people_on_board: int
    route: str
    aircraft_icao: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FlightPlan':
        """Create FlightPlan from dictionary."""
        aircraft = data.get("aircraft") or {}
        return cls(
            departure_id=(data.get("departureId") or "").upper(),
            arrival_id=(data.get("arrivalId") or "").upper(),
            people_on_board=int(data.get("peopleOnBoard") or 0),
            route=clean_route(data.get("route") or "No route"),
            aircraft_icao=(aircraft.get("icaoCode") or "UNKNOWN").upper()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "departureId": self.departure_id,
            "arrivalId": self.arrival_id,
            "peopleOnBoard": self.people_on_board,
            "route": self.route,
            "aircraft": {"icaoCode": self.aircraft_icao}
        }

@dataclass(slots=True)
class Pilot:
    """Pilot information."""
    user_id: Optional[str]
    callsign: str
    flight_plan: FlightPlan
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'Pilot':
        """Create Pilot from API data."""
        if not isinstance(data, dict):
            return cls(
                user_id=None,
                callsign=str(data).upper(),
                flight_plan=FlightPlan("", "", 0, "No route", "UNKNOWN")
            )
        
        user_id = data.get("userId")
        callsign = str(data.get("callsign") or "").upper()
        fp_data = data.get("flightPlan") or {}
        
        return cls(
            user_id=user_id,
            callsign=callsign,
            flight_plan=FlightPlan.from_dict(fp_data)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "userId": self.user_id,
            "callsign": self.callsign,
            "flightPlan": self.flight_plan.to_dict()
        }
