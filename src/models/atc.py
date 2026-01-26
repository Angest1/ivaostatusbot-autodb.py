"""
ATC data model.
Represents an air traffic controller."""

from dataclasses import dataclass
import json
from typing import Optional, Dict, Any
from ..utils.text_utils import parse_atis

@dataclass(slots=True)
class ATC:
    """Air traffic controller information."""
    user_id: Optional[str]
    callsign: str
    frequency: Optional[float]
    atis: Optional[str]
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> Optional['ATC']:
        """Create ATC from API data."""
        if not isinstance(data, dict):
            return None
        
        callsign = (data.get("callsign") or "").upper()
        if not callsign:
            return None
        
        # Get frequency from atcSession or directly
        freq = None
        atc_session = data.get("atcSession")
        if isinstance(atc_session, dict):
            freq = atc_session.get("frequency")
        else:
            freq = data.get("frequency")
        
        # Parse ATIS
        atis_data = data.get("atis")
        atis_clean = None
        if atis_data:
            parsed = parse_atis(atis_data)
            atis_clean = json.dumps(parsed)
            
        return cls(
            user_id=data.get("userId"),
            callsign=callsign,
            frequency=freq,
            atis=atis_clean
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "userId": self.user_id,
            "callsign": self.callsign,
            "frequency": self.frequency,
            "atis": self.atis
        }
