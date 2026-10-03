"""SQLite local. Todas las llamadas se serializan mediante el bloqueo del servicio."""
import sqlite3
import json
from pathlib import Path
from .contract import ASSET

DEFAULT_RULES = {"temperature_limit": 45.0, "temperature_hysteresis": 3.0,
                 "vibration_limit": 2.0, "vibration_hysteresis": 0.3,
                 "minimum_duration_s": 3.0, "no_data_s": 5.0}

class Storage:
    def __init__(self, path, asset_id=ASSET, asset_name="Lavadora de prueba", default_rules=None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS assets(id TEXT PRIMARY KEY, name TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS measurements(
            id INTEGER PRIMARY KEY, schema_version INTEGER NOT NULL, device_id TEXT NOT NULL,
            asset_id TEXT NOT NULL REFERENCES assets(id), sequence INTEGER NOT NULL,
            acquired_at TEXT NOT NULL, received_at TEXT NOT NULL,
            source TEXT NOT NULL CHECK(source IN ('simulated','real')), quality TEXT NOT NULL,
            temperature_c REAL NOT NULL, vibration_rms REAL NOT NULL,
            vibration_unit TEXT NOT NULL, vibration_method TEXT NOT NULL, window_s REAL NOT NULL,
            UNIQUE(device_id,source,sequence));
        CREATE INDEX IF NOT EXISTS measurement_time ON measurements(acquired_at);
        CREATE TABLE IF NOT EXISTS alarms(id INTEGER PRIMARY KEY, kind TEXT NOT NULL,
            started_at TEXT NOT NULL, recovered_at TEXT, acknowledged_at TEXT, acknowledged_by TEXT,
            start_value REAL, start_limit REAL, source TEXT NOT NULL DEFAULT 'simulated');
        CREATE UNIQUE INDEX IF NOT EXISTS one_active_alarm ON alarms(kind) WHERE recovered_at IS NULL;
        CREATE TABLE IF NOT EXISTS alarm_events(id INTEGER PRIMARY KEY,
            alarm_id INTEGER NOT NULL REFERENCES alarms(id), at TEXT NOT NULL,
            event TEXT NOT NULL, detail TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS interventions(id INTEGER PRIMARY KEY,
            asset_id TEXT NOT NULL REFERENCES assets(id), intervention_at TEXT NOT NULL,
            recorded_at TEXT NOT NULL, author TEXT NOT NULL, work_type TEXT NOT NULL,
            observations TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS reception_events(id INTEGER PRIMARY KEY, at TEXT NOT NULL,
            code TEXT NOT NULL, detail TEXT NOT NULL);
        PRAGMA user_version=1;
        """)
        existing = self.db.execute("SELECT id FROM assets LIMIT 1").fetchone()
        if existing and existing[0] != asset_id:
            self.db.close()
            raise ValueError("Esta base pertenece a otro activo. Use una carpeta de datos separada.")
        self.db.execute("INSERT OR IGNORE INTO assets VALUES(?,?)", (asset_id, asset_name))
        self.db.execute("INSERT OR IGNORE INTO settings VALUES('rules',?)", (json.dumps(default_rules or DEFAULT_RULES),))
        self.db.commit()

    def rows(self, sql, args=()):
        return [dict(row) for row in self.db.execute(sql, args)]

    def latest(self):
        rows = self.rows("SELECT * FROM measurements ORDER BY id DESC LIMIT 1")
        return rows[0] if rows else None

    def rules(self):
        return json.loads(self.db.execute("SELECT value FROM settings WHERE key='rules'").fetchone()[0])

    def save_rules(self, rules, at):
        with self.db:
            self.db.execute("UPDATE settings SET value=? WHERE key='rules'", (json.dumps(rules),))
            self.db.execute("INSERT INTO reception_events(at,code,detail) VALUES(?,?,?)",
                            (at, "configuration", json.dumps(rules)))

    def insert(self, packet):
        cols = tuple(packet)
        with self.db:
            self.db.execute(f"INSERT INTO measurements({','.join(cols)}) VALUES({','.join('?' for _ in cols)})", tuple(packet.values()))

    def reception_event(self, at, code, detail):
        with self.db:
            self.db.execute("INSERT INTO reception_events(at,code,detail) VALUES(?,?,?)", (at, code, detail))

    def close(self):
        self.db.close()
