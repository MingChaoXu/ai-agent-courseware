---
name: medical-assistant
description: "基层门诊AI辅助诊疗 skill. Provides 5 AI modules (medical record generation, lab report interpretation, treatment plan recommendation, medical record quality control, patient timeline analysis) and patient database management (vitals, medications, diagnoses). Use when user asks about medical record generation, lab interpretation, treatment recommendation, quality control, patient timeline analysis, or patient database operations (list/detail/add vital/add medication/add diagnosis)."
name_cn: "基层门诊AI辅助诊疗"
description_cn: "基层门诊AI辅助诊疗：5个AI分析模块 + 患者档案管理"
---

# 基层门诊AI辅助诊疗

## Configuration

This skill requires the backend project running. Set the environment variable before use:

```
MEDICAL_PROJECT_ROOT=D:\电信\工作文档\培训\2607区县AI培训\ai-agent-courseware\exercises\day2\ex3_medical_record
```

Also ensure `.env` in the project root has valid LLM API credentials:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | LLM API key |
| `OPENAI_API_BASE` | LLM API base URL |
| `OPENAI_MODEL_NAME` | Model name |

## AI Analysis Modules

| Tool | Description | Parameters |
|------|-------------|------------|
| `medical_generate_record` | Generate structured outpatient medical record from symptom description | input_text (str) |
| `medical_interpret_lab` | Interpret lab test results with clinical significance | input_text (str) |
| `medical_recommend_treatment` | Recommend examination and treatment plan based on symptoms | input_text (str) |
| `medical_quality_control` | Quality control check on existing medical record | input_text (str) |
| `medical_timeline_analysis` | Analyze patient disease progression across multiple visits | input_text (str) |
| `medical_health_check` | Check agent health and available modules | - |

## Patient Database Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `patient_list` | Query patient list, searchable by name or phone | keyword (str) |
| `patient_detail` | Get full patient profile (diagnoses, meds, vitals, visits) | patient_id (int) |
| `patient_add_vital` | Record a vital sign measurement (BP, glucose, HR, etc.) | patient_id, metric, value, measure_date |
| `patient_add_medication` | Add a medication record for a patient | patient_id, drug_name, dosage, frequency |
| `patient_add_diagnosis` | Add a diagnosis record (can mark as chronic) | patient_id, diagnosis_name, is_chronic |

## Vital Sign Metrics

| Key | Label | Unit | Normal Range |
|-----|-------|------|-------------|
| systolic_bp | 收缩压 | mmHg | 90-140 |
| diastolic_bp | 舒张压 | mmHg | 60-90 |
| heart_rate | 心率 | 次/分 | 60-100 |
| fasting_glucose | 空腹血糖 | mmol/L | 3.9-6.1 |
| hba1c | 糖化血红蛋白 | % | 4.0-6.0 |
| temperature | 体温 | ℃ | 36.0-37.3 |
| spo2 | 血氧饱和度 | % | 95-100 |
| weight | 体重 | kg | - |
| bmi | BMI | kg/m² | 18.5-24.0 |
| cr | 肌酐 | μmol/L | 44-133 |
| alt | 谷丙转氨酶 | U/L | 0-40 |
| hb | 血红蛋白 | g/L | 115-150 |
| wbc | 白细胞 | ×10⁹/L | 4-10 |
| tc | 总胆固醇 | mmol/L | 0-5.2 |
| ldl_c | LDL-C | mmol/L | 0-3.4 |
| ua | 尿酸 | μmol/L | 150-420 |

## CLI Usage

```bash
# Set project root first
set MEDICAL_PROJECT_ROOT=D:\电信\工作文档\培训\2607区县AI培训\ai-agent-courseware\exercises\day2\ex3_medical_record

# AI modules
python skill/tools/tool.py record -q "55岁男性，反复咳嗽1月余"
python skill/tools/tool.py lab -q "血红蛋白95g/L，MCV 72fL"
python skill/tools/tool.py treatment -q "慢阻肺急性加重"
python skill/tools/tool.py qc -q "门诊病历：患者张某..."
python skill/tools/tool.py timeline -q "患者张建国，男55岁，3次就诊记录..."
python skill/tools/tool.py health

# Patient DB
python skill/tools/tool.py patient-list --keyword 张
python skill/tools/tool.py patient-detail --patient-id 1
python skill/tools/tool.py patient-add-vital --patient-id 1 --metric systolic_bp --value 130
python skill/tools/tool.py patient-add-med --patient-id 1 --drug "氨氯地平" --dosage "5mg"
python skill/tools/tool.py patient-add-diag --patient-id 1 --diagnosis "高血压病" --chronic
```
