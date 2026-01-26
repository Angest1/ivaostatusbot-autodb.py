"""
Global constants for the IVAO bot.
Defines file paths, API URLs, cache durations, and chart colors."""

import os
from .settings import Settings

class Constants:
    """Global constants container."""
    
    def __init__(self):
        settings = Settings()
        
        # Base directory
        self.BASE_DIR = settings.base_dir
        
        # API URLs
        self.WHAZZUP_URL = "https://api.ivao.aero/v2/tracker/whazzup"
        
        # File paths
        self.HISTORICAL_DAILY_FILE = os.path.join(self.BASE_DIR, "history_daily.json")
        self.HISTORICAL_WEEKLY_FILE = os.path.join(self.BASE_DIR, "history_weekly.json")
        self.HISTORICAL_MONTHLY_FILE = os.path.join(self.BASE_DIR, "history_monthly.json")
        self.MESSAGE_ID_FILE = os.path.join(self.BASE_DIR, "message_id.json")

        self.LAST_SNAPSHOT_FILE = os.path.join(self.BASE_DIR, "last_snapshot.json")

        
        # All historical files for migration
        self.HISTORICAL_FILES = [
            self.HISTORICAL_DAILY_FILE,
            self.HISTORICAL_WEEKLY_FILE,
            self.HISTORICAL_MONTHLY_FILE,

            self.LAST_SNAPSHOT_FILE
        ]
        
        # Cache settings
        self.METAR_REFRESH_SECONDS = 300
        self.CHART_CACHE_DURATION_SECONDS = 60
        
        # Chart colors
        self.CHART_COLORS = {
            "realtime_atc_active": "#2FFF9A",
            "realtime_atc_active_secondary": "#A0FFD1",
            "realtime_no_atc": "#FF5250",
            "realtime_no_atc_secondary": "#FFA5A3",
            "daily_primary": "#007BFF",
            "daily_secondary": "#80DFFF",
            "weekly_primary": "#8000FF",
            "weekly_secondary": "#D580FF",
            "monthly_primary": "#AAAAAA",
            "monthly_secondary": "#FFFFFF",
        }
        
        # Update intervals (seconds)
        self.COLLECTION_INTERVAL = 60  # 1 minute
        self.REALTIME_UPDATE_INTERVAL = 10  # 10 seconds
        self.REPORT_CHECK_INTERVAL = 10  # 10 seconds
        
        # Discord embed limits
        self.DISCORD_FIELD_LIMIT = 1024
