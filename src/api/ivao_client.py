"""
IVAO API client.
Handles communication with the IVAO whazzup API."""

import aiohttp
from typing import Optional, Dict, Any
from ..config import Constants

class IVAOClient:
    """Client for IVAO API."""
    
    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        """Initialize IVAO client."""
        self.session = session
        self.constants = Constants()
        self._owns_session = session is None
    
    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure we have an active session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def fetch_whazzup(self) -> Optional[Dict[str, Any]]:
        """Fetch current network status from IVAO API."""
        try:
            session = await self._ensure_session()
            async with session.get(self.constants.WHAZZUP_URL, timeout=20) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    print(f"[ERROR] IVAO API returned status {resp.status}")
                    return None
        except Exception as e:
            print(f"[ERROR] Error fetching whazzup: {e}")
            return None
    
    async def close(self):
        """Close the session if we own it."""
        if self._owns_session and self.session and not self.session.closed:
            await self.session.close()
