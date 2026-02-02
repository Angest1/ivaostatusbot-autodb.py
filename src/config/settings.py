"""
Configuration loader and validator.
Handles loading settings from config.json and providing singleton access."""

import json
import os
import sys
from typing import Optional

class Settings:
    """Singleton configuration manager."""
    
    _instance: Optional['Settings'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self._initialized = True
        self._last_mtime = 0
        self._config_cache = {}
        self._load_config()

    @property
    def mcd_config(self):
        """Configuration for Multi-Country Divisions."""
        return {
            # --- Priority Auto-Grouping MCDs (Defined by User detailed list) ---
            "XT": { "prefixes": ["UB", "UD", "UG"], "name": "South Caucasus", "flag": "🌍", "lang": "en", "autoSelect": True },
            "XM": { "prefixes": ["OJ", "OR", "OS"], "name": "Middle East", "flag": "🌏", "lang": "ar", "autoSelect": True },
            "XY": { "prefixes": ["WB", "WM", "WS"], "name": "Malaysia & Singapore", "flag": "🌏", "lang": "en", "autoSelect": True },
            "XR": { 
                "prefixes": ["UA", "UE", "UH", "UI", "UL", "UM", "UN", "UR", "US", "UT", "UU", "UW"], 
                "name": "Eastern Europe & Northern Asia", "flag": "🌏", "lang": "ru", "autoSelect": True 
            },
            "XE": { "prefixes": ["RC", "RK", "RP", "VH", "VV", "ZK"], "name": "East Asia", "flag": "🌏", "lang": "en", "autoSelect": True },
            "XS": { "prefixes": ["MH", "MP", "MR", "MS", "MG", "MN", "MZ"], "name": "Central America", "flag": "🌎", "lang": "es", "autoSelect": True },
            "WM": { "prefixes": ["WM", "WB"], "name": "Malaysia", "flag": "🇲🇾", "lang": "en", "autoSelect": True },
            
            # --- Other Active MCDS / Regions ---
            "XB": { "prefixes": ["EB", "EL"], "name": "BELUX Region", "flag": "🌍", "lang": "fr", "autoSelect": True },
            "XC": { "prefixes": ["TN"], "name": "Dutch Caribbean", "flag": "🌎", "lang": "nl", "autoSelect": True },
            "XG": { "prefixes": ["OK", "OE", "OB", "OT", "OM", "OO"], "name": "GCC Region", "flag": "🌏", "lang": "ar", "autoSelect": True },
            "XN": { "prefixes": ["EK", "EF", "BI", "EN", "ES"], "name": "Nordic Region", "flag": "🌍", "lang": "en", "autoSelect": True },
            "XO": { "prefixes": ["NF", "NV", "NW", "AY", "AG", "AN", "NG", "NI", "NS", "NT", "PL"], "name": "Oceanic Region", "flag": "🌏", "lang": "en", "autoSelect": True },
            "XZ": { "prefixes": ["FA", "FB", "FD", "FL", "FQ", "FV", "FW", "FX", "FY"], "name": "Southern Africa", "flag": "🌍", "lang": "en", "autoSelect": True },
            "XU": { "prefixes": ["EG", "EI"], "name": "United Kingdom & Ireland", "flag": "🌍", "lang": "en", "autoSelect": True },

            # --- Legacy / Specific Definitions ---
            "MACA": { "prefixes": ["MZ", "MR", "MS", "MG", "MH", "MN"], "name": "Multi-Country Central America", "flag": "🌎", "lang": "es", "autoSelect": True }, # Kept key for manual manual config
            "IO":   { "prefixes": ["FM", "FI", "FS"], "name": "Indian Ocean", "flag": "🌍", "lang": "en", "autoSelect": True },
            
            # --- Standard Divisions with Multiple Prefixes ---
            "SB": { "prefixes": ["SB", "SD", "SI", "SJ", "SN", "SS", "SW"], "name": "Brasil", "flag": "🇧🇷", "lang": "pt", "autoSelect": True },
            "WA": { "prefixes": ["WA", "WI", "WR", "WQ"], "name": "Indonesia", "flag": "🇮🇩", "lang": "id", "autoSelect": True },
            "VI": { "prefixes": ["VI", "VA", "VE", "VO"], "name": "India", "flag": "🇮🇳", "lang": "en", "autoSelect": True },
            "Z":  { "prefixes": ["ZB", "ZG", "ZH", "ZL", "ZP", "ZS", "ZU", "ZW", "ZY"], "name": "China", "flag": "🇨🇳", "lang": "zh", "autoSelect": True },
            "RJ": { "prefixes": ["RJ", "RO"], "name": "Japan", "flag": "🇯🇵", "lang": "jp", "autoSelect": True },
            "ED": { "prefixes": ["ED", "ET"], "name": "Germany", "flag": "🇩🇪", "lang": "de", "autoSelect": True },
            "SC": { "prefixes": ["SC", "SH"], "name": "Chile", "flag": "🇨🇱", "lang": "es", "autoSelect": True },
            "GM": { "prefixes": ["GM"], "name": "Morocco", "flag": "🇲🇦", "lang": "ar", "autoSelect": True },
            "LE": { "prefixes": ["LE", "GC", "GE"], "name": "España", "flag": "🇪🇸", "lang": "es", "autoSelect": True },

            # --- Colonial / Implicit MCDs ---
            "FR": { "prefixes": ["LF", "TF", "SO", "NT", "NW"], "name": "France", "flag": "🇫🇷", "lang": "fr", "autoSelect": True },
            "LF": { "prefixes": ["LF"], "name": "France", "flag": "🇫🇷", "lang": "fr", "autoSelect": True },
            "NL": { "prefixes": ["EH", "TN"], "name": "Netherlands & Caribbean", "flag": "🇳🇱", "lang": "nl", "autoSelect": True },
            "EH": { "prefixes": ["EH"], "name": "Netherlands", "flag": "🇳🇱", "lang": "nl", "autoSelect": True },
            "DK": { "prefixes": ["EK", "BG"], "name": "Denmark & Greenland", "flag": "🇩🇰", "lang": "en", "autoSelect": True },
            "EK": { "prefixes": ["EK"], "name": "Denmark", "flag": "🇩🇰", "lang": "en", "autoSelect": True },
            "USA": { "prefixes": ["K", "P", "TJ"], "name": "USA", "flag": "🇺🇸", "lang": "en", "autoSelect": True },
            "K":  { "prefixes": ["K"], "name": "USA", "flag": "🇺🇸", "lang": "en", "autoSelect": True },
        }
    
    def _get_base_dir(self) -> str:
        """Get the base directory for the application."""
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    def _load_config(self):
        """Load configuration from config.json."""
        self.base_dir = self._get_base_dir()
        self.config_file = os.path.join(self.base_dir, "config.json")
        
        # Create default config if it doesn't exist
        if not os.path.exists(self.config_file):
            self._create_default_config()
            print(f"[INFO] {self.config_file} created. Please fill in the values and restart the bot.")
            input("[ENTER] Press Enter to exit...")
            sys.exit(1)
        
        # Update modification time
        try:
            self._last_mtime = os.path.getmtime(self.config_file)
        except Exception:
            pass
        
        # Load config
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            print(f"[ERROR] Error reading {self.config_file}: {e}")
            input("[ENTER] Press Enter to exit...")
            sys.exit(1)
        
        self._apply_config(config)
    
    def _create_default_config(self):
        """Create a default config.json file."""
        default_config = {
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
            "NEXT_EVENT": "",
            "SSH_ENABLED": False,
            "SSH_HOST": "REMOTE_IP",
            "SSH_PORT": 22,
            "SSH_USER": "ubuntu",
            "SSH_KEY_PATH": "path/to/key.pem",
            "SSH_PASSWORD": ""
        }
        
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[ERROR] Error creating {self.config_file}: {e}")
            input("[ENTER] Press Enter to exit...")
            sys.exit(1)

    def check_and_reload(self) -> bool:
        """Check for config file updates and reload if changed."""
        try:
            current_mtime = os.path.getmtime(self.config_file)
            if current_mtime > self._last_mtime:
                # File changed, try to reload
                
                try:
                    with open(self.config_file, "r", encoding="utf-8") as f:
                        new_config = json.load(f)
                    
                    # Detect changes
                    changes = []
                    for key, value in new_config.items():
                        old_value = self._config_cache.get(key)
                        if old_value != value:
                            changes.append(f"{key}: {old_value} -> {value}")
                    
                    # Check for removed keys
                    for key in self._config_cache:
                        if key not in new_config:
                            changes.append(f"{key}: {self._config_cache[key]} -> [REMOVED]")

                    if not changes:
                        # Even if mtime changed, content might be same
                        self._last_mtime = current_mtime
                        return False

                    print(f"[CONFIG] Configuration change detected.")
                    for change in changes:
                        print(f"  > {change}")

                    # Capture old state of derived variables
                    old_state = {
                        "lang": self.lang,
                        "country_name": self.country_name,
                        "metar_airport": self.metar_airport,
                        "airport_name": self.airport_name,
                        "timezone": self.timezone,
                        "country_prefix": self.country_prefix
                    }

                    if self._apply_config(new_config, fatal_errors=False):
                        self._last_mtime = current_mtime
                        
                        # Check effective changes in derived variables
                        new_state = {
                            "lang": self.lang,
                            "country_name": self.country_name,
                            "metar_airport": self.metar_airport,
                            "airport_name": self.airport_name,
                            "timezone": self.timezone,
                            "country_prefix": self.country_prefix
                        }
                        
                        for key, old_val in old_state.items():
                            new_val = new_state.get(key)
                            if old_val != new_val:
                                print(f"  > Resolved {key}: {old_val} -> {new_val}")
                            
                        print("[CONFIG] Configuration reloaded successfully.")
                        return True
                    else:
                        print("[CONFIG] Reload failed due to missing fields. Retaining old config.")
                except json.JSONDecodeError as e:
                    print(f"[CONFIG] Reload failed: Invalid JSON format: {e}")
                except Exception as e:
                    print(f"[CONFIG] Reload failed: {e}")
        except Exception:
            pass
        
        return False

    def _apply_config(self, config, fatal_errors=True):
        """Apply configuration from dictionary."""
        # Required fields
        self.discord_token = config.get("DISCORD_TOKEN")
        self.discord_channel_id = config.get("DISCORD_CHANNEL_ID")
        
        if not self.discord_token or not self.discord_channel_id:
            msg = f"[ERROR] {self.config_file} is missing required fields (DISCORD_TOKEN, DISCORD_CHANNEL_ID)."
            print(msg)
            if fatal_errors:
                input("[ENTER] Press Enter to exit...")
                sys.exit(1)
            return False
            
        # Optional fields with defaults
        self.avwx_token = config.get("AVWX_TOKEN", "")
        self.country_prefix = config.get("COUNTRY_PREFIX", "SC")
        self.country_prefixes = self._get_related_prefixes(self.country_prefix)
        
        # Country Name auto-detection
        manual_name = config.get("COUNTRY_NAME")
        if not manual_name or manual_name == "AUTO_COUNTRY_NAME":
             self.country_name = self._get_country_name(self.country_prefix)
        else:
             self.country_name = manual_name
        
        # Flag auto-detection
        manual_flag = config.get("COUNTRY_FLAG")
        if not manual_flag or manual_flag == "AUTO_EMOJI_FLAG":
             self.country_flag = self._get_flag(self.country_prefix)
        else:
             self.country_flag = manual_flag
        self.metar_airport = config.get("METAR_AIRPORT", config.get("METAR_STATION", "SCEL"))
        self.airport_name = config.get("AIRPORT_NAME", "Airport")
        self.timezone = config.get("TIMEZONE", "America/Santiago")
        self.lang = config.get("LANG", "AUTO_LANG")
        if self.lang:
            self.lang = self.lang.strip()
            
        self.next_event = config.get("NEXT_EVENT", "")

        # World Emoji Auto-Detection
        self.world_emoji = self._get_world_emoji(self.country_prefix)
        self.world_emoji_foreign = self._get_foreign_world_emoji(self.world_emoji)
        
        # Database Configuration
        self.db_host = config.get("DB_HOST")
        self.db_port = config.get("DB_PORT")
        self.db_name = config.get("DB_NAME")

        # Fallback for backward compatibility or ease of setup
        # If specific names aren't provided, try to derive them or fail later?
        # Let's enforce them or default to None and let validation catch it if needed.
        # Ideally, we require them.
        self.db_user = config.get("DB_USER")
        self.db_password = config.get("DB_PASSWORD")
        self.db_pool_name = "ivao_bot_pool"
        self.db_pool_size = 5

        # SSH Configuration
        self.ssh_enabled = config.get("SSH_ENABLED", False)
        self.ssh_host = config.get("SSH_HOST")
        self.ssh_port = config.get("SSH_PORT", 22)
        self.ssh_user = config.get("SSH_USER")
        self.ssh_password = config.get("SSH_PASSWORD")
        self.ssh_key_path = config.get("SSH_KEY_PATH")

        # Validate Database Config
        # We check for at least one valid DB configuration or all three depending on strictness.
        # The plan implies we need all three.
        # Note: If SSH is enabled, DB_HOST should likely be 127.0.0.1 (or localhost) in config, 
        # but we don't strictly enforce that here to allow flexibility.
        if not all([self.db_host, self.db_port, self.db_name, self.db_user, self.db_password]):
            msg = f"[ERROR] {self.config_file} is missing required Database fields (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)."
            print(msg)
            if fatal_errors:
                input("[ENTER] Press Enter to exit...")
                sys.exit(1)
            return False
            
        # Convert port to int after validation
        try:
            self.db_port = int(self.db_port)
        except ValueError:
             print(f"[ERROR] DB_PORT must be a number.")
             if fatal_errors:
                sys.exit(1)
             return False
        
        # Auto-detect language if auto
        if self.lang == "AUTO_LANG":
            prefix = self.country_prefix.upper()
            
            # Mapping of ICAO prefixes (first 2 letters) to language codes
            prefix_map = {
                # Portuguese
                "SB": "pt", "SD": "pt", "SI": "pt", "SJ": "pt", "SN": "pt", "SS": "pt", "SW": "pt", # Brasil
                "LP": "pt", # Portugal
                "FQ": "pt", "FN": "pt", "GV": "pt", "GG": "pt", # Lusophone Africa
                
                # Spanish
                "SC": "es", "SA": "es", "SL": "es", "SK": "es", "SE": "es", "SP": "es", "SV": "es", 
                "SG": "es", "SU": "es", # South America
                "MM": "es", "MH": "es", "MP": "es", "MR": "es", "MS": "es", "MG": "es", "MN": "es", 
                "MD": "es", "MU": "es", # Central/North America/Caribbean
                "LE": "es", "GC": "es", "GE": "es", # Spain
                
                # French
                "LF": "fr", # France
                "TF": "fr", # French Antilles
                "EB": "fr", # Belgium
                
                # German
                "ED": "de", "ET": "de", # Germany
                "LO": "de", # Austria
                "LS": "de", # Switzerland
                
                # Italian
                "LI": "it",
                
                # Dutch
                "EH": "nl",
                
                # Turkish
                "LT": "tr",
                
                # Polish
                "EP": "pl",
                
                # Indonesian
                "WA": "id", "WI": "id", "WR": "id",
                
                # English
                "EG": "en", "EGG": "en", # UK
                "EI": "en", # Ireland
                "K":  "en", # USA
                "C":  "en", # Canada
                "Y":  "en", # Australia
                "NZ": "en", # New Zealand
                "FA": "en", # South Africa
                
                # Greek
                "LG": "el",

                # Romanian
                "LR": "ro",

                # Hungarian
                "LH": "hu",

                # Czech
                "LK": "cs",

                # Ukrainian
                "UK": "uk",

                # Arabic (Middle East & North Africa)
                "HE": "ar", # Egypt
                "OB": "ar", # Bahrain
                "OE": "ar", # Saudi Arabia
                "OJ": "ar", # Jordan
                "OK": "ar", # Kuwait
                "OL": "ar", # Lebanon
                "OM": "ar", # UAE
                "OO": "ar", # Oman
                "OT": "ar", # Qatar
                "OY": "ar", # Yemen
                "OR": "ar", # Iraq
                "OS": "ar", # Syria
                "HL": "ar", # Libya
                "DT": "ar", # Tunisia
                "DA": "ar", # Algeria
                "DA": "ar", # Algeria
                "GM": "ar", # Morocco

                # Chinese
                "Z": "zh",  # Mainland China
                "RC": "zh", # Taiwan
                "VH": "zh", # Hong Kong
                "VM": "zh", # Macau
            }
            
            # 1. Check strict 2-letter match
            if prefix[:2] in prefix_map:
                self.lang = prefix_map[prefix[:2]]
            # 2. Check 1-letter match (e.g. K, C, Y, Z)
            elif prefix[:1] in prefix_map:
                self.lang = prefix_map[prefix[:1]]
            # 4. Check MCDs (Moved UP to prioritize specific configs like USA/K)
            elif prefix in self.mcd_config:
                self.lang = self.mcd_config[prefix]["lang"]
            elif prefix.startswith("U") and not prefix.startswith("UK"):
                self.lang = "ru"
            # 5. Default to English
            else:
                self.lang = "en"
        else:
            # Normalize manually set language
             self.lang = self.lang.lower()
        
        # Update cache
        self._config_cache = config
        return True

    def _get_related_prefixes(self, prefix: str) -> list[str]:
        """
        Get all related prefixes for a country based on its primary prefix.
        """
        prefix = prefix.upper()
        p2 = prefix[:2]
        
        # Map of primary prefix -> list of all prefixes
        # This handles countries with multiple ICAO prefixes
        # Migrated to self.mcd_config properly
        pass
        
        # 1. Check exact match in MCD config (e.g. "MACA")
        if prefix in self.mcd_config:
            return self.mcd_config[prefix]["prefixes"]
            
        # 2. Check 2-letter Code in MCD config keys
        p2 = prefix[:2]
        if p2 in self.mcd_config:
             return self.mcd_config[p2]["prefixes"]

        # 3. Check 1-letter Code in MCD config keys
        p1 = prefix[:1]
        if p1 in self.mcd_config:
             return self.mcd_config[p1]["prefixes"]
        pass

        # 4. Check for custom comma-separated list
        if "," in prefix:
            return [p.strip().upper() for p in prefix.split(",") if p.strip()]

        # Default: just the configured prefix
        return [prefix]

    def _get_flag(self, prefix: str) -> str:
        """
        Get flag emoji based on ICAO prefix.
        """
        prefix = prefix.upper()
        p2 = prefix[:2]
        p1 = prefix[:1]
        
        # Mapping of ICAO prefixes to Flag Emojis
        flag_map = {
            # Europe (Northern)
            "EF": "🇫🇮", # Finland
            "EE": "🇪🇪", # Estonia
            "ES": "🇸🇪", # Sweden
            "EN": "🇳🇴", # Norway
            "EK": "🇩🇰", # Denmark
            "EV": "🇱🇻", # Latvia
            "EY": "🇱🇹", # Lithuania
            "BI": "🇮🇸", # Iceland

            # Europe (Western/Central)
            "EG": "🇬🇧", # UK
            "EI": "🇮🇪", # Ireland
            "EH": "🇳🇱", # Netherlands
            "EB": "🇧🇪", # Belgium
            "EL": "🇱🇺", # Luxembourg
            "LF": "🇫🇷", # France
            "ED": "🇩🇪", "ET": "🇩🇪", # Germany
            "LO": "🇦🇹", # Austria
            "LS": "🇨🇭", # Switzerland
            "LI": "🇮🇹", # Italy
            "LE": "🇪🇸", # Spain
            "LP": "🇵🇹", # Portugal
            
            # Europe (Eastern/Southern)
            "EP": "🇵🇱", # Poland
            "LK": "🇨🇿", # Czechia
            "LZ": "🇸🇰", # Slovakia
            "LH": "🇭🇺", # Hungary
            "LJ": "🇸🇮", # Slovenia
            "LD": "🇭🇷", # Croatia
            "LQ": "🇧🇦", # Bosnia
            "LY": "🇷🇸", # Serbia (LYBE) / Montenegro (LYPG)
            "LW": "🇲🇰", # North Macedonia
            "LA": "🇦🇱", # Albania
            "LR": "🇷🇴", # Romania
            "LB": "🇧🇬", # Bulgaria
            "LG": "🇬🇷", # Greece
            "LC": "🇨🇾", # Cyprus
            "LT": "🇹🇷", # Turkey
            "LU": "🇲🇩", # Moldova
            "UM": "🇧🇾", # Belarus
            "UK": "🇺🇦", # Ukraine
            
            # North America
            "MM": "🇲🇽", # Mexico
            
            # Central America / Caribbean
            "MY": "🇧🇸", # Bahamas
            "MU": "🇨🇺", # Cuba
            "MK": "🇯🇲", # Jamaica
            "MD": "🇩🇴", # Dominican Republic
            "MT": "🇭🇹", # Haiti
            "TJ": "🇵🇷", # Puerto Rico (US)
            "MW": "🇰🇾", # Cayman Islands
            "MG": "🇬🇹", # Guatemala
            "MH": "🇭🇳", # Honduras
            "MS": "🇸🇻", # El Salvador
            "MN": "🇳🇮", # Nicaragua
            "MR": "🇨🇷", # Costa Rica
            "MP": "🇵🇦", # Panama
            "MB": "🇹🇨", # Turks & Caicos
            "MZ": "🇧🇿", # Belize

            # South America
            "SK": "🇨🇴", # Colombia
            "SV": "🇻🇪", # Venezuela
            "SY": "🇬🇾", # Guyana
            "SM": "🇸🇷", # Suriname
            "SO": "🇬🇫", # French Guiana
            "SE": "🇪🇨", # Ecuador
            "SP": "🇵🇪", # Peru
            "SB": "🇧🇷", "SD": "🇧🇷", "SI": "🇧🇷", "SJ": "🇧🇷", "SN": "🇧🇷", "SS": "🇧🇷", "SW": "🇧🇷", # Brasil
            "SL": "🇧🇴", # Bolivia
            "SG": "🇵🇾", # Paraguay
            "SC": "🇨🇱", # Chile
            "SA": "🇦🇷", # Argentina
            "SU": "🇺🇾", # Uruguay
            
            # Asia
            "LZ": "🇸🇰", # Slovakia
            "LL": "🇮🇱", # Israel
            "OJ": "🇯🇴", # Jordan
            "OS": "🇸🇾", # Syria
            "OL": "🇱🇧", # Lebanon
            "OR": "🇮🇶", # Iraq
            "OI": "🇮🇷", # Iran
            "OK": "🇰🇼", # Kuwait
            "OB": "🇧🇭", # Bahrain
            "OT": "🇶🇦", # Qatar
            "OE": "🇸🇦", # Saudi Arabia
            "OM": "🇦🇪", # UAE
            "OO": "🇴🇲", # Oman
            "OY": "🇾🇪", # Yemen
            
            "OA": "🇦🇫", # Afghanistan
            "OP": "🇵🇰", # Pakistan
            "VI": "🇮🇳", "VA": "🇮🇳", "VE": "🇮🇳", "VO": "🇮🇳", # India
            "VC": "🇱🇰", # Sri Lanka
            "VR": "🇲🇻", # Maldives
            "VG": "🇧🇩", # Bangladesh
            "VN": "🇳🇵", # Nepal
            "VQ": "🇧🇹", # Bhutan
            
            "VY": "🇲🇲", # Myanmar
            "VT": "🇹🇭", # Thailand
            "VL": "🇱🇦", # Laos
            "VD": "🇰🇭", # Cambodia
            "VV": "🇻🇳", # Vietnam
            "WM": "🇲🇾", # Malaysia
            "WS": "🇸🇬", # Singapore
            "WB": "🇧🇳", # Brunei
            "WP": "🇹🇱", # Timor-Leste
            "WI": "🇮🇩", "WA": "🇮🇩", "WR": "🇮🇩", "WQ": "🇮🇩", # Indonesia
            "RP": "🇵🇭", # Philippines
            
            "RC": "🇹🇼", # Taiwan
            "RJ": "🇯🇵", "RO": "🇯🇵", # Japan
            "RK": "🇰🇷", # South Korea
            "ZK": "🇰🇵", # North Korea
            "ZM": "🇲🇳", # Mongolia
            
            # Africa
            "GM": "🇲🇦", # Morocco
            "DA": "🇩🇿", # Algeria
            "DT": "🇹🇳", # Tunisia
            "HL": "🇱🇾", # Libya
            "HE": "🇪🇬", # Egypt
            "GQ": "🇲🇷", # Mauritania
            "GO": "🇸🇳", # Senegal
            "GB": "🇬🇲", # Gambia
            "GU": "🇬🇳", # Guinea
            "GF": "🇸🇱", # Sierra Leone
            "GL": "🇱🇷", # Liberia
            "DI": "🇨🇮", # Cote d'Ivoire
            "DG": "🇬🇭", # Ghana
            "DX": "🇹🇬", # Togo
            "DB": "🇧🇯", # Benin
            "DN": "🇳🇬", # Nigeria
            "DB": "🇧🇯", # Benin
            "DF": "🇧🇫", # Burkina Faso
            "DR": "🇳🇪", # Niger
            "FT": "🇹🇩", # Chad
            "HK": "🇰🇪", # Kenya
            "HU": "🇺🇬", # Uganda
            "HT": "🇹🇿", # Tanzania
            "HR": "🇷🇼", # Rwanda
            "HB": "🇧🇮", # Burundi
            "HC": "🇸🇴", # Somalia
            "HA": "🇪🇹", # Ethiopia
            "HSS": "🇸🇩", "HSO": "🇸🇩", # Sudan
            "FK": "🇨🇲", # Cameroon
            "FE": "🇨🇫", # CAR
            "FO": "🇬🇦", # Gabon
            "FC": "🇨🇬", # Congo
            "FZ": "🇨🇩", # DRC
            "FG": "🇬🇶", # Equatorial Guinea
            "FN": "🇦🇴", # Angola
            "FB": "🇧🇼", # Botswana
            "FL": "🇿🇲", # Zambia
            "FV": "🇿🇼", # Zimbabwe
            "FW": "🇲🇼", # Malawi
            "FQ": "🇲🇿", # Mozambique
            "FA": "🇿🇦", # South Africa
            "FX": "🇱🇸", # Lesotho
            "FD": "🇸🇿", # Eswatini
            "FM": "🇲🇬", # Madagascar
            "FIM": "🇲🇺", # Mauritius
            "FS": "🇸🇨", # Seychelles
            
            # Oceania
            "NZ": "🇳🇿", # New Zealand
            "AY": "🇵🇬", # Papua New Guinea
            "AG": "🇸🇧", # Solomon Islands
            "AN": "🇳🇷", # Nauru
            "NF": "🇫🇯", # Fiji
            "NV": "🇻🇺", # Vanuatu
            "NW": "🇳🇨", # New Caledonia
            "NG": "🇰🇮", # Kiribati
            "NI": "🇳🇺", # Niue
            "NL": "🇼🇫", # Wallis and Futuna
            "NS": "🇼🇸", # Samoa
            "NT": "🇵🇫", # French Polynesia
            "PL": "🇰🇮", # Line Islands (Kiribati)
            
            # Special/Others
            "TX": "🇧🇲", # Bermuda
            "TF": "🇬🇵", # Guadaloupe/Martinique
            "TFF": "🇲🇶", # Martinique
            "TFG": "🇬🇵", # Guadeloupe
            "TN": "🇦🇼", # Aruba
            "TU": "🇻🇬", # BVI
        }
        
        # Refined checks
        if p2 in flag_map:
            return flag_map[p2]
            
        # 1-char matches
        if p1 == "K": return "🇺🇸" # USA
        if p1 == "C": return "🇨🇦" # Canada
        if p1 == "Y": return "🇦🇺" # Australia
        if p1 == "Z": return "🇨🇳" # China
        
        if prefix in self.mcd_config:
            return self.mcd_config[prefix]["flag"]

        # Check MCD AutoSelect Reverse Lookup
        for key, config in self.mcd_config.items():
            if config.get("autoSelect", True):
                if p2 in config["prefixes"] or p1 in config["prefixes"]:
                    return config["flag"]

        # Russia Special Case
        if p1 == "U" and p2 != "UK":
            return "🇷🇺"

        return "🏳️" # Default/Unknown

    def _get_world_emoji(self, prefix: str) -> str:
        """
        Get world emoji based on prefix region.
        """
        prefix = prefix.upper()
        p1 = prefix[:1]
        
        # MCD Override - Use the globe defined in MCD config if available and it is a globe
        if prefix in self.mcd_config:
            flag = self.mcd_config[prefix]["flag"]
            if flag in ["🌍", "🌎", "🌏"]:
                return flag

        # Americas (North, Central, South, Caribbean)
        # M (Central/Mexico), S (South), K (USA), C (Canada), T (Caribbean)
        if p1 in ["M", "S", "K", "C", "T"]:
            return "🌎"
            
        # Asia / Oceania / Middle East
        # R (East Asia), V (South Asia), Z (China), A (Pacific), Y (Australia), 
        # W (SE Asia), P (North Pacific), O (Middle East)
        if p1 in ["R", "V", "Z", "A", "Y", "W", "P", "O"]:
            return "🌏"
            
        return "🌍"

    def _get_foreign_world_emoji(self, local_emoji: str) -> str:
        """
        Get a different world emoji for international departures.
        """
        if local_emoji == "🌎": # Americas
            return "🌍" # Europe/Africa
        if local_emoji == "🌏": # Asia/Oceania
            return "🌍" # Europe/Africa
            
        # Default (Europe/Africa 🌍) -> Americas 🌎
        return "🌎"

    def _get_country_name(self, prefix: str) -> str:
        """
        Get country name based on ICAO prefix.
        """
        prefix = prefix.upper()
        p2 = prefix[:2]
        p1 = prefix[:1]
        
        # Mapping of ICAO prefixes to Country Names
        name_map = {
            # Europe (Northern)
            "EF": "Finland",
            "EE": "Estonia",
            "ES": "Sweden",
            "EN": "Norway",
            "EK": "Denmark",
            "EV": "Latvia",
            "EY": "Lithuania",
            "BI": "Iceland",

            # Europe (Western/Central)
            "EG": "United Kingdom",
            "EI": "Ireland",
            "EH": "Netherlands",
            "EB": "Belgium",
            "EL": "Luxembourg",
            "LF": "France",
            "ED": "Germany", "ET": "Germany",
            "LO": "Austria",
            "LS": "Switzerland",
            "LI": "Italy",
            "LE": "España",
            "LP": "Portugal",
            
            # Europe (Eastern/Southern)
            "EP": "Poland",
            "LK": "Czechia",
            "LZ": "Slovakia",
            "LH": "Hungary",
            "LJ": "Slovenia",
            "LD": "Croatia",
            "LQ": "Bosnia and Herzegovina",
            "LY": "Serbia", # / Montenegro
            "LW": "North Macedonia",
            "LA": "Albania",
            "LR": "Romania",
            "LB": "Bulgaria",
            "LG": "Greece",
            "LC": "Cyprus",
            "LT": "Turkey",
            "LU": "Moldova",
            "UM": "Belarus",
            "UK": "Ukraine",
            
            # North America
            "MM": "Mexico",
            
            # Central America / Caribbean
            "MY": "Bahamas",
            "MU": "Cuba",
            "MK": "Jamaica",
            "MD": "Dominican Republic",
            "MT": "Haiti",
            "TJ": "Puerto Rico",
            "MW": "Cayman Islands",
            "MG": "Guatemala",
            "MH": "Honduras",
            "MS": "El Salvador",
            "MN": "Nicaragua",
            "MR": "Costa Rica",
            "MP": "Panama",
            "MB": "Turks & Caicos",
            "MZ": "Belize",

            # South America
            "SK": "Colombia",
            "SV": "Venezuela",
            "SY": "Guyana",
            "SM": "Suriname",
            "SO": "French Guiana",
            "SE": "Ecuador",
            "SP": "Peru",
            "SB": "Brasil", "SD": "Brasil", "SI": "Brasil", "SJ": "Brasil", "SN": "Brasil", "SS": "Brasil", "SW": "Brasil",
            "SL": "Bolivia",
            "SG": "Paraguay",
            "SC": "Chile",
            "SA": "Argentina",
            "SU": "Uruguay",
            
            # Asia
            "LL": "Israel",
            "OJ": "Jordan",
            "OS": "Syria",
            "OL": "Lebanon",
            "OR": "Iraq",
            "OI": "Iran",
            "OK": "Kuwait",
            "OB": "Bahrain",
            "OT": "Qatar",
            "OE": "Saudi Arabia",
            "OM": "UAE",
            "OO": "Oman",
            "OY": "Yemen",
            
            "OA": "Afghanistan",
            "OP": "Pakistan",
            "VI": "India", "VA": "India", "VE": "India", "VO": "India",
            "VC": "Sri Lanka",
            "VR": "Maldives",
            "VG": "Bangladesh",
            "VN": "Nepal",
            "VQ": "Bhutan",
            
            "VY": "Myanmar",
            "VT": "Thailand",
            "VL": "Laos",
            "VD": "Cambodia",
            "VV": "Vietnam",
            "WM": "Malaysia",
            "WS": "Singapore",
            "WB": "Brunei",
            "WP": "Timor-Leste",
            "WI": "Indonesia", "WA": "Indonesia", "WR": "Indonesia", "WQ": "Indonesia",
            "RP": "Philippines",
            
            "RC": "Taiwan",
            "RJ": "Japan", "RO": "Japan",
            "RK": "South Korea",
            "ZK": "North Korea",
            "ZM": "Mongolia",
            
            # Africa
            "GM": "Morocco",
            "DA": "Algeria",
            "DT": "Tunisia",
            "HL": "Libya",
            "HE": "Egypt",
            "GQ": "Mauritania",
            "GO": "Senegal",
            "GB": "Gambia",
            "GU": "Guinea",
            "GF": "Sierra Leone",
            "GL": "Liberia",
            "DI": "Cote d'Ivoire",
            "DG": "Ghana",
            "DX": "Togo",
            "DB": "Benin",
            "DN": "Nigeria",
            "DF": "Burkina Faso",
            "DR": "Niger",
            "FT": "Chad",
            "HK": "Kenya",
            "HU": "Uganda",
            "HT": "Tanzania",
            "HR": "Rwanda",
            "HB": "Burundi",
            "HC": "Somalia",
            "HA": "Ethiopia",
            "HSS": "Sudan", "HSO": "Sudan",
            "FK": "Cameroon",
            "FE": "CAR",
            "FO": "Gabon",
            "FC": "Congo",
            "FZ": "DRC",
            "FG": "Equatorial Guinea",
            "FN": "Angola",
            "FB": "Botswana",
            "FL": "Zambia",
            "FV": "Zimbabwe",
            "FW": "Malawi",
            "FQ": "Mozambique",
            "FA": "South Africa",
            "FX": "Lesotho",
            "FD": "Eswatini",
            "FM": "Madagascar",
            "FIM": "Mauritius",
            "FS": "Seychelles",
            
            # Oceania
            "NZ": "New Zealand",
            "AY": "Papua New Guinea",
            "AG": "Solomon Islands",
            "AN": "Nauru",
            "NF": "Fiji",
            "NV": "Vanuatu",
            "NW": "New Caledonia",
            "NG": "Kiribati",
            "NI": "Niue",
            "NL": "Wallis and Futuna",
            "NS": "Samoa",
            "NT": "French Polynesia",
            "PL": "Line Islands",
            
            # Special/Others
            "TX": "Bermuda",
            "TF": "Guadeloupe/Martinique",
            "TFF": "Martinique",
            "TFG": "Guadeloupe",
            "TN": "Aruba",
            "TU": "Virgin Islands",
        }
        
        if p2 in name_map:
            return name_map[p2]
            
        # 1-char matches
        if p1 == "K": return "USA"
        if p1 == "C": return "Canada"
        if p1 == "Y": return "Australia"
        if p1 == "Z": return "China"
        
        if prefix in self.mcd_config:
            return self.mcd_config[prefix]["name"]

        # Check MCD AutoSelect Reverse Lookup
        for key, config in self.mcd_config.items():
            if config.get("autoSelect", True):
                if p2 in config["prefixes"] or p1 in config["prefixes"]:
                    return config["name"]

        # Russia Special Case
        if p1 == "U" and p2 != "UK":
            return "Russia"

        return "Unknown Country"
