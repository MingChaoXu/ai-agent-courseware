"""
Medical AI Assistant API - 5 modules + auto-archiving + smart extraction
"""

import re
from fastapi import APIRouter, HTTPException
from models.schemas import ChatRequest, ChatResponse
from typing import Optional

router = APIRouter(tags=["chat"])

# Global agent instance (initialized in main.py)
agent_instance = None

VALID_MODULES = ["record", "lab", "treatment", "qc", "timeline"]


def _extract_diagnoses_from_record(result: dict) -> list:
    """Try to extract diagnosis names from a record result."""
    diagnoses = []
    diag_text = result.get("preliminary_diagnosis", "")
    if not diag_text:
        return diagnoses
    # Split by common delimiters: numbered list, semicolons, Chinese semicolons
    parts = re.split(r'[；;]', diag_text)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Remove leading number like "1." or "1、"
        part = re.sub(r'^\d+[.、．)\]]\s*', '', part).strip()
        # Remove trailing quality/risk tags
        part = re.sub(r'[（(].*?[）)]$', '', part).strip()
        if part:
            diagnoses.append(part)
    return diagnoses


def _extract_medications_from_record(result: dict) -> list:
    """Try to extract medications from treatment_plan or medication_suggestions."""
    meds = []
    med_text = result.get("treatment_plan", "") or result.get("medication_suggestions", "")
    if not med_text:
        return meds
    # Split by semicolons/newlines
    parts = re.split(r'[；;\n]', med_text)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Remove leading number
        part = re.sub(r'^\d+[.、．)\]]\s*', '', part).strip()
        # Heuristic: if contains dosage pattern (number + mg/g/ml/μg), likely a medication
        if re.search(r'\d+\s*(mg|g|ml|μg|U|IU|片|粒|支|袋)', part, re.IGNORECASE):
            meds.append(part)
    return meds


def _extract_vitals_from_lab(result: dict) -> list:
    """Try to extract vital sign values from lab interpretation result."""
    vitals = []
    indicators = result.get("key_indicators", [])
    if not isinstance(indicators, list):
        return vitals

    # Mapping from common indicator names to vital_signs metric keys
    name_to_metric = {
        "血红蛋白": "hb", "hb": "hb",
        "白细胞": "wbc", "wbc": "wbc",
        "肌酐": "cr", "cr": "cr",
        "谷丙转氨酶": "alt", "alt": "alt",
        "总胆固醇": "tc", "tc": "tc",
        "LDL-C": "ldl_c", "ldl-c": "ldl_c",
        "尿酸": "ua", "ua": "ua",
        "空腹血糖": "fasting_glucose", "glu": "fasting_glucose", "血糖": "fasting_glucose",
        "糖化血红蛋白": "hba1c", "hba1c": "hba1c",
    }

    for ind in indicators:
        if not isinstance(ind, dict):
            continue
        name = ind.get("name", "").strip()
        is_abnormal = ind.get("is_abnormal", False)
        # Only extract abnormal indicators (most clinically relevant)
        if not is_abnormal:
            continue
        metric = None
        name_lower = name.lower()
        for key, m in name_to_metric.items():
            if key.lower() in name_lower:
                metric = m
                break
        if not metric:
            continue
        # Try to extract numeric value from the value field
        val_str = str(ind.get("value", ""))
        num_match = re.search(r'(\d+\.?\d*)', val_str)
        if num_match:
            value = float(num_match.group(1))
            vitals.append({"metric": metric, "value": value})
    return vitals


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Analyze input text and return structured result.

    The 'module' field selects which analysis to run:
    - 'record': 门诊病历生成
    - 'lab': 检验报告解读
    - 'treatment': 诊疗方案推荐
    - 'qc': 病历质控校验
    - 'timeline': 时序病情分析

    Optional 'patient_id' will archive the result to that patient's record
    and auto-extract diagnoses, medications, and vital signs.
    """
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized. Check API configuration.")

    module = getattr(request, "module", "record") or "record"
    if module not in VALID_MODULES:
        raise HTTPException(status_code=400, detail=f"Invalid module: {module}. Valid: {VALID_MODULES}")

    try:
        from agent.agent import analyze
        result = analyze(agent_instance, module, request.question)

        # Auto-archive to patient if patient_id provided
        patient_id = getattr(request, "patient_id", None)
        if patient_id and result.get("answer") and not result.get("error"):
            try:
                from db.database import (
                    add_visit, get_patient,
                    add_diagnosis, add_medication, add_vital_sign,
                    get_diagnoses,
                )
                if get_patient(patient_id):
                    # Archive the visit
                    add_visit(patient_id, module, request.question, result["answer"])

                    answer = result["answer"]
                    if isinstance(answer, dict):
                        # Extract diagnoses from record module
                        if module == "record":
                            new_diags = _extract_diagnoses_from_record(answer)
                            existing = get_diagnoses(patient_id, active_only=True)
                            existing_names = {d["diagnosis_name"] for d in existing}
                            for diag_name in new_diags:
                                # Only add if not already exists (fuzzy match)
                                if diag_name not in existing_names and not any(
                                    diag_name in en or en in diag_name for en in existing_names
                                ):
                                    # Heuristic: mark as chronic if contains common chronic keywords
                                    is_chronic = any(kw in diag_name for kw in [
                                        "慢性", "高血压", "糖尿病", "冠心病", "慢阻肺",
                                        "COPD", "高脂血症", "痛风", "哮喘",
                                    ])
                                    add_diagnosis(patient_id, diag_name, is_chronic=is_chronic)

                        # Extract medications from record/treatment module
                        if module in ("record", "treatment"):
                            new_meds = _extract_medications_from_record(answer)
                            if new_meds:
                                from db.database import get_medications
                                existing_meds = get_medications(patient_id, current_only=True)
                                existing_drug_names = {m["drug_name"] for m in existing_meds}
                                for med_text in new_meds[:5]:  # Limit to 5 to avoid noise
                                    # Try to split drug name from dosage
                                    # Pattern: "药品名 剂量 频次" or "药品名剂量频次"
                                    parts = re.split(r'\s+', med_text, maxsplit=2)
                                    drug_name = parts[0] if parts else med_text
                                    dosage = parts[1] if len(parts) > 1 else ""
                                    freq = parts[2] if len(parts) > 2 else ""
                                    # Only add if drug name not already present
                                    if drug_name not in existing_drug_names:
                                        add_medication(patient_id, drug_name, dosage, freq)

                        # Extract vital signs from lab module
                        if module == "lab":
                            new_vitals = _extract_vitals_from_lab(answer)
                            for vs in new_vitals:
                                add_vital_sign(patient_id, vs["metric"], vs["value"], source="lab_auto")

            except Exception:
                pass  # Archiving/extraction failure should not block the response

        return ChatResponse(answer=result["answer"], error=result.get("error"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")
