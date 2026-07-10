"""
Day 4 实战课题 — 数据分析与多模态场景 + 工具生态
===============================================
课题8.5:  多模态处理三种模式对比（原理层）
课题9:    制造领域BI分析（LangChain Agent + Python执行工具）
课题10:   消费领域精准营销（PydanticOutputParser 客户画像）
课题11:   金融领域舆情洞察（LCEL Chain 情感分析）
课题12:   制造领域AI质量检测（Agent + 多模态工具）
课题13:   能源领域CV安全助手（Agent + 安全检测工具）
课题13.5: MCP工具协议演示（原理层）

技术栈：LangChain 原生 API（ChatOpenAI, LCEL, create_react_agent, Tool, PydanticOutputParser）—— LangChain 1.x / LangGraph
"""

import sys
import os
import json
import time
import warnings; warnings.filterwarnings("ignore", category=DeprecationWarning)

# ============================================================
#  环境配置 & LangChain 核心导入
# ============================================================

from dotenv import load_dotenv
_env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(_env_path)

# ---- LangChain 核心 ----
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import Tool
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

# ---- 培训工具 ----
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "common"))
from training_utils import MCPClient, EventDrivenAgent

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
#  课题8.5: 多模态处理三种模式对比（原理层）
# ============================================================

def exercise8_5_run():
    print("=" * 60)
    print("课题8.5: 多模态处理三种模式对比")
    print("=" * 60)

    # 步骤1: 讲解三种模式
    print("\n--- 步骤1: 三种多模态处理模式 ---")
    print("""
多模态信息进入LLM的三种模式：

1. NATIVE（原生多模态）
   图片 → 直接送入多模态LLM（如GPT-4o） → LLM直接理解视觉内容
   特点：保真度最高，但需要多模态模型支持，成本较高

2. EXTRACT_TO_TEXT（提取为文本）
   图片 → OCR/目标检测 → 提取文本/标签 → 送入纯文本LLM
   特点：成本较低，但信息有损，丢失空间关系和视觉语义

3. TOOL（多模态工具）
   Agent → 调用视觉分析工具 → 获取结构化结果 → 送入LLM
   特点：灵活性高，可组合多个专用模型，但延迟较高

┌─────────┐     NATIVE      ┌──────────┐
│  图片    │ ──────────────► │ 多模态LLM │ → 直接理解
│         │                 └──────────┘
│         │     EXTRACT     ┌──────────┐  ┌──────────┐
│         │ ──────────────► │ OCR/检测  │→│ 文本LLM  │ → 间接理解
│         │                 └──────────┘  └──────────┘
│         │     TOOL        ┌──────────┐  ┌──────────┐
│         │ ──────────────► │ 视觉工具  │→│ Agent+LLM│ → 结构化理解
└─────────┘                 └──────────┘  └──────────┘""")

    # 步骤2: 用同一张产品图片对比三种模式
    print("\n--- 步骤2: 同一图片的三种模式处理对比 ---")
    image_description = "一张PCB电路板产品照片，上面有多个电子元件、焊点和丝印标签"

    print(f"\n测试图片: {image_description}")
    print("-" * 50)

    # NATIVE模式
    print("\n【模式1: NATIVE — 原生多模态】")
    print("  流程: 图片 → GPT-4o 直接理解")
    print("  Prompt: 「请分析这张PCB板图片，识别所有可见的元件和潜在缺陷」")
    print("  模拟输出:")
    native_result = {
        "元件识别": ["U1-主控芯片(BGA封装)", "C1-C8-贴片电容", "R1-R5-贴片电阻", "J1-排针连接器"],
        "缺陷检测": ["U1焊盘疑似桥接", "C3偏移约1mm"],
        "空间关系": "U1位于板中心，C1-C4环绕U1，C5-C8在板边缘",
        "整体评估": "板面基本整洁，发现2处疑似缺陷，建议重点复检U1焊盘"
    }
    for key, val in native_result.items():
        if isinstance(val, list):
            print(f"    {key}: {', '.join(val)}")
        else:
            print(f"    {key}: {val}")
    print("  优势: 保留完整视觉信息，可感知空间关系和外观细节")
    print("  劣势: 需要多模态模型，token消耗大（图片按token计费）")

    # EXTRACT_TO_TEXT模式
    print("\n【模式2: EXTRACT_TO_TEXT — 提取为文本】")
    print("  流程: 图片 → OCR提取文本 → 目标检测标签 → 纯文本LLM")
    print("  第一阶段 - OCR/检测提取:")
    print("    OCR结果: 「PCB-V3.2  SN:2026070801  MADE IN CN」")
    print("    检测标签: [芯片x1, 电容x8, 电阻x5, 连接器x1, 疑似桥接x1, 偏移x1]")
    print("  第二阶段 - 送入文本LLM:")
    print("    Prompt: 「基于以下提取信息分析PCB板: ...」")
    print("  模拟输出:")
    extract_result = {
        "元件识别": "检测到1个芯片、8个电容、5个电阻、1个连接器",
        "缺陷检测": "发现1处疑似桥接、1处偏移",
        "空间关系": "信息缺失 — 无法从文本推断空间布局",
        "整体评估": "存在2处缺陷标记，建议人工复检"
    }
    for key, val in extract_result.items():
        print(f"    {key}: {val}")
    print("  优势: 成本低，可用纯文本LLM，OCR能力强")
    print("  劣势: 丢失空间关系、颜色、纹理等视觉信息，信息有损")

    # TOOL模式
    print("\n【模式3: TOOL — 多模态工具】")
    print("  流程: Agent调度 → 调用专用视觉工具 → 获取结构化结果")
    print("  工具调用链:")
    print("    Tool1: defect_detection(image) → {桥接:1, 偏移:1, 置信度:0.92}")
    print("    Tool2: ocr_extract(image) → {丝印: 'PCB-V3.2', 序列号: '2026070801'}")
    print("    Tool3: component_count(image) → {芯片:1, 电容:8, 电阻:5}")
    print("  Agent整合:")
    print("  模拟输出:")
    tool_result = {
        "元件统计": "芯片1/Capacitor8/电阻5/连接器1",
        "缺陷报告": "[桥接]U1焊盘,置信92% | [偏移]C3,偏移1mm,置信88%",
        "OCR信息": "型号PCB-V3.2, 序列号2026070801",
        "整体评估": "缺陷率2/15=13.3%, 超出阈值5%, 判定不合格",
        "建议操作": "标记U1/C3区域, 生成返工工单, 通知产线负责人"
    }
    for key, val in tool_result.items():
        print(f"    {key}: {val}")
    print("  优势: 灵活组合专用模型，输出结构化，可执行后续动作")
    print("  劣势: 多次调用延迟高，工具编排复杂度高")

    # 步骤3: 分析权衡
    print("\n--- 步骤3: 三种模式权衡分析 ---")
    print("""
┌──────────────┬──────────┬──────────┬──────────┬──────────┐
│     维度      │  NATIVE  │ EXTRACT  │   TOOL   │   推荐   │
├──────────────┼──────────┼──────────┼──────────┼──────────┤
│ 信息保真度    │  ★★★★★  │  ★★★☆☆  │  ★★★★☆  │ NATIVE   │
│ 计算成本      │  ★★★☆☆  │  ★★★★★  │  ★★☆☆☆  │ EXTRACT  │
│ 灵活性        │  ★★★☆☆  │  ★★☆☆☆  │  ★★★★★  │ TOOL     │
│ 响应速度      │  ★★★★☆  │  ★★★★☆  │  ★★☆☆☆  │ NATIVE   │
│ 输出结构化    │  ★★☆☆☆  │  ★★★☆☆  │  ★★★★★  │ TOOL     │
│ 无多模态模型  │  不可用   │  可用     │  可用     │ EXTRACT  │
└──────────────┴──────────┴──────────┴──────────┴──────────┘

适用场景建议：
  NATIVE  → 需要理解视觉细节：产品外观审核、设计稿评审、医学影像
  EXTRACT → 以文字信息为主：发票识别、证件录入、表格提取
  TOOL    → 需要结构化输出+后续动作：质检流水线、安全巡检、自动告警

实战建议：优先用TOOL模式（结构化+可执行），复杂视觉理解叠加NATIVE，
   OCR场景用EXTRACT。三种模式可组合使用！""")

    print("\n课题8.5完成！")


