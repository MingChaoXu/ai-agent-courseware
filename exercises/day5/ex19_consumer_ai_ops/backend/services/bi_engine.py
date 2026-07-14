"""
BI Analysis Engine — LangGraph ReAct Agent with data tools.
Supports natural language querying of sales/business data and auto-chart generation.
"""

import json
from typing import Optional

from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.prebuilt import create_react_agent

from config import get_llm, check_config
from data_loader import DataLoader


# ═══════════════════════════════════════════════════════════
# Tool definitions
# ═══════════════════════════════════════════════════════════

def _query_sales(query: str) -> str:
    """Query sales data with natural language filters.
    Accepts JSON like: {"region":"华东","category":"美妆个护","date":"2025-06"}
    All fields are optional. Returns matching sales records.
    """
    try:
        filters = json.loads(query) if query.strip().startswith("{") else {}
    except json.JSONDecodeError:
        filters = {}

    records = DataLoader.sales()
    results = []
    for r in records:
        match = True
        if "region" in filters and r["region"] != filters["region"]:
            match = False
        if "category" in filters and r["category"] != filters["category"]:
            match = False
        if "channel" in filters and r["channel"] != filters["channel"]:
            match = False
        if "date" in filters and r["date"] != filters["date"]:
            match = False
        if "date_from" in filters and r["date"] < filters["date_from"]:
            match = False
        if "date_to" in filters and r["date"] > filters["date_to"]:
            match = False
        if match:
            results.append(r)

    # Limit to 30 records for readability
    return json.dumps(results[:30], ensure_ascii=False)


def _query_customers(query: str) -> str:
    """Query customer data. Accepts JSON filters: {"segment":"高价值活跃","churn_risk":"高","member_level":"金卡"}"""
    try:
        filters = json.loads(query) if query.strip().startswith("{") else {}
    except json.JSONDecodeError:
        filters = {}

    records = DataLoader.customers()
    results = []
    for r in records:
        match = True
        for key in ["segment", "churn_risk", "member_level", "region", "preferred_category", "preferred_channel"]:
            if key in filters and r.get(key) != filters[key]:
                match = False
        if match:
            results.append(r)

    return json.dumps(results[:20], ensure_ascii=False)


def _calc_statistics(query: str) -> str:
    """Perform statistical calculations on data.
    Input format: {"metric":"sales_amount","aggregate":"sum|avg|max|min|growth_rate","group_by":"region|category|channel|date","filters":{...}}
    """
    try:
        params = json.loads(query)
    except json.JSONDecodeError:
        return "Invalid JSON input"

    metric = params.get("metric", "sales_amount")
    agg = params.get("aggregate", "sum")
    group_by = params.get("group_by")
    filters = params.get("filters", {})

    records = DataLoader.sales()

    # Apply filters
    filtered = []
    for r in records:
        match = True
        for k, v in filters.items():
            if r.get(k) != v:
                match = False
        if match:
            filtered.append(r)

    if not filtered:
        return "No data matches the filters"

    if group_by:
        groups = {}
        for r in filtered:
            key = r.get(group_by, "unknown")
            groups.setdefault(key, []).append(r.get(metric, 0))

        result = {}
        for key, values in sorted(groups.items()):
            if agg == "sum":
                result[key] = round(sum(values), 2)
            elif agg == "avg":
                result[key] = round(sum(values) / len(values), 2)
            elif agg == "max":
                result[key] = round(max(values), 2)
            elif agg == "min":
                result[key] = round(min(values), 2)
            elif agg == "count":
                result[key] = len(values)
            elif agg == "growth_rate":
                if len(values) >= 2:
                    result[key] = round((values[-1] - values[0]) / max(abs(values[0]), 0.01) * 100, 1)
                else:
                    result[key] = 0
        return json.dumps(result, ensure_ascii=False)
    else:
        values = [r.get(metric, 0) for r in filtered]
        if agg == "sum":
            return str(round(sum(values), 2))
        elif agg == "avg":
            return str(round(sum(values) / len(values), 2))
        elif agg == "max":
            return str(round(max(values), 2))
        elif agg == "min":
            return str(round(min(values), 2))
        elif agg == "count":
            return str(len(values))
        return str(round(sum(values), 2))


def _generate_chart_spec(query: str) -> str:
    """Generate ECharts chart specification JSON.
    Input: {"chart_type":"line|bar|pie|scatter|heatmap","title":"...","data":{...},"x_field":"...","y_field":"..."}
    """
    try:
        params = json.loads(query)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON"})

    chart_type = params.get("chart_type", "bar")
    title = params.get("title", "数据分析图表")
    data = params.get("data", {})
    x_field = params.get("x_field", "name")
    y_field = params.get("y_field", "value")

    # Build ECharts option based on chart type
    if chart_type == "pie":
        if isinstance(data, dict):
            pie_data = [{"name": k, "value": v} for k, v in data.items()]
        elif isinstance(data, list):
            pie_data = data
        else:
            pie_data = []
        option = {
            "title": {"text": title, "left": "center"},
            "tooltip": {"trigger": "item"},
            "legend": {"orient": "vertical", "left": "left"},
            "series": [{"type": "pie", "radius": "55%", "data": pie_data,
                        "emphasis": {"itemStyle": {"shadowBlur": 10, "shadowOffsetX": 0, "shadowColor": "rgba(0,0,0,0.5)"}}}],
        }
    elif chart_type == "line":
        x_data = list(data.keys()) if isinstance(data, dict) else [d.get(x_field, "") for d in (data if isinstance(data, list) else [])]
        y_data = list(data.values()) if isinstance(data, dict) else [d.get(y_field, 0) for d in (data if isinstance(data, list) else [])]
        option = {
            "title": {"text": title},
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": x_data},
            "yAxis": {"type": "value"},
            "series": [{"type": "line", "data": y_data, "smooth": True,
                        "itemStyle": {"color": "#4F6EF7"}, "areaStyle": {"opacity": 0.15}}],
        }
    else:  # bar
        x_data = list(data.keys()) if isinstance(data, dict) else [d.get(x_field, "") for d in (data if isinstance(data, list) else [])]
        y_data = list(data.values()) if isinstance(data, dict) else [d.get(y_field, 0) for d in (data if isinstance(data, list) else [])]
        option = {
            "title": {"text": title},
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": x_data},
            "yAxis": {"type": "value"},
            "series": [{"type": chart_type, "data": y_data,
                        "itemStyle": {"color": "#4F6EF7"}}],
        }

    return json.dumps({"echarts_option": option}, ensure_ascii=False)


