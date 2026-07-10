"""
课题3: 医疗领域病历生成（PydanticOutputParser 结构化输出）
==========================================================
- 步骤1: PydanticOutputParser — 让 LLM 输出结构化 JSON
- 步骤2: 构建 LCEL Chain（Prompt + LLM + Parser）
- 步骤3: 病历生成测试
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'common'))

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from shared_utils import get_llm, check_api_config


# ============================================================
#  课题3: 医疗领域病历生成（PydanticOutputParser 结构化输出）
# ============================================================

class MedicalRecord(BaseModel):
    """门诊病历结构化输出模型 — Pydantic 定义输出格式"""
    chief_complaint: str = Field(description="主诉：患者主要症状及持续时间")
    present_illness: str = Field(description="现病史：症状发生发展过程")
    past_history: str = Field(description="既往史：既往疾病、手术、过敏史")
    physical_examination: str = Field(description="体格检查：生命体征和阳性体征")
    preliminary_diagnosis: str = Field(description="初步诊断：根据病史和体征得出的诊断")
    treatment_plan: str = Field(description="处理意见：用药处方、检查建议、注意事项")


def exercise3_step1_pydantic_parser():
    """步骤1: PydanticOutputParser — 让 LLM 输出结构化 JSON"""
    print("=" * 60)
    print("课题3: 医疗领域病历生成")
    print("步骤1: PydanticOutputParser 结构化输出")
    print("=" * 60)
    print("""
问题：LLM 默认输出自由文本，但业务需要结构化数据（JSON）

PydanticOutputParser 的作用：
  1) 定义 Pydantic 模型 → 自动生成 JSON Schema
  2) 将 Schema 注入 Prompt → LLM 按 Schema 格式输出
  3) 解析 LLM 输出 → 自动转为 Pydantic 对象（带类型校验）

流程：
  Pydantic 模型 → parser.get_format_instructions() → 注入 Prompt
  LLM 输出 JSON → parser.parse() → MedicalRecord 对象
    """)

    parser = PydanticOutputParser(pydantic_object=MedicalRecord)

    print("MedicalRecord 字段：")
    for name, field in MedicalRecord.model_fields.items():
        print(f"  - {name}: {field.description}")

    print(f"\n自动生成的格式指令（将注入 Prompt）：")
    format_instr = parser.get_format_instructions()
    print(f"  {format_instr[:200]}...")

    return parser


def exercise3_step2_build_chain(parser):
    """步骤2: 构建 LLMChain — ChatPromptTemplate + PydanticOutputParser"""
    print("\n" + "=" * 60)
    print("步骤2: 构建 LCEL Chain（Prompt + LLM + Parser）")
    print("=" * 60)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是一个门诊病历辅助生成助手，帮助基层医生快速生成规范的门诊病历。\n\n"
         "生成规则：\n"
         "1. 严格按照门诊病历规范格式生成\n"
         "2. 使用规范医学术语，不使用口语化表达\n"
         "3. 药品使用通用名，标注剂量、用法、频次\n"
         "4. 需要进一步检查的，明确标注检查项目\n\n"
         "重要：本助手仅辅助生成病历草稿，最终诊断和处方必须由执业医师确认签字。\n\n"
         "{format_instructions}"),
        ("human", "请根据以下信息生成门诊病历：\n{input_text}"),
    ])

    # 将 format_instructions 部分绑定到 prompt
    prompt = prompt.partial(format_instructions=parser.get_format_instructions())

    llm = get_llm(temperature=0.3)

    # LCEL Chain: prompt → llm → parser
    chain = prompt | llm | parser

    print("Chain 组装：")
    print("  prompt(注入 format_instructions) → llm → PydanticOutputParser")
    print("  prompt.partial(format_instructions=...) 预绑定格式指令")
    print("\n✅ 病历生成 Chain 构建完成！")
    return chain


def exercise3_step3_test(chain):
    """步骤3: 病历生成测试"""
    print("\n" + "=" * 60)
    print("步骤3: 病历生成测试")
    print("=" * 60)

    if chain is None:
        print("⚠️ Chain 未构建，跳过测试")
        return

    test_cases = [
        "患者女，45岁，反复头痛3天，伴恶心，无呕吐，既往高血压病史5年，目前服用氨氯地平5mg qd。查体：BP 155/95mmHg，神清，颈软。",
        "患儿男，3岁，发热2天，T 38.5℃，伴咳嗽、流涕，精神可，进食略减。查体：咽红，双肺呼吸音粗，未闻及啰音。",
    ]

    for case in test_cases:
        print(f"\n👤 医生输入: {case}")
        try:
            result = chain.invoke({"input_text": case})
            print(f"🤖 结构化病历:")
            print(f"  主诉:     {result.chief_complaint}")
            print(f"  现病史:   {result.present_illness}")
            print(f"  既往史:   {result.past_history}")
            print(f"  体格检查: {result.physical_examination}")
            print(f"  初步诊断: {result.preliminary_diagnosis}")
            print(f"  处理意见: {result.treatment_plan}")
            print(f"  ✅ 输出类型: {type(result).__name__}（Pydantic 模型，可序列化为 JSON/dict）")
        except Exception as e:
            print(f"⚠️ 生成失败: {e}")
            print("  Parser 解析失败时，LLM 输出格式可能不匹配，需调整 prompt 或重试")

    print("""
💡 PydanticOutputParser vs 纯文本输出：
  - 纯文本：LLM 自由输出，格式不可控，后续处理需正则解析
  - Parser：LLM 按 Schema 输出 JSON → 自动校验 + 类型转换 → 直接 .属性 访问
  - 注意：Parser 依赖 LLM 严格遵循格式，偶尔解析失败需重试
    """)


def run_exercise3():
    """运行课题3完整流程"""
    parser = exercise3_step1_pydantic_parser()
    chain = exercise3_step2_build_chain(parser)
    exercise3_step3_test(chain)
    print("\n✅ 课题3完成！你已掌握 PydanticOutputParser 结构化输出。")


if __name__ == "__main__":
    check_api_config()
    run_exercise3()
