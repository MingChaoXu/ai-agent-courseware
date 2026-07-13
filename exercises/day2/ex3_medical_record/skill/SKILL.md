# Medical AI Assistant Skill

## Description

基层门诊AI辅助诊疗 skill for TeleAgent. Provides 5 modules: medical record generation, lab report interpretation, treatment plan recommendation, medical record quality control, and patient timeline analysis.

## Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `medical_generate_record` | Generate structured outpatient medical record from symptom description | input_text (str) |
| `medical_interpret_lab` | Interpret lab test results with clinical significance | input_text (str) |
| `medical_recommend_treatment` | Recommend examination and treatment plan based on symptoms | input_text (str) |
| `medical_quality_control` | Quality control check on existing medical record | input_text (str) |
| `medical_timeline_analysis` | Analyze patient disease progression across multiple visits | input_text (str) |
| `medical_health_check` | Check agent health and available modules | - |

## Installation

Copy or symlink the `skill/` directory into the TeleAgent skills folder:

```bash
ln -s /path/to/ex3_medical_record/skill ~/.config/TeleAgent/skills/ex3_medical_record
```

## Configuration

Requires a `.env` file in the project root:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | LLM API key |
| `OPENAI_API_BASE` | LLM API base URL |
| `OPENAI_MODEL_NAME` | Model name |

## CLI Usage

```bash
  python skill/tools/tool.py record -q "55岁男性，反复咳嗽1月余"
  python skill/tools/tool.py lab -q "血红蛋白95g/L，MCV 72fL"
  python skill/tools/tool.py treatment -q "慢阻肺急性加重"
  python skill/tools/tool.py qc -q "门诊病历：患者张某..."
  python skill/tools/tool.py timeline -q "患者张建国，男55岁，3次就诊记录..."
  python skill/tools/tool.py health
```

## Module Details

### 1. 门诊病历生成 (record)
Input: Doctor's oral symptom description
Output: Structured outpatient record (chief complaint, present illness, past history, physical exam, diagnosis, treatment plan)

### 2. 检验报告解读 (lab)
Input: Lab test data text
Output: Key indicators with abnormality flags, clinical significance, overall interpretation, follow-up suggestions

### 3. 诊疗方案推荐 (treatment)
Input: Symptom description or diagnosis
Output: Possible diagnoses, recommended exams, medication plan, precautions, risk alerts

### 4. 病历质控校验 (qc)
Input: Complete outpatient record text
Output: Quality grade (甲/乙/丙), missing items, nonstandard terms, logic issues, modification suggestions, score

### 5. 时序病情分析 (timeline)
Input: Patient's multiple visit records (auto-assembled by backend from database)
Output: Patient summary, disease progression, key changes, treatment effectiveness, risk assessment, future recommendations, follow-up plan