# ============================================================
#  课题9: 制造领域BI分析 — LangChain Agent + Python执行工具
# ============================================================

# ---- 模拟数据 ----
_PRODUCTION_DATA = {
    "产线A": {"6月产量": [450, 480, 465, 490], "良品率": [0.92, 0.93, 0.91, 0.94]},
    "产线B": {"6月产量": [380, 395, 370, 400], "良品率": [0.88, 0.90, 0.86, 0.89]},
    "产线C": {"6月产量": [520, 510, 495, 530], "良品率": [0.95, 0.94, 0.93, 0.96]},
}

def _mock_data_query(query: str) -> str:
    """模拟生产数据查询工具"""
    data_summary = "6月生产数据汇总：\n"
    for line, d in _PRODUCTION_DATA.items():
        avg_rate = sum(d["良品率"]) / len(d["良品率"])
        total = sum(d["6月产量"])
        data_summary += f"  {line}: 产量{d['6月产量']}, 总计{total}, 平均良品率{avg_rate:.1%}\n"
    return data_summary


def _mock_code_execute(code: str) -> str:
    """模拟代码执行工具（安全沙箱，仅允许基本数学运算）"""
    try:
        # 仅允许基本数学计算，不执行真实代码
        allowed = set("0123456789+-*/()., %=\n")
        if not all(c in allowed for c in code[:200]):
            return "[沙箱] 仅允许基本数学运算"
        # 简单统计
        import statistics
        lines_code = code.strip()
        if "mean" in code or "平均" in code:
            result = "产线A平均良品率: 92.5%, 产线B平均良品率: 88.3%, 产线C平均良品率: 94.5%"
            return result
        if "std" in code or "标准差" in code or "变异系数" in code:
            return "产线A产量标准差: 16.8, 变异系数3.5%; 产线B产量标准差: 12.9, 变异系数3.3%; 产线C产量标准差: 15.1, 变异系数2.9%"
        if "correl" in code or "相关" in code:
            return "温度与缺陷率皮尔逊相关系数: r=0.78, p=0.003, 显著正相关"
        return "[沙箱] 代码执行完成。请使用 data_query 工具查询具体数据。"
    except Exception as e:
        return f"[沙箱] 执行错误: {e}"


