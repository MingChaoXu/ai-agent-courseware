"""
SQLite Database Layer for Patient Records
Tables: patients, visits, vital_signs, medications, diagnoses
Lightweight, zero-config, no extra dependencies.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

DB_PATH = str(Path(__file__).resolve().parent.parent / "data" / "patients.db")


def get_conn() -> sqlite3.Connection:
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create all tables if not exist."""
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            gender TEXT NOT NULL DEFAULT '未知',
            age INTEGER,
            phone TEXT DEFAULT '',
            id_card TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            visit_date TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            module TEXT NOT NULL DEFAULT 'record',
            input_text TEXT NOT NULL DEFAULT '',
            result_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS vital_signs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            measure_date TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            metric TEXT NOT NULL,
            value REAL NOT NULL,
            unit TEXT NOT NULL DEFAULT '',
            source TEXT DEFAULT 'manual',
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            drug_name TEXT NOT NULL,
            dosage TEXT DEFAULT '',
            frequency TEXT DEFAULT '',
            start_date TEXT DEFAULT '',
            end_date TEXT DEFAULT '',
            is_current INTEGER NOT NULL DEFAULT 1,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS diagnoses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            diagnosis_name TEXT NOT NULL,
            icd_code TEXT DEFAULT '',
            is_chronic INTEGER NOT NULL DEFAULT 0,
            diagnosed_date TEXT DEFAULT '',
            status TEXT DEFAULT 'active',
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_visits_patient ON visits(patient_id);
        CREATE INDEX IF NOT EXISTS idx_visits_date ON visits(patient_id, visit_date);
        CREATE INDEX IF NOT EXISTS idx_vitals_patient ON vital_signs(patient_id);
        CREATE INDEX IF NOT EXISTS idx_vitals_metric ON vital_signs(patient_id, metric);
        CREATE INDEX IF NOT EXISTS idx_vitals_date ON vital_signs(patient_id, metric, measure_date);
        CREATE INDEX IF NOT EXISTS idx_meds_patient ON medications(patient_id);
        CREATE INDEX IF NOT EXISTS idx_diag_patient ON diagnoses(patient_id);
    """)
    conn.commit()
    conn.close()


# ============================================================
# Patient CRUD
# ============================================================

def create_patient(name: str, gender: str = "未知", age: int = None,
                   phone: str = "", id_card: str = "", notes: str = "") -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO patients (name, gender, age, phone, id_card, notes) VALUES (?, ?, ?, ?, ?, ?)",
        (name, gender, age, phone, id_card, notes)
    )
    patient_id = cur.lastrowid
    conn.commit()
    row = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    conn.close()
    return dict(row)


def list_patients(keyword: str = "") -> List[Dict[str, Any]]:
    conn = get_conn()
    if keyword:
        rows = conn.execute(
            "SELECT * FROM patients WHERE name LIKE ? OR phone LIKE ? ORDER BY id DESC",
            (f"%{keyword}%", f"%{keyword}%")
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM patients ORDER BY id DESC").fetchall()
    conn.close()
    result = []
    for r in rows:
        p = dict(r)
        conn2 = get_conn()
        vc = conn2.execute("SELECT COUNT(*) as cnt FROM visits WHERE patient_id = ?", (p["id"],)).fetchone()["cnt"]
        mc = conn2.execute("SELECT COUNT(*) as cnt FROM medications WHERE patient_id = ? AND is_current = 1", (p["id"],)).fetchone()["cnt"]
        dc = conn2.execute("SELECT COUNT(*) as cnt FROM diagnoses WHERE patient_id = ? AND status = 'active'", (p["id"],)).fetchone()["cnt"]
        conn2.close()
        p["visit_count"] = vc
        p["med_count"] = mc
        p["diag_count"] = dc
        result.append(p)
    return result


def get_patient(patient_id: int) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_patient(patient_id: int, **kwargs) -> Optional[Dict[str, Any]]:
    allowed = {"name", "gender", "age", "phone", "id_card", "notes"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return get_patient(patient_id)
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    conn = get_conn()
    conn.execute(f"UPDATE patients SET {set_clause} WHERE id = ?", (*updates.values(), patient_id))
    conn.commit()
    conn.close()
    return get_patient(patient_id)


def delete_patient(patient_id: int) -> bool:
    conn = get_conn()
    conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    conn.commit()
    affected = conn.total_changes
    conn.close()
    return affected > 0


# ============================================================
# Visit CRUD
# ============================================================

def add_visit(patient_id: int, module: str, input_text: str, result: Any) -> Dict[str, Any]:
    conn = get_conn()
    result_json = json.dumps(result, ensure_ascii=False) if isinstance(result, (dict, list)) else str(result)
    cur = conn.execute(
        "INSERT INTO visits (patient_id, module, input_text, result_json) VALUES (?, ?, ?, ?)",
        (patient_id, module, input_text, result_json)
    )
    visit_id = cur.lastrowid
    conn.commit()
    row = conn.execute("SELECT * FROM visits WHERE id = ?", (visit_id,)).fetchone()
    conn.close()
    return dict(row)


def get_visits(patient_id: int) -> List[Dict[str, Any]]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM visits WHERE patient_id = ? ORDER BY visit_date DESC",
        (patient_id,)
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        v = dict(r)
        try:
            v["result"] = json.loads(v["result_json"])
        except (json.JSONDecodeError, TypeError):
            v["result"] = v["result_json"]
        result.append(v)
    return result


def get_visit(visit_id: int) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM visits WHERE id = ?", (visit_id,)).fetchone()
    conn.close()
    if not row:
        return None
    v = dict(row)
    try:
        v["result"] = json.loads(v["result_json"])
    except (json.JSONDecodeError, TypeError):
        v["result"] = v["result_json"]
    return v


def delete_visit(visit_id: int) -> bool:
    conn = get_conn()
    conn.execute("DELETE FROM visits WHERE id = ?", (visit_id,))
    conn.commit()
    affected = conn.total_changes
    conn.close()
    return affected > 0


# ============================================================
# Vital Signs (key metrics for trend charts)
# ============================================================

VITAL_METRICS = {
    "systolic_bp": {"label": "收缩压", "unit": "mmHg", "normal_range": [90, 140]},
    "diastolic_bp": {"label": "舒张压", "unit": "mmHg", "normal_range": [60, 90]},
    "heart_rate": {"label": "心率", "unit": "次/分", "normal_range": [60, 100]},
    "fasting_glucose": {"label": "空腹血糖", "unit": "mmol/L", "normal_range": [3.9, 6.1]},
    "hba1c": {"label": "糖化血红蛋白", "unit": "%", "normal_range": [4.0, 6.0]},
    "temperature": {"label": "体温", "unit": "℃", "normal_range": [36.0, 37.3]},
    "spo2": {"label": "血氧饱和度", "unit": "%", "normal_range": [95, 100]},
    "weight": {"label": "体重", "unit": "kg", "normal_range": None},
    "bmi": {"label": "BMI", "unit": "kg/m²", "normal_range": [18.5, 24.0]},
    "cr": {"label": "肌酐", "unit": "μmol/L", "normal_range": [44, 133]},
    "alt": {"label": "谷丙转氨酶", "unit": "U/L", "normal_range": [0, 40]},
    "hb": {"label": "血红蛋白", "unit": "g/L", "normal_range": [115, 150]},
    "wbc": {"label": "白细胞", "unit": "×10⁹/L", "normal_range": [4, 10]},
    "tc": {"label": "总胆固醇", "unit": "mmol/L", "normal_range": [0, 5.2]},
    "ldl_c": {"label": "LDL-C", "unit": "mmol/L", "normal_range": [0, 3.4]},
    "ua": {"label": "尿酸", "unit": "μmol/L", "normal_range": [150, 420]},
}


def add_vital_sign(patient_id: int, metric: str, value: float,
                   unit: str = "", measure_date: str = "",
                   source: str = "manual") -> Dict[str, Any]:
    """Add a vital sign measurement. metric must be a key in VITAL_METRICS."""
    if not measure_date:
        measure_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    if not unit and metric in VITAL_METRICS:
        unit = VITAL_METRICS[metric]["unit"]
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO vital_signs (patient_id, measure_date, metric, value, unit, source) VALUES (?, ?, ?, ?, ?, ?)",
        (patient_id, measure_date, metric, value, unit, source)
    )
    vs_id = cur.lastrowid
    conn.commit()
    row = conn.execute("SELECT * FROM vital_signs WHERE id = ?", (vs_id,)).fetchone()
    conn.close()
    return dict(row)


def get_vital_signs(patient_id: int, metric: str = None) -> List[Dict[str, Any]]:
    """Get vital signs, optionally filtered by metric."""
    conn = get_conn()
    if metric:
        rows = conn.execute(
            "SELECT * FROM vital_signs WHERE patient_id = ? AND metric = ? ORDER BY measure_date ASC",
            (patient_id, metric)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM vital_signs WHERE patient_id = ? ORDER BY measure_date ASC",
            (patient_id,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_vital_trends(patient_id: int) -> Dict[str, List[Dict]]:
    """Get all metrics as {metric: [{date, value, unit}, ...]} for frontend charting."""
    all_signs = get_vital_signs(patient_id)
    trends: Dict[str, List[Dict]] = {}
    for s in all_signs:
        m = s["metric"]
        if m not in trends:
            trends[m] = []
        trends[m].append({
            "date": s["measure_date"],
            "value": s["value"],
            "unit": s["unit"],
        })
    return trends


def delete_vital_sign(vital_id: int) -> bool:
    conn = get_conn()
    conn.execute("DELETE FROM vital_signs WHERE id = ?", (vital_id,))
    conn.commit()
    affected = conn.total_changes
    conn.close()
    return affected > 0


# ============================================================
# Medications
# ============================================================

def add_medication(patient_id: int, drug_name: str, dosage: str = "",
                   frequency: str = "", start_date: str = "",
                   end_date: str = "", is_current: bool = True,
                   notes: str = "") -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO medications (patient_id, drug_name, dosage, frequency, start_date, end_date, is_current, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (patient_id, drug_name, dosage, frequency, start_date, end_date, 1 if is_current else 0, notes)
    )
    med_id = cur.lastrowid
    conn.commit()
    row = conn.execute("SELECT * FROM medications WHERE id = ?", (med_id,)).fetchone()
    conn.close()
    return dict(row)


def get_medications(patient_id: int, current_only: bool = False) -> List[Dict[str, Any]]:
    conn = get_conn()
    if current_only:
        rows = conn.execute(
            "SELECT * FROM medications WHERE patient_id = ? AND is_current = 1 ORDER BY start_date DESC",
            (patient_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM medications WHERE patient_id = ? ORDER BY is_current DESC, start_date DESC",
            (patient_id,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_medication(med_id: int, **kwargs) -> Optional[Dict[str, Any]]:
    allowed = {"drug_name", "dosage", "frequency", "start_date", "end_date", "is_current", "notes"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if "is_current" in updates and isinstance(updates["is_current"], bool):
        updates["is_current"] = 1 if updates["is_current"] else 0
    if not updates:
        return None
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    conn = get_conn()
    conn.execute(f"UPDATE medications SET {set_clause} WHERE id = ?", (*updates.values(), med_id))
    conn.commit()
    row = conn.execute("SELECT * FROM medications WHERE id = ?", (med_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def stop_medication(med_id: int) -> Optional[Dict[str, Any]]:
    """Mark a medication as discontinued."""
    return update_medication(med_id, is_current=False, end_date=datetime.now().strftime("%Y-%m-%d"))


def delete_medication(med_id: int) -> bool:
    conn = get_conn()
    conn.execute("DELETE FROM medications WHERE id = ?", (med_id,))
    conn.commit()
    affected = conn.total_changes
    conn.close()
    return affected > 0


# ============================================================
# Diagnoses
# ============================================================

def add_diagnosis(patient_id: int, diagnosis_name: str, icd_code: str = "",
                  is_chronic: bool = False, diagnosed_date: str = "",
                  status: str = "active", notes: str = "") -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO diagnoses (patient_id, diagnosis_name, icd_code, is_chronic, diagnosed_date, status, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (patient_id, diagnosis_name, icd_code, 1 if is_chronic else 0, diagnosed_date, status, notes)
    )
    diag_id = cur.lastrowid
    conn.commit()
    row = conn.execute("SELECT * FROM diagnoses WHERE id = ?", (diag_id,)).fetchone()
    conn.close()
    return dict(row)


def get_diagnoses(patient_id: int, active_only: bool = False) -> List[Dict[str, Any]]:
    conn = get_conn()
    if active_only:
        rows = conn.execute(
            "SELECT * FROM diagnoses WHERE patient_id = ? AND status = 'active' ORDER BY is_chronic DESC, diagnosed_date DESC",
            (patient_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM diagnoses WHERE patient_id = ? ORDER BY status ASC, diagnosed_date DESC",
            (patient_id,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_diagnosis(diag_id: int, **kwargs) -> Optional[Dict[str, Any]]:
    allowed = {"diagnosis_name", "icd_code", "is_chronic", "diagnosed_date", "status", "notes"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if "is_chronic" in updates and isinstance(updates["is_chronic"], bool):
        updates["is_chronic"] = 1 if updates["is_chronic"] else 0
    if not updates:
        return None
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    conn = get_conn()
    conn.execute(f"UPDATE diagnoses SET {set_clause} WHERE id = ?", (*updates.values(), diag_id))
    conn.commit()
    row = conn.execute("SELECT * FROM diagnoses WHERE id = ?", (diag_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def resolve_diagnosis(diag_id: int) -> Optional[Dict[str, Any]]:
    """Mark a diagnosis as resolved."""
    return update_diagnosis(diag_id, status="resolved")


# ============================================================
# Patient Summary (comprehensive)
# ============================================================

def get_patient_summary(patient_id: int) -> Dict[str, Any]:
    """Get comprehensive patient summary for display."""
    patient = get_patient(patient_id)
    if not patient:
        return {}
    visits = get_visits(patient_id)
    vitals = get_vital_trends(patient_id)
    meds = get_medications(patient_id, current_only=True)
    diags = get_diagnoses(patient_id, active_only=True)
    return {
        "patient": patient,
        "visits": visits,
        "vital_trends": vitals,
        "medications": meds,
        "diagnoses": diags,
    }


# ============================================================
# Timeline text for AI analysis
# ============================================================

def get_patient_timeline_text(patient_id: int) -> str:
    """Get a formatted text of all visits + vitals + meds for AI timeline analysis."""
    summary = get_patient_summary(patient_id)
    if not summary:
        return ""

    patient = summary["patient"]
    lines = [f"患者：{patient['name']}，{patient['gender']}，{patient['age']}岁"]
    lines.append(f"手机：{patient['phone']}")
    if patient.get("notes"):
        lines.append(f"备注：{patient['notes']}")

    # Active diagnoses
    if summary["diagnoses"]:
        lines.append("\n=== 当前诊断 ===")
        for d in summary["diagnoses"]:
            chronic_tag = " [慢病]" if d.get("is_chronic") else ""
            lines.append(f"- {d['diagnosis_name']}{chronic_tag}（确诊：{d.get('diagnosed_date', '不详')}）")

    # Current medications
    if summary["medications"]:
        lines.append("\n=== 当前用药 ===")
        for m in summary["medications"]:
            freq = f" {m['frequency']}" if m.get("frequency") else ""
            lines.append(f"- {m['drug_name']} {m['dosage']}{freq}")

    # Vital trends
    if summary["vital_trends"]:
        lines.append("\n=== 关键指标时序 ===")
        for metric, points in summary["vital_trends"].items():
            label = VITAL_METRICS.get(metric, {}).get("label", metric)
            unit = VITAL_METRICS.get(metric, {}).get("unit", "")
            values_str = ", ".join(f"{p['date'][:10]}:{p['value']}{unit}" for p in points)
            lines.append(f"{label}：{values_str}")

    # Visit records
    if summary["visits"]:
        lines.append("\n=== 就诊记录时序 ===\n")
        for i, v in enumerate(reversed(summary["visits"]), 1):
            lines.append(f"【第{i}次就诊】 {v['visit_date']}")
            lines.append(f"功能模块：{_module_label(v['module'])}")
            lines.append(f"输入内容：{v['input_text'][:200]}")
            if isinstance(v.get("result"), dict):
                for k, val in v["result"].items():
                    lines.append(f"  {k}：{str(val)[:150]}")
            lines.append("")

    return "\n".join(lines)


def _module_label(module: str) -> str:
    return {"record": "病历生成", "lab": "检验解读", "treatment": "诊疗推荐",
            "qc": "病历质控", "timeline": "时序分析"}.get(module, module)


# ============================================================
# Seed Data
# ============================================================

def seed_if_empty():
    """Insert sample patients with rich history if DB is empty."""
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) as cnt FROM patients").fetchone()["cnt"]
    conn.close()
    if count > 0:
        return

    # ---- Patient 1: 张建国 - 慢性支气管炎 → 慢阻肺 ----
    p1 = create_patient("张建国", "男", 55, phone="13812345678", notes="长期吸烟史，高血压")
    add_diagnosis(p1["id"], "慢性阻塞性肺疾病", "J44.1", is_chronic=True, diagnosed_date="2026-03-15", notes="GOLD II级")
    add_diagnosis(p1["id"], "高血压病", "I10", is_chronic=True, diagnosed_date="2024-06-10", notes="2级中危")
    add_medication(p1["id"], "噻托溴铵粉吸入剂", "18μg", "qd", start_date="2026-03-15")
    add_medication(p1["id"], "沙美特罗替卡松吸入剂", "50/250μg", "bid", start_date="2026-03-15")
    add_medication(p1["id"], "氨氯地平片", "5mg", "qd", start_date="2024-06-10")

    # Vitals over time
    for date, sbp, dbp, hr in [
        ("2026-01-10", 145, 92, 82), ("2026-02-14", 138, 88, 78),
        ("2026-03-15", 132, 85, 76), ("2026-04-20", 128, 82, 74),
        ("2026-05-18", 130, 84, 72), ("2026-06-22", 126, 80, 70),
    ]:
        add_vital_sign(p1["id"], "systolic_bp", sbp, measure_date=date, source="visit")
        add_vital_sign(p1["id"], "diastolic_bp", dbp, measure_date=date, source="visit")
        add_vital_sign(p1["id"], "heart_rate", hr, measure_date=date, source="visit")

    for date, wbc, hb in [
        ("2026-01-10", 12.5, 145), ("2026-03-15", 8.2, 142),
        ("2026-05-18", 6.8, 140),
    ]:
        add_vital_sign(p1["id"], "wbc", wbc, measure_date=date, source="lab")
        add_vital_sign(p1["id"], "hb", hb, measure_date=date, source="lab")

    # Visits
    add_visit(p1["id"], "record", "患者张某，男，55岁，反复咳嗽1月余，伴胸闷气短，咳白色粘痰，晨起加重",
              {"patient_info": "张建国，男，55岁", "chief_complaint": "反复咳嗽1月余", "present_illness": "受凉后咳嗽加重，咳白色粘痰，活动后气促", "past_history": "慢性支气管炎5年，高血压2年", "physical_examination": "T 36.5℃，P 82次/分，R 20次/分，BP 145/92mmHg。双肺呼吸音粗，可闻散在干啰音", "preliminary_diagnosis": "1.慢性支气管炎急性加重；2.高血压病", "treatment_plan": "盐酸氨溴索口服液10ml tid；头孢克洛0.375g bid；氨氯地平5mg qd"})
    add_visit(p1["id"], "lab", "血常规：WBC 12.5×10^9/L，中性粒82%，CRP 35mg/L",
              {"report_type": "血常规", "key_indicators": [{"name": "WBC", "value": "12.5×10^9/L", "is_abnormal": True, "clinical_significance": "提示细菌感染"}, {"name": "中性粒细胞%", "value": "82%", "is_abnormal": True, "clinical_significance": "细菌感染"}, {"name": "CRP", "value": "35mg/L", "is_abnormal": True, "clinical_significance": "炎症标志物升高"}], "overall_interpretation": "白细胞及中性粒细胞升高，提示急性细菌感染", "follow_up_suggestions": "3天后复查血常规"})
    add_visit(p1["id"], "record", "患者张建国复诊，咳嗽减轻但仍气促，活动后明显，肺功能检查FEV1/FVC=62%",
              {"patient_info": "张建国，男，55岁", "chief_complaint": "气促2月，活动后加重", "present_illness": "上次就诊后咳嗽减轻，但气促无明显改善", "past_history": "慢性支气管炎5年，高血压2年", "physical_examination": "T 36.3℃，双肺呼吸音低，呼气延长", "preliminary_diagnosis": "1.慢性阻塞性肺疾病（GOLD II级）；2.高血压病", "treatment_plan": "噻托溴铵粉吸入剂18μg qd；沙美特罗替卡松吸入bid；继续氨氯地平5mg qd"})

    # ---- Patient 2: 李红 - 2型糖尿病进展 ----
    p2 = create_patient("李红", "女", 48, phone="13698765432", notes="糖尿病家族史，BMI 27.5")
    add_diagnosis(p2["id"], "2型糖尿病", "E11.9", is_chronic=True, diagnosed_date="2026-01-08", notes="初诊HbA1c 8.1%")
    add_diagnosis(p2["id"], "高脂血症", "E78.5", is_chronic=True, diagnosed_date="2026-01-08")
    add_diagnosis(p2["id"], "糖尿病肾病?", "E11.2", is_chronic=False, diagnosed_date="2026-04-12", notes="Cr偏高待确认")
    add_medication(p2["id"], "二甲双胍缓释片", "0.5g", "bid", start_date="2026-01-08")
    add_medication(p2["id"], "恩格列净片", "10mg", "qd", start_date="2026-04-12", notes="因肾功能异常加用")
    add_medication(p2["id"], "阿托伐他汀钙片", "20mg", "qn", start_date="2026-01-08")

    for date, fg, hba1c, cr_val in [
        ("2026-01-08", 9.2, 8.1, 78), ("2026-02-12", 8.5, 7.6, 85),
        ("2026-03-10", 7.8, 7.2, 110), ("2026-04-12", 7.5, 6.9, 135),
        ("2026-05-15", 7.0, 6.8, 128), ("2026-06-20", 6.8, 6.6, 122),
    ]:
        add_vital_sign(p2["id"], "fasting_glucose", fg, measure_date=date, source="lab")
        add_vital_sign(p2["id"], "hba1c", hba1c, measure_date=date, source="lab")
        add_vital_sign(p2["id"], "cr", cr_val, measure_date=date, source="lab")

    for date, sbp, dbp in [
        ("2026-01-08", 128, 82), ("2026-02-12", 125, 80),
        ("2026-03-10", 122, 78), ("2026-04-12", 130, 84),
        ("2026-05-15", 118, 76), ("2026-06-20", 120, 78),
    ]:
        add_vital_sign(p2["id"], "systolic_bp", sbp, measure_date=date, source="visit")
        add_vital_sign(p2["id"], "diastolic_bp", dbp, measure_date=date, source="visit")

    add_visit(p2["id"], "treatment", "体检发现空腹血糖9.2mmol/L，HbA1c 8.1%，口干多饮多尿3月，体重下降5kg",
              {"possible_diagnoses": "1.2型糖尿病；2.高脂血症", "recommended_exams": "空腹血糖、餐后2h血糖、HbA1c、尿常规、眼底检查", "medication_suggestions": "二甲双胍缓释片0.5g bid；阿托伐他汀20mg qn", "precautions": "控制饮食，每日运动30分钟", "risk_alerts": "注意监测血糖，警惕低血糖反应"})
    add_visit(p2["id"], "lab", "空腹血糖7.8mmol/L，HbA1c 7.2%，Cr 135μmol/L，UA 480μmol/L",
              {"report_type": "肾功能+血糖", "key_indicators": [{"name": "Cr", "value": "135μmol/L", "is_abnormal": True, "clinical_significance": "肾功能轻度受损"}, {"name": "HbA1c", "value": "7.2%", "is_abnormal": True, "clinical_significance": "血糖控制欠佳"}, {"name": "UA", "value": "480μmol/L", "is_abnormal": True, "clinical_significance": "高尿酸血症"}], "overall_interpretation": "血糖较前下降但未达标，肾功能出现异常，尿酸偏高", "follow_up_suggestions": "调整降糖方案，肾内科会诊"})
    add_visit(p2["id"], "record", "李红复诊，血糖控制欠佳，肌酐偏高，需调整方案",
              {"patient_info": "李红，女，48岁", "chief_complaint": "2型糖尿病复诊，血糖未达标", "present_illness": "服用二甲双胍3月，空腹血糖7.8，肾功能异常", "past_history": "2型糖尿病，父亲糖尿病史", "physical_examination": "BMI 26.5，双下肢无水肿", "preliminary_diagnosis": "1.2型糖尿病（血糖未达标）；2.糖尿病肾病？", "treatment_plan": "加用恩格列净10mg qd；肾内科会诊；低蛋白饮食"})

    # ---- Patient 3: 王小明 - 儿科反复呼吸道感染 ----
    p3 = create_patient("王小明", "男", 5, phone="15900001111", notes="按时接种疫苗")
    add_diagnosis(p3["id"], "反复呼吸道感染", "J98.9", is_chronic=False, diagnosed_date="2026-05-20", notes="3次/年")
    add_medication(p3["id"], "布洛芬混悬液", "5ml", "prn", start_date="2026-05-20", notes="发热时使用")

    for date, temp_val in [
        ("2026-04-15", 38.5), ("2026-05-20", 39.0), ("2026-06-10", 37.2),
    ]:
        add_vital_sign(p3["id"], "temperature", temp_val, measure_date=date, source="visit")

    for date, wbc_val in [
        ("2026-04-15", 11.2), ("2026-05-20", 14.8), ("2026-06-10", 7.5),
    ]:
        add_vital_sign(p3["id"], "wbc", wbc_val, measure_date=date, source="lab")

    add_visit(p3["id"], "record", "患儿男，5岁，发热3天，T38.5℃，咳嗽流涕，咽红，双肺呼吸音粗",
              {"patient_info": "王小明，男，5岁", "chief_complaint": "发热3天", "present_illness": "发热伴咳嗽流涕，食欲下降", "past_history": "既往体健", "physical_examination": "T38.5℃，咽充血，扁桃体I度", "preliminary_diagnosis": "急性上呼吸道感染", "treatment_plan": "布洛芬混悬液退热；小儿氨酚黄那敏颗粒"})
    add_visit(p3["id"], "record", "患儿王小明，1月后再发发热咳嗽，T39℃，咳黄痰，右肺湿啰音",
              {"patient_info": "王小明，男，5岁", "chief_complaint": "发热咳嗽2天", "present_illness": "1月前曾患上呼吸道感染，此次再发伴黄痰", "past_history": "反复呼吸道感染3次/年", "physical_examination": "T39℃，右下肺湿啰音", "preliminary_diagnosis": "1.支气管肺炎；2.反复呼吸道感染", "treatment_plan": "阿莫西林克拉维酸钾；胸片检查；免疫球蛋白检测"})

    # ---- Patient 4: 赵秀英 - 高血压+冠心病 ----
    p4 = create_patient("赵秀英", "女", 62, phone="13755556666", notes="冠心病支架术后2年")
    add_diagnosis(p4["id"], "冠状动脉性心脏病", "I25.1", is_chronic=True, diagnosed_date="2024-03-20", notes="支架术后")
    add_diagnosis(p4["id"], "高血压病3级", "I11.9", is_chronic=True, diagnosed_date="2023-01-15", notes="很高危")
    add_diagnosis(p4["id"], "高脂血症", "E78.5", is_chronic=True, diagnosed_date="2023-01-15")
    add_medication(p4["id"], "阿司匹林肠溶片", "100mg", "qd", start_date="2024-03-20")
    add_medication(p4["id"], "氯吡格雷片", "75mg", "qd", start_date="2024-03-20")
    add_medication(p4["id"], "阿托伐他汀钙片", "20mg", "qn", start_date="2024-03-20")
    add_medication(p4["id"], "美托洛尔缓释片", "47.5mg", "qd", start_date="2024-03-20")
    add_medication(p4["id"], "氨氯地平片", "5mg", "qd", start_date="2023-01-15")

    for date, sbp, dbp, hr in [
        ("2026-01-05", 155, 95, 78), ("2026-02-08", 148, 92, 76),
        ("2026-03-12", 142, 88, 72), ("2026-04-15", 135, 84, 70),
        ("2026-05-20", 132, 82, 68), ("2026-06-25", 130, 80, 66),
    ]:
        add_vital_sign(p4["id"], "systolic_bp", sbp, measure_date=date, source="visit")
        add_vital_sign(p4["id"], "diastolic_bp", dbp, measure_date=date, source="visit")
        add_vital_sign(p4["id"], "heart_rate", hr, measure_date=date, source="visit")

    for date, ldl, tc_val in [
        ("2026-01-05", 3.8, 5.8), ("2026-03-12", 2.6, 4.5),
        ("2026-05-20", 1.8, 3.9),
    ]:
        add_vital_sign(p4["id"], "ldl_c", ldl, measure_date=date, source="lab")
        add_vital_sign(p4["id"], "tc", tc_val, measure_date=date, source="lab")

    add_visit(p4["id"], "record", "赵秀英，女，62岁，冠心病支架术后2年定期复诊，偶有胸闷，血压偏高",
              {"patient_info": "赵秀英，女，62岁", "chief_complaint": "冠心病术后复诊，血压偏高", "present_illness": "支架术后2年，偶有活动后胸闷，血压控制欠佳", "past_history": "冠心病支架术后、高血压3级、高脂血症", "physical_examination": "BP 155/95mmHg，心率78次/分，律齐", "preliminary_diagnosis": "1.冠心病（支架术后）；2.高血压3级（很高危）；3.高脂血症", "treatment_plan": "继续双抗+他汀治疗；调整降压方案；定期复查血脂"})

    # ---- Patient 5: 陈伟 - 高尿酸→痛风 ----
    p5 = create_patient("陈伟", "男", 38, phone="18677778888", notes="饮酒史，嗜海鲜")
    add_diagnosis(p5["id"], "痛风", "M10.0", is_chronic=True, diagnosed_date="2026-04-08", notes="首次急性发作")
    add_diagnosis(p5["id"], "高尿酸血症", "E79.0", is_chronic=True, diagnosed_date="2025-11-20")
    add_medication(p5["id"], "非布司他片", "40mg", "qd", start_date="2026-04-15", notes="降尿酸")
    add_medication(p5["id"], "秋水仙碱片", "0.5mg", "prn", start_date="2026-04-08", notes="急性发作时服用")

    for date, ua_val, alt_val in [
        ("2025-11-20", 520, 28), ("2026-01-15", 490, 35),
        ("2026-03-10", 480, 42), ("2026-04-08", 510, 38),
        ("2026-05-20", 380, 30), ("2026-06-25", 350, 25),
    ]:
        add_vital_sign(p5["id"], "ua", ua_val, measure_date=date, source="lab")
        add_vital_sign(p5["id"], "alt", alt_val, measure_date=date, source="lab")

    add_visit(p5["id"], "record", "陈伟，男，38岁，右足第一跖趾关节红肿疼痛1天，既往高尿酸血症",
              {"patient_info": "陈伟，男，38岁", "chief_complaint": "右足关节肿痛1天", "present_illness": "饮酒后右足第一跖趾关节突发红肿热痛", "past_history": "高尿酸血症半年，饮酒嗜海鲜", "physical_examination": "右足第一跖趾关节红肿触痛，局部皮温升高", "preliminary_diagnosis": "1.急性痛风性关节炎；2.高尿酸血症", "treatment_plan": "秋水仙碱0.5mg q6h（首日）；非布司他40mg qd（急性期后开始）；禁酒禁海鲜"})

    print(f"[DB] Seeded 5 patients with rich history")


# Initialize on import
init_db()
seed_if_empty()
