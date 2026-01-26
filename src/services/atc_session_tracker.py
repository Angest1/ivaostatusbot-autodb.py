"""
ATC session tracker.
Tracks ATC session durations using database and in-memory state.
"""

from typing import List, Dict
from datetime import datetime, timezone, timedelta
from ..models import ATC
from .db_service import DatabaseService

class ATCSessionTracker:
    """Tracks ATC session durations using database directly (stateless)."""
    
    def __init__(self):
        """Initialize ATC session tracker."""
        from .db_service import DatabaseService
        self.db_service = DatabaseService()
    
    def calculate_session_duration(self, current_atcs: List[ATC]) -> Dict[str, int]:
        """
        Calculate session duration in minutes for current ATCs by querying DB history.
        Finds the start of the current continuous session (gap detection).
        """
        if not current_atcs:
            return {}
            
        sessions = {}
        target_callsigns = [atc.callsign.upper() for atc in current_atcs if atc.callsign]
        
        if not target_callsigns:
            return {}
            
        conn = self.db_service.get_connection()
        if not conn:
            return {cs: 0 for cs in target_callsigns}

        try:
            cursor = conn.cursor(dictionary=True)
            
            # Prepare query for all callsigns
            # Get timestamps and snapshot IDs for these callsigns from the last 24 hours
            format_strings = ','.join(['%s'] * len(target_callsigns))
            query = f"""
                SELECT a.callsign, s.timestamp, s.id as snapshot_id
                FROM atcs_day a 
                JOIN snapshots_day s ON a.snapshot_id = s.id 
                WHERE a.callsign IN ({format_strings}) 
                AND s.timestamp >= %s 
                ORDER BY a.callsign, s.timestamp DESC
            """
            
            since = datetime.now(timezone.utc) - timedelta(hours=24)
            params = target_callsigns + [since]
            
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            
            # Group data by callsign
            history = {}
            for row in rows:
                cs = row['callsign'].upper()
                ts = row['timestamp']
                sid = row['snapshot_id']
                
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                
                if cs not in history:
                    history[cs] = []
                history[cs].append({'ts': ts, 'id': sid})
            
            # Calculate duration for each callsign
            now = datetime.now(timezone.utc)
            
            for cs in target_callsigns:
                entries = history.get(cs)
                if not entries:
                    sessions[cs] = 0
                    continue
                
                # entries are DESC (newest first)
                # Find the earliest timestamp in the current contiguous block
                start_time = entries[0]['ts']
                
                # Iterate to find breaks in snapshot continuity
                for i in range(len(entries) - 1):
                    current = entries[i]
                    prev = entries[i+1]
                    
                    # Check snapshot continuity
                    # If the difference between snapshot IDs is > 1, it means there was at least
                    # one snapshot where this ATC was NOT present (disconnected).
                    # If the bot was off, the snapshot IDs will be sequential (diff=1)
                    # even if time gap is large, preserving the session.
                    if (current['id'] - prev['id']) > 1:
                        break
                    
                    start_time = prev['ts']
                
                duration_seconds = (now - start_time).total_seconds()
                sessions[cs] = int(duration_seconds / 60) + 1
                
        except Exception as e:
            print(f"[ERROR] Error calculating session durations: {e}")
            return {cs: 0 for cs in target_callsigns}
        finally:
            if conn:
                conn.close()
        
        return sessions