def exercise9_run():
    print("=" * 60)
    print("课题9: 制造领域BI分析（LangChain Agent + 工具）")
    print("=" * 60)

    print("\n--- 步骤1: 构建 LangChain ReAct Agent（含数据分析工具） ---")
    print("""
本课题用 LangGraph create_react_agent 构建 BI 分析 Agent：
  ① 定义工具函数（数据查询 + 代码执行）
  ② 包装为 Tool 对象
  ③ create_react_agent(llm, tools=tools, prompt="system prompt")
  ④ agent.invoke({"messages": [("user", question)]})

  Agent 会自主决定：何时查数据、何时算统计、直接回答还是调工具
    """)

    # ---- ① 定义工具函数 ----
    print("① 定义工具函数：")
    print("  - data_query(query): 查询生产数据")
    print("  - code_execute(code): 执行统计分析代码")

    # ---- ② 包装为 Tool 对象 ----
    print("\n② 包装为 LangChain Tool 对象：")
    tools = [
        Tool(
            name="data_query",
            func=_mock_data_query,
            description="查询工厂生产数据，包括各产线的产量、良品率等数据。输入为查询描述，返回数据汇总。",
        ),
        Tool(
            name="code_execute",
            func=_mock_code_execute,
            description="在沙箱中执行Python统计分析代码，支持mean/std/correlation等统计计算。输入为Python代码字符串。",
        ),
    ]
    print(f"  已创建 {len(tools)} 个 Tool 对象: data_query, code_execute")

    # ---- ③ 创建 ReAct Agent ----
    print("\n③ 创建 ReAct Agent：")
    llm = get_llm(temperature=0)

    bi_prompt = (
        "你是一个生产数据BI分析助手，帮助生产管理人员通过自然语言查询和分析生产数据。\n\n"
        "分析能力：\n"
        "1. 【产量分析】按产线/产品/时间段统计产量、达成率\n"
        "2. 【质量分析】良品率、缺陷率趋势，缺陷类型分布\n"
        "3. 【异常检测】识别产量骤降、缺陷率突增等异常\n"
        "4. 【根因分析】对异常情况进行原因推断\n"
        "5. 【统计验证】通过代码执行做统计检验\n\n"
        "分析要求：\n"
        "- 数据结论必须有具体数字支撑\n"
        "- 异常必须标注并给出可能原因\n"
        "- 给出可操作的管理建议"
    )

    agent = create_react_agent(llm, tools=tools, prompt=bi_prompt)
    print("  Agent 创建成功！")

    # 步骤2: 自然语言查询测试
    print("\n--- 步骤2: 自然语言查询测试 ---")
    queries = [
        "6月份各产线的平均良品率是多少？",
    ]

    for q in queries:
        print(f"\n管理者: {q}")
        print("-" * 40)
        try:
            result = agent.invoke({"messages": [("user", q)]})
            output = result["messages"][-1].content
            print(f"\nBI助手: {output}")
        except Exception as e:
            print(f"Agent执行出错: {e}")
            print("  回退到 LCEL Chain 模式...")
            # 降级为 LCEL Chain
            fallback_prompt = ChatPromptTemplate.from_messages([
                ("system", "你是一个生产数据BI分析助手。以下是生产数据：\n{data}"),
                ("human", "{question}"),
            ])
            chain = fallback_prompt | llm | StrOutputParser()
            try:
                answer = chain.invoke({
                    "question": q,
                    "data": _mock_data_query(q),
                })
                print(f"  [Chain模式] {answer[:300]}...")
            except Exception as e2:
                print(f"  [Chain模式也失败: {e2}]")

    # 步骤3: 代码解释器统计分析
    print("\n--- 步骤3: 代码解释器统计分析 ---")
    stat_queries = [
        "请计算6月各周产量的标准差和变异系数，判断产量稳定性",
    ]

    for q in stat_queries:
        print(f"\n管理者: {q}")
        print("-" * 40)
        try:
            result = agent.invoke({"messages": [("user", q)]})
            print(f"\n统计分析结果: {result['messages'][-1].content}")
        except Exception as e:
            print(f"Agent执行出错: {e}")

    print("\n代码解释器让BI助手从「描述性分析」升级到「推断性分析」:")
    print("  - 描述性：良品率92.3% → 仅陈述事实")
    print("  - 推断性：p=0.003，温度与缺陷率显著正相关 → 可以指导决策")

    print("\n课题9完成！")


# ============================================================
#  课题10: 消费领域精准营销
# ============================================================

class CustomerProfile(BaseModel):
    """客户画像结构化输出"""
    customer_id: str = Field(description="客户ID")
    rfm_segment: str = Field(description="RFM分群：高价值/成长/流失风险/低价值")
    consumption_preference: list[str] = Field(description="偏好品类列表")
    shopping_habit: str = Field(description="购物习惯描述")
    marketing_strategy: str = Field(description="推荐营销策略")
    expected_roi: str = Field(description="预估ROI")


def exercise10_run():
    print("=" * 60)
    print("课题10: 消费领域精准营销")
    print("=" * 60)

    llm = get_llm()

    print("\n--- 步骤1: 构建精准营销 LCEL Chain（PydanticOutputParser） ---")
    print("""
精准营销 Chain 设计：
  ① Pydantic 定义 CustomerProfile 输出结构（RFM分群+营销策略）
  ② ChatPromptTemplate 注入客户数据 + format_instructions
  ③ LCEL: prompt → llm → PydanticOutputParser
  ④ 输出为 CustomerProfile 对象，直接访问字段
    """)

    parser = PydanticOutputParser(pydantic_object=CustomerProfile)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是一个精准营销助手，帮助零售企业分析客户数据并制定营销策略。\n\n"
         "核心能力：\n"
         "1. 【客户画像】根据消费记录、行为数据生成客户画像标签\n"
         "2. 【客户分群】基于RFM模型（最近消费时间/频次/金额）进行客户分群\n"
         "3. 【营销推荐】针对不同客户群推荐差异化营销策略\n"
         "4. 【效果预测】预估营销活动ROI\n\n"
         "客户分群参考：\n"
         "- 高价值客户：R近、F高、M高 → VIP维护、专属权益\n"
         "- 成长客户：R近、F中、M中 → 提升频次、交叉推荐\n"
         "- 流失风险：R远、F低、M高 → 召回优惠、个性化推荐\n"
         "- 低价值客户：R远、F低、M低 → 促销引流、降低服务成本\n\n"
         "{format_instructions}"),
        ("human", "请对以下客户生成画像分析，并推荐精准营销策略：\n\n{customer_data}"),
    ])

    prompt = prompt.partial(format_instructions=parser.get_format_instructions())

    # 支持多客户的 LCEL Chain
    profile_chain = prompt | llm | parser

    print("精准营销 Chain 构建完成")

    # 步骤2: 客户画像与营销推荐
    print("\n--- 步骤2: 客户画像与营销策略测试 ---")
    customer_data = """
客户ID: C20260001
基本信息：张女士，32岁，居住于市中心商圈
消费记录（近6个月）：
- 总消费：8,560元
- 消费频次：23次
- 最近消费：3天前
- 偏好品类：美妆(35%)、服饰(28%)、食品(22%)、家居(15%)
- 客单价：372元
- 常购时段：周末下午、工作日晚8点后
- 优惠券使用率：68%"""

    try:
        profile: CustomerProfile = profile_chain.invoke({"customer_data": customer_data})
        print(f"  客户ID:       {profile.customer_id}")
        print(f"  RFM分群:      {profile.rfm_segment}")
        print(f"  偏好品类:     {', '.join(profile.consumption_preference)}")
        print(f"  购物习惯:     {profile.shopping_habit}")
        print(f"  营销策略:     {profile.marketing_strategy}")
        print(f"  预估ROI:      {profile.expected_roi}")
    except Exception as e:
        print(f"  [结构化输出失败: {e}]，降级为文本模式...")
        try:
            text_chain = prompt | llm | StrOutputParser()
            result = text_chain.invoke({"customer_data": customer_data})
            print(f"  {result[:400]}...")
        except Exception as e2:
            print(f"  [文本模式也失败: {e2}]")

    print("\n课题10完成！")


