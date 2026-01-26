"""
Statistics calculation service.
Calculates various statistics from pilot and ATC data."""

from typing import List, Set, Tuple, Iterable
from collections import defaultdict
from datetime import datetime
from ..models import Pilot, ATC, Snapshot, Statistics
from .flight_classifier import FlightClassifier

class StatisticsService:
    """Service for calculating network statistics."""
    
    def __init__(self):
        """Initialize statistics service."""
        self.classifier = FlightClassifier()
    
    def calculate_unique_flights(self, pilots: List[Pilot]) -> dict:
        """Calculate unique flights and categorize them."""
        unique_flights = set()
        domestic = 0
        intl_departures = 0
        intl_arrivals = 0
        unique_pilot_ids = set()
        
        for pilot in pilots:
            # Create unique flight identifier
            vid = str(pilot.user_id or pilot.callsign).upper()
            if not vid:
                continue
            
            dep = pilot.flight_plan.departure_id
            arr = pilot.flight_plan.arrival_id
            route = pilot.flight_plan.route
            
            flight_id = (vid, dep, arr, route)
            
            if flight_id not in unique_flights:
                unique_flights.add(flight_id)
                unique_pilot_ids.add(vid)
                
                # Categorize flight
                if self.classifier.is_domestic(pilot):
                    domestic += 1
                elif self.classifier.is_international_departure(pilot):
                    intl_departures += 1
                elif self.classifier.is_international_arrival(pilot):
                    intl_arrivals += 1
        
        return {
            "total_flights": len(unique_flights),
            "domestic": domestic,
            "intl_departures": intl_departures,
            "intl_arrivals": intl_arrivals,
            "unique_pilots": len(unique_pilot_ids)
        }
    
    def calculate_realtime_stats(
        self,
        history_iterator: Iterable[Snapshot],
        current_snapshot: Snapshot,
        current_pilots: List[Pilot],
        current_atcs: List[ATC]
    ) -> Statistics:
        """Calculate realtime statistics from recent snapshots."""
        # Calculate unique flights from current pilots
        flight_stats = self.calculate_unique_flights(current_pilots)
        
        # Calculate total people on board
        total_pob = sum(p.flight_plan.people_on_board for p in current_pilots)
        
        # Build active flights list (callsign, dep, arr, route, pob, aircraft)
        active_flights = []
        seen_flights = set()
        
        for pilot in current_pilots:
            callsign = pilot.callsign
            dep = pilot.flight_plan.departure_id
            arr = pilot.flight_plan.arrival_id
            route = pilot.flight_plan.route
            pob = pilot.flight_plan.people_on_board
            aircraft = pilot.flight_plan.aircraft_icao
            
            flight_key = (callsign, dep, arr, route, pob, aircraft)
            if flight_key not in seen_flights and self.classifier.involves_country(pilot):
                seen_flights.add(flight_key)
                active_flights.append(flight_key)
        
        # Calculate time statistics from streamed history
        pilot_minutes = defaultdict(set)
        atc_minutes = defaultdict(set)
        


        # Stream history
        for snapshot in history_iterator:
            # Check for timestamp presence and format
            if not snapshot.timestamp:
                continue
                
            try:
                minute_key = snapshot.timestamp.strftime("%Y-%m-%d %H:%M")
            except Exception:
                continue
            
            # Check if this is the 00:00 snapshot
            is_midnight = snapshot.timestamp.hour == 0 and snapshot.timestamp.minute == 0

            for pilot in snapshot.pilots:
                # Skip 00:00 snapshot for pilots so count starts at 00:01
                if is_midnight:
                    continue
                    
                uid = str(pilot.user_id or pilot.callsign).upper()
                if uid:
                    pilot_minutes[uid].add(minute_key)
            
            for atc in snapshot.atcs:
                uid = str(atc.user_id or atc.callsign).upper()
                if uid:
                    atc_minutes[uid].add(minute_key)
        
        flight_time_total = sum(len(minutes) for minutes in pilot_minutes.values())
        atc_time_total = sum(len(minutes) for minutes in atc_minutes.values())
        
        return Statistics(
            total_flights=flight_stats["total_flights"],
            domestic_flights=flight_stats["domestic"],
            intl_departures=flight_stats["intl_departures"],
            intl_arrivals=flight_stats["intl_arrivals"],
            unique_pilots=flight_stats["unique_pilots"],
            people_on_board_total=total_pob,
            flight_time_total_min=flight_time_total,
            atc_time_total_min=atc_time_total,
            atc_count=len(current_atcs),
            active_flights=active_flights,
            active_atcs=current_atcs
        )

    def compose_realtime_stats(
        self,
        db_stats: dict,
        current_pilots: List[Pilot],
        current_atcs: List[ATC]
    ) -> Statistics:
        """
        Compose statistics from DB aggregated data and current snapshot.
        Eliminates the need for history iteration in Python.
        """
        # Calculate active flights from current pilots (for Embed details)
        active_flights = []
        seen_flights = set()
        total_pob = 0
        
        domestic = 0
        intl_departures = 0
        intl_arrivals = 0

        for pilot in current_pilots:
            callsign = pilot.callsign
            dep = pilot.flight_plan.departure_id
            arr = pilot.flight_plan.arrival_id
            route = pilot.flight_plan.route
            pob = pilot.flight_plan.people_on_board
            aircraft = pilot.flight_plan.aircraft_icao
            
            total_pob += pob
            
            flight_key = (callsign, dep, arr, route, pob, aircraft)
            if flight_key not in seen_flights and self.classifier.involves_country(pilot):
                seen_flights.add(flight_key)
                active_flights.append(flight_key)

                # Categorize flight
                if self.classifier.is_domestic(pilot):
                    domestic += 1
                elif self.classifier.is_international_departure(pilot):
                    intl_departures += 1
                elif self.classifier.is_international_arrival(pilot):
                    intl_arrivals += 1
        
        return Statistics(
            total_flights=len(seen_flights), # Use current total flights
            domestic_flights=domestic,       # Use current domestic
            intl_departures=intl_departures, # Use current intl dep
            intl_arrivals=intl_arrivals,     # Use current intl arr
            unique_pilots=len(seen_flights), # Use current unique pilots count (Online)
            people_on_board_total=total_pob, # Use current POB total or max? Usually current online POB is displayed.
            flight_time_total_min=db_stats.get("flight_time_total_min", 0),
            atc_time_total_min=db_stats.get("atc_time_total_min", 0),
            atc_count=len(current_atcs), # Current active ATCs
            active_flights=active_flights,
            active_atcs=current_atcs
        )
    
    def calculate_historical_stats(self, snapshots: Iterable[Snapshot]) -> Statistics:
        """Calculate historical statistics from all snapshots."""
        pilot_minutes = defaultdict(set)
        atc_minutes = defaultdict(set)
        unique_flights = set()
        total_pob = 0
        domestic = 0
        intl_departures = 0
        intl_arrivals = 0
        
        for snapshot in snapshots:
            minute_key = snapshot.timestamp.strftime("%Y-%m-%d %H:%M")
            
            # Process pilots
            for pilot in snapshot.pilots:
                vid = str(pilot.user_id or pilot.callsign).upper()
                if not vid:
                    continue
                
                pilot_minutes[vid].add(minute_key)
                
                # Track unique flights
                dep = pilot.flight_plan.departure_id
                arr = pilot.flight_plan.arrival_id
                route = pilot.flight_plan.route
                pob = pilot.flight_plan.people_on_board
                
                flight_key = (vid, dep, arr, route)
                
                if flight_key not in unique_flights and self.classifier.involves_country(pilot):
                    unique_flights.add(flight_key)
                    total_pob += pob
                    
                    if self.classifier.is_domestic(pilot):
                        domestic += 1
                    elif self.classifier.is_international_departure(pilot):
                        intl_departures += 1
                    elif self.classifier.is_international_arrival(pilot):
                        intl_arrivals += 1
            
            # Process ATCs
            for atc in snapshot.atcs:
                vid = str(atc.user_id or atc.callsign).upper()
                if vid:
                    atc_minutes[vid].add(minute_key)
        
        flight_time_total = sum(len(minutes) for minutes in pilot_minutes.values())
        atc_time_total = sum(len(minutes) for minutes in atc_minutes.values())
        
        return Statistics(
            total_flights=len(unique_flights),
            domestic_flights=domestic,
            intl_departures=intl_departures,
            intl_arrivals=intl_arrivals,
            unique_pilots=len(pilot_minutes),
            people_on_board_total=total_pob,
            flight_time_total_min=flight_time_total,
            atc_time_total_min=atc_time_total,
            atc_count=len(atc_minutes)
        )
