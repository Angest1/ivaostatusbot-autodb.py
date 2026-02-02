"""
Main Discord bot class.
Coordinates all bot components and manages lifecycle."""

import asyncio
import aiohttp
import discord
from discord.ext import commands

from ..config import Settings, Constants
from ..api import IVAOClient, METARClient
from ..services import (
    DataCollector,
    ATCSessionTracker,
    ConsolidationService,
    ChartService
)
from .embed_builder import EmbedBuilder
from .tasks import BotTasks
from .commands import BotCommands

class IVAOBot(commands.Bot):
    """Main IVAO Discord bot."""
    
    def __init__(self):
        """Initialize the bot."""
        self.settings = Settings()
        self.constants = Constants()
        
        # Setup intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        super().__init__(command_prefix="!", intents=intents, max_messages=None)
        
        # HTTP session
        self.http_session: aiohttp.ClientSession = None
        
        # API clients
        self.ivao_client: IVAOClient = None
        self.metar_client: METARClient = None
        
        # Services
        self.data_collector: DataCollector = None
        self.atc_tracker: ATCSessionTracker = None
        self.consolidation_service: ConsolidationService = None
        self.chart_service: ChartService = None
        
        # Discord components
        self.embed_builder: EmbedBuilder = None
        self.bot_tasks: BotTasks = None
        self.bot_commands: BotCommands = None
        
        # Task flags
        self._tasks_started = False
    
    async def setup_hook(self):
        """Setup hook called when bot is starting."""
        # Create HTTP session
        self.http_session = aiohttp.ClientSession()
        
        # Initialize API clients
        self.ivao_client = IVAOClient(self.http_session)
        self.metar_client = METARClient(self.http_session)
        
        # Initialize services
        self.data_collector = DataCollector(self.ivao_client)
        self.atc_tracker = ATCSessionTracker()
        self.consolidation_service = ConsolidationService()
        self.chart_service = ChartService(self.consolidation_service.db_service)
        
        # Initialize Discord components
        self.embed_builder = EmbedBuilder(self.chart_service, self.atc_tracker)
        self.bot_tasks = BotTasks(
            self,
            self.data_collector,
            self.atc_tracker,
            self.consolidation_service,
            self.chart_service,
            self.metar_client,
            self.embed_builder
        )
        self.bot_commands = BotCommands(
            self,
            self.consolidation_service,
            self.chart_service,
            self.embed_builder
        )
    
    async def on_ready(self):
        """Called when bot is ready."""
        print(f"[-] BOT connected as {self.user}")
        
        # Get channel
        channel = self.get_channel(int(self.settings.discord_channel_id))
        
        if not channel:
            print("[ERROR] Could not find configured channel")
            return
        
        # Start tasks once
        if not self._tasks_started:
            self._tasks_started = True
            
            # Start collection task
            asyncio.create_task(self.bot_tasks.collection_task())
            print("[START] Collection task started")
            
            # Start realtime update task
            asyncio.create_task(self.bot_tasks.realtime_update_task(channel))
            print("[START] Realtime update task started")
            
            # Start scheduled reports task
            asyncio.create_task(self.bot_tasks.scheduled_reports_task(channel))
            print("[START] Scheduled reports task started")
    
    async def on_command_error(self, ctx: commands.Context, error):
        """Handle command errors."""
        if isinstance(error, commands.CommandNotFound):
            # Delete unknown command messages
            if ctx.message:
                try:
                    await asyncio.sleep(1)
                    await ctx.message.delete()
                except Exception:
                    pass
            return
    
    async def on_message(self, message: discord.Message):
        """Handle incoming messages."""
        # Ignore own messages
        if message.author == self.user:
            return
        
        # Ignore DMs
        if not message.guild:
            return
        
        # Ignore messages from other channels
        if message.channel.id != int(self.settings.discord_channel_id):
            return

        # Auto-delete messages in the configured channel
        try:
            await message.delete()
        except discord.errors.Forbidden:
            print(f"[WARNING] Could not delete message from {message.author}")
        except discord.errors.NotFound:
            pass
        
        # Process commands
        await self.process_commands(message)
    
    async def close(self):
        """Cleanup when bot is closing."""
        # Close HTTP session
        if self.http_session and not self.http_session.closed:
            await self.http_session.close()
        
        # Close API clients
        if self.ivao_client:
            await self.ivao_client.close()
        if self.metar_client:
            await self.metar_client.close()
        
        await super().close()

async def run_bot_with_restart():
    """Run bot with automatic restart on errors."""
    while True:
        bot = None
        try:
            bot = IVAOBot()
            settings = Settings()
            await bot.start(settings.discord_token)
        except discord.errors.LoginFailure:
            print("[ERROR] Invalid token or unauthorized. Check your configuration.")
            break
        except discord.errors.ConnectionClosed as e:
            print(f"[ERROR] Connection closed unexpectedly: {e}")
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
        finally:
            if bot:
                print("[INFO] Closing bot instance...")
                await bot.close()
        
        print("[-] Bot stopped. Restarting in 10 seconds...")
        await asyncio.sleep(10)
