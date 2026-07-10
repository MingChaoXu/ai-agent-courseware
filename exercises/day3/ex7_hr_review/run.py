"""
课题7: 人力资源领域制度审查（含记忆联动）
==========================================
使用PydanticOutputParser结构化输出，联动MemoryManager历史审查记忆。
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'common'))
from shared_utils import get_llm, check_api_config, DATA_DIR
from training_utils import MemoryManager

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from pydantic import BaseModel, Field


class PolicyReviewItem(BaseModel):
    """制度审查条目"""
    clause: str = Field(description="制度条款")
    dimension: str = Field(description="审查维度：法律法规合规/内部一致性/权利义务平衡/可操作性/时效性/历史一致性")
    status: str = Field(description="合规状态：合规/风险/建议修改")
    issue: str = Field(description="问题描述")
    suggestion: str = Field(description="修改建议")


class PolicyReviewReport(BaseModel):
    """制度审查报告"""
    overall_risk: str = Field(description="整体合规风险：高/中/低")
    items: list[PolicyReviewItem] = Field(description="逐条审查意见")
    consistency_warnings: list[str] = Field(description="一致性警告列表")


def exercise7_run():
    print("=" * 60)
    print("课题7: 人力资源领域制度审查（含记忆联动）")
    print("=" * 60)

    llm = get_llm(temperature=0.1)

    # 初始化历史审查记忆
    print("\n--- 步骤0: 初始化历史审查记忆 ---")
    mem_path = os.path.join(DATA_DIR, "hr_review_memory.json")
    os.makedirs(DATA_DIR, exist_ok=True)
    mm = MemoryManager(filepath=mem_path)
    mm.add_fact("审查记录", "2025-12-加班制度",
                "发现3处违规：加班费计算标准低于法定、调休时限过短、强制加班条款",
                metadata={"risk_level": "high", "status": "已修改"})
    mm.add_fact("审查记录", "2026-01-请假制度",
                "整体合规，建议补充：病假工资计算方式、孕期特殊保护条款",
                metadata={"risk_level": "low", "status": "已补充"})
    mm.add_fact("审查记录", "2026-03-薪酬制度",
                "发现2处风险：绩效工资占比超50%、未明确发放时间",
                metadata={"risk_level": "medium", "status": "修改中"})
    mm.add_fact("合规基准", "加班费标准",
                "工作日150%/休息日200%/法定节假日300%，不得以调休替代法定节假日加班费")
    mm.add_fact("合规基准", "试用期上限",
                "合同期<1年≤1个月，1-3年≤2个月，≥3年≤6个月，同一用人单位只能约定一次")
    print(f"  已加载 {len(mm.memory)} 条历史审查记忆")

    # 步骤1: 构建 LCEL Chain（带记忆注入）
    print("\n--- 步骤1: 构建制度审查 LCEL Chain（含记忆联动） ---")

    history_context = mm.get_context_for_prompt("制度审查")

    parser = PydanticOutputParser(pydantic_object=PolicyReviewReport)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是一个企业制度合规审查助手，帮助HR部门审查公司内部制度的合规性。\n\n"
         "审查维度：\n"
         "1. 【法律法规合规】是否符合《劳动法》《劳动合同法》《社会保险法》等\n"
         "2. 【内部一致性】是否与公司章程、其他制度文件存在冲突\n"
         "3. 【权利义务平衡】是否过度偏向企业一方，侵犯员工合法权益\n"
         "4. 【可操作性】制度条款是否明确、可执行，避免模糊表述\n"
         "5. 【时效性】是否引用了已废止的法规或过时的标准\n"
         "6. 【历史一致性】是否与同类制度的历史审查结论一致\n\n"
         "常见审查要点：\n"
         "- 加班费计算标准是否符合法定要求（150%/200%/300%）\n"
         "- 试用期长度是否超出法定上限\n"
         "- 离职补偿金计算是否合规\n"
         "- 考勤制度是否侵犯员工休息权\n\n"
         "历史审查记忆（用于一致性对比）：\n{memory_context}\n\n"
         "{format_instructions}"),
        ("human", "请审查以下公司制度，识别所有不合规条款，并对比历史审查记录检查一致性：\n\n{policy_text}"),
    ])

    prompt = prompt.partial(format_instructions=parser.get_format_instructions())
    review_chain = prompt | llm | parser

    print("Chain 组装：")
    print("  ChatPromptTemplate(含 {memory_context} + {format_instructions}) → ChatOpenAI → PydanticOutputParser")

    # 步骤2: 审查制度
    print("\n--- 步骤2: 制度审查测试（联动历史记忆） ---")
    policy_text = """
《XX公司考勤与加班管理制度》

第三条 工作时间
公司实行标准工时制，每日工作8小时，每周工作6天。

第五条 加班管理
5.1 公司因生产经营需要安排加班的，员工应服从安排。
5.2 加班费统一按基本工资的100%计算，不分工作日/休息日/法定节假日。

第七条 迟到处罚
迟到15分钟以内扣款50元，15-30分钟扣款100元，30分钟以上按旷工处理。

第九条 试用期
管理岗位试用期6个月，普通岗位试用期3个月。试用期工资为正式工资的70%。"""

    try:
        report: PolicyReviewReport = review_chain.invoke({
            "policy_text": policy_text,
            "memory_context": history_context,
        })
        print(f"  整体风险: {report.overall_risk}")
        for item in report.items:
            icon = "风险" if item.status == "风险" else ("建议" if item.status == "建议修改" else "合规")
            print(f"  [{item.dimension}] {item.clause}: {item.issue[:60]} → {icon}")
        if report.consistency_warnings:
            print(f"  一致性警告:")
            for w in report.consistency_warnings:
                print(f"    ⚠️ {w}")
    except Exception as e:
        print(f"  [审查调用失败: {e}]")
        try:
            text_chain = prompt | llm | StrOutputParser()
            result = text_chain.invoke({"policy_text": policy_text, "memory_context": history_context})
            print(f"  [文本模式] {result[:400]}...")
        except Exception as e2:
            print(f"  [文本模式也失败: {e2}]")

    # 步骤3: 更新审查记忆
    print("\n--- 步骤3: 更新审查记忆 ---")
    mm.add_fact("审查记录", "2026-07-考勤加班制度",
                "发现多项违规：每周6天工时违法、加班费仅100%低于法定、试用期工资70%低于80%下限",
                metadata={"risk_level": "high", "status": "待修改"})
    print(f"  已存入新审查记录，当前共 {len(mm.memory)} 条记忆")

    # 演示一致性检查
    print("\n--- 步骤4: 一致性审查演示 ---")
    print("  对比本次审查与历史审查的加班费问题:")
    old_records = mm.search("加班费")
    for r in old_records:
        print(f"  [{r['category']}] {r['key']}: {r['value']}")

    print("\n记忆联动价值:")
    print("  - 自动关联历史审查结论，避免同类问题遗漏")
    print("  - 建立合规检查知识库，审查标准逐步统一")
    print("  - 新制度与旧制度冲突自动检测（一致性审查）")

    print("\n课题7完成！")


if __name__ == "__main__":
    exercise7_run()
