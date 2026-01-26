# IVAO Status Bot

A modern Discord bot designed for the IVAO community. It provides real-time tracking of Pilots and ATC in any specified region, generates detailed daily, weekly, and monthly activity reports, and displays live METAR weather information. Built with Python and Discord.py, it features a modular architecture that makes it easy to configure for any country or division.

## Features

- **Real-time monitoring** - Live updates of pilots and ATCs in your region.
- **Automated reports** - Daily, weekly, and monthly activity statistics.
- **Beautiful charts** - Generated graphs visualizing traffic trends.
- **Fully Configurable** - Adaptable for any country or region via `config.json`.
- **Modern Architecture** - Clean, modular design for reliability and ease of maintenance.

## Requirements

- Python 3.10+.
- Discord Bot Token.
- Discord Channel ID.
- AVWX API Token (for real-time weather/METAR).
- MySQL 8.0+ Database.

## Installation

1. **Install dependencies:**
   - Ensure you have `discord.py`, `aiohttp`, `matplotlib`, `numpy`, `mysql-connector-python`, `psutil` installed.
   - *Note: This is not required if you use the executable (.exe).*

2. **Configure the bot:**
   - Create a `config.json` file in the root directory, if not, on first launch the bot will create one with default values *(Use the example below as a template)*.

3. **Run the bot:**
   - Use `run.bat`.
   - Or compile a .exe file using `execompiler.bat`.
   - Or use command `python -m src.main`.

4. **Database Setup:**
   - Ensure you have a MySQL database running.
   - Import the `src/database/schema.sql` file to create the necessary tables and structure.

## Auto-Configuration
To simplify setup, you can leave `COUNTRY_NAME`, `COUNTRY_FLAG`, and `LANG` to their `AUTO` values. The bot will then infer these settings directly from your `COUNTRY_PREFIX`.
*   `AUTO_COUNTRY_NAME`: Derives the full country name.
*   `AUTO_EMOJI_FLAG`: Picks the appropriate national flag.
*   `AUTO_LANG`: Selects the default language for the region.

*This is a fallback feature and manual configuration is preferred if auto-detection is incorrect.*

## Configuration

The bot uses a simple `config.json` file.

```json
{
      "DB_HOST": "localhost",
      "DB_PORT": 3306,
      "DB_NAME": "ivaostatusbot",
      "DB_USER": "DB_USER",
      "DB_PASSWORD": "DB_PASSWORD",
      "DISCORD_TOKEN": "YOUR_TOKEN_HERE",
      "DISCORD_CHANNEL_ID": 1234567890,
      "AVWX_TOKEN": "AVWX_TOKEN_HERE",
      "COUNTRY_PREFIX": "XX",
      "COUNTRY_NAME": "AUTO_COUNTRY_NAME",
      "COUNTRY_FLAG": "AUTO_EMOJI_FLAG",
      "LANG": "AUTO_LANG",
      "METAR_AIRPORT": "ICAO_CODE",
      "AIRPORT_NAME": "AIRPORT_NAME",
      "TIMEZONE": "REGION/TIMEZONE",
      "NEXT_EVENT": ""
}
```

### Hot Reloading
You can modify `config.json` while the bot is running. The bot checks for file changes every **minute** and automatically reapplies the new configuration without needing a restart.
*   **Console Logging**: The bot logs specific changes detected in the console (e.g., `> Resolved AIRPORT_NAME: Old -> New`).
*   **Effective Changes**: It intelligently detects if derived values (like Language or Country Name) have changed based on your edits.

### Configuration Parameters

| Key | Description | Example |
|-----|-------------|---------|
| `DB_HOST` | Database Host Address | `"DB_HOST"` |
| `DB_PORT` | Database Port | `DB_PORT` |
| `DB_NAME` | Database Name | `"DB_NAME"` |
| `DB_USER` | Database User | `"DB_USER"` |
| `DB_PASSWORD` | Database Password | `"DB_PASSWORD"` |
| `DISCORD_TOKEN` | Your Discord Bot Token | `"YOUR_TOKEN_HERE"` |
| `DISCORD_CHANNEL_ID` | ID of the channel where the bot will post (integer) | `1234567890` |
| `AVWX_TOKEN` | Token for AVWX API (Weather) | `"AVWX_TOKEN_HERE"` |
| `COUNTRY_PREFIX` | ICAO prefix for the country/region *Supports secondary prefixes (e.g., `SB` auto-detects `SW`, `SD`, etc.)* | `"XX"` |
| `COUNTRY_NAME` | `"AUTO_COUNTRY_NAME"` for auto detection, or custom name | `"AUTO_COUNTRY_NAME"` |
| `COUNTRY_FLAG` | `"AUTO_EMOJI_FLAG"` for auto detection, or custom emoji | `"AUTO_EMOJI_FLAG"` |
| `LANG` | `"AUTO_LANG"` Language code for auto detection, or specific code *(see [LANGUAGES.md](LANGUAGES.md))* | `"AUTO_LANG"` |
| `METAR_AIRPORT` | ICAO code for the main airport weather | `"ICAO_CODE"` |
| `AIRPORT_NAME` | Display name for the airport | `"AIRPORT_NAME"` |
| `TIMEZONE` | Local timezone string | `"REGION/TIMEZONE"` |
| `NEXT_EVENT` | Text for the "Next Event" footer state. If empty, the state is skipped. | `""` |

