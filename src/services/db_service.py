"""
Database service.
Handles MySQL connections and query execution.
"""

import mysql.connector
from mysql.connector import pooling
from typing import List, Optional, Iterator, Generator, Any, Dict
from datetime import datetime
from ..config.settings import Settings
from ..models import Snapshot, Pilot, ATC, FlightPlan

class DatabaseService:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize database service with connection pool."""
        if self._initialized:
            return
            
        self._initialized = True
        msg = "Initializing Database Pool..."
        print(f"[DB] {msg}")
        self.settings = Settings()
        try:
            self.connection_pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name=self.settings.db_pool_name,
                pool_size=self.settings.db_pool_size,
                pool_reset_session=True,
                host=self.settings.db_host,
                database=self.settings.db_name,
                user=self.settings.db_user,
                password=self.settings.db_password,
                port=self.settings.db_port,
                charset='utf8mb4'
            )
            print("[DB] Database Pool Initialized.")
        except mysql.connector.Error as err:
            print(f"[ERROR] Error initializing database pool: {err}")
            
    def get_connection(self):
        """Get a connection from the pool."""
        try:
            conn = self.connection_pool.get_connection()
            # Enforce utf8mb4
            cursor = conn.cursor()
            cursor.execute("SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.close()
            return conn
        except mysql.connector.Error as err:
            print(f"[ERROR] Error getting connection: {err}")
            return None

    def save_snapshot(self, snapshot: Snapshot) -> bool:
        """
        Save a snapshot to ALL table partitions (day, week, month).
        """
        conn = self.get_connection()
        if not conn:
            return False
            
        cursor = None
        success_all = True
        
        try:
            cursor = conn.cursor()
            
            # Save to each partition
            for suffix in ['_day', '_week', '_month']:
                try:
                    # 1. Insert Snapshot
                    query_snap = f"INSERT INTO snapshots{suffix} (timestamp) VALUES (%s)"
                    cursor.execute(query_snap, (snapshot.timestamp,))
                    snapshot_id = cursor.lastrowid
                    
                    # 2. Insert Pilots
                    if snapshot.pilots:
                        pilot_values = []
                        for p in snapshot.pilots:
                            user_id = p.user_id if p.user_id else None
                            dep = p.flight_plan.departure_id or ""
                            arr = p.flight_plan.arrival_id or ""
                            aircraft = p.flight_plan.aircraft_icao or ""
                            pob = p.flight_plan.people_on_board or 0
                            route = p.flight_plan.route or ""

                            pilot_values.append((
                                snapshot_id, 
                                user_id, 
                                p.callsign, 
                                dep, 
                                arr, 
                                aircraft, 
                                pob, 
                                route,
                                snapshot.timestamp
                            ))
                        
                        pilot_query = f"""
                            INSERT INTO pilots{suffix} 
                            (snapshot_id, user_id, callsign, departure, arrival, aircraft, pob, route, created_at) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        cursor.executemany(pilot_query, pilot_values)

                    # 3. Insert ATCs
                    if snapshot.atcs:
                        atc_values = []
                        for a in snapshot.atcs:
                            user_id = a.user_id if a.user_id else None
                            atis = str(a.atis) if a.atis else None
                            
                            atc_values.append((
                                snapshot_id,
                                user_id,
                                a.callsign,
                                a.frequency,
                                atis,
                                snapshot.timestamp
                            ))
                        
                        atc_query = f"""
                            INSERT INTO atcs{suffix} 
                            (snapshot_id, user_id, callsign, frequency, atis, created_at) 
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """
                        cursor.executemany(atc_query, atc_values)
                        
                except Exception as e:
                    print(f"[ERROR] Failed to save to partition {suffix}: {e}")
                    success_all = False

            conn.commit()
            return success_all

        except mysql.connector.Error as err:
            print(f"[ERROR] Error saving snapshot: {err}")
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_last_snapshot(self, scope: str = 'day') -> Optional[Snapshot]:
        """
        Get the most recent snapshot from the specified DB scope (suffix).
        """
        conn = self.get_connection()
        if not conn:
            return None
            
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True) # Use dictionary cursor for convenience
            
            # Get latest snapshot ID
            table_snap = f"snapshots_{scope}"
            table_pilots = f"pilots_{scope}"
            table_atcs = f"atcs_{scope}"
            
            cursor.execute(f"SELECT id, timestamp FROM {table_snap} ORDER BY id DESC LIMIT 1")
            snap_row = cursor.fetchone()
            
            if not snap_row:
                return None
                
            snapshot_id = snap_row['id']
            timestamp = snap_row['timestamp']
            
            # Get Pilots
            cursor.execute(f"SELECT * FROM {table_pilots} WHERE snapshot_id = %s", (snapshot_id,))
            pilot_rows = cursor.fetchall()
            pilots = []
            for r in pilot_rows:
                fp = FlightPlan(
                    departure_id=r['departure'],
                    arrival_id=r['arrival'],
                    people_on_board=r['pob'],
                    route=r['route'],
                    aircraft_icao=r['aircraft']
                )
                pilots.append(Pilot(
                    user_id=r['user_id'],
                    callsign=r['callsign'],
                    flight_plan=fp
                ))
            
            # Get ATCs
            cursor.execute(f"SELECT * FROM {table_atcs} WHERE snapshot_id = %s", (snapshot_id,))
            atc_rows = cursor.fetchall()
            atcs = []
            for r in atc_rows:
                atcs.append(ATC(
                    user_id=r['user_id'],
                    callsign=r['callsign'],
                    frequency=r['frequency'],
                    atis=r['atis']
                ))
                
            return Snapshot(
                timestamp=timestamp,
                pilots=pilots,
                atcs=atcs
            )

        except mysql.connector.Error as err:
            print(f"[ERROR] Error getting last snapshot: {err}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def stream_snapshots(self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None, scope: str = 'day') -> Generator[Snapshot, None, None]:
        """
        Yields snapshots efficiently.
        """
        conn = self.get_connection()
        if not conn:
            return

        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Build query
            table_snap = f"snapshots_{scope}"
            query = f"SELECT id, timestamp FROM {table_snap} WHERE 1=1"
            params = []
            
            if start_time:
                query += " AND timestamp >= %s"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= %s"
                params.append(end_time)
                
            query += " ORDER BY id ASC"
            
            cursor.execute(query, tuple(params))
            
            # Fetch all snapshot IDs first
            snapshot_metas = cursor.fetchall()
            
            cursor.close() 
            
            # Iterate and fetch full details
            for meta in snapshot_metas:
                yield self._get_snapshot_by_id(conn, meta['id'], meta['timestamp'], scope)
                
        except mysql.connector.Error as err:
            print(f"[ERROR] Error streaming snapshots: {err}")
        finally:
            if conn:
                conn.close()

    def _get_snapshot_by_id(self, conn, snap_id: int, timestamp: datetime, scope: str) -> Snapshot:
        """Helper to fetch details for a single snapshot using an existing connection."""
        cursor = conn.cursor(dictionary=True)
        table_pilots = f"pilots_{scope}"
        table_atcs = f"atcs_{scope}"
        try:
            # Pilots
            cursor.execute(f"SELECT * FROM {table_pilots} WHERE snapshot_id = %s", (snap_id,))
            pilots = []
            for r in cursor.fetchall():
                fp = FlightPlan(
                    departure_id=r['departure'],
                    arrival_id=r['arrival'],
                    people_on_board=r['pob'],
                    route=r['route'],
                    aircraft_icao=r['aircraft']
                )
                pilots.append(Pilot(
                    user_id=r['user_id'],
                    callsign=r['callsign'],
                    flight_plan=fp
                ))
            
            # ATCs
            cursor.execute(f"SELECT * FROM {table_atcs} WHERE snapshot_id = %s", (snap_id,))
            atcs = []
            for r in cursor.fetchall():
                atcs.append(ATC(
                    user_id=r['user_id'],
                    callsign=r['callsign'],
                    frequency=r['frequency'],
                    atis=r['atis']
                ))
                
            return Snapshot(
                timestamp=timestamp,
                pilots=pilots,
                atcs=atcs
            )
        finally:
            cursor.close()

    def get_statistics_aggregated(self, start_time: datetime, country_prefixes: List[str], scope: str = 'day') -> dict:
        """
        Get aggregated statistics directly from DB.
        """
        conn = self.get_connection()
        if not conn:
            return {}
            
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Construct prefix LIKE clauses
            # prefix is like 'SC', 'SA', etc.
            # departure LIKE 'SC%' OR departure LIKE 'SA%' ...
            prefix_clauses = [f"p.departure LIKE '{p}%'" for p in country_prefixes]
            dep_in_country_sql = f"({' OR '.join(prefix_clauses)})"
            
            prefix_clauses = [f"p.arrival LIKE '{p}%'" for p in country_prefixes]
            arr_in_country_sql = f"({' OR '.join(prefix_clauses)})"
            
            # 1. Total Unique Pilots, Flights, and Categorizations
            # tables
            t_snap = f"snapshots_{scope}"
            t_pilots = f"pilots_{scope}"
            
            query_flights = f"""
                SELECT 
                    COUNT(DISTINCT p.user_id, p.departure, p.arrival, p.route) as total_flights,
                    COUNT(DISTINCT CASE WHEN {dep_in_country_sql} AND {arr_in_country_sql} THEN CONCAT(p.user_id, p.departure, p.arrival, p.route) END) as domestic_flights,
                    COUNT(DISTINCT CASE WHEN {dep_in_country_sql} AND NOT {arr_in_country_sql} THEN CONCAT(p.user_id, p.departure, p.arrival, p.route) END) as intl_departures,
                    COUNT(DISTINCT CASE WHEN NOT {dep_in_country_sql} AND {arr_in_country_sql} THEN CONCAT(p.user_id, p.departure, p.arrival, p.route) END) as intl_arrivals,
                    COUNT(DISTINCT p.user_id) as unique_pilots,
                    SUM(p.pob) as total_pob_raw 
                FROM {t_snap} s
                JOIN {t_pilots} p ON s.id = p.snapshot_id
                WHERE s.timestamp >= %s
                AND ({dep_in_country_sql} OR {arr_in_country_sql})
            """
            
            cursor.execute(query_flights, (start_time,))
            stats_flights = cursor.fetchone()

            # 1.5 Total POB (Sum of MAX pob for each unique flight leg)
            query_pob = f"""
                SELECT SUM(max_pob) as total_pob
                FROM (
                    SELECT MAX(p.pob) as max_pob
                    FROM {t_snap} s
                    JOIN {t_pilots} p ON s.id = p.snapshot_id
                    WHERE s.timestamp >= %s
                    AND ({dep_in_country_sql} OR {arr_in_country_sql})
                    GROUP BY p.user_id, p.departure, p.arrival, p.route
                ) as sub
            """
            cursor.execute(query_pob, (start_time,))
            pob_row = cursor.fetchone()
            total_pob = pob_row['total_pob'] if pob_row and pob_row['total_pob'] else 0
            
            # 2. Flight Time (Man-Minutes)
            # Count distinct (user_id, minute) pairs.
            # Assuming snapshots are roughly every minute.
            # We skip the very first snapshot of the day (00:00) for time calc if needed, 
            # but usually counting all is fine or we strictly follow start_time.
            # Notes: Python version skips 00:00 snapshot. We can try to exclude it if hour=0 and min=0.
            # 2. Flight Time (Man-Minutes)
            query_time_pilots = f"""
                SELECT Count(*) as total_minutes
                FROM (
                    SELECT DISTINCT p.user_id, DATE_FORMAT(s.timestamp, '%Y-%m-%d %H:%i') as minute_key
                    FROM {t_snap} s
                    JOIN {t_pilots} p ON s.id = p.snapshot_id
                    WHERE s.timestamp >= %s
                    AND ({dep_in_country_sql} OR {arr_in_country_sql})
                    AND NOT (HOUR(s.timestamp) = 0 AND MINUTE(s.timestamp) = 0)
                ) as sub
            """
            cursor.execute(query_time_pilots, (start_time,))
            stats_pilot_time = cursor.fetchone()
            
            # 3. ATC Time (Man-Minutes) & Count
            t_atcs = f"atcs_{scope}"
            prefix_clauses = [f"a.callsign LIKE '{p}%'" for p in country_prefixes]
            atc_in_country_sql = f"({' OR '.join(prefix_clauses)})"
            
            query_atc = f"""
                SELECT 
                    COUNT(DISTINCT a.callsign) as unique_atcs, 
                    (
                        SELECT Count(*) 
                        FROM (
                            SELECT DISTINCT callsign, DATE_FORMAT(s2.timestamp, '%Y-%m-%d %H:%i')
                            FROM {t_snap} s2
                            JOIN {t_atcs} a2 ON s2.id = a2.snapshot_id
                            WHERE s2.timestamp >= %s
                            AND (
                                {' OR '.join([f"a2.callsign LIKE '{p}%'" for p in country_prefixes])}
                            )
                        ) as sub
                    ) as total_minutes
                FROM {t_snap} s
                JOIN {t_atcs} a ON s.id = a.snapshot_id
                WHERE s.timestamp >= %s
                AND ({atc_in_country_sql})
            """
            # We pass start_time twice
            cursor.execute(query_atc, (start_time, start_time))
            stats_atc = cursor.fetchone()
            
            return {
                "total_flights": stats_flights['total_flights'],
                "domestic_flights": stats_flights['domestic_flights'],
                "intl_departures": stats_flights['intl_departures'],
                "intl_arrivals": stats_flights['intl_arrivals'],
                "unique_pilots": stats_flights['unique_pilots'],
                "people_on_board_total": total_pob,
                "flight_time_total_min": stats_pilot_time['total_minutes'],
                "atc_time_total_min": stats_atc['total_minutes'],
                "atc_count": stats_atc['unique_atcs'] # Note: This is unique ATCs in period, might differ from "current" ATCs
            }
            
        except mysql.connector.Error as err:
            print(f"[ERROR] Error getting aggregated statistics: {err}")
            return {}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_chart_time_series(self, start_time: Optional[datetime], end_time: Optional[datetime], scope: str = 'day') -> List[tuple]:
        """
        Get time series data (counts) for charts.
        """
        conn = self.get_connection()
        if not conn:
            return []
            
        cursor = None
        try:
            cursor = conn.cursor()
            
            # Efficient query using COUNT and GROUP BY
            t_snap = f"snapshots_{scope}"
            t_pilots = f"pilots_{scope}"
            t_atcs = f"atcs_{scope}"

            query = f"""
                SELECT 
                    s.timestamp,
                    COUNT(DISTINCT p.id) as pilot_count,
                    COUNT(DISTINCT a.id) as atc_count
                FROM {t_snap} s
                LEFT JOIN {t_pilots} p ON s.id = p.snapshot_id
                LEFT JOIN {t_atcs} a ON s.id = a.snapshot_id
                WHERE 1=1
            """
            
            params = []
            if start_time:
                query += " AND s.timestamp >= %s"
                params.append(start_time)
            
            if end_time:
                query += " AND s.timestamp <= %s"
                params.append(end_time)
                
            query += " GROUP BY s.id ORDER BY s.timestamp ASC"
            
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
            
        except mysql.connector.Error as err:
            print(f"[ERROR] Error getting time series data: {err}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_chart_aggregated_daily(self, start_time: Optional[datetime], scope: str = 'day') -> List[tuple]:
        """
        Get daily aggregated unique counts for weekly/monthly charts.
        """
        conn = self.get_connection()
        if not conn:
            return []
            
        cursor = None
        try:
            cursor = conn.cursor()
            
            # Aggregate by DATE(timestamp) and count DISTINCT user_id/callsign
            t_snap = f"snapshots_{scope}"
            t_pilots = f"pilots_{scope}"
            t_atcs = f"atcs_{scope}"
            
            query = f"""
                SELECT 
                    DATE(s.timestamp) as day,
                    COUNT(DISTINCT COALESCE(p.user_id, p.callsign)) as unique_pilots,
                    COUNT(DISTINCT COALESCE(a.user_id, a.callsign)) as unique_atcs
                FROM {t_snap} s
                LEFT JOIN {t_pilots} p ON s.id = p.snapshot_id
                LEFT JOIN {t_atcs} a ON s.id = a.snapshot_id
                WHERE 1=1
            """
            
            params = []
            if start_time:
                query += " AND s.timestamp >= %s"
                params.append(start_time)
                
            query += " GROUP BY DATE(s.timestamp) ORDER BY day ASC"
            
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
            
        except mysql.connector.Error as err:
            print(f"[ERROR] Error getting aggregated chart data: {err}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    # --- Cleanup Methods ---

    def prune_daily_data(self) -> bool:
        """
        Prunes data older than 36 hours from the 'day' tables.
        """
        conn = self.get_connection()
        if not conn:
            return False
            
        cursor = None
        try:
            cursor = conn.cursor()
            # Disable safe updates to allow deletion by timestamp (non-key)
            cursor.execute("SET SQL_SAFE_UPDATES = 0")
            
            # Delete snapshots older than 36 hours. 
            cursor.execute("DELETE FROM snapshots_day WHERE timestamp < NOW() - INTERVAL 36 HOUR")
            deleted = cursor.rowcount
            
            # Re-enable safe updates
            cursor.execute("SET SQL_SAFE_UPDATES = 1")
            
            conn.commit()
            if deleted > 0:
                print(f"[DB] Pruned {deleted} old snapshots from daily tables.")
            return True
        except mysql.connector.Error as err:
            print(f"[ERROR] Error pruning daily data: {err}")
            return False
        finally:
            if cursor: cursor.close()
            if conn: conn.close()
            
    def reset_weekly_data(self) -> bool:
        """
        Truncates the 'week' tables.
        """
        return self._truncate_partition('week')

    def reset_monthly_data(self) -> bool:
        """
        Truncates the 'month' tables.
        """
        return self._truncate_partition('month')

    def _truncate_partition(self, suffix: str) -> bool:
        """Helper to truncate all relevant tables for a suffix."""
        conn = self.get_connection()
        if not conn:
            return False
            
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            cursor.execute(f"TRUNCATE TABLE pilots_{suffix}")
            cursor.execute(f"TRUNCATE TABLE atcs_{suffix}")
            cursor.execute(f"TRUNCATE TABLE snapshots_{suffix}")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            conn.commit()
            print(f"[DB] Truncated (Reset) tables for partition: {suffix}")
            return True
        except mysql.connector.Error as err:
            print(f"[ERROR] Error resetting {suffix} tables: {err}")
            return False
        finally:
            if cursor: cursor.close()
            if conn: conn.close()
