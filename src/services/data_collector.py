"""
Data collector service.
Collects snapshots from IVAO API and saves to historical files."""

from datetime import datetime, timezone
from typing import List
from ..models import Pilot, ATC, Snapshot
from ..api import IVAOClient
from ..config import Constants
from .flight_classifier import FlightClassifier

class DataCollector:
    """Service for collecting and saving network data."""
    
    def __init__(self, ivao_client: IVAOClient):
        """Initialize data collector."""
        self.ivao_client = ivao_client
        self.classifier = FlightClassifier()
        self.constants = Constants()
        # Initialize Database Service
        from .db_service import DatabaseService
        self.db_service = DatabaseService()
    
    async def collect_and_save(self) -> None:
        """Collect current network data and save to database."""
        # Fetch data from IVAO API
        data = await self.ivao_client.fetch_whazzup()
        if not data:
            return
        
        # Extract pilots and ATCs
        clients = data.get("clients", {})
        all_pilots_data = clients.get("pilots", [])
        all_atcs_data = clients.get("atcs", [])
        
        # Parse into models
        all_pilots = [Pilot.from_api_data(p) for p in all_pilots_data]
        all_atcs = [atc for atc in (ATC.from_api_data(a) for a in all_atcs_data) if atc is not None]
        
        # Filter for country
        country_pilots = [p for p in all_pilots if self.classifier.involves_country(p) and p.user_id]
        country_atcs = [a for a in all_atcs if self.classifier.is_country_atc(a) and a.user_id]
        
        # Create snapshot
        now = datetime.now(timezone.utc)
        snapshot = Snapshot(
            timestamp=now,
            pilots=country_pilots,
            atcs=country_atcs
        )
        
        # Save to database
        if self.db_service.save_snapshot(snapshot):
            # Log success
            unique_pilots = {str(p.user_id or p.callsign).upper() for p in country_pilots}
            unique_atcs = {str(a.user_id or a.callsign).upper() for a in country_atcs}
            
            minute_key = now.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[IVAO] {minute_key} | Pilots: {len(unique_pilots)}, ATCs: {len(unique_atcs)}")
        else:
            print(f"[ERROR] Failed to save snapshot to database")
        
        # Manual cleanup to replicate original script behavior
        del snapshot
        del all_pilots
        del all_atcs
        del country_pilots
        del country_atcs
