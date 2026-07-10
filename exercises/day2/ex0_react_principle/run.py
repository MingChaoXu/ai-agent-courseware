"""
课题0: ReAct循环原理实验
=========================
- 步骤1: 理解Agent核心框架（LLM + Context + Tools）
- 步骤2: 手动模拟ReAct循环（Thought → Action → Observation）
- 步骤3: 上下文消融实验
- 步骤4: 用 LangChain 原生 API 构建真实 ReAct Agent
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'common'))

from langchain_core.tools import Tool
from langgraph.prebuilt import create_react_agent

from shared_utils import get_llm, check_api_config
from training_utils import ReActLoopSimulator


# ============================================================
#  课题0: ReAct循环原理实验
# ============================================================

def exercise0_step1_demo_agent_framework():
    """步骤1: 演示 Agent = 模型 + 上下文 + 工具 框架"""
    print("=" * 60)
    print("课题0: ReAct循环原理实验")
    print("步骤1: 理解Agent核心框架")
    print("=" * 60)
    print("""
Agent 核心公式：

    Agent = LLM + Context + Tools

    ┌─────────────────────────────────────────┐
    │              Agent 运行循环              │
    │                                         │
    │  ┌─────┐   ┌─────────┐   ┌───────┐    │
    │  │ LLM │ ◄─┤ Context │ ◄─┤ Tools │    │
    │  │(推理)│──►│(上下文) │──►│(工具) │    │
    │  └─────┘   └─────────┘   └───────┘    │
    │     │           ▲             │        │
    │     │           │             │        │
    │     ▼           │             ▼        │
    │  Thought ──► Action ──► Observation    │
    │     │                               │   │
    │     └─────► 更新Context ◄────────────┘   │
    │                                         │
    │  三大组件：                              │
    │  1) LLM：大语言模型，负责推理和决策       │
    │  2) Context：对话历史+系统提示+工具结果   │
    │  3) Tools：可调用的外部工具集             │
    └─────────────────────────────────────────┘

    ReAct (Reasoning + Acting) 循环：
    每轮迭代 = Thought → Action → Observation
    循环直到得到最终答案或达到最大迭代次数
    """)

    print("💡 关键洞察：")
    print("  - 没有LLM：无法推理，Agent无智能")
    print("  - 没有Context：无法记忆，每轮都是「失忆」状态")
    print("  - 没有Tools：无法行动，只能纯文本对话")
    print("  - 三者缺一不可，组合才能产生真正的Agent行为")


def exercise0_step2_run_react_loop():
    """步骤2: 用模拟器跑完整的ReAct循环（手动预设，理解原理）"""
    print("\n" + "=" * 60)
    print("步骤2: 手动模拟ReAct循环（理解原理）")
    print("=" * 60)

    def mock_search(query: str) -> str:
        mock_data = {
            "苏州户口迁移": "苏州市户口迁移需满足：1)合法稳定住所；2)参加社保满3年；3)无犯罪记录。办理地点：辖区派出所户籍窗口。",
            "苏州社保转移": "苏州社保转移流程：1)原参保地开具参保凭证；2)新参保地提交转移申请；3)45个工作日内完成转移。线上可通过国家社会保险公共服务平台办理。",
            "苏州公积金": "苏州公积金提取条件：购房、租房、退休、离职等。购房提取额度为账户余额的90%。",
        }
        for key, value in mock_data.items():
            if any(k in query for k in key):
                return value
        return f"未找到与「{query}」直接相关的结果，建议缩小搜索范围。"

    def mock_calculator(expression: str) -> str:
        try:
            allowed = set("0123456789+-*/().% ")
            if all(c in allowed for c in expression):
                return f"计算结果: {eval(expression)}"
            return "表达式包含不允许的字符"
        except Exception:
            return "计算错误，请检查表达式格式"

    tools = {"搜索": mock_search, "计算器": mock_calculator}
    sim = ReActLoopSimulator(tools=tools, max_iterations=5, verbose=True)

    iteration_plan = [
        {"thought": "用户问的是户口迁移的条件，我需要先搜索苏州户口迁移政策",
         "action": "搜索", "action_input": "苏州户口迁移"},
        {"thought": "搜索结果提到需要社保满3年，我来算一下用户2018年开始交社保到现在够不够3年",
         "action": "计算器", "action_input": "2026 - 2018"},
        {"thought": "已交社保8年，满足3年条件。再搜索一下社保转移能否同步办理",
         "action": "搜索", "action_input": "苏州社保转移"},
        {"thought": "现在信息足够了，可以综合回答。户口迁移需3年社保（用户满足8年），社保转移可线上同步办理",
         "action": "完成", "action_input": "根据查询结果：1)户口迁移需合法稳定住所+社保满3年+无犯罪记录（您已交8年社保，满足条件）；2)社保转移可同步在线办理，通过国家社会保险公共服务平台，45个工作日完成。"},
    ]

    question = "我是外地户口在苏州工作8年，想把户口迁过来，社保能一起转吗？"
    context = f"问题：{question}\n\n请使用 Thought-Action-Observation 格式推理。"
    sim.history = []

    print(f"\n用户问题: {question}")
    from training_utils import ReActStep
    for i, plan in enumerate(iteration_plan):
        print(f"\n--- 迭代 {i + 1} ---")
        thought = plan["thought"]
        action = plan["action"]
        action_input = plan["action_input"]

        print(f"💭 Thought: {thought}")
        print(f"🔧 Action: {action}({action_input})")

        if action == "完成":
            print(f"✅ 最终答案: {action_input}")
            break

        observation = sim.tools[action](action_input)
        print(f"👁 Observation: {observation}")

        step = ReActStep(
            iteration=i + 1, thought=thought, action=action,
            action_input=action_input, observation=observation,
            tokens_used=len(context) // 4,
        )
        sim.history.append(step)
        context += f"\nThought: {thought}\nAction: {action}[{action_input}]\nObservation: {observation}"

    print("""
