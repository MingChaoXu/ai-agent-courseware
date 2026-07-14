"""SQLite database for low-altitude platform: drones, orders, events, flight_paths."""
import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime

from config import settings

logger = logging.getLogger(__name__)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    Path(settings.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS drones (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        status TEXT DEFAULT 'idle',
        battery REAL DEFAULT 100.0,
        lat REAL DEFAULT 30.5728,
        lng REAL DEFAULT 104.0668,
        altitude REAL DEFAULT 0.0,
        speed REAL DEFAULT 0.0,
        payload REAL DEFAULT 0.0,
        max_payload REAL DEFAULT 5.0,
        order_id INTEGER,
        model_type TEXT DEFAULT 'multirotor',
        range_km REAL DEFAULT 30.0
    );

    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        pickup_lat REAL, pickup_lng REAL,
        dropoff_lat REAL, dropoff_lng REAL,
        pickup_name TEXT DEFAULT '',
        dropoff_name TEXT DEFAULT '',
        cargo_type TEXT DEFAULT 'general',
        weight REAL DEFAULT 1.0,
        priority INTEGER DEFAULT 1,
        status TEXT DEFAULT 'pending',
        drone_id INTEGER,
        description TEXT DEFAULT '',
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY,
        type TEXT NOT NULL,
        description TEXT,
        severity TEXT DEFAULT 'info',
        lat REAL, lng REAL,
        status TEXT DEFAULT 'active',
        drone_id INTEGER,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS flight_paths (
        id INTEGER PRIMARY KEY,
        drone_id INTEGER,
        waypoints TEXT DEFAULT '[]',
        status TEXT DEFAULT 'planned',
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT,
        content TEXT,
        agent_used TEXT,
        created_at TEXT
    );
    """)
    conn.commit()
    conn.close()
    logger.info("DB initialized.")


def seed_if_empty():
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM drones").fetchone()[0]
    if count > 0:
        conn.close()
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Drones - 6 drones around Chengdu
    drones = [
        (1, "UAV-001 鹰眼", "idle", 95.0, 30.5728, 104.0668, 0, 0, 0, 5.0, None, "multirotor", 30),
        (2, "UAV-002 猎鹰", "flying", 72.0, 30.5828, 104.0768, 120, 45, 2.5, 5.0, 1, "multirotor", 30),
        (3, "UAV-003 信鸽", "flying", 58.0, 30.5628, 104.0568, 80, 50, 1.0, 3.0, 2, "multirotor", 20),
        (4, "UAV-004 翼龙", "charging", 30.0, 30.5728, 104.0668, 0, 0, 0, 8.0, None, "fixed-wing", 80),
        (5, "UAV-005 蜂鸟", "idle", 88.0, 30.5928, 104.0868, 0, 0, 0, 2.0, None, "multirotor", 15),
        (6, "UAV-006 雷霆", "maintenance", 0.0, 30.5728, 104.0668, 0, 0, 0, 10.0, None, "heavy-lift", 50),
    ]
    conn.executemany(
        "INSERT INTO drones (id,name,status,battery,lat,lng,altitude,speed,payload,max_payload,order_id,model_type,range_km) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", drones
    )

    # Orders
    orders = [
        (1, 30.5728, 104.0668, 30.6128, 104.1068, "天府广场", "龙泉驿站", "medical", 1.5, 3, "assigned", 2, "急救药品配送", now),
        (2, 30.5828, 104.0768, 30.5528, 104.0468, "春熙路", "双流机场", "general", 3.0, 1, "assigned", 3, "文件快递", now),
        (3, 30.5928, 104.0868, 30.6228, 104.0968, "高新区", "天府新区", "electronics", 2.0, 2, "pending", None, "电子配件", now),
    ]
    conn.executemany(
        "INSERT INTO orders (id,pickup_lat,pickup_lng,dropoff_lat,dropoff_lng,pickup_name,dropoff_name,cargo_type,weight,priority,status,drone_id,description,created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", orders
    )

    # Events
    events = [
        (1, "route_deviation", "UAV-003 偏离预定航线约200米", "warning", 30.5628, 104.0568, "monitoring", 3, now),
        (2, "weather_alert", "检测到侧风风速12m/s，影响飞行稳定性", "warning", 30.5828, 104.0768, "active", 2, now),
        (3, "low_battery", "UAV-004 电量低于30%，建议返航", "danger", 30.5728, 104.0668, "active", 4, now),
    ]
    conn.executemany(
        "INSERT INTO events (id,type,description,severity,lat,lng,status,drone_id,created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?)", events
    )

    # Flight paths
    paths = [
        (1, 2, json.dumps([
            {"lat": 30.5728, "lng": 104.0668, "alt": 0, "action": "takeoff"},
            {"lat": 30.5828, "lng": 104.0768, "alt": 100, "action": "cruise"},
            {"lat": 30.6028, "lng": 104.0968, "alt": 120, "action": "cruise"},
            {"lat": 30.6128, "lng": 104.1068, "alt": 0, "action": "land"},
        ]), "active", now),
        (2, 3, json.dumps([
            {"lat": 30.5828, "lng": 104.0768, "alt": 0, "action": "takeoff"},
            {"lat": 30.5728, "lng": 104.0668, "alt": 80, "action": "cruise"},
            {"lat": 30.5528, "lng": 104.0468, "alt": 0, "action": "land"},
        ]), "active", now),
    ]
    conn.executemany(
        "INSERT INTO flight_paths (id,drone_id,waypoints,status,created_at) VALUES (?,?,?,?,?)", paths
    )

    conn.commit()
    conn.close()
    logger.info("Seed data inserted.")


# ---- CRUD helpers ----
def get_all_drones() -> list[dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM drones ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_drone(drone_id: int) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM drones WHERE id=?", (drone_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_drone(drone_id: int, **kwargs):
    conn = get_conn()
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [drone_id]
    conn.execute(f"UPDATE drones SET {sets} WHERE id=?", vals)
    conn.commit()
    conn.close()


def get_all_orders() -> list[dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM orders ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_pending_orders() -> list[dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM orders WHERE status IN ('pending','assigned') ORDER BY priority DESC, id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_order(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng,
                 pickup_name="", dropoff_name="", cargo_type="general",
                 weight=1.0, priority=1, description="") -> dict:
    conn = get_conn()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.execute(
        "INSERT INTO orders (pickup_lat,pickup_lng,dropoff_lat,dropoff_lng,pickup_name,dropoff_name,cargo_type,weight,priority,status,description,created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (pickup_lat, pickup_lng, dropoff_lat, dropoff_lng, pickup_name, dropoff_name,
         cargo_type, weight, priority, "pending", description, now)
    )
    conn.commit()
    oid = cur.lastrowid
    row = conn.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone()
    conn.close()
    return dict(row)


def update_order(order_id: int, **kwargs):
    conn = get_conn()
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [order_id]
    conn.execute(f"UPDATE orders SET {sets} WHERE id=?", vals)
    conn.commit()
    conn.close()


def get_all_events() -> list[dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM events ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_active_events() -> list[dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM events WHERE status IN ('active','monitoring') ORDER BY severity DESC, id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_event(event_type, description, severity, lat, lng, drone_id=None) -> dict:
    conn = get_conn()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.execute(
        "INSERT INTO events (type,description,severity,lat,lng,status,drone_id,created_at) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (event_type, description, severity, lat, lng, "active", drone_id, now)
    )
    conn.commit()
    eid = cur.lastrowid
    row = conn.execute("SELECT * FROM events WHERE id=?", (eid,)).fetchone()
    conn.close()
    return dict(row)


def update_event(event_id: int, **kwargs):
    conn = get_conn()
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [event_id]
    conn.execute(f"UPDATE events SET {sets} WHERE id=?", vals)
    conn.commit()
    conn.close()


def get_all_flight_paths() -> list[dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM flight_paths ORDER BY id").fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["waypoints"] = json.loads(d["waypoints"])
        result.append(d)
    return result


def get_flight_paths_for_drone(drone_id: int) -> list[dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM flight_paths WHERE drone_id=? AND status='active'", (drone_id,)).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["waypoints"] = json.loads(d["waypoints"])
        result.append(d)
    return result


def create_flight_path(drone_id: int, waypoints: list, status="planned") -> dict:
    conn = get_conn()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.execute(
        "INSERT INTO flight_paths (drone_id,waypoints,status,created_at) VALUES (?,?,?,?)",
        (drone_id, json.dumps(waypoints), status, now)
    )
    conn.commit()
    fpid = cur.lastrowid
    row = conn.execute("SELECT * FROM flight_paths WHERE id=?", (fpid,)).fetchone()
    conn.close()
    d = dict(row)
    d["waypoints"] = json.loads(d["waypoints"])
    return d


def add_chat_message(role: str, content: str, agent_used: str = ""):
    conn = get_conn()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("INSERT INTO chat_history (role,content,agent_used,created_at) VALUES (?,?,?,?)",
                 (role, content, agent_used, now))
    conn.commit()
    conn.close()


def get_chat_history(limit: int = 20) -> list[dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM chat_history ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]