# ============================================================
#  课题11: 金融领域舆情洞察
# ============================================================

class SentimentResult(BaseModel):
    """舆情情感分析结果"""
    item: str = Field(description="舆情条目摘要")
    sentiment: str = Field(description="情感判断：正面/中性/负面")
    sentiment_score: float = Field(description="情感得分(-1到+1)")
    risk_level: str = Field(description="舆情分级：红色预警/黄色关注/绿色正常")
    key_topic: str = Field(description="核心主题")
    suggested_action: str = Field(description="建议措施")


class SentimentReport(BaseModel):
    """舆情分析报告"""
    overall_sentiment: str = Field(description="整体舆情倾向")
    red_count: int = Field(description="红色预警数")
    yellow_count: int = Field(description="黄色关注数")
    green_count: int = Field(description="绿色正常数")
    hot_topics: list[str] = Field(description="热点关键词列表")
    items: list[SentimentResult] = Field(description="逐条分析")
    summary: str = Field(description="综述与建议")


def exercise11_run():
    print("=" * 60)
    print("课题11: 金融领域舆情洞察")
    print("=" * 60)

    llm = get_llm(temperature=0.1)

    print("\n--- 步骤1: 构建舆情分析 LCEL Chain（PydanticOutputParser） ---")

    parser = PydanticOutputParser(pydantic_object=SentimentReport)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是一个舆情洞察助手，帮助银行监测和分析品牌舆情。\n\n"
         "分析能力：\n"
         "1. 【情感分析】判断舆情正面/中性/负面，给出情感得分(-1到+1)\n"
         "2. 【热点提取】识别高频关键词和主题\n"
         "3. 【风险研判】判断舆情是否可能升级为公关危机\n"
         "4. 【报告生成】生成舆情分析报告\n\n"
         "舆情分级：\n"
         "- 红色预警：负面情感>0.7，涉及监管/诉讼/群体事件\n"
         "- 黄色关注：负面情感0.3-0.7，有传播趋势\n"
         "- 绿色正常：正面/中性为主，无风险迹象\n\n"
         "{format_instructions}"),
        ("human", "请分析以下舆情数据，给出情感的逐条判断、风险研判和建议：\n\n{news_data}"),
    ])

    prompt = prompt.partial(format_instructions=parser.get_format_instructions())

    sentiment_chain = prompt | llm | parser
    print("舆情分析 Chain 构建完成")

    # 步骤2: 舆情分析
    print("\n--- 步骤2: 舆情分析测试 ---")
    news_items = """
舆情数据（2026年6月25日-7月1日）：

1. [微博] 「XX银行APP又崩了，转账转了半小时！」#XX银行APP故障# 阅读量12万，评论856条
2. [知乎] 「在XX银行办房贷是什么体验」 - 作者分享了3天批贷的顺利经历，获赞320
3. [抖音] 博主曝光XX银行信用卡隐藏收费项目，视频播放量45万，转发2000+
4. [小红书] 「XX银行新出的数字藏品太酷了」 - 正面种草帖，互动800+
5. [贴吧] 多人反映XX银行网点排队2小时以上，帖子被反复引用
6. [新闻] XX银行发布半年报，净利润同比增长12%，多家券商给出买入评级"""

    try:
        report: SentimentReport = sentiment_chain.invoke({"news_data": news_items})
        print(f"  整体舆情: {report.overall_sentiment}")
        print(f"  红/黄/绿: {report.red_count}/{report.yellow_count}/{report.green_count}")
        print(f"  热点: {', '.join(report.hot_topics[:5])}")
        for item in report.items[:4]:
            icon = "🔴" if item.risk_level == "红色预警" else ("🟡" if item.risk_level == "黄色关注" else "🟢")
            print(f"  {icon} [{item.sentiment}] {item.item[:40]}... → {item.suggested_action[:40]}")
        print(f"  综述: {report.summary[:200]}...")
    except Exception as e:
        print(f"  [结构化输出失败: {e}]，降级为文本模式...")
        try:
            text_chain = prompt | llm | StrOutputParser()
            result = text_chain.invoke({"news_data": news_items})
            print(f"  {result[:400]}...")
        except Exception as e2:
            print(f"  [文本模式也失败: {e2}]")

    print("\n课题11完成！")


# ============================================================
#  课题12: 制造领域AI质量检测 — LangChain Agent + 多模态工具
# ============================================================

