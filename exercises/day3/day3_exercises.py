"""
Day 3 实战课题 — 文档生成与审核 + 上下文工程
============================================
课题3.8: 用户记忆系统实验（原理层）
课题4  : 金融领域自动化合同审核（含HITL审批节点）
课题5  : 制造领域招投标文件应用
课题6  : 建筑/交通领域管理文件生成
课题7  : 人力资源领域制度审查（含记忆联动）
课题7.5: Prompt消融实验（原理层，接入真实LLM）

技术栈：LangChain 原生 API（ChatOpenAI, LCEL, PydanticOutputParser, Memory）
"""

import sys
import os
import json
import time
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# ============================================================
#  环境配置 & LangChain 核心导入
# ============================================================

from dotenv import load_dotenv
_env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(_env_path)

# ---- LangChain 核心 ----
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_classic.memory import ConversationBufferMemory, ConversationSummaryMemory
from pydantic import BaseModel, Field

# ---- 培训工具 ----
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))
from training_utils import MemoryManager, AblationFramework

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


# ============================================================
#  公共辅助函数
# ============================================================

def get_llm(temperature: float = 0.3, max_tokens: int = 2000) -> ChatOpenAI:
    """创建 LLM 实例 — 所有课题共用"""
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY", ""),
        base_url=os.getenv("OPENAI_API_BASE", ""),
        temperature=temperature,
        max_tokens=max_tokens,
    )


def check_api_config():
    """检查 API 配置"""
    api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_API_BASE", "")
    if not api_key or api_key == "sk-your-api-key-here":
        print("[警告] 未配置 OPENAI_API_KEY，请在 .env 文件中设置")
        print(f"  .env 文件位置: {_env_path}")
        return False
    if not base_url:
        print("[警告] 未配置 OPENAI_API_BASE，请在 .env 文件中设置")
        return False
    print(f"  API 地址: {base_url}")
    print(f"  模型名称: {os.getenv('OPENAI_MODEL_NAME', 'gpt-4o-mini')}")
    print(f"  API Key:  {'已配置' if api_key else '未配置'}")
    return True


# ============================================================
#  课题3.8: 用户记忆系统实验（新增原理层）
# ============================================================

