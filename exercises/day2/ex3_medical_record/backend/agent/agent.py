"""
Medical AI Assistant - Multi-function Structured Output Agent
4 modules: 门诊病历生成, 检验报告解读, 诊疗方案推荐, 病历质控校验
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser

from config import settings


# ============================================================
# Module 1: 门诊病历生成
# ============================================================

class MedicalRecord(BaseModel):
    """门诊病历结构化输出"""
    patient_info: str = Field(description="患者信息：姓名、性别、年龄")
    chief_complaint: str = Field(description="主诉：患者主要症状及持续时间")
    present_illness: str = Field(description="现病史：症状发生发展过程、伴随症状、诊治经过")
    past_history: str = Field(description="既往史：既往疾病、手术史、过敏史、家族史")
    physical_examination: str = Field(description="体格检查：体温、脉搏、呼吸、血压及阳性体征")
    preliminary_diagnosis: str = Field(description="初步诊断：根据病史和体征得出的诊断")
    treatment_plan: str = Field(description="处理意见：用药处方（通用名+剂量+用法+频次）、检查建议、注意事项")


# ============================================================
# Module 2: 检验报告解读
# ============================================================

class LabIndicator(BaseModel):
    """单项检验指标"""
    name: str = Field(description="指标名称")
    value: str = Field(description="检测结果数值及单位")
    reference_range: str = Field(description="参考范围")
    is_abnormal: bool = Field(description="是否异常")
    clinical_significance: str = Field(description="临床意义解读")


class LabReportInterpretation(BaseModel):
    """检验报告解读结构化输出"""
    report_type: str = Field(description="检验报告类型（如：血常规、肝功能、肾功能、血糖血脂等）")
    key_indicators: List[LabIndicator] = Field(description="关键指标列表")
    overall_interpretation: str = Field(description="综合解读：各项指标的整体分析")
    clinical_correlation: str = Field(description="临床关联：结合常见疾病的可能提示")
    follow_up_suggestions: str = Field(description="建议复查项及注意事项")


# ============================================================
# Module 3: 诊疗方案推荐
# ============================================================

class TreatmentPlan(BaseModel):
    """诊疗方案推荐结构化输出"""
    possible_diagnoses: str = Field(description="可能的诊断：按可能性排列，含鉴别诊断要点")
    recommended_exams: str = Field(description="推荐检查项目：实验室检查、影像检查、特殊检查")
    medication_suggestions: str = Field(description="推荐用药方案：药品通用名+剂量+用法+疗程，注意禁忌")
    precautions: str = Field(description="注意事项：生活饮食建议、禁忌事项、随访要求")
    risk_alerts: str = Field(description="风险提示：需警惕的严重疾病可能、紧急就医指征")


# ============================================================
# Module 4: 病历质控校验
# ============================================================

class QualityControlResult(BaseModel):
    """病历质控校验结构化输出"""
    quality_level: str = Field(description="质控等级：甲级/乙级/丙级")
    missing_items: str = Field(description="缺项清单：病历中缺失的必填项")
    nonstandard_terms: str = Field(description="不规范用语：口语化表达、非医学术语、缩写不规范")
    logic_issues: str = Field(description="逻辑矛盾：诊断与病史不符、用药与诊断不符等")
    modification_suggestions: str = Field(description="修改建议：逐条列出具体修改意见")
    overall_score: str = Field(description="综合评分：满分100分，附扣分明细")


# ============================================================
# Module 5: 时序病情分析
# ============================================================

class TimelineAnalysis(BaseModel):
    """时序病情分析结构化输出"""
    patient_summary: str = Field(description="患者概况：基本信息与主要诊断总结")
    disease_progression: str = Field(description="病情演变轨迹：按时间线梳理各次就诊变化")
    key_changes: str = Field(description="关键变化点：重要指标、诊断、方案的转折点")
    treatment_effectiveness: str = Field(description="治疗效果评估：用药方案是否有效，指标是否达标")
    risk_assessment: str = Field(description="风险预警：病情恶化信号、并发症风险、需紧急关注的指标")
    future_recommendations: str = Field(description="后续建议：用药调整、复查计划、生活方式、转诊建议")
    follow_up_plan: str = Field(description="随访计划：下次复诊时间、必查项目、监测指标")


# ============================================================
# Chain Factory
# ============================================================

# Module configs: (Pydantic model, system prompt)
MODULE_CONFIGS = {
    "record": {
        "model": MedicalRecord,
        "system_prompt": """你是一个门诊病历辅助生成助手，帮助基层医生快速生成规范的门诊病历。

