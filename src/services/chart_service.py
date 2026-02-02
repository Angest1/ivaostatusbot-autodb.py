"""
Chart generation service.
Generates matplotlib charts with caching for daily, weekly, and monthly views."""

import os
import time
import sys
import ctypes
import gc
from collections import defaultdict
from datetime import datetime
import threading
from typing import Optional, List, Tuple
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib.ticker as mticker
import numpy as np
from matplotlib.colors import to_rgba
from matplotlib.path import Path
from matplotlib.patches import PathPatch

from ..config import Constants

from ..config.settings import Settings
from ..config.languages import get_text
from ..models import Snapshot

class ChartService:
    """Service for generating charts with caching."""
    
    def __init__(self, db_service):
        """Initialize chart service."""
        self.constants = Constants()
        self.db_service = db_service
        self._cache = {}
        self._cache_time = {}
        self._lock = threading.Lock()
    
    def _fill_with_gradient(self, ax, x, y, color):
        """Fill area under curve with gradient."""
        if x is None or y is None or len(x) == 0 or len(y) == 0:
            return
        
        y_max = float(np.max(y))
        if y_max <= 0:
            return
        if y_max <= 1:
            y_max = 2
        
        r, g, b, _ = to_rgba(color)
        n = 256
        gradient = np.zeros((1, n, 4))
        
        for j in range(n):
            alpha = 0.25 * (j / (n - 1))
            gradient[0, j, :3] = (r, g, b)
            gradient[0, j, 3] = alpha
        
        im = ax.imshow(gradient, extent=[x[0], x[-1], 0, y_max], origin="lower", aspect="auto", zorder=1)
        
        verts = [(x[0], 0)] + list(zip(x, y)) + [(x[-1], 0)]
        path = Path(verts)
        patch = PathPatch(path, transform=ax.transData)
        im.set_clip_path(patch)
    
    def _read_chart_data(
        self,
        chart_type: str
    ) -> Tuple[List[str], List[int], List[int]]:
        """Read and process data for chart generation from database efficiently."""
        times = []
        pilot_counts = []
        atc_counts = []
        
        from datetime import timezone, timedelta
        now = datetime.now(timezone.utc)
        start_time = None
        end_time = None
        
        # Determine time range
        if chart_type == "daily":
             # Start of today
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif chart_type == "realtime":
             # Last 26 hours (to ensure the first visible tick at index 1 is exactly -24h)
             start_time = now - timedelta(hours=26)
        elif chart_type == "weekly":
             # Start of week (Monday)
            start_time = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        elif chart_type == "monthly":
             # Start of month
            start_time = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
        # Determine scope based on chart type
        scope = 'day'
        if chart_type == "weekly":
            scope = 'week'
        elif chart_type == "monthly":
            scope = 'month'
        # daily and realtime use 'day'
            
        # Use optimized DB queries based on chart type
        if chart_type in ("weekly", "monthly"):
            # Get aggregated daily counts directly from DB
            rows = self.db_service.get_chart_aggregated_daily(start_time, scope=scope)
            
            if not rows:
                return [], [], []
                
            # Convert rows to dict for easy lookup
            # Row mapping: date, pilot_count, atc_count
            pilots_map = {r[0]: r[1] for r in rows}
            atcs_map = {r[0]: r[2] for r in rows}
            
            # Generate full range of days
            current_date = start_time.date()
            end_date = now.date()
            
            while current_date <= end_date:
                times.append(current_date.strftime("%d/%m"))
                pilot_counts.append(pilots_map.get(current_date, 0))
                atc_counts.append(atcs_map.get(current_date, 0))
                current_date += timedelta(days=1)
                
        else:
            # Realtime / Daily: Get time series counts directly from DB
            rows = self.db_service.get_chart_time_series(start_time, end_time, scope=scope)
            
            if not rows:
                # Fallback for daily/realtime when no data exists yet
                if chart_type in ("daily", "realtime"):
                    last_snapshot = self.db_service.get_last_snapshot()
                    if last_snapshot:
                        # Create a flat line using the last known values
                        p_count = len(last_snapshot.pilots)
                        a_count = len(last_snapshot.atcs)
                        
                        start_date_str = start_time.strftime("%H:%M")
                        now_str = now.strftime("%H:%M")

                        return [start_date_str, now_str], [p_count, p_count], [a_count, a_count]
                    else:
                         # If really no data even before
                        now_str = now.strftime("%H:%M")
                        return ["00:00", now_str], [0, 0], [0, 0]
                else:
                    return [], [], []

            # Row: timestamp, pilot_count, atc_count
            rows.sort(key=lambda x: x[0])

            # Populate lists
            for r in rows:
                ts = r[0] # datetime object
                times.append(ts.strftime("%H:%M"))
                    
                pilot_counts.append(r[1])
                atc_counts.append(r[2])
        
        return times, pilot_counts, atc_counts
    
    def generate_chart(
        self,
        file_path: str, # Kept for compatibility but ignored
        output: str,
        chart_type: str,
        color_primary: Optional[str] = None,
        color_atc: Optional[str] = None
    ) -> Optional[str]:
        # Check cache
        # Clean old cache periodically (every 5 minutes)
        current_time = time.time()
        if not hasattr(self, '_last_clean_time') or current_time - self._last_clean_time > 300:
            self.clean_old_cache()
            self._last_clean_time = current_time

        cache_key = f"{chart_type}_{output}_{color_primary}_{color_atc}"
        
        if (cache_key in self._cache and
            cache_key in self._cache_time and
            current_time - self._cache_time[cache_key] < self.constants.CHART_CACHE_DURATION_SECONDS and
            os.path.exists(self._cache[cache_key])):
            return self._cache[cache_key]
        
        # Read data
        times, pilot_counts, atc_counts = self._read_chart_data(chart_type)
        
        if not times:
            return None
        
        # Ensure at least 2 points for interpolation
        if len(times) == 1:
            times.append(times[0])
            pilot_counts.append(pilot_counts[0])
            atc_counts.append(atc_counts[0])
        
        # Determine colors
        if chart_type == "daily":
            color_primary = color_primary or self.constants.CHART_COLORS["daily_primary"]
            color_atc = color_atc or self.constants.CHART_COLORS["daily_secondary"]
        elif chart_type == "weekly":
            color_primary = color_primary or self.constants.CHART_COLORS["weekly_primary"]
            color_atc = color_atc or self.constants.CHART_COLORS["weekly_secondary"]
        elif chart_type == "monthly":
            color_primary = color_primary or self.constants.CHART_COLORS["monthly_primary"]
            color_atc = color_atc or self.constants.CHART_COLORS["monthly_secondary"]
        else:  # realtime
            has_atc = atc_counts[-1] > 0 if atc_counts else False
            if has_atc:
                color_primary = color_primary or self.constants.CHART_COLORS["realtime_atc_active"]
                color_atc = color_atc or self.constants.CHART_COLORS["realtime_atc_active_secondary"]
            else:
                color_primary = color_primary or self.constants.CHART_COLORS["realtime_no_atc"]
                color_atc = color_atc or self.constants.CHART_COLORS["realtime_no_atc_secondary"]
        
        # Get translated labels
        settings = Settings()
        
        # Force English for languages with unsupported characters in standard fonts (CJK, Arabic, etc)
        # to avoid "tofu" (squares) in the chart generation
        chart_lang = settings.lang
        if any(code in chart_lang.lower() for code in ["zh", "ar", "ja", "ko", "th"]):
            chart_lang = "en"
            
        label_pilots = get_text(chart_lang, "presence_pilots")
        label_atcs = get_text(chart_lang, "presence_atcs")
 
        # Generate chart
        # Use thread lock to protect shared resources (like font cache)
        # and use OO interface to avoid global state API (pyplot)
        with self._lock:
            # Create Figure (stateless)
            fig = Figure(figsize=(6, 1.75))
            fig.patch.set_facecolor("#1c1c1c")
            
            # Create canvas
            FigureCanvasAgg(fig)
            
            # Add Axes
            ax = fig.add_subplot(111)
            ax.set_facecolor("#1c1c1c")
            
            x = np.arange(len(times))
            x_ext = np.insert(x, 0, 0)
            pilots_ext = np.insert(pilot_counts, 0, pilot_counts[0])
            atcs_ext = np.insert(atc_counts, 0, atc_counts[0])
            
            # Smooth interpolation
            points = min(180, len(x_ext) * 6)
            x_smooth = np.linspace(0, len(x_ext) - 1, points)
            pilots_smooth = np.interp(x_smooth, x_ext, pilots_ext)
            atcs_smooth = np.interp(x_smooth, x_ext, atcs_ext)
            
            # Plot lines
            ax.plot(x_smooth, pilots_smooth, color=color_primary, linewidth=2, label=label_pilots)
            self._fill_with_gradient(ax, x_smooth, pilots_smooth, color_primary)
            
            ax.plot(x_smooth, atcs_smooth, color=color_atc, linewidth=2, label=label_atcs)
            self._fill_with_gradient(ax, x_smooth, atcs_smooth, color_atc)
            
            # Set limits
            y_max = max(max(pilot_counts), max(atc_counts))
            if y_max <= 1:
                ax.set_ylim(0, 2)
            else:
                ax.set_ylim(0, y_max * 1.10)
            
            # Draw vertical line at 00:00 for realtime chart
            if chart_type == "realtime" and "00:00" in times:
                try:
                    # Find and use the last occurrence of "00:00" (most recent midnight)
                    midnight_indices = [i for i, t in enumerate(times) if t == "00:00"]
                    if midnight_indices:
                        idx_00 = midnight_indices[-1]
                        ax.axvline(x=idx_00, color=color_primary, linestyle="--", linewidth=1, alpha=0.7)
                except ValueError:
                    pass
            
            ax.set_xlim(0, len(x_ext) - 1)
            
            # Set ticks
            n = len(times)
            ticks = [0]
            labels = [""]
            
            if chart_type == "weekly":
                # Show only weekdays starting from Monday
                step = max(1, n // 7)
                for i in range(0, n, step):
                    ticks.append(i + 1)
                    labels.append(times[i])
            elif chart_type == "monthly":
                # Show ~12 labels across the month
                step = max(1, n // 12)
                for i in range(0, n, step):
                    ticks.append(i + 1)
                    labels.append(times[i])
                if ticks[-1] != n:
                    ticks.append(n)
                    labels.append(times[-1])
            else:
                # Realtime/daily - show ~12 time labels
                # For realtime (26h range), divide by 13 to get 2h steps (so index 1 is -24h)
                if chart_type == "realtime":
                    step = max(1, n // 13)
                else:
                    step = max(1, n // 12)
                for i in range(step, n, step):
                    ticks.append(i)
                    labels.append(times[i])
                
                if ticks[-1] != n - 1:
                    if ticks[-1] > 0 and (n - 1 - ticks[-1]) < (step * 0.75):
                        ticks.pop()
                        labels.pop()
                    
                    ticks.append(n - 1)
                    labels.append(times[n - 1])
            
            ax.set_xticks(ticks)
            ax.set_xticklabels(labels, rotation=45, fontsize=10, color="white", fontweight="bold")
            
            # Y-axis on right
            ax.yaxis.tick_right()
            ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
            for label in ax.get_yticklabels():
                label.set_fontweight('bold')
                label.set_color("white") # Re-apply white color manually
            
            # Grid and legend
            ax.grid(True, linewidth=0.3, alpha=0.3)
            # Fix legend text color manually since we're not using style context
            legend = ax.legend(loc="upper left", frameon=False, prop={'weight': 'bold', 'size': 8})
            for text in legend.get_texts():
                text.set_color("white")
            
            # Style spines
            for side, spine in ax.spines.items():
                if side in ("bottom", "right"):
                    spine.set_color(color_primary)
                else:
                    spine.set_visible(False)
            
            # Save
            fig.set_tight_layout(True) # Ensure layout is tight
            fig.tight_layout(pad=0)
            fig.savefig(output, dpi=300, transparent=True)
            
            # Explicit clear (although not strictly needed if we drop ref)
            fig.clear()
            
            # Force memory release on Linux
            if sys.platform == "linux":
                try:
                    ctypes.CDLL('libc.so.6').malloc_trim(0)
                except Exception:
                    pass

        
        # Update cache
        self._cache[cache_key] = output
        self._cache_time[cache_key] = current_time
        
        return output
    
    def clean_old_cache(self):
        """Clean old cached charts."""
        try:
            current_time = time.time()
            charts_to_remove = []
            
            for cache_key, file_path in self._cache.items():
                if cache_key in self._cache_time:
                    if current_time - self._cache_time[cache_key] > self.constants.CHART_CACHE_DURATION_SECONDS * 2:
                        charts_to_remove.append(cache_key)
                        if os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                            except:
                                pass
            
            for key in charts_to_remove:
                self._cache.pop(key, None)
                self._cache_time.pop(key, None)
        except Exception as e:
            print(f"[ERROR] Error cleaning chart cache: {e}")
