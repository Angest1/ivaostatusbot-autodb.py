"""
Statistics data model.
Represents calculated statistics from snapshots."""

from dataclasses import dataclass
from typing import List, Optional, Tuple
from .atc import ATC

@dataclass
class Statistics:
    """Network activity statistics."""
    
    # Flight statistics
    total_flights: int
    domestic_flights: int
    intl_departures: int
    intl_arrivals: int
    unique_pilots: int
    people_on_board_total: int
    
    # Time statistics (in minutes)
    flight_time_total_min: float
    atc_time_total_min: float
    
    # ATC statistics
    atc_count: int
    
    # Realtime-only fields
    active_flights: Optional[List[Tuple]] = None  # (callsign, dep, arr, route, pob, aircraft)
    active_atcs: Optional[List[ATC]] = None
    metar: Optional[str] = None
    top_airports: Optional[List[Tuple]] = None  # (airport, dep_count, arr_count)
    top_pilots: Optional[List[Tuple]] = None # (count, user_id, mins)
    top_atcs: Optional[List[Tuple]] = None # (count, user_id, mins)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for compatibility."""
        result = {
            "total_flights": self.total_flights,
            "domestic_flights": self.domestic_flights,
            "intl_departures": self.intl_departures,
            "intl_arrivals": self.intl_arrivals,
            "unique_pilots": self.unique_pilots,
            "people_on_board_total": self.people_on_board_total,
            "flight_time_total_min": self.flight_time_total_min,
            "atc_time_total_min": self.atc_time_total_min,
            "atc_count": self.atc_count,
        }
        
        if self.active_flights is not None:
            result["active_flights"] = self.active_flights
        
        if self.active_atcs is not None:
            result["active_atcs"] = self.active_atcs
        
        if self.metar is not None:
            result["metar"] = self.metar
        
        return result