def exercise38_run():
    print("=" * 60)
    print("课题3.8: 用户记忆系统实验")
    print("=" * 60)

    # 步骤1: 演示三种记忆架构
    print("\n--- 步骤1: 三种记忆架构对比 ---")

    print("\n架构1: 扁平笔记")
    flat_memory = []
    flat_memory.append({"content": "用户姓名：王主任", "timestamp": time.time()})
    flat_memory.append({"content": "负责领域：社会综合治理", "timestamp": time.time()})
    flat_memory.append({"content": "偏好：简报要求数据先行", "timestamp": time.time()})
    print("  存储格式: [{content, timestamp}, ...]")
    print(f"  示例: {flat_memory[0]}")
    print("  优缺点: 简单易实现 / 无结构化，检索效率低")

    print("\n架构2: JSON层级")
    json_memory = {
        "个人信息": {"姓名": "王主任", "职务": "综治中心主任"},
        "业务偏好": {"简报风格": "数据先行", "关注领域": "矛盾纠纷"},
        "交互记录": {"咨询次数": 5, "上次话题": "劳资纠纷处理"}
    }
    print("  存储格式: {category: {key: value, ...}, ...}")
    print(f"  示例: {json.dumps(json_memory, ensure_ascii=False, indent=2)}")
    print("  优缺点: 结构清晰 / 层级固定，扩展性差")

    print("\n架构3: 高级JSON卡片（MemoryManager）")
    mem_file = os.path.join(DATA_DIR, "memory_demo.json")
    os.makedirs(DATA_DIR, exist_ok=True)
    mm = MemoryManager(filepath=mem_file)
    mm.add_fact("个人信息", "姓名", "王主任")
    mm.add_fact("个人信息", "职务", "综治中心主任")
    mm.add_fact("业务偏好", "简报风格", "数据先行")
    mm.add_fact("业务偏好", "关注领域", "矛盾纠纷")
    mm.add_fact("交互记录", "咨询次数", "5次")
    mm.add_fact("交互记录", "上次话题", "劳资纠纷处理")
    print("  存储格式: [{category, key, value, timestamp, metadata}, ...]")
    for m in mm.memory:
        print(f"  [{m['category']}] {m['key']}: {m['value']}")
    print("  优缺点: 灵活可扩展 / 实现复杂度较高")

    # 步骤2: 政务场景实践 — 用 LCEL Chain 演示记忆注入
    print("\n--- 步骤2: 政务场景实践：记录→检索→注入Prompt ---")
    llm = get_llm()

    print("\n记录用户信息...")
    mm2 = MemoryManager(filepath=os.path.join(DATA_DIR, "gov_memory.json"))
    mm2.add_fact("用户画像", "部门", "XX区住建局", {"来源": "首次对话"})
    mm2.add_fact("用户画像", "负责业务", "老旧小区改造", {"来源": "首次对话"})
    mm2.add_fact("用户画像", "职级", "科室负责人", {"来源": "首次对话"})
    mm2.add_fact("工作偏好", "报告风格", "数据驱动、问题导向", {"来源": "对话推断"})
    mm2.add_fact("工作偏好", "常用文种", "通知、情况报告", {"来源": "对话推断"})
    mm2.add_fact("历史任务", "上次生成", "第三季度安全检查通知", {"来源": "交互记录"})
    print(f"  已记录 {len(mm2.memory)} 条记忆")

    print("\n检索与「报告」相关记忆...")
    results = mm2.search("报告")
    for r in results:
        print(f"  [{r['category']}] {r['key']}: {r['value']} (score={r['score']})")

    print("\n注入Prompt记忆上下文...")
    mem_context = mm2.get_context_for_prompt("老旧小区改造报告")
    print(f"  注入的记忆片段:\n{mem_context}")

    # ---- 用 LCEL 构建有记忆的 Chain ----
    print("\n构建 LCEL Chain（记忆增强版 vs 无记忆版）...")

    # 有记忆版 Chain
    prompt_with_mem = ChatPromptTemplate.from_messages([
        ("system",
         "你是一个政务文件生成助手。\n\n"
         "{memory_context}\n\n"
         "根据以上用户记忆，个性化生成文件：\n"
         "- 匹配用户部门和工作领域\n"
         "- 采用用户偏好的文风和格式\n"
         "- 参考历史任务经验"),
        ("human", "{question}"),
    ])

    chain_with_mem = prompt_with_mem | llm | StrOutputParser()

    # 无记忆版 Chain
    prompt_no_mem = ChatPromptTemplate.from_messages([
        ("system", "你是一个政务文件生成助手，请根据用户需求生成文件。"),
        ("human", "{question}"),
    ])

    chain_no_mem = prompt_no_mem | llm | StrOutputParser()

    # 步骤3: 对比有无记忆的对话质量
    print("\n--- 步骤3: 对比有无记忆的对话质量差异 ---")

    test_prompt = "帮我写一份老旧小区改造进展报告"

    print(f"\n无记忆版回答:")
    try:
        no_mem_answer = chain_no_mem.invoke({"question": test_prompt})
        print(f"  {no_mem_answer[:300]}...")
    except Exception as e:
        print(f"  [调用失败: {e}]")

    print(f"\n有记忆版回答:")
    try:
        with_mem_answer = chain_with_mem.invoke({
            "question": test_prompt,
            "memory_context": mem_context,
        })
        print(f"  {with_mem_answer[:300]}...")
    except Exception as e:
        print(f"  [调用失败: {e}]")

    print("\n对比分析:")
    print("  ┌──────────┬────────────────┬────────────────┐")
    print("  │ 维度     │ 无记忆         │ 有记忆         │")
    print("  ├──────────┼────────────────┼────────────────┤")
    print("  │ 部门归属 │ 泛化（未知）   │ XX区住建局     │")
    print("  │ 文风匹配 │ 默认公文风     │ 数据驱动风     │")
    print("  │ 业务深度 │ 通用水准       │ 老旧小区专项   │")
    print("  │ 历史参考 │ 无             │ 参考上次任务   │")
    print("  └──────────┴────────────────┴────────────────┘")

    print("\n核心洞察:")
    print("  - 记忆系统让Agent从「通用工具」进化为「专属助手」")
    print("  - 三种架构选择: 轻量用扁平，业务用JSON层级，复杂用高级卡片")
    print("  - 记忆注入Prompt是最简单有效的上下文工程手段之一")
    print("  - LCEL Chain: prompt模板中 {memory_context} 占位符 → invoke时传入记忆内容")

    print("\n课题3.8完成！")