def exercise12_run():
    print("=" * 60)
    print("课题12: 制造领域AI质量检测（Agent + 多模态工具）")
    print("=" * 60)

    print("\n--- 步骤1: 构建质量检测 LangChain Agent ---")
    print("""
质检 Agent 设计（TOOL模式）：
  ① 模拟视觉检测工具（defect_detect, ocr_extract, component_count）
  ② 包装为 Tool 对象
   ③ create_react_agent（LangGraph 版）

  三种多模态模式通过不同工具组合实现：
  - NATIVE：Agent 直接理解图片描述
  - EXTRACT：调用 ocr_extract 工具
  - TOOL：调用 defect_detect + component_count 工具
    """)

    # ---- 模拟视觉工具 ----
    def defect_detect(image_desc: str) -> str:
        """模拟缺陷检测工具"""
        return json.dumps({
            "桥接": [{"location": "U1-pin3", "confidence": 0.95},
                     {"location": "U1-pin7", "confidence": 0.91},
                     {"location": "U2-pin2", "confidence": 0.88}],
            "偏移": [{"location": "C3", "offset": "2mm", "confidence": 0.93}],
            "划伤": [{"location": "板面左侧", "length": "2cm", "confidence": 0.87}]
        }, ensure_ascii=False)

    def ocr_extract(image_desc: str) -> str:
        """模拟OCR提取工具"""
        return json.dumps({
            "丝印": "PCB-V3.2",
            "序列号": "SN20260708",
            "产地": "MADE IN CN"
        }, ensure_ascii=False)

    def component_count(image_desc: str) -> str:
        """模拟元件计数工具"""
        return json.dumps({
            "芯片": 1, "电容": 8, "电阻": 5, "连接器": 1,
            "总元件数": 15, "缺陷数": 5, "缺陷率": "33.3%"
        }, ensure_ascii=False)

    # ---- 包装为 Tool ----
    tools = [
        Tool(
            name="defect_detect",
            func=defect_detect,
            description="对PCB板图片进行缺陷检测，返回桥接、偏移、划伤等缺陷的检测结果（位置+置信度）。输入为图片描述。",
        ),
        Tool(
            name="ocr_extract",
            func=ocr_extract,
            description="对PCB板图片进行OCR文字提取，返回丝印、序列号等信息。输入为图片描述。",
        ),
        Tool(
            name="component_count",
            func=component_count,
            description="对PCB板图片进行元件计数，返回各类元件数量和缺陷率统计。输入为图片描述。",
        ),
    ]

    llm = get_llm(temperature=0)

    quality_prompt = (
        "你是一个AI质量检测助手，帮助工厂对产品外观进行自动缺陷检测。\n\n"
        "检测流程：\n"
        "1. 接收产品图片描述\n"
        "2. 使用工具进行缺陷检测、OCR提取和元件计数\n"
        "3. 综合分析并生成检测报告\n"
        "4. 判定合格/不合格\n\n"
        "常见缺陷类型：\n"
        "- 焊点缺陷：虚焊、桥接、冷焊、漏焊\n"
        "- 元件缺陷：偏移、缺件、极性反、损伤\n"
        "- 板面缺陷：划伤、污渍、镀层脱落\n\n"
        "判定标准：缺陷率>5%判定不合格，置信度<80%标记需人工复检"
    )

    agent = create_react_agent(llm, tools=tools, prompt=quality_prompt)

    # 步骤2: 三种多模态模式质检对比
    print("\n--- 步骤2: 三种多模态模式质检对比 ---")
    test_image = "PCB板：板面有3处焊点桥接，1个电容偏移2mm，板面有2cm划伤，丝印标注PCB-V3.2"

    print(f"\n测试图片描述: {test_image}")

    # NATIVE模式 — 直接 LCEL Chain 调用（无需工具）
    print("\n【NATIVE模式质检】")
    print("  → 图片直接送入LLM理解")
    native_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "你是AI质检助手。请基于图片描述直接分析产品缺陷。\n"
         "输出：检测结果 | 缺陷数量 | 缺陷明细 | 整体判定"),
        ("human", "请直接分析这张PCB板图片：{image_desc}。识别所有缺陷并给出检测结果。"),
    ])
    native_chain = native_prompt | llm | StrOutputParser()
    try:
        result = native_chain.invoke({"image_desc": test_image})
        print(f"  NATIVE检测结果:\n  {result[:300]}...")
    except Exception as e:
        print(f"  [NATIVE模式失败: {e}]")

    # EXTRACT模式 — 先提取再分析
    print("\n【EXTRACT_TO_TEXT模式质检】")
    print("  → 先OCR/检测提取，再文本分析")
    extract_info = ocr_extract(test_image)
    extract_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是AI质检助手。基于以下OCR提取信息分析PCB板缺陷，判断是否合格。"),
        ("human", "OCR提取信息: {extract_data}\n\n请判断PCB板是否合格。"),
    ])
    extract_chain = extract_prompt | llm | StrOutputParser()
    try:
        result = extract_chain.invoke({"extract_data": extract_info})
        print(f"  EXTRACT检测结果:\n  {result[:300]}...")
    except Exception as e:
        print(f"  [EXTRACT模式失败: {e}]")

    # TOOL模式 — Agent + 视觉工具
    print("\n【TOOL模式质检】")
    print("  → Agent调用专用视觉工具获取结构化结果")
    try:
        result = agent.invoke({
            "messages": [("user", f"请对以下PCB板进行全面质检：{test_image}。依次调用缺陷检测、OCR提取和元件计数工具，然后综合判定是否合格。")]
        })
        print(f"\n  TOOL检测报告:\n  {result['messages'][-1].content[:300]}...")
    except Exception as e:
        print(f"  Agent执行出错: {e}")
        # 降级：手动拼接工具结果 + LCEL Chain
        print("  降级为手动工具调用 + LCEL Chain...")
        tool_data = f"缺陷检测: {defect_detect(test_image)}\nOCR: {ocr_extract(test_image)}\n计数: {component_count(test_image)}"
        tool_prompt = ChatPromptTemplate.from_messages([
            ("system", "你是AI质检助手。基于视觉工具返回的结构化结果生成检测报告并判定合格/不合格。"),
            ("human", "工具返回数据：\n{tool_data}\n\n请生成检测报告。"),
        ])
        tool_chain = tool_prompt | llm | StrOutputParser()
        try:
            result = tool_chain.invoke({"tool_data": tool_data})
            print(f"  [Chain模式] {result[:300]}...")
        except Exception as e2:
            print(f"  [Chain模式也失败: {e2}]")

    print("\n三种模式在质检场景的对比：")
    print("  NATIVE：能感知焊点颜色和光泽差异，但token成本高")
    print("  EXTRACT：准确提取丝印文字，但丢失焊点外观细节")
    print("  TOOL：结构化输出适合自动化流水线，可触发返工工单")
    print("  产线推荐：TOOL为主 + NATIVE复核疑难件")

    print("\n课题12完成！")


# ============================================================
#  课题13: 能源领域CV安全助手 — Agent + 安全检测工具
# ============================================================

