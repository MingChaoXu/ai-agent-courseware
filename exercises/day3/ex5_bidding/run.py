"""
课题5: 制造领域招投标文件应用
==============================
使用两个LCEL Chain：技术方案生成 + 合规检查（PydanticOutputParser结构化输出）。
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'common'))
from shared_utils import get_llm, check_api_config, DATA_DIR

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from pydantic import BaseModel, Field


class BiddingComplianceCheck(BaseModel):
    """合规检查结构化输出"""
    qualification_ok: bool = Field(description="资质要求是否满足")
    experience_ok: bool = Field(description="业绩要求是否满足")
    format_ok: bool = Field(description="格式要求是否满足")
    responsiveness_ok: bool = Field(description="响应性是否满足")
    issues: list[str] = Field(description="不满足的具体问题列表")
    suggestions: list[str] = Field(description="改进建议列表")


def exercise5_run():
    print("=" * 60)
    print("课题5: 制造领域招投标文件应用")
    print("=" * 60)

    llm = get_llm()

    # 步骤1: 构建 LCEL Chain — 技术方案生成
    print("\n--- 步骤1: 构建招投标文件生成 LCEL Chain ---")
    print("""
本课题两个 LCEL Chain：
  ① 技术方案生成 Chain: ChatPromptTemplate → ChatOpenAI → StrOutputParser
  ② 合规检查 Chain: ChatPromptTemplate → ChatOpenAI → PydanticOutputParser
    """)

    gen_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是一个招投标文件助手，帮助企业快速生成技术方案并检查合规性。\n\n"
         "功能一：技术方案生成\n"
         "输入项目需求，生成包含以下章节的技术方案：\n"
         "1. 项目理解与技术路线\n"
         "2. 实施方案与进度计划\n"
         "3. 项目团队与资质\n"
         "4. 质量保障措施\n"
         "5. 售后服务承诺\n\n"
         "语言要求：专业严谨，不使用模糊表述。"),
        ("human", "请根据以下招标需求生成技术方案：\n{requirement}"),
    ])

    gen_chain = gen_prompt | llm | StrOutputParser()
    print("技术方案生成 Chain 构建完成")

    # 步骤2: 生成技术方案
    print("\n--- 步骤2: 基于需求生成技术方案 ---")
    requirement = """
项目名称：XX市智慧水务数据中台建设项目
预算金额：280万元
核心需求：
1. 建设水务数据中台，整合供水、排水、污水三大系统数据
2. 实现实时数据采集与监控，支持10000+点位并发
3. 构建水务数据资产目录与数据质量管理体系
4. 开发3个典型数据分析应用（漏损分析、水质预警、调度优化）
5. 提供数据API服务，支持第三方系统对接

资质要求：
- 软件开发CMMI3级及以上
- 水务行业信息化项目经验不少于3个
- 项目团队不少于15人"""

    try:
        proposal = gen_chain.invoke({"requirement": requirement})
        print(f"生成技术方案:\n{proposal}")
    except Exception as e:
        print(f"[生成失败: {e}]")
        proposal = ""

    # 步骤3: 合规检查（PydanticOutputParser 结构化输出）
    print("\n--- 步骤3: 合规性检查 ---")
    compliance_parser = PydanticOutputParser(pydantic_object=BiddingComplianceCheck)

    compliance_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是招投标合规检查助手。检查投标方案是否满足以下要求：\n\n"
         "检查维度：\n"
         "1. 资质要求（营业执照、行业资质等）\n"
         "2. 业绩要求（类似项目案例）\n"
         "3. 格式要求（页数、字体、盖章等）\n"
         "4. 响应性要求（是否逐条响应招标文件要求）\n\n"
         "{format_instructions}"),
        ("human", "请对以下技术方案进行合规性检查，判断是否满足资质要求：\n\n{proposal_text}"),
    ])

    compliance_prompt = compliance_prompt.partial(
        format_instructions=compliance_parser.get_format_instructions()
    )

    compliance_chain = compliance_prompt | llm | compliance_parser

    try:
        check: BiddingComplianceCheck = compliance_chain.invoke({
            "proposal_text": proposal[:1000] if proposal else requirement,
        })
        print(f"  资质要求: {'满足' if check.qualification_ok else '不满足'}")
        print(f"  业绩要求: {'满足' if check.experience_ok else '不满足'}")
        print(f"  格式要求: {'满足' if check.format_ok else '不满足'}")
        print(f"  响应性:   {'满足' if check.responsiveness_ok else '不满足'}")
        if check.issues:
            print(f"  问题:")
            for issue in check.issues:
                print(f"    - {issue}")
        if check.suggestions:
            print(f"  建议:")
            for sug in check.suggestions:
                print(f"    - {sug}")
    except Exception as e:
        print(f"  [合规检查失败: {e}]")
        # 降级为文本输出
        try:
            text_chain = compliance_prompt | llm | StrOutputParser()
            result = text_chain.invoke({"proposal_text": proposal[:1000] if proposal else requirement})
            print(f"  [文本模式] {result[:300]}...")
        except:
            pass

    print("\n课题5完成！")


if __name__ == "__main__":
    exercise5_run()