*Search for your timezone before launching the bot in [here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).*

### Multi-Country Divisions (MCD) Support
The bot natively supports IVAO Multi-Country Divisions. You can configure `COUNTRY_PREFIX` to configure for MCD:

*   **Explicit MCD Code**: To track a full Multi-Country Division, you must use its specific code (e.g., `XT` for South Caucasus).
*   **Supported MCDs List**:

| Code | Region Name | Prefixes (Auto-Tracked) |
| :--- | :--- | :--- |
| **XT** | South Caucasus | UB, UD, UG |
| **XM** | Middle East | OJ, OR, OS |
| **XY** | Malaysia & Singapore | WB, WM, WS |
| **XR** | Eastern Europe & N. Asia | UA, UE, UH, UI, UL, UM, UN, UR, US, UT, UU, UW |
| **XE** | East Asia | RC, RK, RP, VH, VV, ZK |
| **XS** | Central America | MH, MP, MR, MS, MG, MN, MZ |
| **XB** | BELUX | EB, EL |
| **XC** | Dutch Caribbean | TN |
| **XG** | GCC Region | OK, OE, OB, OT, OM, OO |
| **XN** | Nordic Region | EK, EF, BI, EN, ES |
| **XO** | Oceanic Region | NF, NV, NW, AY, AG, AN, NG, NI, NS, NT, PL |
| **XZ** | Southern Africa | FA, FB, FD, FL, FQ, FV, FW, FX, FY |
| **XU** | UK & Ireland | EG, EI |
| **IO** | Indian Ocean | FM, FI, FS |
*   *Note: Using a member country's prefix (e.g., `UB`) will ONLY track that specific country, not the whole group.*

### Smart Prefix Grouping (Colonial/Regional Support)

For countries with overseas territories or specific regional groupings, the bot distinguishes between the "Metropolitan/Local" code and the "Global/Group" code:

| Country | Code | Behavior | Includes |
| :--- | :--- | :--- | :--- |
| **Spain** | **LE** | **Group** | **LE** (Mainland) + **GC** (Canaries) + **GE** (Ceuta/Melilla) |
| **Malaysia** | **WM** | **Group** | **WM** (Mainland) + **WB** (Borneo) |
| **France** | **FR** | **Group** | **LF** (Metropolitan) + **TF, SO, NT, NW** (Overseas) |
| | **LF** | Local | **LF** (Metropolitan Only) |
| **Netherlands**| **NL** | **Group** | **EH** (Mainland) + **TN** (Caribbean) |
| | **EH** | Local | **EH** (Mainland Only) |
| **Denmark** | **DK** | **Group** | **EK** (Mainland) + **BG** (Greenland) |
| | **EK** | Local | **EK** (Mainland Only) |
| **USA** | **USA** | **Group** | **K** (Mainland) + **P** (Alaska/Hawaii/Pacific) + **TJ** (Puerto Rico) |
| | **K** | Local | **K** (Mainland Only) |

## Functionality

### Realtime Monitoring
The bot provides a continuously updating "Live Status" embed in the configured Discord channel.
- **Traffic Overview**: Displays the current number of Pilots and ATCs active in the configured region.
- **Active Lists**: Lists specific callsigns of Pilots and ATCs currently online.
- **Weather (METAR)**: Shows the raw METAR string for the configured main airport.
- **Smart Updates**: The message edits itself to avoid spamming the channel, providing a dashboard-like experience.
- **Top 5 Airports**: Rotating footer displays the top 5 airports by activity (Departures + Arrivals).
- **Event Highlights**: Configurable `NEXT_EVENT` footer that displays upcoming events with a localized label (e.g., "Next Event: ...").

### Automated Reports
Generates statistics based on collected data.

- **Daily Report**: Summary of the day's total connections and hours.
- **Weekly Report**: A review of the week's activity with a traffic graph.
- **Monthly Report**: Aggregated statistics for the entire month.

*Reports are sent daily at 23:59 UTC.*

### Database Optimization
The bot includes an automated system to keep the database efficient and lightweight.
- **Partitioning**: Data is split into `daily`, `weekly`, and `monthly` tables.
- **Auto-Cleanup**:
    - **Daily Data**: Automatically resets daily data (Rolling Window).
    - **Weekly Data**: Tables are reset (truncated) every Sunday after the weekly report.
    - **Monthly Data**: Tables are reset (truncated) on the 1st of each month after the monthly report.

## Commands

- `!rr` - **Refresh Realtime**: Force an immediate update of the live status embed.
- `!rd` - **Report Daily**: Generate and send a daily statistics report.
- `!rs` - **Report Weekly**: Generate and send a weekly statistics report.
- `!rm` - **Report Monthly**: Generate and send a monthly statistics report.

*!rd !rs !rm commands reports only generates messages for 30 seconds before autodelete.*

## Architecture

The project follows a clean, modular structure:

```
src/
├── api/             # API Clients (IVAO, METAR)
├── config/          # Configuration management
├── discord_bot/     # Discord interaction layer
├── models/          # Data models (Pilot, ATC, Snapshot, Statistics)
├── services/        # Core business logic
├── utils/           # Utilities (File ops, Time, Text)
└── main.py          # Application entry point
```


By @746048 in collab with Brasil, Colombia, USA, Morocco and Chile divisions for the IVAO Community ✈️.