生成规则：
1. 严格按照门诊病历规范格式生成
2. 使用规范医学术语，不使用口语化表达
3. 药品使用通用名，标注剂量、用法、频次
4. 需要进一步检查的，明确标注检查项目
5. 主诉不超过20个字，包含主要症状+持续时间

重要：本助手仅辅助生成病历草稿，最终诊断和处方必须由执业医师确认签字。""",
    },
    "lab": {
        "model": LabReportInterpretation,
        "system_prompt": """你是一个检验报告解读助手，帮助患者和基层医生理解检验结果。

解读规则：
1. 准确标注每项指标是否在参考范围内
2. 对异常指标给出临床意义解读，结合常见疾病提示
3. 综合分析多项指标关联性（如Hb+MCV+MCH判断贫血类型）
4. 注意指标的临床敏感性和特异性
5. 不做确诊，只做辅助解读

重要：检验结果解读仅供参考，最终诊断需结合临床表现由医生判断。""",
    },
    "treatment": {
        "model": TreatmentPlan,
        "system_prompt": """你是一个基层门诊诊疗方案推荐助手，根据患者症状辅助推荐检查和治疗方案。

推荐规则：
1. 鉴别诊断按可能性从高到低排列
2. 推荐检查优先考虑基层可开展的常规项目
3. 用药方案遵循基本药物目录和合理用药原则
4. 标注药品禁忌、不良反应和特殊人群注意
5. 对可能危及生命的严重疾病给出预警

重要：本助手仅提供辅助建议，最终诊疗方案由执业医师决定。""",
    },
    "qc": {
        "model": QualityControlResult,
        "system_prompt": """你是一个病历质控校验助手，按照《病历书写基本规范》对门诊病历进行质量检查。

质控规则：
1. 检查必填项是否齐全（主诉、现病史、体检、诊断、处理意见）
2. 检查医学术语规范性（不得使用口语化表达如"肚子疼"，应为"腹痛"）
3. 检查逻辑一致性（诊断与病史、用药是否匹配）
4. 甲级病历：无缺项、无语病、无逻辑矛盾
5. 乙级病历：存在1-2处非关键缺陷
6. 丙级病历：存在关键缺项或严重逻辑矛盾

评分标准：满分100分，缺主诉-15分，缺现病史-15分，缺诊断-20分，口语化用语每处-3分，逻辑矛盾每处-10分。""",
    },
    "timeline": {
        "model": TimelineAnalysis,
        "system_prompt": """你是一个患者病情时序分析助手，根据患者的多次就诊记录，分析病情变化趋势并给出建议。

分析规则：
1. 按时间顺序梳理病情演变轨迹
2. 对比各次就诊的关键指标变化（如血糖、血压、肺功能等）
3. 评估当前治疗效果，判断是否达标
4. 识别病情恶化或并发症风险信号
5. 给出针对性的后续管理建议

重要：分析仅供参考，临床决策由执业医师综合判断。""",
    },
}


def _create_chain(pydantic_model, system_prompt):
    """Create a structured output chain for a given model."""
    parser = PydanticOutputParser(pydantic_object=pydantic_model)

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt + "\n\n{format_instruction}"),
        ("human", "{input_text}"),
    ]).partial(format_instruction=parser.get_format_instructions())

    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_API_BASE,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
    )

    chain = prompt | llm | parser
    fallback_chain = prompt | llm | StrOutputParser()
    return {"chain": chain, "parser": parser, "fallback_chain": fallback_chain}


def create_agent() -> Dict[str, Any]:
    """Create all 5 module chains."""
    if not settings.is_configured():
        return None

    agents = {}
    for module_key, config in MODULE_CONFIGS.items():
        agents[module_key] = _create_chain(config["model"], config["system_prompt"])
    return agents


def analyze(agent: Dict[str, Any], module: str, input_text: str) -> Dict[str, Any]:
    """Run analysis for a specific module."""
    if module not in agent:
        return {"answer": None, "error": f"Unknown module: {module}"}

    module_agent = agent[module]
    try:
        result = module_agent["chain"].invoke({"input_text": input_text})
        return {"answer": result.model_dump(), "error": None}
    except Exception as e:
        try:
            text_result = module_agent["fallback_chain"].invoke({"input_text": input_text})
            return {"answer": text_result, "error": None}
        except Exception as e2:
            return {"answer": None, "error": f"Analysis failed: {str(e2)}"}