# ============================================================
#  课题4: 金融领域自动化合同审核（增加HITL审批节点）
# ============================================================

# ---- Pydantic 输出模型 ----
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


# ============================================================
#  课题5: 制造领域招投标文件应用
# ============================================================

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


# ============================================================
#  课题6: 建筑/交通领域管理文件生成
# ============================================================

def exercise6_run():
    print("=" * 60)
    print("课题6: 建筑/交通领域管理文件生成")
    print("=" * 60)

    llm = get_llm()

    print("\n--- 步骤1: 构建公文生成 LCEL Chain ---")
    print("""
公文生成 Chain 设计：
  - 一个 ChatPromptTemplate，通过 {doc_type} 变量支持多种文种
  - System Prompt 包含公文规范（语体、格式、结构）
  - 输出: StrOutputParser（公文为自由格式文本，不需结构化解析）
    """)

    doc_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是一个公文写作助手，帮助政府部门工作人员快速生成规范的公文。\n\n"
         "当前生成文种：{doc_type}\n\n"
         "支持的公文类型：\n"
         "1. 【通知】会议通知、工作通知、检查通知\n"
         "2. 【报告】工作汇报、情况报告、调研报告\n"
         "3. 【纪要】会议纪要、专题会议纪要\n\n"
         "公文规范：\n"
         "- 使用正式公文语体，不使用口语\n"
         "- 标题格式：发文机关+事由+文种\n"
         "- 正文结构完整：开头（目的/依据）+主体+结尾\n"
         "- 涉及时间、数字使用阿拉伯数字\n"
         "- 禁止使用「大概」「可能」等模糊表述\n\n"
         "输出时按公文格式排版，包含标题、主送机关、正文、落款。"),
        ("human", "{content}"),
    ])

    doc_chain = doc_prompt | llm | StrOutputParser()
    print("公文生成 Chain 构建完成")

    # 步骤2: 生成不同类型公文
    print("\n--- 步骤2: 生成公文测试 ---")

    print("\n生成【会议通知】")
    try:
        notice = doc_chain.invoke({
            "doc_type": "通知",
            "content": "请生成一份会议通知：关于召开2026年第三季度住建系统安全生产工作会议，时间7月15日上午9:00，地点市住建局会议室，参会人员为各区住建局分管领导。"
        })
        print(f"  {notice}")
    except Exception as e:
        print(f"  [生成失败: {e}]")

    print("\n生成【工作报告】")
    try:
        report = doc_chain.invoke({
            "doc_type": "报告",
            "content": "请生成一份情况报告：关于XX区老旧小区改造进展情况，已完成8个小区改造，惠及居民3200户，投资额1.2亿元，当前存在问题：部分小区居民配合度不高。"
        })
        print(f"  {report}")
    except Exception as e:
        print(f"  [生成失败: {e}]")

    print("\n课题6完成！")


# ============================================================
#  课题7: 人力资源领域制度审查（增加记忆联动）
# ============================================================

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


# ============================================================
#  课题7.5: Prompt消融实验（新增原理层）
# ============================================================