def exercise13_run():
    print("=" * 60)
    print("课题13: 能源领域CV安全助手（Agent + 安全检测工具）")
    print("=" * 60)

    print("\n--- 步骤1: 构建安全检测 LangChain Agent ---")

    # ---- 模拟安全检测工具 ----
    def ppe_check(scene_desc: str) -> str:
        """模拟PPE（个人防护装备）检测工具"""
        return json.dumps({
            "人员A": {"安全帽": "已佩戴", "绝缘手套": "未佩戴", "绝缘鞋": "已佩戴"},
            "人员B": {"安全帽": "已佩戴", "绝缘手套": "已佩戴", "绝缘鞋": "已佩戴"},
        }, ensure_ascii=False)

    def distance_check(scene_desc: str) -> str:
        """模拟安全距离检测工具"""
        return json.dumps({
            "电压等级": "10kV",
            "实测距离": "0.5m",
            "要求距离": "≥0.7m",
            "判定": "违规",
        }, ensure_ascii=False)

    def environment_check(scene_desc: str) -> str:
        """模拟环境检测工具"""
        return json.dumps({
            "围栏完整性": "3面/应4面",
            "警示标志": "有",
            "通道畅通": "否（杂物堵塞）",
        }, ensure_ascii=False)

    tools = [
        Tool(
            name="ppe_check",
            func=ppe_check,
            description="检测作业人员PPE（安全帽、绝缘手套、绝缘鞋、安全带等）佩戴情况。输入为场景描述。",
        ),
        Tool(
            name="distance_check",
            func=distance_check,
            description="检测作业人员与带电设备的安全距离是否合规。输入为场景描述。",
        ),
        Tool(
            name="environment_check",
            func=environment_check,
            description="检测作业环境安全（围栏、警示标志、通道等）。输入为场景描述。",
        ),
    ]

    llm = get_llm(temperature=0)

    safety_prompt = (
        "你是作业现场安全检测助手，帮助能源企业识别现场安全隐患。\n\n"
        "检测项目：\n"
        "1. 【个人防护装备】安全帽、绝缘手套、护目镜、安全带是否佩戴\n"
        "2. 【作业环境】围栏设置、警示标志、安全距离是否合规\n"
        "3. 【设备状态】接地线、绝缘工具、验电器是否正确使用\n\n"
        "风险分级：\n"
        "- 严重：未佩戴安全帽/绝缘手套、带电作业无防护 → 立即停工\n"
        "- 一般：围栏不完整、警示标志缺失 → 限期整改\n"
        "- 提示：工具摆放不规范、通道不畅 → 建议改进\n\n"
        "电力作业安全规程：\n"
        "- 安全距离：10kV≥0.7m，35kV≥1.0m，110kV≥1.5m\n"
        "- 高处作业≥2m必须使用安全带\n"
        "- 带电作业必须使用绝缘工具并有专人监护"
    )

    agent = create_react_agent(llm, tools=tools, prompt=safety_prompt)

    # 步骤2: 三种多模态模式安全检测对比
    print("\n--- 步骤2: 三种模式安全检测对比 ---")
    scene = "10kV配电室检修现场，2名作业人员，1人未戴绝缘手套，围栏缺少一面，0.5m处有非作业人员"

    print(f"\n场景描述: {scene}")

    # NATIVE模式
    print("\n【NATIVE模式 - 直接理解】")
    native_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是安全检测助手。基于现场描述直接判断所有安全隐患。\n电力规程：10kV安全距离≥0.7m，绝缘手套必须佩戴。"),
        ("human", "直接观察现场：{scene}。判断所有安全隐患。"),
    ])
    native_chain = native_prompt | llm | StrOutputParser()
    try:
        result = native_chain.invoke({"scene": scene})
        print(f"  NATIVE安全检测:\n  {result[:300]}...")
    except Exception as e:
        print(f"  [NATIVE模式失败: {e}]")

    # EXTRACT模式
    print("\n【EXTRACT模式 - 标签提取后分析】")
    ppe_labels = "人员A=[安全帽已佩戴, 绝缘手套未佩戴, 绝缘鞋已佩戴], 人员B=[全部合规]\n围栏[3面/应4面], 距离[0.5m/要求≥0.7m]"
    extract_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是安全检测助手。基于检测标签分析安全隐患并评估。"),
        ("human", "检测标签：{labels}\n\n请给出安全评估。"),
    ])
    extract_chain = extract_prompt | llm | StrOutputParser()
    try:
        result = extract_chain.invoke({"labels": ppe_labels})
        print(f"  EXTRACT安全评估:\n  {result[:300]}...")
    except Exception as e:
        print(f"  [EXTRACT模式失败: {e}]")

    # TOOL模式
    print("\n【TOOL模式 - Agent + 专用安全工具】")
    try:
        result = agent.invoke({
            "messages": [("user", f"请对以下场景进行安全检测：{scene}。依次调用PPE检测、距离检测和环境检测工具，然后综合给出安全评估。")]
        })
        print(f"\n  TOOL安全报告:\n  {result['messages'][-1].content[:300]}...")
    except Exception as e:
        print(f"  Agent执行出错: {e}")
        # 降级
        tool_data = f"PPE: {ppe_check(scene)}\n距离: {distance_check(scene)}\n环境: {environment_check(scene)}"
        tool_prompt = ChatPromptTemplate.from_messages([
            ("system", "你是安全检测助手。基于安全工具返回的结构化结果生成安全检测报告并定级。"),
            ("human", "工具数据：\n{tool_data}\n\n请生成安全报告。"),
        ])
        tool_chain = tool_prompt | llm | StrOutputParser()
        try:
            result = tool_chain.invoke({"tool_data": tool_data})
            print(f"  [Chain模式] {result[:300]}...")
        except Exception as e2:
            print(f"  [Chain模式也失败: {e2}]")

    # 拓展
    print("\n--- 拓展：电力设备智能巡检 ---")
    patrol_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是电力设备巡检助手。基于巡检数据判断设备状态。"),
        ("human", "变压器巡检：外观有轻微渗油痕迹，油位计指示偏低，呼吸器硅胶变色1/3，温度计显示65℃。请判断状态。"),
    ])
    patrol_chain = patrol_prompt | llm | StrOutputParser()
    try:
        result = patrol_chain.invoke({})
        print(f"  巡检分析:\n  {result[:300]}...")
    except Exception as e:
        print(f"  [调用失败: {e}]")

    print("\n三种模式在安全场景的对比：")
    print("  NATIVE：能发现PPE标签检测不到的问题（如手套破损、安全带未扣紧）")
    print("  EXTRACT：快速批量检测PPE佩戴，适合人员众多的场景")
    print("  TOOL：结构化违规清单可直接对接工单系统，触发整改流程")
    print("  安全推荐：TOOL做初筛 + NATIVE复核高风险场景")

    print("\n课题13完成！")


