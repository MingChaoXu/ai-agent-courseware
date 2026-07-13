"""
SQLite Database Layer for Patient Records
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
    """Create tables if not exist."""
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

        CREATE INDEX IF NOT EXISTS idx_visits_patient ON visits(patient_id);
        CREATE INDEX IF NOT EXISTS idx_visits_date ON visits(patient_id, visit_date);
    """)
    conn.commit()
    conn.close()


# ---- Patient CRUD ----

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
    # Add visit count
    result = []
    for r in rows:
        p = dict(r)
        conn2 = get_conn()
        p["visit_count"] = conn2.execute("SELECT COUNT(*) as cnt FROM visits WHERE patient_id = ?", (p["id"],)).fetchone()["cnt"]
        conn2.close()
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


# ---- Visit CRUD ----

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


# ---- Timeline summary for AI analysis ----

def get_patient_timeline_text(patient_id: int) -> str:
    """Get a formatted text of all visits for AI timeline analysis."""
    patient = get_patient(patient_id)
    if not patient:
        return ""
    visits = get_visits(patient_id)
    if not visits:
        return ""

    lines = [f"患者：{patient['name']}，{patient['gender']}，{patient['age']}岁"]
    lines.append(f"手机：{patient['phone']}\n")
    lines.append("=== 就诊记录时序 ===\n")

    for i, v in enumerate(reversed(visits), 1):
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


# ---- Seed Data ----

def seed_if_empty():
    """Insert sample patients with multiple visits if DB is empty."""
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) as cnt FROM patients").fetchone()["cnt"]
    conn.close()
    if count > 0:
        return

    # Patient 1: 张建国 - 慢性支气管炎 → 慢阻肺发展
    p1 = create_patient("张建国", "男", 55, phone="13812345678", notes="长期吸烟史")
    add_visit(p1["id"], "record", "患者张某，男，55岁，反复咳嗽1月余，伴胸闷气短，咳白色粘痰，晨起加重",
              {"patient_info": "张建国，男，55岁", "chief_complaint": "反复咳嗽1月余", "present_illness": "受凉后咳嗽加重，咳白色粘痰，活动后气促", "past_history": "慢性支气管炎5年", "physical_examination": "T 36.5℃，双肺呼吸音粗", "preliminary_diagnosis": "1.慢性支气管炎急性加重；2.高血压病", "treatment_plan": "盐酸氨溴索口服液10ml tid；头孢克洛0.375g bid"})
    add_visit(p1["id"], "lab", "血常规：WBC 12.5，中性粒82%，CRP 35mg/L",
              {"report_type": "血常规", "key_indicators": [{"name": "WBC", "value": "12.5×10^9/L", "is_abnormal": True, "clinical_significance": "提示细菌感染"}], "overall_interpretation": "白细胞及中性粒细胞升高，提示急性细菌感染", "follow_up_suggestions": "3天后复查血常规"})
    add_visit(p1["id"], "record", "患者张建国复诊，咳嗽减轻但仍气促，活动后明显，肺功能检查FEV1/FVC=62%",
              {"patient_info": "张建国，男，55岁", "chief_complaint": "气促2月，活动后加重", "present_illness": "上次就诊后咳嗽减轻，但气促无明显改善", "past_history": "慢性支气管炎5年，高血压2年", "physical_examination": "双肺呼吸音低，呼气延长", "preliminary_diagnosis": "1.慢性阻塞性肺疾病（GOLD II级）；2.高血压病", "treatment_plan": "噻托溴铵粉吸入剂18μg qd；沙美特罗替卡松吸入bid"})

    # Patient 2: 李红 - 2型糖尿病进展
    p2 = create_patient("李红", "女", 48, phone="13698765432", notes="糖尿病家族史")
    add_visit(p2["id"], "treatment", "体检发现空腹血糖9.2mmol/L，HbA1c 8.1%，口干多饮多尿3月，体重下降5kg",
              {"possible_diagnoses": "1.2型糖尿病；2.高脂血症", "recommended_exams": "空腹血糖、餐后2h血糖、HbA1c、尿常规、眼底检查", "medication_suggestions": "二甲双胍缓释片0.5g bid", "precautions": "控制饮食，每日运动30分钟", "risk_alerts": "注意监测血糖，警惕低血糖反应"})
    add_visit(p2["id"], "lab", "空腹血糖7.8mmol/L，HbA1c 7.2%，Cr 135μmol/L，UA 480μmol/L",
              {"report_type": "肾功能+血糖", "key_indicators": [{"name": "Cr", "value": "135μmol/L", "is_abnormal": True, "clinical_significance": "肾功能轻度受损"}, {"name": "HbA1c", "value": "7.2%", "is_abnormal": True, "clinical_significance": "血糖控制欠佳"}], "overall_interpretation": "血糖较前下降但未达标，肾功能出现异常", "follow_up_suggestions": "调整降糖方案，肾内科会诊"})
    add_visit(p2["id"], "record", "李红复诊，血糖控制欠佳，肌酐偏高，需调整方案",
              {"patient_info": "李红，女，48岁", "chief_complaint": "2型糖尿病复诊，血糖未达标", "present_illness": "服用二甲双胍3月，空腹血糖7.8，肾功能异常", "past_history": "2型糖尿病，父亲糖尿病史", "physical_examination": "BMI 26.5，双下肢无水肿", "preliminary_diagnosis": "1.2型糖尿病（血糖未达标）；2.糖尿病肾病？", "treatment_plan": "加用恩格列净10mg qd；肾内科会诊；低蛋白饮食"})

    # Patient 3: 王小明 - 儿科反复呼吸道感染
    p3 = create_patient("王小明", "男", 5, phone="15900001111", notes="按时接种疫苗", id_card="")
    add_visit(p3["id"], "record", "患儿男，5岁，发热3天，T38.5℃，咳嗽流涕，咽红，双肺呼吸音粗",
              {"patient_info": "王小明，男，5岁", "chief_complaint": "发热3天", "present_illness": "发热伴咳嗽流涕，食欲下降", "past_history": "既往体健", "physical_examination": "T38.5℃，咽充血，扁桃体I度", "preliminary_diagnosis": "急性上呼吸道感染", "treatment_plan": "布洛芬混悬液退热；小儿氨酚黄那敏颗粒"})
    add_visit(p3["id"], "record", "患儿王小明，1月后再发发热咳嗽，T39℃，咳黄痰，右肺湿啰音",
              {"patient_info": "王小明，男，5岁", "chief_complaint": "发热咳嗽2天", "present_illness": "1月前曾患上呼吸道感染，此次再发伴黄痰", "past_history": "反复呼吸道感染3次/年", "physical_examination": "T39℃，右下肺湿啰音", "preliminary_diagnosis": "1.支气管肺炎；2.反复呼吸道感染", "treatment_plan": "阿莫西林克拉维酸钾；胸片检查；免疫球蛋白检测"})

    print(f"[DB] Seeded 3 patients with visit history")


# Initialize on import
init_db()
seed_if_empty()
