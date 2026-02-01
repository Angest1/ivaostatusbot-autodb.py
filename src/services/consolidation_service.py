"""
Data consolidation service.
Consolidates snapshots into statistics for historical and realtime views."""

import os
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from ..models import Snapshot, Statistics
from .statistics_service import StatisticsService
from .flight_classifier import FlightClassifier

class ConsolidationService:
    """Service for consolidating snapshot data."""
    
    def __init__(self):
        """Initialize consolidation service."""
        from .db_service import DatabaseService
        from ..config import Constants
        
        self.statistics_service = StatisticsService()
        self.classifier = FlightClassifier()
        self.db_service = DatabaseService()
        self.constants = Constants()
    
    def consolidate_historical(self, file_path: str) -> Optional[Statistics]:
        """Consolidate snapshots from database based on file type using optimized DB queries."""
        now = datetime.now(timezone.utc)
        start_time = None
        
        # Determine time range based on file path constant
        if file_path == self.constants.HISTORICAL_DAILY_FILE:
            # Start of today (UTC)
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif file_path == self.constants.HISTORICAL_WEEKLY_FILE:
            # Start of week (Monday)
            start_time = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        elif file_path == self.constants.HISTORICAL_MONTHLY_FILE:
            # Start of month
            start_time = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            return None
            
        # Determine scope based on file type
        scope = 'day'
        if file_path == self.constants.HISTORICAL_WEEKLY_FILE:
            scope = 'week'
        elif file_path == self.constants.HISTORICAL_MONTHLY_FILE:
            scope = 'month'
            
        # Get aggregated stats directly from DB
        prefixes = self.classifier.prefixes
        db_stats = self.db_service.get_statistics_aggregated(start_time, list(prefixes), scope=scope)
        
        if not db_stats:
            return None

        # Fetch top airports
        top_airports = self.db_service.get_top_airports(
            start_time, 
            list(prefixes), 
            scope=scope, 
            limit=3
        )
        
        # Fetch top pilots and ATCs
        top_pilots = self.db_service.get_top_pilots(
            start_time,
            list(prefixes),
            scope=scope,
            limit=3
        )
        
        top_atcs = self.db_service.get_top_atcs(
            start_time,
            list(prefixes),
            scope=scope,
            limit=3
        )

        # Create Statistics object directly from DB result
        # Note: Historical stats don't need active_flights/active_atcs lists usually, 
        # or we could leave them empty/None.
        return Statistics(
            total_flights=db_stats.get("total_flights", 0),
            domestic_flights=db_stats.get("domestic_flights", 0),
            intl_departures=db_stats.get("intl_departures", 0),
            intl_arrivals=db_stats.get("intl_arrivals", 0),
            unique_pilots=db_stats.get("unique_pilots", 0),
            people_on_board_total=db_stats.get("people_on_board_total", 0),
            flight_time_total_min=db_stats.get("flight_time_total_min", 0),
            atc_time_total_min=db_stats.get("atc_time_total_min", 0),
            atc_count=db_stats.get("atc_count", 0), # Unique ATCs in period
            top_airports=top_airports,
            top_pilots=top_pilots,
            top_atcs=top_atcs
        )
    
    def consolidate_realtime(self, file_path: str) -> Optional[Statistics]:
        """
        Consolidate realtime data using database aggregation.
        """
        # Get last snapshot from DB for current status
        last_snapshot = self.db_service.get_last_snapshot()
        if not last_snapshot:
            return None
            
        # Filter pilots and ATCs for country
        current_pilots = [
            p for p in last_snapshot.pilots
            if self.classifier.involves_country(p)
        ]
        
        current_atcs = [
            a for a in last_snapshot.atcs
            if self.classifier.is_country_atc(a)
        ]
        
        # Determine start of day for history
        now = datetime.now(timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get aggregated stats from DB
        prefixes = self.classifier.prefixes
        db_stats = self.db_service.get_statistics_aggregated(start_of_day, list(prefixes))

        # Compose final stats
        return self.statistics_service.compose_realtime_stats(
            db_stats,
            current_pilots,
            current_atcs
        )