def exercise75_run():
    print("=" * 60)
    print("课题7.5: Prompt消融实验")
    print("=" * 60)

    # 步骤1: 消融实验方法论
    print("\n--- 步骤1: 消融实验方法论 ---")
    print("""
消融实验（Ablation Study）是Prompt工程的核心评估方法：
  原理：逐个移除Prompt组件，观察输出质量变化，量化各组件贡献度

  典型Prompt组件：
  ┌──────────────────────────────────────┐
  │ System Prompt（系统提示）             │  角色定义、行为约束
  │ Few-shot Examples（少样本示例）       │  输出格式参照
  │ Tool Descriptions（工具描述）         │  工具选择依据
  │ Reasoning Chain（推理链引导）         │  复杂推理能力
  │ Tone/Style（语气风格）               │  输出语气控制
  └──────────────────────────────────────┘

  消融实验步骤：
  1. 建立Baseline（完整Prompt配置）
  2. 逐个移除组件，记录输出变化
  3. 用评估函数量化差异
  4. 排序各组件贡献度
    """)

    # 步骤2: 合同审核场景消融实践 — 用 LCEL Chain
    print("\n--- 步骤2: 合同审核场景消融实践 ---")

    test_contract = "贷款合同：金额300万元，年利率浮动（银行可单方面调整），担保方式为企业资产整体抵押（未评估），违约金为贷款总额的8%，银行可随时要求提前还款。"

    # 定义不同Prompt配置 → 不同的 LCEL Chain
    prompt_configs = {
        "baseline": {
            "label": "完整配置（Baseline）",
            "system_prompt": (
                "你是一个专业的金融合同审核助手。\n\n"
                "审核维度：\n"
                "1. 利率条款风险\n"
                "2. 担保条款风险\n"
                "3. 违约条款风险\n"
                "4. 权利平衡性\n\n"
                "输出格式：\n"
                "风险等级 | 风险条款数 | 详细审核意见 | 修改建议"
            ),
        },
        "no_system_prompt": {
            "label": "移除系统提示",
            "system_prompt": "请审核以下合同。",
        },
        "no_tool_description": {
            "label": "移除审核维度指引",
            "system_prompt": "你是一个合同审核助手。\n\n请审核合同。（无审核维度指引）",
        },
        "informal_tone": {
            "label": "改为非正式语气",
            "system_prompt": (
                "嘿！来帮我看看这个合同有没有坑哈～\n\n"
                "大概看看这几点就行：\n"
                "- 利率有问题不\n"
                "- 担保靠谱不\n"
                "- 违约金离谱不\n"
                "- 有没有特别霸王的地方\n\n"
                "随便说说就好，不用太正式～"
            ),
        },
    }

    llm = get_llm()
    results_cache = {}

    # 为每种配置创建不同的 LCEL Chain
    print("构建4个不同配置的 LCEL Chain...")

    def build_chain(system_prompt: str):
        """根据系统提示构建 LCEL Chain"""
        p = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{question}"),
        ])
        return p | llm | StrOutputParser()

    def evaluate_contract_review(question, answer):
        score = 0.0
        if not answer or len(answer) < 20:
            return 0.0
        risk_keywords = ["风险", "违约", "担保", "利率", "霸王", "不合规", "违规", "建议修改", "条款"]
        found = sum(1 for kw in risk_keywords if kw in answer)
        score += found / len(risk_keywords) * 0.6
        structure_keywords = ["|", "1.", "2.", "3.", "4.", "报告", "审核"]
        found_struct = sum(1 for kw in structure_keywords if kw in answer)
        score += found_struct / len(structure_keywords) * 0.2
        score += min(0.2, len(answer) / 1000)
        return round(min(1.0, score), 3)

    questions = [f"请审核以下合同并给出专业审核意见：\n{test_contract}"]

    print("开始消融实验...\n")

    all_mode_results = []
    mode_names = ["baseline", "no_system_prompt", "no_tool_description", "informal_tone"]

    for mode in mode_names:
        config = prompt_configs[mode]
        chain = build_chain(config["system_prompt"])
        scores = []
        for q in questions:
            try:
                answer = chain.invoke({"question": q})
                results_cache[mode] = answer
                score = evaluate_contract_review(q, answer)
                scores.append(score)
            except Exception as e:
                print(f"  [配置 {mode} 调用失败: {e}]")
                scores.append(0.0)

        avg = sum(scores) / len(scores) if scores else 0
        all_mode_results.append({
            "mode": mode,
            "label": config["label"],
            "avg_score": avg,
        })
        answer_preview = results_cache.get(mode, "")[:150].replace("\n", " ")
        print(f"  {config['label']}")
        print(f"     得分: {avg:.3f} | 回答预览: {answer_preview}...")

    # 步骤3: 量化评估
    print("\n--- 步骤3: 量化评估结果 ---")
    baseline_score = all_mode_results[0]["avg_score"] if all_mode_results else 0

    print(f"\n{'配置':<25} {'得分':>8} {'变化':>10}")
    print("-" * 50)
    for r in all_mode_results:
        delta = r["avg_score"] - baseline_score
        delta_str = f"{'+' if delta >= 0 else ''}{delta:.3f}"
        marker = "  baseline" if r["mode"] == "baseline" else ""
        bar = "#" * int(r["avg_score"] * 20)
        print(f"{r['label']:<25} {r['avg_score']:>8.3f} {delta_str:>10}{marker}")
        print(f"{'':>25} {bar}")

    print("\n消融实验洞察:")
    print("  - 系统提示贡献最大 → 定义了角色、审核维度、输出格式")
    print("  - 审核维度指引影响显著 → 没有指引则审核零散无体系")
    print("  - 语气风格影响中等 → 非正式语气导致输出不专业")
    print("  - Baseline配置综合最优 → 各组件协同效果 > 单组件之和")

    print("\n实践建议:")
    print("  - 做Prompt优化时，先用消融实验定位最关键组件")
    print("  - 系统提示是最值得投入优化时间的部分")
    print("  - 语气风格虽影响不大，但在正式场景不可或缺")
    print("  - LCEL Chain 让消融实验变得简单：只需替换 system_prompt 部分")

    print("\n课题7.5完成！")