💡 ReAct循环解析：
  - 第1轮：识别核心问题（户口迁移）→ 调用搜索工具
  - 第2轮：发现需要量化判断（社保年限）→ 调用计算器工具
  - 第3轮：发现关联问题（社保转移）→ 再次搜索
  - 第4轮：信息充分 → 输出最终答案
  这种「思考→行动→观察→再思考」的循环就是ReAct的核心
    """)
    return sim


def exercise0_step3_ablation(sim: ReActLoopSimulator):
    """步骤3: 上下文消融实验"""
    print("\n" + "=" * 60)
    print("步骤3: 上下文消融实验")
    print("=" * 60)
    print("消融实验目的：验证Agent各组件的不可替代性")

    results = sim.context_ablation("外地户口迁移苏州")

    print(f"\n{'消融模式':<25} {'估计Token':>10} {'效果说明'}")
    print("-" * 50)
    for mode, info in results.items():
        print(f"{mode:<25} {info['estimated_tokens']:>10}  {info['effect']}")

    print("""
💡 结论：Context是Agent的「工作记忆」，每个组件都不可省略
    """)


def exercise0_step4_real_agent():
    """步骤4: 用 LangChain 原生 API 构建真实 ReAct Agent"""
    print("\n" + "=" * 60)
    print("步骤4: 用 LangChain 原生 API 构建真实 ReAct Agent")
    print("=" * 60)
    print("""
上一节我们手动模拟了 ReAct 循环，现在用 LangGraph Agent 真实实现。

LangGraph ReAct Agent 的三大要素（对应课题0步骤1的公式）：
  1) LLM        → ChatOpenAI（推理引擎）
  2) Context    → Agent 自动管理（对话历史 + 工具描述 + 中间步骤）
  3) Tools      → langchain_core.tools.Tool（可调用工具）