# Create Tool instances
tools = [
    Tool(
        name="query_sales",
        func=_query_sales,
        description="查询销售数据。输入JSON筛选条件，如 {\"region\":\"华东\",\"category\":\"美妆个护\",\"date\":\"2025-06\"}，所有字段可选",
    ),
    Tool(
        name="query_customers",
        func=_query_customers,
        description="查询客户数据。输入JSON筛选条件，如 {\"segment\":\"高价值活跃\",\"churn_risk\":\"高\"}",
    ),
    Tool(
        name="calc_statistics",
        func=_calc_statistics,
        description="统计分析。输入JSON：{\"metric\":\"sales_amount\",\"aggregate\":\"sum|avg|max|min|growth_rate\",\"group_by\":\"region|category|channel\",\"filters\":{...}}",
    ),
    Tool(
        name="generate_chart",
        func=_generate_chart_spec,
        description="生成ECharts图表。输入JSON：{\"chart_type\":\"line|bar|pie\",\"title\":\"标题\",\"data\":{...}}",
    ),
]


# ═══════════════════════════════════════════════════════════
# BI Agent
# ═══════════════════════════════════════════════════════════

BI_SYSTEM_PROMPT = """你是一个专业的消费领域BI数据分析师。

你可以使用以下工具来回答问题：
1. query_sales - 查询销售数据（支持按区域、品类、渠道、时间筛选）
2. query_customers - 查询客户数据（支持按分群、流失风险、会员等级筛选）
3. calc_statistics - 做统计分析（求和、均值、增长率等，支持分组聚合）
4. generate_chart - 生成可视化图表（折线图、柱状图、饼图等）

分析流程：
1. 理解用户的问题，确定需要的维度和指标
2. 使用 query_sales / query_customers 获取原始数据
3. 使用 calc_statistics 进行统计计算
4. 使用 generate_chart 生成可视化图表
5. 用中文给出专业的数据分析解读

注意事项：
- 先用查询工具获取数据，再计算，不要凭空编造数据
- 对比分析时注意使用增长率指标
- 图表标题要清晰准确
- 解读要包含趋势判断、异常识别和行动建议
"""


def create_bi_agent():
    """Create the BI ReAct Agent."""
    llm = get_llm(temperature=0.1)
    agent = create_react_agent(llm, tools=tools, prompt=BI_SYSTEM_PROMPT)
    return agent


def bi_analyze(question: str, conversation_history: list = None) -> dict:
    """
    Run BI analysis with a natural language question.
    Returns {answer, chart_spec, raw_tool_calls}.
    """
    if not check_config():
        return {"error": "LLM未配置，请检查.env文件"}

    agent = create_bi_agent()
    messages = []
    if conversation_history:
        messages.extend(conversation_history)
    messages.append(("user", question))

    try:
        result = agent.invoke({"messages": messages})
    except Exception as e:
        # Fallback: direct LLM call
        llm = get_llm()
        prompt = ChatPromptTemplate.from_messages([
            ("system", BI_SYSTEM_PROMPT),
            ("human", "{question}"),
        ])
        chain = prompt | llm | StrOutputParser()
        answer = chain.invoke({"question": question})
        return {"answer": answer, "chart_spec": None, "error": str(e)}

    # Extract answer and any chart specs from tool calls
    answer = ""
    chart_spec = None
    tool_calls_log = []

    for msg in result["messages"]:
        # Extract answer: take the LAST AI message that has text content
        # (LangGraph AI messages always have tool_calls attr, may be empty list)
        if hasattr(msg, "type") and msg.type == "ai" and msg.content:
            tc = getattr(msg, "tool_calls", None)
            if not tc:  # No tool calls = final answer
                answer = msg.content
        # Check for chart generation in tool outputs
        if hasattr(msg, "name") and msg.name == "generate_chart":
            try:
                parsed = json.loads(msg.content)
                if "echarts_option" in parsed:
                    chart_spec = parsed["echarts_option"]
            except (json.JSONDecodeError, TypeError):
                pass
        # Log tool calls
        if hasattr(msg, "type") and msg.type == "tool":
            tool_calls_log.append({"tool": getattr(msg, "name", "unknown"), "output_preview": msg.content[:200]})

    return {
        "answer": answer,
        "chart_spec": chart_spec,
        "tool_calls": tool_calls_log,
    }
