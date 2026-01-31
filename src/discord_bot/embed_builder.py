"""
Discord embed builder.
Creates Discord embeds for realtime and historical reports."""

import os
import re
import json
import discord
from datetime import datetime
from typing import Tuple, Optional, List
from collections import Counter
from ..models import Statistics, ATC
from ..config import Settings, Constants
from ..config.languages import get_text
from ..utils.time_utils import format_hours_minutes
from ..utils.text_utils import join_with_limit, clean_dependency, move_garbage_to_detail
from ..services import ChartService, ATCSessionTracker

class EmbedBuilder:
    """Builds Discord embeds for various report types."""
    
    def __init__(self, chart_service: ChartService, atc_tracker: ATCSessionTracker):
        """Initialize embed builder."""
        self.settings = Settings()
        self.constants = Constants()
        self.chart_service = chart_service
        self.atc_tracker = atc_tracker
        self.atc_rotation_index = 0
        self.flight_rotation_index = 0
        self.footer_rotation_index = 0
    
    def build_realtime_embed(
        self,
        stats: Statistics,
        date: datetime,
        metar_emoji: str,
        chart_path: Optional[str] = None
    ) -> Tuple[discord.Embed, Optional[discord.File]]:
        """Build realtime embed with current network status."""
        has_atc = stats.atc_count > 0
        embed_color = discord.Color.green() if has_atc else discord.Color.red()
        
        title = get_text(
            self.settings.lang, 
            "live_title", 
            country=self.settings.country_name, 
            date=date.strftime('%d/%m/%Y %H:%M UTC')
        )
        embed = discord.Embed(title=title, color=embed_color)
        
        # Attach chart if provided
        file = None
        if chart_path and os.path.exists(chart_path):
            try:
                file = discord.File(chart_path, filename="chart_realtime.png")
                embed.set_image(url="attachment://chart_realtime.png")
            except Exception as e:
                print(f"[ERROR] Error attaching realtime chart: {e}")
        

        if stats.total_flights > 0:
            embed.add_field(
                name=get_text(self.settings.lang, "domestic_flights", flag=self.settings.country_flag),
                value=str(stats.domestic_flights),
                inline=True
            )
            embed.add_field(
                name=get_text(self.settings.lang, "intl_arrivals", world=self.settings.world_emoji),
                value=str(stats.intl_arrivals),
                inline=True
            )
            embed.add_field(
                name=get_text(self.settings.lang, "intl_departures", world=self.settings.world_emoji_foreign),
                value=str(stats.intl_departures),
                inline=True
            )
        

        total_pob = stats.people_on_board_total
        flight_time = format_hours_minutes(stats.flight_time_total_min)
        embed.add_field(
            name=get_text(self.settings.lang, "pilots_online"),
            value=f'{stats.unique_pilots} ({total_pob} POB)',
            inline=True
        )
        embed.add_field(
            name=get_text(self.settings.lang, "flight_hours"),
            value=flight_time,
            inline=True
        )
        

        if has_atc and stats.active_atcs:
            atcs = stats.active_atcs
            
            # Remove duplicates and sort
            seen = set()
            unique_atcs = []
            for atc in atcs:
                if atc.callsign not in seen:
                    seen.add(atc.callsign)
                    unique_atcs.append(atc)
            unique_atcs.sort(key=lambda x: x.callsign)
            
            # Calculate session duration
            sessions = self.atc_tracker.calculate_session_duration(unique_atcs)
            
            # Get current ATC for rotation
            if self.atc_rotation_index >= len(unique_atcs):
                self.atc_rotation_index = 0
            
            current_atc = unique_atcs[self.atc_rotation_index]
            session_minutes = sessions.get(current_atc.callsign, 0)
            
            embed.add_field(
                name=get_text(self.settings.lang, "controllers"),
                value=f"{len(unique_atcs)} ATC ({format_hours_minutes(session_minutes)})",
                inline=True
            )
            
            # Build ATC detail
            self._add_atc_detail(embed, unique_atcs, current_atc)
            
            # Rotate for next update
            if len(unique_atcs) > 1:
                self.atc_rotation_index = (self.atc_rotation_index + 1) % len(unique_atcs)
        else:
            embed.add_field(
                name=get_text(self.settings.lang, "status_title"),
                value=get_text(self.settings.lang, "status_no_atc"),
                inline=True
            )
            

        # Calculate Top 5 first to determine availability
        top_airports_text = self._get_top_airports(stats.active_flights or [])
        
        footer_states = []
        if self.settings.next_event:
            footer_states.append("event")
            if top_airports_text:
                footer_states.append("top5")
        else:
            if top_airports_text:
                footer_states.append("top5")
            else:
                footer_states.append("default")
        
        # Ensure index is within bounds
        if self.footer_rotation_index >= len(footer_states):
            self.footer_rotation_index = 0
            
        current_footer_state = footer_states[self.footer_rotation_index]
        footer_text = ""
        
        if current_footer_state == "event":
            label = get_text(self.settings.lang, "next_event_label")
            footer_text = f"{label}: {self.settings.next_event}"
        elif current_footer_state == "top5":
            footer_text = top_airports_text
        else:
            # Default fallback
            footer_text = "International Virtual Aviation Organisation ✈️ - @746048"
        
        embed.set_footer(text=footer_text)
        
        self.footer_rotation_index = (self.footer_rotation_index + 1) % len(footer_states)
        

        if stats.active_flights:
            self._add_flights_detail(embed, stats.active_flights)
        

        if stats.metar:
            metar_text = stats.metar
            embed.add_field(
                name=get_text(self.settings.lang, "metar", emoji=metar_emoji, airport=self.settings.airport_name),
                value=metar_text,
                inline=False
            )
        
        return embed, file
    
    def _add_atc_detail(self, embed: discord.Embed, atcs: List[ATC], current_atc: ATC):
        """Add ATC controlling detail to embed."""
        highlight = len(atcs) > 1
        
        # Build callsign list
        callsign_list = []
        for atc in atcs:
            cs = atc.callsign
            if highlight and atc == current_atc:
                callsign_list.append(f"***{cs}***")
            else:
                callsign_list.append(f"*{cs}*")
        
        # Parse ATIS for detail
        dependency = ""
        atis_text = ""
        has_detail = False
        
        if current_atc.atis:
            try:
                # ATIS is now stored as a JSON string
                data = json.loads(current_atc.atis)
                dependency = data.get("dependency", "")
                atis_text = data.get("text", "")
                has_detail = True
            except (json.JSONDecodeError, TypeError, AttributeError):
                # Handle case where atis might be malformed or legacy format
                pass
        
        # No cleaning needed as it is done before saving
        
        
        # Add frequency
        freq_text = ""
        if current_atc.frequency is not None:
            try:
                freq_text = f" {float(current_atc.frequency):.1f}"
            except (ValueError, TypeError):
                pass
        
        # Build detail text
        detail_text = ""
        if has_detail:
            # Check if we should hide the detail line completely (redundant with callsign)
            # Only if: name is same as callsign AND no atis text
            # We ignore frequency presence here as user requested to hide it too if condition met.
            effective_name = dependency or current_atc.callsign
            
            if effective_name == current_atc.callsign and not atis_text:
                detail_text = ""
            else:
                if highlight:
                    detail_text = f"***{effective_name}{freq_text}**{atis_text}*"
                else:
                    detail_text = f"*{effective_name}{freq_text}{atis_text}*"
        
        # Combine callsigns and detail
        reserved = len(detail_text) + (1 if detail_text else 0)
        callsigns_limit = self.constants.DISCORD_FIELD_LIMIT - reserved
        callsigns_text = join_with_limit(callsign_list, limit=max(0, callsigns_limit))
        
        if detail_text and callsigns_limit > 0:
            value = f"{callsigns_text}\n{detail_text}"
        else:
            value = callsigns_text
        
        embed.add_field(name=get_text(self.settings.lang, "controlling"), value=value, inline=False)
    
    def _add_flights_detail(self, embed: discord.Embed, flights: List[Tuple]):
        """Add active flights detail to embed."""
        sorted_flights = sorted(flights, key=lambda f: f[0])  # Sort by callsign
        
        highlight = len(sorted_flights) > 1
        
        if self.flight_rotation_index >= len(sorted_flights):
            self.flight_rotation_index = 0
        
        current_flight = sorted_flights[self.flight_rotation_index]
        callsign, dep, arr, route, pob, aircraft = current_flight
        
        # Build callsign list
        flight_list = []
        for i, flight in enumerate(sorted_flights):
            cs = flight[0]
            if highlight and i == self.flight_rotation_index:
                flight_list.append(f"***{cs}***")
            else:
                flight_list.append(f"*{cs}*")
        
        # Build route detail
        webeye_url = f"https://webeye.ivao.aero/?callsign={callsign}"
        route_detail = f"*(**{aircraft}**/{pob})* [→]({webeye_url}) *{dep}/{route}/{arr}*"
        
        # Combine
        flights_text = "/".join(flight_list)
        value_full = f"{flights_text}\n{route_detail}"
        
        if len(value_full) <= self.constants.DISCORD_FIELD_LIMIT:
            value = value_full
        else:
            # Field too long, just show callsigns
            flight_list_no_bold = [f.replace("***", "*") for f in flight_list]
            value = join_with_limit(flight_list_no_bold, limit=self.constants.DISCORD_FIELD_LIMIT)
        
        embed.add_field(name=get_text(self.settings.lang, "flying"), value=value, inline=False)
        
        # Rotate for next update
        if highlight:
            self.flight_rotation_index += 1

    def _get_top_airports(self, flights: List[Tuple]) -> str:
        """Get formatted string for Top 5 airports."""
        if not flights:
            return ""
            
        counter = Counter()
        for flight in flights:
            # flight = (callsign, dep, arr, route, pob, aircraft)
            if len(flight) >= 3:
                dep, arr = flight[1], flight[2]
                
                # Check if airports are local
                is_local_dep = any(dep.startswith(p) for p in self.settings.country_prefixes) if dep else False
                is_local_arr = any(arr.startswith(p) for p in self.settings.country_prefixes) if arr else False
                
                if dep == arr:
                    # Same airport (e.g. patterns), count only once if local
                    if dep and len(dep) == 4 and is_local_dep:
                        counter[dep] += 1
                else:
                    # Different airports, count both if local
                    if dep and len(dep) == 4 and is_local_dep:
                        counter[dep] += 1
                    if arr and len(arr) == 4 and is_local_arr:
                        counter[arr] += 1
        
        most_common = counter.most_common(5)
        
        if not most_common:
            return ""
            
        parts = []
        medals = ["🥇", "🥈", "🥉", "🎖️", "🎖️"]
        
        for i, (airport, count) in enumerate(most_common):
            medal = medals[i]
            parts.append(f"{medal} {airport}: {count}")
            
        return " ".join(parts)
    
    def build_historical_embed(
        self,
        stats: Statistics,
        date: datetime,
        mode: str,
        include_hour: bool = False
    ) -> discord.Embed:
        """Build historical embed (daily, weekly, monthly)."""
        if mode == "daily":
            if include_hour:
                title = get_text(self.settings.lang, "daily_title", country=self.settings.country_name, date=date.strftime('%d/%m/%Y %H:%M UTC'))
            else:
                title = get_text(self.settings.lang, "daily_title", country=self.settings.country_name, date=date.strftime('%d/%m/%Y'))
            embed_color = discord.Color.blue()
        elif mode == "weekly":
            iso = date.isocalendar()
            title = get_text(self.settings.lang, "weekly_title", country=self.settings.country_name, year=iso.year, week=iso.week)
            embed_color = discord.Color.purple()
        else:  # monthly
            title = get_text(self.settings.lang, "monthly_title", country=self.settings.country_name, date=date.strftime('%B %Y'))
            embed_color = discord.Color.light_gray()
        
        embed = discord.Embed(title=title, color=embed_color)
        

        embed.add_field(
            name=get_text(self.settings.lang, "domestic_flights", flag=self.settings.country_flag),
            value=str(stats.domestic_flights),
            inline=True
        )
        embed.add_field(
            name=get_text(self.settings.lang, "intl_arrivals", world=self.settings.world_emoji),
            value=str(stats.intl_arrivals),
            inline=True
        )
        embed.add_field(
            name=get_text(self.settings.lang, "intl_departures", world=self.settings.world_emoji_foreign),
            value=str(stats.intl_departures),
            inline=True
        )
        

        total_pob = stats.people_on_board_total
        flight_time = format_hours_minutes(stats.flight_time_total_min)
        atc_time = format_hours_minutes(stats.atc_time_total_min)
        
        embed.add_field(
            name=get_text(self.settings.lang, "total_flights"),
            value=f'{stats.total_flights} ({total_pob} POB)',
            inline=True
        )
        embed.add_field(
            name=get_text(self.settings.lang, "pilots"),
            value=f'{stats.unique_pilots} ({flight_time})',
            inline=True
        )
        embed.add_field(
            name=get_text(self.settings.lang, "controllers"),
            value=f'{stats.atc_count} ATC ({atc_time})',
            inline=True
        )
        
        return embed
