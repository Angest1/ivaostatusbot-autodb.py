"""Time formatting and timezone utilities."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from ..config import Settings

def format_hours_minutes(total_minutes: float) -> str:
    """Format minutes as 'Xh Ym'."""
    hours = int(total_minutes // 60)
    minutes = int(total_minutes % 60)
    return f"{hours:02d}:{minutes:02d}"

def time_remaining(target_datetime: datetime) -> str:
    """Calculate time remaining until target datetime."""
    now = datetime.now(timezone.utc)
    remaining = target_datetime - now
    
    days = remaining.days
    hours, remainder = divmod(remaining.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}min")
    
    return " ".join(parts) if parts else "0min"

def get_timezone() -> ZoneInfo:
    """Get the configured timezone."""
    settings = Settings()
    return ZoneInfo(settings.timezone)
