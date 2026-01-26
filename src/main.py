"""Main entry point for the IVAO Discord bot."""

import sys
import os
import asyncio
import ctypes

# Add project root to sys.path to allow absolute imports from src
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config import Settings, Constants, LANGUAGES

from src.discord_bot import IVAOBot
from src.discord_bot.bot import run_bot_with_restart

def disable_quick_edit():
    """Disable Windows console quick edit mode to prevent accidental pausing."""
    if sys.platform != "win32":
        return
    
    try:
        kernel32 = ctypes.windll.kernel32
        h_stdin = kernel32.GetStdHandle(-10)
        mode = ctypes.c_uint()
        kernel32.GetConsoleMode(h_stdin, ctypes.byref(mode))
        new_mode = mode.value & ~(0x0040 | 0x0020)
        kernel32.SetConsoleMode(h_stdin, new_mode)
    except Exception:
        pass

def set_console_title():
    """Set console window title."""
    if sys.platform == "win32":
        try:
            settings = Settings()
            # Use ctypes to avoid shell injection issues with special characters like '&'
            ctypes.windll.kernel32.SetConsoleTitleW(f"IVAO {settings.country_name} Status Bot")
        except Exception:
            ctypes.windll.kernel32.SetConsoleTitleW("IVAO Status Bot")

def main():
    """Main entry point."""
    # Disable quick edit on Windows
    disable_quick_edit()
    
    # Set console title
    set_console_title()
    
    # Load settings (will exit if config is invalid)
    settings = Settings()
    constants = Constants()
    

    
    # Ensure data format consistency (REMOVED: Historical files are now in MySQL)
    # convert_all_historical_files(constants.HISTORICAL_FILES)
    
    print(f"[INIT] Starting IVAO {settings.country_name} Status Bot")
    print(f"[INIT] Country: {settings.country_name} (Prefixes: {', '.join(settings.country_prefixes)})")
    print(f"[INIT] METAR Airport: {settings.metar_airport}")
    print(f"[INIT] Timezone: {settings.timezone}")
    # Check valid language
    lang_code = settings.lang.split('-')[0].lower()
    if lang_code in LANGUAGES:
        print(f"[INIT] Language: {settings.lang} (Loaded)")
    else:
        print(f"[INIT] Language: {settings.lang} (Not found, defaulted to 'en')")
    
    # Run bot
    try:
        asyncio.run(run_bot_with_restart())
    except KeyboardInterrupt:
        print("\n[EXIT] Bot stopped by user")

if __name__ == "__main__":
    main()
