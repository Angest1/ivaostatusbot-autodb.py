"""
METAR API client.
Handles communication with AVWX API and weather emoji mapping."""

import time
import re
import aiohttp
from datetime import datetime, timezone
from typing import Optional
from ..config import Settings, Constants
from ..utils.time_utils import get_timezone

class METARClient:
    """Client for METAR/AVWX API with caching."""
    
    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        """Initialize METAR client."""
        self.settings = Settings()
        self.constants = Constants()
        self.session = session
        self._owns_session = session is None
        self._cache = {}
    
    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure we have an active session with auth header."""
        if self.session is None or self.session.closed:
            headers = {}
            if self.settings.avwx_token:
                headers["Authorization"] = f"Bearer {self.settings.avwx_token}"
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session
    
    async def get_metar(self, icao: str) -> str:
        """Get METAR for an ICAO code with caching."""
        now = time.time()
        
        # Check cache
        if icao in self._cache:
            cached_metar, cached_time = self._cache[icao]
            if now - cached_time < self.constants.METAR_REFRESH_SECONDS:
                return cached_metar
        
        # Fetch new METAR
        if not self.settings.avwx_token:
            metar = None
        else:
            try:
                session = await self._ensure_session()
                headers = {}
                if self.settings.avwx_token:
                    headers["Authorization"] = f"Bearer {self.settings.avwx_token}"
                
                url = f"https://avwx.rest/api/metar/{icao}?options=info"
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        metar = data.get("raw", None)
                        print(f"[AVWX] {metar}")
                    elif resp.status == 404:
                        print(f"[AVWX] Station {icao} not found (404)")
                        metar = None
                    else:
                        print(f"[AVWX] Failed to fetch: {resp.status} - {await resp.text()}")
                        metar = None
            except Exception as e:
                print(f"[ERROR] Error fetching METAR {icao}: {e}")
                metar = None
        
        # Update cache
        self._cache[icao] = (metar, now)
        return metar
    
    def get_weather_emoji(self, metar_raw: str) -> str:
        """Get weather emoji based on METAR."""
        if not metar_raw:
            return ""
        
        tokens = metar_raw.upper().split()
        metar_tokens = tokens[2:] if len(tokens) > 2 else []
        metar_text = " ".join(metar_tokens)
        
        # Thunderstorm
        if "TS" in metar_text:
            return "⛈️"
        
        # Rain
        rain_codes = ["SHRA", "RA", "DZ", "FZRA", "-SHRA", "+SHRA", "-RA", "+RA",
                      "-DZ", "+DZ", "-FZRA", "+FZRA", "RESHRA"]
        if any(x in metar_text for x in rain_codes):
            return "🌧️"
        
        # Snow
        snow_codes = ["SN", "SG", "GS", "-SN", "+SN", "-SG", "+SG", "-GS", "+GS"]
        if any(x in metar_text for x in snow_codes):
            return "❄️"
        
        # Mixed precipitation
        mixed_codes = ["RASN", "SNRA", "SHSN", "-RASN", "+RASN",
                       "-SNRA", "+SNRA", "-SHSN", "+SHSN"]
        if any(x in metar_text for x in mixed_codes):
            return "🌨️"
        
        # Hail
        hail_codes = ["GR", "+GR", "-GR"]
        if any(x in metar_text for x in hail_codes):
            return "🧊"
        
        # Fog/Mist
        fog_codes = ["FG", "BR", "HZ"]
        if any(x in metar_text for x in fog_codes):
            return "🌫️"
        
        # Ice
        ice_codes = ["IC", "PL"]
        if any(x in metar_text for x in ice_codes):
            return "🧊"
        
        # Determine day/night based on local time
        now_utc = datetime.now(timezone.utc)
        local_tz = get_timezone()
        now_local = now_utc.astimezone(local_tz)
        hour_local = now_local.hour + now_local.minute / 60
        is_day = 7 <= hour_local < 20
        
        # Cloud coverage
        if "OVC" in metar_text or "BKN" in metar_text:
            return "☁️"
        elif "SCT" in metar_text:
            return "⛅" if is_day else "🌙"
        elif "FEW" in metar_text:
            return "🌤️" if is_day else "🌙"
        
        # Clear
        return "☀️" if is_day else "🌙"
    
    async def close(self):
        """Close the session if we own it."""
        if self._owns_session and self.session and not self.session.closed:
            await self.session.close()