# ============================================================
#  课题13.5: MCP工具协议演示（原理层）
# ============================================================

def exercise13_5_run():
    print("=" * 60)
    print("课题13.5: MCP工具协议演示")
    print("=" * 60)

    # 步骤1: MCP协议概念
    print("\n--- 步骤1: MCP协议概念演示 ---")
    mcp = MCPClient()
    print("""
MCP (Model Context Protocol) 是什么？
─────────────────────────────────────
一个开放协议，让AI应用能以标准化方式连接外部工具和数据源。

┌──────────────┐  MCP协议   ┌──────────────┐
│  AI应用      │ ◄────────► │  MCP Server  │
│  (AI应用)  │  JSON-RPC  │  (工具服务)   │
└──────────────┘            └──────────────┘
      │                           │
      │ 可连接多个Server           │ 可提供多个Tool
      ├─► 感知服务器              ├─► web_search
      ├─► 执行服务器              ├─► code_execute
      └─► 协作服务器              └─► send_notification

核心流程：
  1. Client → Server: 连接（connect）
  2. Client → Server: 发现工具（discover_tools）
  3. Client → Server: 调用工具（call_tool）
  4. Server → Client: 返回结果""")

    mcp.connect("mcp://teleagent-perception:3001")
    tools = mcp.discover_tools()
    print(f"\n发现 {len(tools)} 个工具:")
    for t in tools:
        print(f"  - {t['name']}: {t['description']}")

    # 步骤2: 三大工具类型演示
    print("\n--- 步骤2: 三大工具类型演示 ---")

    # 感知工具
    print("\n【感知工具】— 获取外部信息")
    perception_server = MCPClient()
    perception_server.connect("mcp://perception-server:3001")
    perception_server.tools = {
        "web_search": {"name": "web_search", "description": "搜索互联网信息",
                       "inputSchema": {"query": {"type": "string"}}},
        "image_analyze": {"name": "image_analyze", "description": "多模态图片理解",
                          "inputSchema": {"image_url": {"type": "string"}, "prompt": {"type": "string"}}},
        "file_read": {"name": "file_read", "description": "读取文件内容",
                      "inputSchema": {"path": {"type": "string"}}},
        "database_query": {"name": "database_query", "description": "查询数据库",
                           "inputSchema": {"sql": {"type": "string"}}},
    }
    print("  可用工具:")
    for name, tool in perception_server.tools.items():
        print(f"    - {name}: {tool['description']}")
    print("\n  调用演示:")
    perception_server.call_tool("web_search", {"query": "2026年电信行业数字化转型政策"})
    perception_server.call_tool("image_analyze", {"image_url": "https://example.com/pcb.jpg", "prompt": "检测缺陷"})

    # 执行工具
    print("\n【执行工具】— 执行操作和代码")
    execution_server = MCPClient()
    execution_server.connect("mcp://execution-server:3002")
    execution_server.tools = {
        "code_execute": {"name": "code_execute", "description": "在沙箱中执行Python代码",
                         "inputSchema": {"code": {"type": "string"}}},
        "file_write": {"name": "file_write", "description": "写入文件",
                       "inputSchema": {"path": {"type": "string"}, "content": {"type": "string"}}},
        "chart_generate": {"name": "chart_generate", "description": "生成数据可视化图表",
                           "inputSchema": {"data": {"type": "object"}, "chart_type": {"type": "string"}}},
    }
    print("  可用工具:")
    for name, tool in execution_server.tools.items():
        print(f"    - {name}: {tool['description']}")
    print("\n  调用演示:")
    execution_server.call_tool("code_execute", {"code": "import pandas as pd\ndf = pd.read_csv('data.csv')\nprint(df.describe())"})
    execution_server.call_tool("chart_generate", {"data": {"labels": ["1月","2月","3月"], "values": [100,120,115]}, "chart_type": "bar"})

    # 协作工具
    print("\n【协作工具】— 通知、审批和人机协同")
    collaboration_server = MCPClient()
    collaboration_server.connect("mcp://collaboration-server:3003")
    collaboration_server.tools = {
        "send_notification": {"name": "send_notification", "description": "发送通知消息（邮件/短信/钉钉）",
                              "inputSchema": {"channel": {"type": "string"}, "message": {"type": "string"}, "recipients": {"type": "array"}}},
        "request_approval": {"name": "request_approval", "description": "请求人工审批",
                             "inputSchema": {"task": {"type": "string"}, "risk_level": {"type": "string"}}},
        "schedule_task": {"name": "schedule_task", "description": "创建定时任务",
                          "inputSchema": {"cron": {"type": "string"}, "action": {"type": "string"}}},
    }
    print("  可用工具:")
    for name, tool in collaboration_server.tools.items():
        print(f"    - {name}: {tool['description']}")
    print("\n  调用演示:")
    collaboration_server.call_tool("send_notification", {"channel": "dingtalk", "message": "产线A缺陷率超过阈值", "recipients": ["line_manager"]})
    collaboration_server.call_tool("request_approval", {"task": "批量返工工单审批", "risk_level": "medium"})

    # 步骤3: 将MCP工具映射为 LangChain Tool + Agent
    print("\n--- 步骤3: 将MCP工具映射为 LangChain Tool + Agent ---")
    print("""
MCP → LangChain 的映射关系：
  MCP Tool    →    LangChain Tool
  ─────────────────────────────────
  name        →    Tool(name=...)
  description →    Tool(description=...)
  inputSchema →    func 参数
  call_tool   →    func 调用

  映射后即可用 create_react_agent 编排 MCP 工具
    """)

    llm = get_llm(temperature=0)

    # 将 MCP 工具映射为 LangChain Tool
    def mcp_web_search(query: str) -> str:
        return f"[MCP感知] 搜索「{query}」: 找到3条相关问题..."

    def mcp_code_execute(code: str) -> str:
        return f"[MCP执行] 代码执行完成: 计算结果=92.5"

    def mcp_send_notification(params: str) -> str:
        return f"[MCP协作] 通知已发送至: {params}"

    langchain_tools = [
        Tool(name="web_search", func=mcp_web_search,
             description="搜索互联网信息，输入搜索关键词。"),
        Tool(name="code_execute", func=mcp_code_execute,
             description="在沙箱中执行Python代码进行统计分析，输入Python代码字符串。"),
        Tool(name="send_notification", func=mcp_send_notification,
             description="发送通知消息，输入为JSON格式: {channel, message, recipients}。"),
    ]

    mcp_prompt_text = (
        "你是一个集成了MCP工具的智能体，可感知、执行、协作。\n\n"
        "决策流程：\n"
        "1. 理解用户需求\n"
        "2. 判断需要哪类工具\n"
        "3. 调用对应工具\n"
        "4. 整合返回结果回答用户"
    )

    try:
        mcp_agent = create_react_agent(llm, tools=langchain_tools, prompt=mcp_prompt_text)
        print("  MCP → LangChain Agent 创建成功！")

        result = mcp_agent.invoke({
            "messages": [("user", "帮我搜一下最新的数字化转型政策，然后用Python统计关键词出现频率")]
        })
        print(f"\n  MCP Agent 回答: {result['messages'][-1].content[:200]}...")
    except Exception as e:
        print(f"  MCP Agent 执行出错: {e}")

    # 步骤4: 事件触发型Agent演示
    print("\n--- 步骤4: 事件触发型Agent演示 ---")
    print("场景：数据异常 → 自动检测 → 发送告警")

    evt_agent = EventDrivenAgent(name="生产监控Agent", client=None)
    # 不传client，仅演示事件框架

    print("\n注册事件处理器...")
    evt_agent.register_handler("data_alert", lambda e: print(f"  数据告警处理: {e.data.get('metric')}={e.data.get('value')}"))
    evt_agent.register_handler("timer", lambda e: print(f"  定时任务: {e.data.get('task')}"))
    evt_agent.register_handler("approval_result", lambda e: print(f"  审批结果: {e.data.get('decision')}"))

    print("\n模拟事件流：")
    print("  ──── 事件1: 数据异常 ────")

    alert_event = EventDrivenAgent.Event(
        event_type="data_alert",
        source="生产监控系统",
        data={"metric": "缺陷率", "value": "5.2%", "threshold": "3%", "line": "产线A"}
    )
    evt_agent.emit_event(alert_event)

    print("\n  → Agent自动推理流程：")
    print("    1. 检测到缺陷率5.2%超过阈值3%")
    print("    2. 通过MCP感知工具查询近1小时缺陷率趋势")
    evt_agent.add_todo("查询缺陷率趋势数据", "high")
    print("    3. 通过MCP执行工具运行Python做异常归因分析")
    evt_agent.add_todo("运行异常归因分析", "high")
    print("    4. 通过MCP协作工具发送告警通知+请求审批")
    evt_agent.add_todo("发送告警+请求返工审批", "high")
    evt_agent.update_system_hints()

    print(f"\n  当前待办: {json.dumps(evt_agent.todo_list, ensure_ascii=False, default=str)}")

    print("\n  ──── 事件2: 审批回调 ────")
    approval_event = EventDrivenAgent.Event(
        event_type="approval_result",
        source="审批系统",
        data={"decision": "approved", "approver": "产线主管王工", "task": "批量返工"}
    )
    evt_agent.emit_event(approval_event)
    print("  → 审批通过，自动触发返工工单创建")

    print("""
MCP + 事件驱动 = 智能自动化：

  传统模式：人看报表 → 人发现问题 → 人写邮件 → 人等审批 → 人下工单
  MCP模式：  数据异常 → Agent自动检测 → Agent调工具分析 → Agent发告警 → Agent等审批 → Agent下工单

  关键变化：
  - 从「人驱动」变成「事件驱动」
  - 从「一个一个操作」变成「全自动链路」
  - 人只做关键决策（审批），其余AI自动完成""")

    print("\n课题13.5完成！")


