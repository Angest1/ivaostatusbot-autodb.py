"""
Snapshot data model.
Represents a point-in-time snapshot of network activity."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any
from .pilot import Pilot
from .atc import ATC

@dataclass(slots=True)
class Snapshot:
    """Network activity snapshot."""
    timestamp: datetime
    pilots: List[Pilot]
    atcs: List[ATC]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Snapshot':
        """Create Snapshot from dictionary."""
        timestamp = datetime.fromisoformat(data["timestamp"])
        
        pilots = [
            Pilot.from_api_data(p)
            for p in data.get("pilots", [])
        ]
        
        atcs = [
            atc for atc in (
                ATC.from_api_data(a)
                for a in data.get("atcs", [])
            )
            if atc is not None
        ]
        
        return cls(
            timestamp=timestamp,
            pilots=pilots,
            atcs=atcs
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "pilots": [p.to_dict() for p in self.pilots],
            "atcs": [a.to_dict() for a in self.atcs]
        }