构建步骤：
  ① 定义工具函数 → ② 包装为 Tool 对象 → ③ create_react_agent(llm, tools, prompt) → ④ agent.invoke()
    """)

    # ---- ① 定义工具函数 ----
    print("① 定义工具函数：")
    def search_policy(query: str) -> str:
        """搜索政务政策信息"""
        mock_data = {
            "苏州户口迁移": "苏州市户口迁移需满足：1)合法稳定住所；2)参加社保满3年；3)无犯罪记录。办理地点：辖区派出所户籍窗口。",
            "苏州社保转移": "苏州社保转移流程：1)原参保地开具参保凭证；2)新参保地提交转移申请；3)45个工作日内完成转移。",
            "苏州公积金": "苏州公积金提取条件：购房、租房、退休、离职等。购房提取额度为账户余额的90%。",
        }
        for key, value in mock_data.items():
            if any(k in query for k in key):
                return value
        return f"未找到与「{query}」直接相关的结果。"

    def calculate(expression: str) -> str:
        """计算数学表达式"""
        try:
            allowed = set("0123456789+-*/().% ")
            if all(c in allowed for c in expression):
                return f"计算结果: {eval(expression)}"
            return "表达式包含不允许的字符"
        except Exception:
            return "计算错误"

    print("  - search_policy(query): 搜索政务政策")
    print("  - calculate(expression): 数学计算")

    # ---- ② 包装为 Tool 对象 ----
    print("\n② 包装为 LangChain Tool 对象：")
    print("  Tool(name, func, description) — description 是 LLM 看到的工具说明书！")

    tools = [
        Tool(
            name="search_policy",
            func=search_policy,
            description="搜索政务政策信息，输入为搜索关键词，返回相关政策内容。适用于户口、社保、公积金等政务咨询。",
        ),
        Tool(
            name="calculate",
            func=calculate,
            description="计算数学表达式，输入为合法的数学表达式字符串，返回计算结果。例如 '2026-2018'。",
        ),
    ]
    print(f"  已创建 {len(tools)} 个 Tool 对象")

    # ---- ③ 创建 ReAct Agent ----
    print("\n③ 创建 ReAct Agent：")
    print("  create_react_agent(llm, tools=tools, prompt='system prompt') — 将 LLM + 工具 + 系统提示绑定为 Agent")

    llm = get_llm(temperature=0)

    system_prompt = (
        "你是一个政务咨询助手，请使用工具回答用户问题。\n\n"
        "你可以使用搜索和计算工具来获取信息。\n"
        "请按照 Thought → Action → Observation 的循环推理，直到得出最终答案。"
    )

    agent = create_react_agent(llm, tools=tools, prompt=system_prompt)
    print("  Agent 创建成功！")

    # ---- ④ 执行 Agent ----
    print("\n④ 执行 Agent：")
    print("  agent.invoke({\"messages\": [(\"user\", question)]})")
    print("  Agent 自动循环：调用LLM → 解析输出 → 执行工具 → 注入Observation → 循环")

    question = "我是外地户口在苏州工作8年，想把户口迁过来，社保能一起转吗？"
    print(f"\n👤 用户: {question}")
    print("-" * 40)

    try:
        result = agent.invoke({"messages": [("user", question)]})
        print(f"\n✅ Agent 最终回答:\n{result['messages'][-1].content}")
    except Exception as e:
        print(f"\n⚠️ Agent 执行出错: {e}")
        print("  可能原因：API 未配置或网络不通，请检查 .env 文件")

    print(f"""
对比总结：
  ┌──────────────┬──────────────────────────────────────────┐
  │ 步骤2（手动） │ 预设推理步骤，展示 ReAct 概念流程         │
  │ 步骤4（真实） │ LLM 自主决策工具调用 + Agent 自动循环     │
  └──────────────┴──────────────────────────────────────────┘
  关键差异：真实 Agent 的推理是不可预设的，LLM 自主选择工具和迭代次数

LangGraph ReAct Agent 构建法：
  ① 定义工具函数 → ② Tool 包装 → ③ create_react_agent(llm, tools, prompt) → ④ agent.invoke()
    """)


def run_exercise0():
    """运行课题0完整流程"""
    exercise0_step1_demo_agent_framework()
    sim = exercise0_step2_run_react_loop()
    exercise0_step3_ablation(sim)
    exercise0_step4_real_agent()
    print("\n课题0完成！你已理解 Agent 核心运行机制，并掌握了 LangChain Agent 四步构建法。")


if __name__ == "__main__":
    check_api_config()
    run_exercise0()
