"""
课题9: 制造领域BI分析 — LangChain Agent + Python执行工具
========================================================
使用 LangGraph create_react_agent 构建 BI 分析 Agent，
自主决定何时查数据、何时算统计、直接回答还是调工具。

技术栈：LangChain 1.x / LangGraph（Tool, create_react_agent, LCEL Chain）
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'common'))
from shared_utils import get_llm

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import Tool
from langgraph.prebuilt import create_react_agent


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


if __name__ == "__main__":
    exercise9_run()
