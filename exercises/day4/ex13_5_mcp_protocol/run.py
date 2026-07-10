"""
课题13.5: MCP工具协议演示（原理层）
====================================
演示 MCP (Model Context Protocol) 协议核心概念：
  - 三大工具类型（感知/执行/协作）
  - MCP → LangChain Tool 映射
  - 事件驱动 Agent + MCP 工具协同

技术栈：LangChain 1.x / LangGraph（Tool, create_react_agent）+ training_utils（MCPClient, EventDrivenAgent）
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'common'))
from shared_utils import get_llm
from training_utils import MCPClient, EventDrivenAgent

from langchain_core.tools import Tool
from langgraph.prebuilt import create_react_agent


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


if __name__ == "__main__":
    exercise13_5_run()
