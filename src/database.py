import psycopg2
from typing import Optional
from models import SensorReading, Alert


class DatabaseManager:
    def __init__(self, dsn: str):
        self._dsn = dsn
        self._conn = None

    def connect(self):
        try:
            self._conn = psycopg2.connect(self._dsn)
            self._conn.autocommit = True
        except psycopg2.Error as e:
            raise ConnectionError(f"Database connection failed: {e}")

    def get_profile_id(self, crop_name: str) -> int:
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM grain_profiles WHERE crop_name = %s;", (crop_name,)
            )
            result = cur.fetchone()
            if not result:
                raise ValueError(f"Profile for '{crop_name}' not found in database.")
            return result[0]

    def start_session(self, profile_id: int) -> int:
        with self._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO drying_sessions (profile_id) VALUES (%s) RETURNING id;",
                (profile_id,),
            )
            return cur.fetchone()[0]

    def log_reading(self, session_id: int, reading: SensorReading):
        with self._conn.cursor() as cur:
            cur.execute(
                """INSERT INTO sensor_logs (session_id, temperature, moisture_in, moisture_out)
                   VALUES (%s, %s, %s, %s);""",
                (
                    session_id,
                    reading.temperature,
                    reading.moisture_in,
                    reading.moisture_out,
                ),
            )

    def log_alert(self, session_id: int, alert: Alert):
        with self._conn.cursor() as cur:
            cur.execute(
                """INSERT INTO alert_logs (session_id, severity, message, action_required)
                   VALUES (%s, %s, %s, %s);""",
                (
                    session_id,
                    alert.severity.value,
                    alert.message,
                    alert.action_required,
                ),
            )

    def finish_session(self, session_id: int):
        with self._conn.cursor() as cur:
            cur.execute(
                "UPDATE drying_sessions SET end_time = CURRENT_TIMESTAMP, status = 'COMPLETED' WHERE id = %s;",
                (session_id,),
            )

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()
