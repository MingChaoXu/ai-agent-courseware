"""
基层门诊AI辅助诊疗 Skill Tool - 5 Modules + Patient DB
Usage:
    from tools.tool import (
        medical_generate_record, medical_interpret_lab,
        medical_recommend_treatment, medical_quality_control,
        medical_timeline_analysis, medical_health_check,
        patient_list, patient_detail, patient_add_vital,
        patient_add_medication, patient_add_diagnosis,
    )
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_BACKEND_DIR = _PROJECT_ROOT / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(_PROJECT_ROOT / ".env")

from config import Settings
from agent.agent import create_agent, analyze

VALID_MODULES = ["record", "lab", "treatment", "qc", "timeline"]


class Tool:
    def __init__(self):
        self._settings = Settings()
        self._agents = create_agent() if self._settings.is_configured() else None

    def is_ready(self) -> bool:
        return self._agents is not None

    def health_check(self) -> dict:
        return {
            "configured": self._settings.is_configured(),
            "ready": self.is_ready(),
            "modules": VALID_MODULES if self.is_ready() else [],
        }

    def initialize(self) -> dict:
        self._agents = create_agent()
        return {"status": "ok" if self._agents else "not_configured"}

    def run(self, module: str, input_text: str) -> str:
        if module not in VALID_MODULES:
            return f"[Error] Invalid module: {module}. Valid: {VALID_MODULES}"
        if not self._agents:
            self.initialize()
        if not self._agents:
            return "[Error] API not configured."
        result = analyze(self._agents, module, input_text)
        if result.get("error"):
            return result["error"]
        if isinstance(result["answer"], dict):
            return json.dumps(result["answer"], ensure_ascii=False, indent=2)
        return str(result["answer"])


_tool_instance: Optional[Tool] = None

def get_tool() -> Tool:
    global _tool_instance
    if _tool_instance is None:
        _tool_instance = Tool()
        _tool_instance.initialize()
    return _tool_instance


# ============================================================
# AI Analysis Modules
# ============================================================

def medical_generate_record(input_text: str) -> str:
    """生成规范门诊病历：从症状描述生成主诉、现病史、体检、诊断、处理意见等结构化病历。"""
    return get_tool().run("record", input_text)


def medical_interpret_lab(input_text: str) -> str:
    """解读检验报告：标注异常指标、解读临床意义、给出综合分析和复查建议。"""
    return get_tool().run("lab", input_text)


def medical_recommend_treatment(input_text: str) -> str:
    """推荐诊疗方案：根据症状推荐可能诊断、检查项目、用药方案和注意事项。"""
    return get_tool().run("treatment", input_text)


def medical_quality_control(input_text: str) -> str:
    """病历质控校验：按《病历书写基本规范》检查病历质量，评定等级并给出修改建议。"""
    return get_tool().run("qc", input_text)


def medical_timeline_analysis(input_text: str) -> str:
    """时序病情分析：根据患者多次就诊记录，分析病情演变趋势、治疗效果、风险预警，并给出后续管理建议。"""
    return get_tool().run("timeline", input_text)


def medical_health_check() -> str:
    """检查助手健康状态及可用模块。"""
    tool = get_tool()
    return json.dumps(tool.health_check(), ensure_ascii=False, indent=2)


# ============================================================
# Patient Database Tools
# ============================================================

def patient_list(keyword: str = "") -> str:
    """查询患者列表，可按姓名或手机号搜索。返回患者ID、姓名、性别、年龄、就诊次数等信息。"""
    from db.database import list_patients as _list
    result = _list(keyword)
    return json.dumps(result, ensure_ascii=False, indent=2)


def patient_detail(patient_id: int) -> str:
    """获取患者完整档案：基本信息、诊断、当前用药、指标趋势、就诊记录。用于查看患者的全貌。"""
    from db.database import get_patient_summary
    summary = get_patient_summary(patient_id)
    if not summary:
        return f"[Error] Patient {patient_id} not found"
    # Simplify for output: truncate large fields
    out = {
        "patient": summary["patient"],
        "diagnoses": summary["diagnoses"],
        "medications": summary["medications"],
        "vital_trends": {k: v for k, v in summary.get("vital_trends", {}).items()},
        "visit_count": len(summary.get("visits", [])),
        "recent_visits": summary.get("visits", [])[:5],
    }
    return json.dumps(out, ensure_ascii=False, indent=2)


def patient_add_vital(patient_id: int, metric: str, value: float,
                      measure_date: str = "", source: str = "manual") -> str:
    """为患者录入一项关键指标数值（如血压、血糖、心率等），用于后续趋势分析。

    可用metric: systolic_bp(收缩压), diastolic_bp(舒张压), heart_rate(心率),
    fasting_glucose(空腹血糖), hba1c(糖化血红蛋白), temperature(体温),
    spo2(血氧), weight(体重), bmi, cr(肌酐), alt(谷丙转氨酶),
    hb(血红蛋白), wbc(白细胞), tc(总胆固醇), ldl_c, ua(尿酸)
    """
    from db.database import add_vital_sign, get_patient
    if not get_patient(patient_id):
        return f"[Error] Patient {patient_id} not found"
    result = add_vital_sign(patient_id, metric, value, measure_date=measure_date, source=source)
    return json.dumps(result, ensure_ascii=False, indent=2)


def patient_add_medication(patient_id: int, drug_name: str, dosage: str = "",
                           frequency: str = "", start_date: str = "") -> str:
    """为患者添加当前用药记录。"""
    from db.database import add_medication, get_patient
    if not get_patient(patient_id):
        return f"[Error] Patient {patient_id} not found"
    result = add_medication(patient_id, drug_name, dosage, frequency, start_date=start_date)
    return json.dumps(result, ensure_ascii=False, indent=2)


def patient_add_diagnosis(patient_id: int, diagnosis_name: str, is_chronic: bool = False,
                          diagnosed_date: str = "") -> str:
    """为患者添加诊断记录，可标记为慢性病。"""
    from db.database import add_diagnosis, get_patient
    if not get_patient(patient_id):
        return f"[Error] Patient {patient_id} not found"
    result = add_diagnosis(patient_id, diagnosis_name, is_chronic=is_chronic, diagnosed_date=diagnosed_date)
    return json.dumps(result, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="基层门诊AI辅助诊疗 Skill Tool")
    parser.add_argument("action", choices=["record", "lab", "treatment", "qc", "timeline", "health",
                                           "patient-list", "patient-detail", "patient-add-vital",
                                           "patient-add-med", "patient-add-diag"], help="Action to perform")
    parser.add_argument("-q", "--question", help="Input text for AI modules")
    parser.add_argument("--patient-id", type=int, help="Patient ID for patient operations")
    parser.add_argument("--keyword", help="Search keyword for patient list")
    parser.add_argument("--metric", help="Vital sign metric key")
    parser.add_argument("--value", type=float, help="Vital sign value")
    parser.add_argument("--drug", help="Drug name")
    parser.add_argument("--dosage", help="Drug dosage")
    parser.add_argument("--diagnosis", help="Diagnosis name")
    parser.add_argument("--chronic", action="store_true", help="Mark as chronic")
    args = parser.parse_args()

    if args.action == "health":
        tool = Tool()
        print(json.dumps(tool.health_check(), ensure_ascii=False, indent=2))
    elif args.action == "patient-list":
        print(patient_list(args.keyword or ""))
    elif args.action == "patient-detail":
        if not args.patient_id: print("Please provide --patient-id"); sys.exit(1)
        print(patient_detail(args.patient_id))
    elif args.action == "patient-add-vital":
        if not all([args.patient_id, args.metric, args.value is not None]):
            print("Please provide --patient-id, --metric, --value"); sys.exit(1)
        print(patient_add_vital(args.patient_id, args.metric, args.value))
    elif args.action == "patient-add-med":
        if not all([args.patient_id, args.drug]):
            print("Please provide --patient-id, --drug"); sys.exit(1)
        print(patient_add_medication(args.patient_id, args.drug, args.dosage or "", ""))
    elif args.action == "patient-add-diag":
        if not all([args.patient_id, args.diagnosis]):
            print("Please provide --patient-id, --diagnosis"); sys.exit(1)
        print(patient_add_diagnosis(args.patient_id, args.diagnosis, args.chronic))
    else:
        # AI module
        if not args.question:
            print("Please provide input with -q"); sys.exit(1)
        tool = Tool()
        if not tool.is_ready(): tool.initialize()
        print(tool.run(args.action, args.question))
