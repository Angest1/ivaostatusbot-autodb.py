"""
Bot commands.
Handles Discord bot commands for manual reports."""

import os
import asyncio
from datetime import datetime, timezone
import discord
from discord.ext import commands

from ..config import Constants
from ..services import ConsolidationService, ChartService
from .embed_builder import EmbedBuilder

class BotCommands:
    """Bot command handlers."""
    
    def __init__(
        self,
        bot: commands.Bot,
        consolidation_service: ConsolidationService,
        chart_service: ChartService,
        embed_builder: EmbedBuilder
    ):
        """Initialize bot commands."""
        self.bot = bot
        self.consolidation_service = consolidation_service
        self.chart_service = chart_service
        self.embed_builder = embed_builder
        self.constants = Constants()
        
        self._register_commands()
    
    def _register_commands(self):
        """Register all bot commands."""
        
        @self.bot.command(name="rr")
        async def cmd_realtime(ctx):
            """Force refresh realtime report."""
            try:
                await ctx.message.delete()
            except (discord.NotFound, discord.Forbidden):
                pass
            
            print(f"[CMD] REALTIME refresh requested")
            channel_id = int(self.bot.settings.discord_channel_id)
            channel = self.bot.get_channel(channel_id)
            if channel:
                await self.bot.bot_tasks._update_realtime_message(channel, force_new=True)
            else:
                print("[ERROR] Channel not found for realtime refresh")
        
        @self.bot.command(name="rd")
        async def cmd_daily(ctx):
            """Show daily report."""
            await self._send_report(ctx, "daily", "Daily Report")
            print("[CMD] Daily report sent")
        
        @self.bot.command(name="rs")
        async def cmd_weekly(ctx):
            """Show weekly report."""
            await self._send_report(ctx, "weekly", "Weekly Report")
            print("[CMD] Weekly report sent")
        
        @self.bot.command(name="rm")
        async def cmd_monthly(ctx):
            """Show monthly report."""
            await self._send_report(ctx, "monthly", "Monthly Report")
            print("[CMD] Monthly report sent")
    
    async def _send_report(self, ctx: commands.Context, mode: str, title_base: str):
        """Send a report embed."""
        # Determine file and chart type
        if mode == "daily":
            hist_file = self.constants.HISTORICAL_DAILY_FILE
            chart_file = "chart_daily.png"
            chart_type = "daily"
        elif mode == "weekly":
            hist_file = self.constants.HISTORICAL_WEEKLY_FILE
            chart_file = "chart_weekly.png"
            chart_type = "weekly"
        else:  # monthly
            hist_file = self.constants.HISTORICAL_MONTHLY_FILE
            chart_file = "chart_monthly.png"
            chart_type = "monthly"
        
        # Get statistics
        stats = self.consolidation_service.consolidate_historical(hist_file)
        
        if not stats:
            await ctx.send(f"No data available for {mode}.", delete_after=60)
            return
        
        # Build embed
        now = datetime.now(timezone.utc)
        embed = self.embed_builder.build_historical_embed(stats, now, mode, include_hour=True)
        
        # Generate chart
        file = None
        try:
            chart_path = self.chart_service.generate_chart(
                hist_file,
                chart_file,
                chart_type
            )
            
            if chart_path and os.path.exists(chart_path):
                file = discord.File(chart_path, filename=chart_file)
                embed.set_image(url=f"attachment://{chart_file}")
        except Exception as e:
            print(f"[ERROR] Error generating chart for {mode}: {e}")
        
        # Send message
        if file:
            msg = await ctx.send(embed=embed, file=file)
        else:
            msg = await ctx.send(embed=embed)
        
        # Auto-delete after 30 seconds
        asyncio.create_task(self._delete_after(msg, 30))
    
    async def _delete_after(self, msg: discord.Message, seconds: int):
        """Delete message after specified seconds."""
        await asyncio.sleep(seconds)
        try:
            await msg.delete()
        except (discord.NotFound, discord.Forbidden):
            pass
