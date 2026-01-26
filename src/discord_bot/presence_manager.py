"""
Presence manager.
Rotates bot presence/status to show current activity."""

import random
import discord
from typing import List
from ..models import ATC
from ..config.languages import get_text
from ..config.settings import Settings

class PresenceManager:
    """Manages bot presence rotation."""
    
    def __init__(self):
        """Initialize presence manager."""
        self.state_index = 0
    
    async def rotate_presence(
        self,
        bot: discord.Client,
        num_pilots: int,
        atcs: List[ATC],
        flights: List[tuple]
    ) -> None:
        """Rotate bot presence to show current activity."""
        total_atc = len(atcs)
        
        # Get settings
        settings = Settings()
        next_event = settings.next_event
        
        # No activity
        if num_pilots == 0 and total_atc == 0:
            if next_event:
                # Show next event if configured
                try:
                    activity = discord.Activity(type=discord.ActivityType.watching, name=next_event)
                    await bot.change_presence(activity=activity)
                except Exception as e:
                    print(f"[WARNING] Error setting NEXT_EVENT presence: {e}")
            else:
                try:
                    await bot.change_presence(activity=None)
                except Exception as e:
                    print(f"[WARNING] Error clearing presence: {e}")
            return
        
        # Build status messages
        states = []
        
        # Get language settings
        lang = Settings().lang
        
         # State 1: Pilot and ATC count
        pilot_label = get_text(lang, "presence_pilots" if num_pilots != 1 else "presence_pilot")
        online_label = get_text(lang, "presence_online")
        
        if total_atc == 0:
            state1 = f"{num_pilots} {pilot_label} {online_label}"
        else:
            atc_label = get_text(lang, "presence_atcs" if total_atc != 1 else "presence_atc")
            state1 = f"{num_pilots} {pilot_label} | {total_atc} {atc_label}"
        states.append(state1)
        
        # State 2: ATC callsigns (if any)
        if total_atc > 0:
            dependencies = [atc.callsign for atc in atcs if atc.callsign]
            random.shuffle(dependencies)
            atc_text = "/".join(dependencies)
            if len(atc_text) > 120:
                atc_text = atc_text[:109] + "..."
            state2 = f"{atc_text} {online_label}"
            states.append(state2)
        
        # State 3: Flight callsigns (if any)
        if flights:
            flight_callsigns = [f[0] for f in flights if isinstance(f, (list, tuple)) and len(f) > 0]
            random.shuffle(flight_callsigns)
            flights_text = "/".join(flight_callsigns)
            if len(flights_text) > 120:
                flights_text = flights_text[:117] + "..."
            state3 = f"{flights_text}"
            states.append(state3)
            
        # State 4: NEXT_EVENT (if configured)
        if next_event:
            states.append(next_event)
        
        # Rotate through states
        text = states[self.state_index % len(states)]
        
        try:
            activity = discord.Activity(type=discord.ActivityType.watching, name=text)
            await bot.change_presence(activity=activity)
        except Exception as e:
            print(f"[WARNING] Error updating presence: {e}")
        
        self.state_index = (self.state_index + 1) % len(states)
