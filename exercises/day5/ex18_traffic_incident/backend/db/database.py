"""
SQLite Database Layer for Traffic Incident Records
Tables: incidents, dispatches
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

DB_PATH = str(Path(__file__).resolve().parent.parent / "data" / "incidents.db")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            incident_type TEXT DEFAULT '',
            location TEXT DEFAULT '',
            severity TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            amap_mode TEXT DEFAULT '',
            ai_analysis TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS dispatches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id INTEGER NOT NULL,
            analysis_text TEXT NOT NULL DEFAULT '',
            dispatch_plan TEXT NOT NULL DEFAULT '',
            publish_text TEXT NOT NULL DEFAULT '',
            review_report TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (incident_id) REFERENCES incidents(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
        CREATE INDEX IF NOT EXISTS idx_incidents_type ON incidents(incident_type);
        CREATE INDEX IF NOT EXISTS idx_dispatches_incident ON dispatches(incident_id);
    """)
    conn.commit()
    conn.close()


# ============================================================
# Incident CRUD
# ============================================================

def create_incident(description: str, incident_type: str = "", location: str = "",
                    severity: str = "", status: str = "pending",
                    amap_mode: str = "", ai_analysis: str = "") -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO incidents (description, incident_type, location, severity, status, amap_mode, ai_analysis) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (description, incident_type, location, severity, status, amap_mode, ai_analysis)
    )
    incident_id = cur.lastrowid
    conn.commit()
    row = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
    conn.close()
    return dict(row)


def list_incidents(keyword: str = "", status: str = "") -> List[Dict[str, Any]]:
    conn = get_conn()
    query = "SELECT * FROM incidents"
    params = []
    conditions = []
    if keyword:
        conditions.append("(description LIKE ? OR location LIKE ? OR incident_type LIKE ?)")
        params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
    if status:
        conditions.append("status = ?")
        params.append(status)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    result = []
    for r in rows:
        inc = dict(r)
        conn2 = get_conn()
        dc = conn2.execute("SELECT COUNT(*) as cnt FROM dispatches WHERE incident_id = ?", (inc["id"],)).fetchone()["cnt"]
        conn2.close()
        inc["dispatch_count"] = dc
        result.append(inc)
    return result


def get_incident(incident_id: int) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_incident(incident_id: int, **kwargs) -> Optional[Dict[str, Any]]:
    allowed = {"incident_type", "location", "severity", "status", "ai_analysis", "amap_mode"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return get_incident(incident_id)
    updates["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    conn = get_conn()
    conn.execute(f"UPDATE incidents SET {set_clause} WHERE id = ?", (*updates.values(), incident_id))
    conn.commit()
    conn.close()
    return get_incident(incident_id)


def delete_incident(incident_id: int) -> bool:
    conn = get_conn()
    conn.execute("DELETE FROM incidents WHERE id = ?", (incident_id,))
    conn.commit()
    affected = conn.total_changes
    conn.close()
    return affected > 0


# ============================================================
# Dispatch CRUD
# ============================================================

def add_dispatch(incident_id: int, analysis_text: str = "", dispatch_plan: str = "",
                 publish_text: str = "", review_report: str = "") -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO dispatches (incident_id, analysis_text, dispatch_plan, publish_text, review_report) "
        "VALUES (?, ?, ?, ?, ?)",
        (incident_id, analysis_text, dispatch_plan, publish_text, review_report)
    )
    dispatch_id = cur.lastrowid
    conn.commit()
    # Update incident status
    conn.execute("UPDATE incidents SET status = 'dispatched', updated_at = datetime('now', 'localtime') WHERE id = ?", (incident_id,))
    conn.commit()
    row = conn.execute("SELECT * FROM dispatches WHERE id = ?", (dispatch_id,)).fetchone()
    conn.close()
    return dict(row)


def get_dispatches(incident_id: int) -> List[Dict[str, Any]]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM dispatches WHERE incident_id = ? ORDER BY created_at DESC",
        (incident_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_dispatch(dispatch_id: int) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM dispatches WHERE id = ?", (dispatch_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_dispatch(dispatch_id: int) -> bool:
    conn = get_conn()
    conn.execute("DELETE FROM dispatches WHERE id = ?", (dispatch_id,))
    conn.commit()
    affected = conn.total_changes
    conn.close()
    return affected > 0


# ============================================================
# Seed Data
# ============================================================

SEED_INCIDENTS = [
    {
        "description": "三环路辅路与人民路交叉口发生多车追尾事故，涉及4辆小轿车，1人受伤，占用外侧两条车道，交通中断",
        "incident_type": "交通事故",
        "location": "三环路辅路与人民路交叉口",
        "severity": "严重",
        "status": "resolved",
        "amap_mode": "offline",
        "ai_analysis": "4车追尾，1人受伤，占道2条，交通中断",
    },
    {
        "description": "成华大道与建设路交叉口路面塌陷，面积约10平方米，深度约2米，影响双向通行",
        "incident_type": "设施故障",
        "location": "成华大道与建设路交叉口",
        "severity": "特重大",
        "status": "dispatched",
        "amap_mode": "offline",
        "ai_analysis": "路面塌陷10平米深2米，双向通行受阻",
    },
    {
        "description": "绕城高速K35+200处发生危险化学品车辆泄漏事故，装载盐酸约20吨，有泄漏风险",
        "incident_type": "交通事故",
        "location": "绕城高速K35+200处",
        "severity": "特重大",
        "status": "dispatched",
        "amap_mode": "offline",
        "ai_analysis": "危化品车盐酸泄漏20吨，需紧急疏散",
    },
    {
        "description": "天府大道南段与科学城路口暴雨导致严重积水，水深约40厘米，多辆车辆熄火抛锚",
        "incident_type": "恶劣天气",
        "location": "天府大道南段与科学城路口",
        "severity": "严重",
        "status": "pending",
        "amap_mode": "offline",
        "ai_analysis": "暴雨积水40cm，多车熄火",
    },
    {
        "description": "光华大道与青羊大道交叉口施工区域围挡倒塌，占用一条机动车道，施工人员1人轻伤",
        "incident_type": "道路施工",
        "location": "光华大道与青羊大道交叉口",
        "severity": "一般",
        "status": "resolved",
        "amap_mode": "offline",
        "ai_analysis": "施工围挡倒塌占道1条，1人轻伤",
    },
]


def seed_if_empty():
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) as cnt FROM incidents").fetchone()["cnt"]
    conn.close()
    if count > 0:
        return

    for inc in SEED_INCIDENTS:
        created = create_incident(**inc)
        # Add a dispatch record for resolved/dispatched incidents
        if inc["status"] in ("resolved", "dispatched"):
            add_dispatch(
                incident_id=created["id"],
                analysis_text=f"事件类型：{inc['incident_type']}\n发生位置：{inc['location']}\n严重程度：{inc['severity']}",
                dispatch_plan="已派驻交警现场指挥，安排清障车清理现场，通知周边医院待命。",
                publish_text="[路况播报] " + inc["location"] + "发生" + inc["incident_type"] + "，请绕行。",
                review_report="事件处置完毕，响应及时，方案合理。" if inc["status"] == "resolved" else "事件正在处置中。",
            )

    print(f"[DB] Seeded {len(SEED_INCIDENTS)} incidents with dispatch records")


# Initialize on import
init_db()
seed_if_empty()