# ============================================================
#  主入口
# ============================================================

EXERCISES = {
    "8.5":  ("课题8.5:  多模态处理三种模式对比（原理层）", exercise8_5_run),
    "9":    ("课题9:    制造领域BI分析（Agent+工具）", exercise9_run),
    "10":   ("课题10:   消费领域精准营销", exercise10_run),
    "11":   ("课题11:   金融领域舆情洞察", exercise11_run),
    "12":   ("课题12:   制造领域AI质量检测（Agent+工具）", exercise12_run),
    "13":   ("课题13:   能源领域CV安全助手（Agent+工具）", exercise13_run),
    "13.5": ("课题13.5: MCP工具协议演示（原理层）", exercise13_5_run),
}

if __name__ == "__main__":
    print("Day 4: 数据分析与多模态场景 + 工具生态")
    print("=" * 50)
    check_api_config()
    print()
    print("可选课题：")
    for key, (desc, _) in EXERCISES.items():
        print(f"  {key:>4} - {desc}")
    print("  all  - 运行全部课题")
    print("  原理 - 仅运行原理层课题(8.5, 13.5)")
    print("  实战 - 仅运行实战层课题(9, 10, 11, 12, 13)")

    choice = input("\n请输入选项: ").strip()

    if choice == "all":
        for key in ["8.5", "9", "10", "11", "12", "13", "13.5"]:
            EXERCISES[key][1]()
    elif choice == "原理":
        for key in ["8.5", "13.5"]:
            EXERCISES[key][1]()
    elif choice == "实战":
        for key in ["9", "10", "11", "12", "13"]:
            EXERCISES[key][1]()
    elif choice in EXERCISES:
        EXERCISES[choice][1]()
    else:
        print(f"无效选项: {choice}")