# ============================================================
#  主入口
# ============================================================

EXERCISES = {
    "3.8": ("课题3.8: 用户记忆系统实验（原理层）", exercise38_run),
    "4":   ("课题4:   金融领域自动化合同审核（含HITL）", exercise4_run),
    "5":   ("课题5:   制造领域招投标文件应用", exercise5_run),
    "6":   ("课题6:   建筑/交通领域管理文件生成", exercise6_run),
    "7":   ("课题7:   人力资源领域制度审查（含记忆联动）", exercise7_run),
    "7.5": ("课题7.5: Prompt消融实验（原理层）", exercise75_run),
}

if __name__ == "__main__":
    print("Day 3 实战课题 — 文档生成与审核 + 上下文工程")
    print("=" * 50)
    check_api_config()
    print()
    print("可选课题：")
    for key, (desc, _) in EXERCISES.items():
        print(f"  {key:>3} - {desc}")
    print("  all  - 运行全部课题")
    print("  原理 - 仅运行原理层课题(3.8, 7.5)")
    print("  实战 - 仅运行实战层课题(4, 5, 6, 7)")

    choice = input("\n请输入选项: ").strip()

    if choice == "all":
        for key in ["3.8", "4", "5", "6", "7", "7.5"]:
            EXERCISES[key][1]()
    elif choice == "原理":
        for key in ["3.8", "7.5"]:
            EXERCISES[key][1]()
    elif choice == "实战":
        for key in ["4", "5", "6", "7"]:
            EXERCISES[key][1]()
    elif choice in EXERCISES:
        EXERCISES[choice][1]()
    else:
        print(f"无效选项: {choice}")
