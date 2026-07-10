"""
课题4: 金融领域自动化合同审核（含HITL审批节点）
=================================================
使用PydanticOutputParser结构化输出，包含Human-in-the-Loop审批流程。
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'common'))
from shared_utils import get_llm, check_api_config, DATA_DIR

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from pydantic import BaseModel, Field


class ContractAuditItem(BaseModel):
    """单条风险条款"""
    clause: str = Field(description="条款名称")
    risk_type: str = Field(description="风险类型：利率条款/担保条款/违约条款/争议解决/权利失衡")
    risk_level: str = Field(description="风险等级：低/中/高")
    description: str = Field(description="问题描述")
    suggestion: str = Field(description="修改建议")


class ContractAuditReport(BaseModel):
    """合同审核报告结构化输出"""
    overall_risk: str = Field(description="整体风险等级：低/中/高")
    risk_count: int = Field(description="风险条款数")
    need_human_approval: bool = Field(description="是否需要人工审批")
    items: list[ContractAuditItem] = Field(description="风险条款详情列表")
    summary: str = Field(description="审核建议汇总")


def exercise4_run():
    print("=" * 60)
    print("课题4: 金融领域自动化合同审核（含HITL审批）")
    print("=" * 60)

    llm = get_llm(temperature=0.1)

    # 步骤1: 构建 LCEL 审核 Chain + PydanticOutputParser
    print("\n--- 步骤1: 构建合同审核 LCEL Chain（PydanticOutputParser） ---")
    print("""
