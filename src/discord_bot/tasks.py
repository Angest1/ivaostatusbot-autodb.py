"""
Bot tasks.
Scheduled background tasks for data collection and report generation."""

import asyncio
import os
from datetime import datetime, timezone, timedelta
from typing import Optional
import discord

from ..config import Constants, Settings
from ..services import DataCollector, ATCSessionTracker, ConsolidationService, ChartService
from ..api import METARClient
from .embed_builder import EmbedBuilder
from .presence_manager import PresenceManager

class BotTasks:
    """Manages bot background tasks."""
    
    def __init__(
        self,
        bot: discord.Client,
        data_collector: DataCollector,
        atc_tracker: ATCSessionTracker,
        consolidation_service: ConsolidationService,
        chart_service: ChartService,
        metar_client: METARClient,
        embed_builder: EmbedBuilder
    ):
        """Initialize bot tasks."""
        self.bot = bot
        self.data_collector = data_collector
        self.atc_tracker = atc_tracker
        self.consolidation_service = consolidation_service
        self.chart_service = chart_service
        self.metar_client = metar_client
        self.embed_builder = embed_builder
        self.constants = Constants()
        
        self.last_daily_date = None
        self.last_weekly_date = None
        self.last_monthly_date = None
        self.realtime_message_id = None
        self.realtime_lock = asyncio.Lock()
        self.presence_manager = PresenceManager()
        self._cached_stats = None
    
    async def collection_task(self):
        """Collect data every minute."""
        await self.bot.wait_until_ready()
        
        attempt = 0
        max_wait = 300
        
        while not self.bot.is_closed():
            try:
                # Check for config updates
                Settings().check_and_reload()
                
                # Collect and save data
                await self.data_collector.collect_and_save()
                
                # Update ATC sessions
                stats = self.consolidation_service.consolidate_realtime(
                    self.constants.HISTORICAL_DAILY_FILE
                )
                
                # Cache stats for realtime update
                self._cached_stats = stats
                

                
                # Cleanup manually to free memory
                del stats
                
                attempt = 0
                
                # Wait until next minute
                now = datetime.now(timezone.utc)
                next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
                wait_seconds = (next_minute - now).total_seconds()
                if wait_seconds < 0:
                    wait_seconds = 0
                
                await asyncio.sleep(wait_seconds)
                
            except Exception as e:
                attempt += 1
                wait_seconds = min(5 * attempt, max_wait)
                print(f"[ERROR] Error in collection task: {e}. Retrying in {wait_seconds}s...")
                await asyncio.sleep(wait_seconds)
    
    async def realtime_update_task(self, channel: discord.TextChannel):
        """Update realtime message every 10 seconds or when new data is available."""
        while not self.bot.is_closed():
            try:
                await self._update_realtime_message(channel, force_new=False)
            except Exception as e:
                print(f"[ERROR] Error in realtime update task: {e}")
            
            try:
                # Wait for interval
                await asyncio.sleep(self.constants.REALTIME_UPDATE_INTERVAL)
            except Exception as e:
                print(f"[ERROR] Error in realtime wait: {e}")
    
    async def scheduled_reports_task(self, channel: discord.TextChannel):
        """Generate scheduled reports (daily, weekly, monthly)."""
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            now = datetime.now(timezone.utc)
            today = now.date()
            report_sent = False
            
            # Daily report at 23:59 UTC
            if self.last_daily_date != today and now.hour == 23 and now.minute >= 59:
                print("[AUTO] Executing DAILY report")
                await self._send_daily_report(channel)
                self.last_daily_date = today
                
                # Clear cache
                self._cached_stats = None
                
                report_sent = True
            
            # Weekly report on Sunday at 23:59 UTC
            if now.weekday() == 6 and self.last_weekly_date != today and now.hour == 23 and now.minute >= 59:
                print("[AUTO] Executing WEEKLY report")
                await self._send_weekly_report(channel)
                self.last_weekly_date = today
                report_sent = True
            
            # Monthly report on last day of month at 23:59 UTC
            is_last_day = (now + timedelta(days=1)).day == 1
            if is_last_day and self.last_monthly_date != today and now.hour == 23 and now.minute >= 59:
                print("[AUTO] Executing MONTHLY report")
                await self._send_monthly_report(channel)
                self.last_monthly_date = today
                report_sent = True
            
            # Recreate realtime message after reports
            if report_sent:
                await asyncio.sleep(60)
                await self._update_realtime_message(channel, force_new=True)
                print(f"[AUTO] REALTIME recreated after reports at {datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC")
            
            await asyncio.sleep(self.constants.REPORT_CHECK_INTERVAL)
    
    # helper methods removed as they are no longer needed

    
    async def _update_realtime_message(self, channel: discord.TextChannel, force_new: bool = False):
        """Update or create realtime message."""
        async with self.realtime_lock:
            try:
                # Always reload saved message ID to ensure state consistency
                self.realtime_message_id = await self._load_message_id()
                
                # Get statistics (use cache if available)
                stats = self._cached_stats
                if not stats:
                    stats = self.consolidation_service.consolidate_realtime(
                        self.constants.HISTORICAL_DAILY_FILE
                    )
                    self._cached_stats = stats
                
                if not stats:
                    # Try historical fallback
                    stats = self.consolidation_service.consolidate_historical(
                        self.constants.HISTORICAL_DAILY_FILE
                    )
                
                if not stats:
                    return
                
                # Get METAR
                from ..config import Settings
                settings = Settings()
                stats.metar = await self.metar_client.get_metar(settings.metar_airport)
                metar_emoji = self.metar_client.get_weather_emoji(stats.metar)
                
                # Generate chart in background thread
                chart_path = None
                try:
                    # Determine colors based on ATC presence
                    # We pass explicit colors to match EmbedBuilder logic 1:1, 
                    # ensuring consistency between Embed color and Chart color
                    has_atc = stats.atc_count > 0
                    color_primary = (self.constants.CHART_COLORS["realtime_atc_active"] if has_atc 
                                   else self.constants.CHART_COLORS["realtime_no_atc"])
                    color_atc = (self.constants.CHART_COLORS["realtime_atc_active_secondary"] if has_atc 
                                else self.constants.CHART_COLORS["realtime_no_atc_secondary"])

                    def generate_realtime_chart():
                        return self.chart_service.generate_chart(
                            self.constants.HISTORICAL_DAILY_FILE,
                            "chart_realtime.png",
                            "realtime",
                            color_primary,
                            color_atc
                        )
                    
                    chart_path = await asyncio.to_thread(generate_realtime_chart)
                except Exception as e:
                    print(f"[ERROR] Error generating realtime chart: {e}")

                # Build embed
                embed, file = self.embed_builder.build_realtime_embed(
                    stats,
                    datetime.now(timezone.utc),
                    metar_emoji,
                    chart_path
                )
                
                # Update presence
                await self.presence_manager.rotate_presence(
                    self.bot,
                    stats.unique_pilots,
                    stats.active_atcs or [],
                    stats.active_flights or []
                )
                
                # Send or update message
                if force_new and self.realtime_message_id:
                    try:
                        old_msg = await channel.fetch_message(self.realtime_message_id)
                        await old_msg.delete()
                    except (discord.NotFound, discord.Forbidden):
                        pass
                    self.realtime_message_id = None
                
                if self.realtime_message_id:
                    try:
                        msg = await channel.fetch_message(self.realtime_message_id)
                        if file:
                            with open(file.fp.name, "rb") as f:
                                df = discord.File(f, filename="chart_realtime.png")
                                await msg.edit(embed=embed, attachments=[df])
                        else:
                            await msg.edit(embed=embed, attachments=[])
                    except discord.NotFound:
                        # Message was deleted, we need to create a new one
                        self.realtime_message_id = None
                    except discord.HTTPException as e:
                        # Network or temporary error, log and abort to avoid duplicates
                        print(f"[ERROR] HTTP error updating message: {e}")
                        return
                    except Exception as e:
                        print(f"[ERROR] Unexpected error updating message: {e}")
                        return
                
                if not self.realtime_message_id:
                    msg = await channel.send(embed=embed, file=file)
                    self.realtime_message_id = msg.id
                    await self._save_message_id(msg.id)
                
            except Exception as e:
                print(f"[ERROR] Error updating realtime message: {e}")
    
    async def _send_with_retry(self, channel: discord.TextChannel, embed: discord.Embed, chart_path: Optional[str] = None, retries: int = 5, initial_delay: int = 5):
        """Send message with retry logic and exponential backoff."""
        attempt = 0
        last_error = None
        
        while attempt < retries:
            try:
                if chart_path and os.path.exists(chart_path):
                    # Open file freshly for each attempt to avoid closed file errors
                    with open(chart_path, "rb") as f:
                        filename = os.path.basename(chart_path)
                        file = discord.File(f, filename=filename)
                        # Ensure embed uses the correct attachment URL
                        embed.set_image(url=f"attachment://{filename}")
                        await channel.send(embed=embed, file=file)
                else:
                    await channel.send(embed=embed)
                
                return # Success
                
            except (discord.HTTPException, TimeoutError, ConnectionError) as e:
                last_error = e
                attempt += 1
                if attempt >= retries:
                    break
                
                wait_time = initial_delay * (2 ** (attempt - 1))
                print(f"[WARN] Error sending report (attempt {attempt}/{retries}): {e}. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                # Non-retryable error
                print(f"[ERROR] Unexpected error sending report: {e}")
                raise e
        
        print(f"[ERROR] Failed to send report after {retries} attempts. Last error: {last_error}")
        raise last_error

    async def _send_daily_report(self, channel: discord.TextChannel):
        """Send daily report."""
        print("[AUTO] Generating DAILY report in background...")
        try:
            # Run heavy lifting in a thread
            def generate():
                now = datetime.now(timezone.utc)
                stats = self.consolidation_service.consolidate_historical(
                    self.constants.HISTORICAL_DAILY_FILE
                )
                
                if not stats:
                    return None, None
                
                chart_path = self.chart_service.generate_chart(
                    self.constants.HISTORICAL_DAILY_FILE,
                    "chart_daily.png",
                    "daily"
                )
                return stats, chart_path

            stats, chart_path = await asyncio.to_thread(generate)
            
            if not stats:
                print("[ERROR] No daily data to consolidate")
                return

            now = datetime.now(timezone.utc)
            embed = self.embed_builder.build_historical_embed(stats, now, "daily")
            
            # Send with retry
            await self._send_with_retry(channel, embed, chart_path)
            
            print(f"[AUTO] DAILY report sent ({now.date()})")
            
            # Manual GC
            import gc
            await asyncio.to_thread(gc.collect)
            
            # Prune daily data (rolling 36h window)
            # Done once a day to avoid overloading the minute loop.
            print("[AUTO] Pruning daily data...")
            self.consolidation_service.db_service.prune_daily_data()
            
        except Exception as e:
            print(f"[ERROR] Error sending daily report: {e}")
    
    async def _send_weekly_report(self, channel: discord.TextChannel):
        """Send weekly report."""
        print("[AUTO] Generating WEEKLY report in background...")
        try:
            def generate():
                now = datetime.now(timezone.utc)
                stats = self.consolidation_service.consolidate_historical(
                    self.constants.HISTORICAL_WEEKLY_FILE
                )
                
                if not stats:
                    return None, None
                
                chart_path = self.chart_service.generate_chart(
                    self.constants.HISTORICAL_WEEKLY_FILE,
                    "chart_weekly.png",
                    "weekly"
                )
                return stats, chart_path

            stats, chart_path = await asyncio.to_thread(generate)
            
            if not stats:
                print("[ERROR] No weekly data to consolidate")
                return

            now = datetime.now(timezone.utc)
            embed = self.embed_builder.build_historical_embed(stats, now, "weekly")
            
            # Send with retry
            await self._send_with_retry(channel, embed, chart_path)
            
            print(f"[AUTO] WEEKLY report sent (week {now.isocalendar()[1]})")
            
            # Manual GC
            import gc
            await asyncio.to_thread(gc.collect)

            # Reset WEEKLY database
            print("[AUTO] Resetting WEEKLY database...")
            self.consolidation_service.db_service.reset_weekly_data()

        except Exception as e:
            print(f"[ERROR] Error sending weekly report: {e}")
    
    async def _send_monthly_report(self, channel: discord.TextChannel):
        """Send monthly report."""
        print("[AUTO] Generating MONTHLY report in background...")
        try:
            def generate():
                now = datetime.now(timezone.utc)
                stats = self.consolidation_service.consolidate_historical(
                    self.constants.HISTORICAL_MONTHLY_FILE
                )
                
                if not stats:
                    return None, None
                
                chart_path = self.chart_service.generate_chart(
                    self.constants.HISTORICAL_MONTHLY_FILE,
                    "chart_monthly.png",
                    "monthly"
                )
                return stats, chart_path

            stats, chart_path = await asyncio.to_thread(generate)
            
            if not stats:
                print("[ERROR] No monthly data to consolidate")
                return
            
            now = datetime.now(timezone.utc)
            embed = self.embed_builder.build_historical_embed(stats, now, "monthly")
            
            # Send with retry
            await self._send_with_retry(channel, embed, chart_path)
            
            print(f"[AUTO] MONTHLY report sent ({now.strftime('%B %Y')})")
            
            # Manual GC
            import gc
            await asyncio.to_thread(gc.collect)

            # Reset MONTHLY database
            print("[AUTO] Resetting MONTHLY database...")
            self.consolidation_service.db_service.reset_monthly_data()

        except Exception as e:
            print(f"[ERROR] Error sending monthly report: {e}")
    
    async def _load_message_id(self) -> Optional[int]:
        """Load saved realtime message ID."""
        if not os.path.exists(self.constants.MESSAGE_ID_FILE):
            return None
        
        try:
            import json
            with open(self.constants.MESSAGE_ID_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("id")
        except Exception:
            return None
    
    async def _save_message_id(self, msg_id: int):
        """Save realtime message ID."""
        try:
            import json
            with open(self.constants.MESSAGE_ID_FILE, "w", encoding="utf-8") as f:
                json.dump({"id": msg_id}, f)
            print("[AUTO] Message ID saved")
        except Exception as e:
            print(f"[ERROR] Error saving message ID: {e}")