合同审核 Chain 构建：
  ① Pydantic 定义输出格式（ContractAuditReport）
  ② PydanticOutputParser 自动生成格式指令
  ③ ChatPromptTemplate + format_instructions → LLM → Parser
  ④ 输出为 ContractAuditReport 对象，直接访问字段
    """)

    parser = PydanticOutputParser(pydantic_object=ContractAuditReport)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是一个专业的合同审核助手，负责审核银行信贷合同并识别风险条款。\n\n"
         "审核维度：\n"
         "1. 【利率条款】检查是否存在银行单方面调价权、浮动利率未设上限\n"
         "2. 【担保条款】检查担保方式是否明确、担保物评估价值是否充足、保证期间是否合理\n"
         "3. 【违约条款】检查违约金比例是否过高（>3%为高风险）、交叉违约条款是否过于宽泛\n"
         "4. 【争议解决】检查仲裁条款是否明确仲裁地点和规则\n"
         "5. 【权利失衡】检查是否存在单方面解除权、不对等的提前还款违约金\n\n"
         "风险等级判定：\n"
         "- 低风险：无风险条款或仅有轻微提示项\n"
         "- 中风险：存在1-2条中等风险条款\n"
         "- 高风险：存在3条及以上风险条款，或任一条款违约金>5%\n\n"
         "{format_instructions}"),
        ("human", "请审核以下合同，识别所有风险条款并生成结构化审核报告：\n\n{contract_text}"),
    ])

    prompt = prompt.partial(format_instructions=parser.get_format_instructions())

    # LCEL Chain: prompt → llm → parser
    audit_chain = prompt | llm | parser

    print("Chain 组装：")
    print("  ChatPromptTemplate(含 format_instructions) → ChatOpenAI(temperature=0.1) → PydanticOutputParser")
    print("  prompt.partial(format_instructions=...) 预绑定格式指令")

    # 步骤2: 上传合同并审核
    print("\n--- 步骤2: 上传合同样本进行审核 ---")
    contracts_path = os.path.join(DATA_DIR, "contract_samples.json")
    if os.path.exists(contracts_path):
        with open(contracts_path, "r", encoding="utf-8") as f:
            contracts = json.load(f)
    else:
        contracts = [
            {
                "title": "个人住房贷款合同（低风险）",
                "content": "贷款金额80万元，年利率4.2%（固定），期限30年，等额本息还款。担保方式：所购房产抵押，评估价值120万元。违约金：提前还款收取1%手续费。争议解决：XX市仲裁委员会。"
            },
            {
                "title": "企业经营贷款合同（高风险）",
                "content": "贷款金额500万元，年利率为浮动利率（基准利率+3%，银行有权单方面调整浮动比例），期限5年。担保方式：企业全部资产抵押（未明确评估价值）。违约金：逾期还款收取每日0.5%罚息+5%违约金。银行有权在任何时候要求提前偿还全部贷款。争议解决：由银行总部所在地法院管辖。"
            }
        ]

    risk_labels = []
    for contract in contracts:
        print(f"\n审核: {contract['title']}")
        try:
            report: ContractAuditReport = audit_chain.invoke({"contract_text": contract["content"]})
            print(f"  整体风险: {report.overall_risk}")
            print(f"  风险条款数: {report.risk_count}")
            print(f"  需人工审批: {'是' if report.need_human_approval else '否'}")
            for item in report.items:
                icon = "🔴" if item.risk_level == "高" else ("🟡" if item.risk_level == "中" else "🟢")
                print(f"  {icon} [{item.risk_type}] {item.clause}: {item.description[:60]}")

            risk_labels.append((contract["title"], report.overall_risk, report.need_human_approval))

        except Exception as e:
            print(f"  [审核调用失败: {e}]")
            # 降级为文本输出
            try:
                text_chain = prompt | llm | StrOutputParser()
                result = text_chain.invoke({"contract_text": contract["content"]})
                print(f"  [文本模式] {result[:200]}...")
                if "高" in result or "🔴" in result:
                    risk_labels.append((contract["title"], "高", True))
                elif "中" in result or "🟡" in result:
                    risk_labels.append((contract["title"], "中", True))
                else:
                    risk_labels.append((contract["title"], "低", False))
            except Exception as e2:
                print(f"  [文本模式也失败: {e2}]")
                risk_labels.append((contract["title"], "未知", False))

    # 步骤3: HITL人工审批流程
    print("\n--- 步骤3: Human-in-the-Loop 人工审批流程 ---")
    print("模拟HITL审批流程：Agent建议 → 人工确认/修改 → 确认执行\n")

    for title, risk, need_approval in risk_labels:
        if risk == "高" or need_approval:
            print(f"合同「{title}」需人工审批")
            print("  Agent建议: 高风险，建议拒绝或要求修改条款")
            print("  ┌─────────────────────────────────┐")
            print("  │ 人工审批选项:                    │")
            print("  │   1. 同意Agent建议（拒绝合同）   │")
            print("  │   2. 修改后通过（指定修改要求）   │")
            print("  │   3. 覆盖风险标记（强制通过）     │")
            print("  └─────────────────────────────────┘")
            human_decision = input("  请选择审批操作 (1/2/3，默认1): ").strip() or "1"

            if human_decision == "1":
                print("  审批结果: 同意Agent建议，合同已拒绝")
            elif human_decision == "2":
                modification = input("  请输入修改要求: ").strip() or "降低违约金比例、明确担保评估价值"
                print(f"  审批结果: 要求修改后通过。修改要求: {modification}")
                # 用 LCEL Chain 生成修改方案
                try:
                    modify_prompt = ChatPromptTemplate.from_messages([
                        ("system", "你是一个合同修改助手。根据人工审批要求，提出具体的合同条款修改方案。"),
                        ("human", "合同「{title}」的审批修改要求: {modification}"),
                    ])
                    modify_chain = modify_prompt | llm | StrOutputParser()
                    modify_result = modify_chain.invoke({"title": title, "modification": modification})
                    print(f"  Agent修改方案: {modify_result[:200]}...")
                except Exception as e:
                    print(f"  [修改方案生成失败: {e}]")
            elif human_decision == "3":
                reason = input("  请输入强制通过原因: ").strip() or "战略客户特批"
                print(f"  审批结果: 覆盖风险标记，强制通过。原因: {reason}")
                print("  审批记录已存档")

        elif risk == "中":
            print(f"合同「{title}」建议人工复核")
            auto_pass = input("  是否自动通过？(y/n，默认n): ").strip().lower()
            if auto_pass == "y":
                print("  人工确认: 自动通过")
            else:
                print("  人工确认: 进入详细复核流程")

        else:
            print(f"合同「{title}」低风险，自动通过")

    print("\nHITL设计要点:")
    print("  - 风险分级: 低风险自动→中风险复核→高风险审批")
    print("  - 审批留痕: 所有人工决策必须记录原因")
    print("  - Agent→Human: Agent给出建议，人做最终决策")
    print("  - 异常兜底: 强制通过需写明特殊原因")
    print("  - LCEL Chain: PydanticOutputParser 保证输出结构化 → 直接判定 need_human_approval")

    print("\n课题4完成！")


if __name__ == "__main__":
    exercise4_run()
