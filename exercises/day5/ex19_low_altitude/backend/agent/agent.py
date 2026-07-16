"""Multi-agent orchestration for Low-Altitude Platform.

4 agents + 1 dispatcher:
  - perception: airspace monitoring, anomaly detection, CV scene analysis
  - logistics:   order management, route planning, drone dispatch, CV landing check
  - traffic:     airspace resource allocation, conflict detection, CV traffic monitor
  - emergency:   incident response, disaster assessment, CV disaster analysis
  - dispatcher:  routes user question to appropriate agent(s)
"""
import logging
import math
from typing import Any, Optional

from config import settings
from db import database as db
from cv_service.yolo_server import get_cv_service
from cv_service.detectors import run_detection
from models.schemas import CVResult

logger = logging.getLogger(__name__)

# ---- LLM setup ----
def _get_llm():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(**settings.llm_kwargs)


def _get_llm_fallback():
    """Low-temperature LLM for structured tasks."""
    kwargs = dict(settings.llm_kwargs)
    kwargs["temperature"] = 0.1
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(**kwargs)


# ---- Geo helpers ----
def haversine_km(lat1, lng1, lat2, lng2) -> float:
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a)), 2)


# ---- CV helper for agents ----
def agent_cv_detect(detect_type: str, drone_id: int = None, sample_name: str = None) -> Optional[CVResult]:
    """Agent tool: run CV detection on a sample image or drone feed."""
    try:
        cv_service = get_cv_service()
        if not cv_service.is_loaded:
            return None

        image = None
        if sample_name:
            image = cv_service.load_sample_image(sample_name)
        if image is None:
            # Try to pick a relevant sample based on detect_type
            sample_map = {
                "aerial": "urban_density",
                "obstacle": "construction_site",
                "intruder": "river_bridge",
                "landing": "open_field",
                "disaster": "construction_site",
                "traffic": "city_intersection",
            }
            fallback = sample_map.get(detect_type, "urban_density")
            image = cv_service.load_sample_image(fallback)

        if image is None:
            return None

        return run_detection(cv_service, image, detect_type, drone_id)
    except Exception as e:
        logger.error(f"Agent CV detect error: {e}")
        return None


# ---- Context builder ----
def _build_context() -> str:
    """Build current system state context for agents."""
    drones = db.get_all_drones()
    orders = db.get_pending_orders()
    events = db.get_active_events()
    paths = db.get_all_flight_paths()

    lines = ["=== 当前系统状态 ==="]

    lines.append(f"\n【无人机编队】({len(drones)}架)")
    for d in drones:
        lines.append(
            f"  {d['name']}(ID:{d['id']}) 状态:{d['status']} 电量:{d['battery']:.0f}% "
            f"位置:({d['lat']:.4f},{d['lng']:.4f}) 高度:{d['altitude']:.0f}m "
            f"载重:{d['payload']:.1f}/{d['max_payload']:.1f}kg 类型:{d['model_type']}"
        )

    lines.append(f"\n【物流订单】({len(orders)}个待处理)")
    for o in orders:
        pri_label = {1: "普通", 2: "加急", 3: "紧急"}.get(o["priority"], "普通")
        lines.append(
            f"  订单#{o['id']} {o['pickup_name']}→{o['dropoff_name']} "
            f"货物:{o['cargo_type']}({o['weight']}kg) 优先级:{pri_label} "
            f"状态:{o['status']} 无人机:{o.get('drone_id') or '未分配'}"
        )

    lines.append(f"\n【活跃事件】({len(events)}个)")
    for e in events:
        lines.append(
            f"  事件#{e['id']} [{e['severity']}] {e['type']}: {e['description']} "
            f"位置:({e['lat']:.4f},{e['lng']:.4f}) 状态:{e['status']}"
        )

    active_paths = [p for p in paths if p["status"] == "active"]
    lines.append(f"\n【飞行航线】({len(active_paths)}条活跃)")
    for p in active_paths:
        wps = p["waypoints"]
        if wps:
            start = wps[0]
            end = wps[-1]
            lines.append(
                f"  航线#{p['id']} 无人机:{p['drone_id']} "
                f"起点:({start['lat']:.4f},{start['lng']:.4f}) "
                f"终点:({end['lat']:.4f},{end['lng']:.4f}) "
                f"途经{len(wps)}个航点"
            )

    return "\n".join(lines)


# ---- Agent system prompts ----
DISPATCHER_PROMPT = """你是低空智能体协同管控平台的调度器。根据用户问题，判断应该由哪个Agent处理。

可选Agent：
1. perception  - 空域感知：监控空域状态、检测异常事件、分析航拍画面、天气评估
2. logistics   - 无人机物流：订单管理、航线规划、无人机调度、配送追踪、降落点评估
3. traffic     - 城市空中交通：空域资源分配、航线冲突检测、流量管控、交通监控
4. emergency   - 应急响应：故障处置、天气突变、空域冲突、紧急降落、灾害评估

规则：
- 如果问题涉及多个方面，选择最主要的一个
- 如果问题模糊或需要综合分析，回答 "auto"
- 只输出Agent名称（perception/logistics/traffic/emergency/auto），不要其他文字
"""

PERCEPTION_PROMPT = """你是低空全域感知智能体，负责空域态势监控与分析。

你的职责：
1. 实时监控无人机编队状态（电量、位置、高度、速度）
2. 检测异常事件（航线偏离、设备故障、入侵飞行器）
3. 分析航拍画面（调用CV检测服务）
4. 评估天气对飞行的影响
5. 输出空域态势报告

回复格式要求：
- 使用简洁的专业中文
- 如有异常，明确标注严重程度（正常/警告/危险）
- 如执行了CV检测，描述检测结果
- 给出 actionable 建议
"""

LOGISTICS_PROMPT = """你是无人机物流智能体，负责订单处理与配送调度。

你的职责：
1. 接收和分析物流订单（起点、终点、货物类型、时效要求）
2. 规划最优配送航线（考虑距离、禁飞区、天气、电量）
3. 调度合适的无人机执行配送
4. 评估降落点安全性（可调用CV检测）
5. 追踪配送状态

航线规划原则：
- 距离 = haversine公式计算
- 优先选择电量充足、载重足够的无人机
- 紧急订单(priority=3)优先分配
- 避开活跃事件区域

回复格式要求：
- 明确列出分配方案（无人机ID、航线、预计时间）
- 如执行了降落点CV检测，描述结果
- 给出配送建议
"""

TRAFFIC_PROMPT = """你是城市空中交通管制智能体，负责空域资源管理与交通管控。

你的职责：
1. 管理城市低空航路网络和起降点资源
2. 检测多无人机航线冲突（空间交叉+时间重叠）
3. 评估空域容量，执行流量管控
4. 监控地面交通态势（可调用CV检测）
5. 协调空域资源分配

冲突检测规则：
- 两架无人机航线交叉点距离 < 500m 且时间差 < 2min 视为冲突
- 同一空域同时飞行器 > 5架 触发流量管控

回复格式要求：
- 如有冲突，明确列出涉及的无人机和冲突位置
- 给出时序调度建议
- 如执行了交通CV检测，描述结果
"""

EMERGENCY_PROMPT = """你是低空应急响应智能体，负责突发事件处置与协调。

你的职责：
1. 接收和分析紧急事件（设备故障、天气突变、航线冲突、安全威胁）
2. 评估事件严重程度和影响范围
3. 制定应急方案（返航/备降/避让/迫降）
4. 协调多Agent响应（通知物流调整计划、请求管制开辟通道）
5. 灾害场景分析（可调用CV检测）

应急分级：
- 一级(危险)：立即返航/迫降，全员待命
- 二级(警告)：调整航线，加强监控
- 三级(提示)：记录观察，持续跟踪

回复格式要求：
- 明确事件分级
- 列出应急处置步骤
- 如执行了CV检测，描述灾害评估结果
- 给出后续跟踪建议
"""


# ---- Agent chain creation ----
def _create_chain(system_prompt: str):
    from langchain_core.prompts import ChatPromptTemplate
    llm = _get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])
    return prompt | llm


def create_agent() -> dict:
    """Create all agent chains and CV service."""
    agents = {}
    if settings.is_configured():
        agents["dispatcher"] = _create_chain(DISPATCHER_PROMPT)
        agents["perception"] = _create_chain(PERCEPTION_PROMPT)
        agents["logistics"] = _create_chain(LOGISTICS_PROMPT)
        agents["traffic"] = _create_chain(TRAFFIC_PROMPT)
        agents["emergency"] = _create_chain(EMERGENCY_PROMPT)
    # Init CV service
    cv_service = get_cv_service()
    cv_service.load()

    return {"chains": agents, "cv_service": cv_service}


# ---- Dispatcher ----
def _dispatch(agent_data: dict, question: str) -> str:
    """Route question to the appropriate agent."""
    chains = agent_data["chains"]
    if not chains:
        return "auto"

    try:
        chain = chains["dispatcher"]
        result = chain.invoke({"input": question})
        agent_name = result.content.strip().lower()
        valid = {"perception", "logistics", "traffic", "emergency", "auto"}
        if agent_name in valid:
            return agent_name
        return "auto"
    except Exception as e:
        logger.error(f"Dispatch error: {e}")
        return "auto"


# ---- CV decision: should agent call CV? ----
def _decide_cv_call(agent_name: str, question: str) -> Optional[dict]:
    """Decide if and how to call CV service based on agent and question.
    
    Uses a two-tier matching strategy:
    1. Agent-specific keywords (higher priority)
    2. Cross-agent keywords (fallback, works regardless of which agent handles it)
    """
    q = question.lower()

    # Cross-agent keywords: always trigger regardless of routing
    cross_agent_map = {
        "降落": "landing", "着陆": "landing", "降落点": "landing", "起降": "landing",
        "交通": "traffic", "车流": "traffic", "拥堵": "traffic", "路口": "traffic",
        "灾害": "disaster", "火灾": "disaster", "烟雾": "disaster", "洪水": "disaster",
        "事故": "disaster", "滑坡": "disaster", "侦察": "disaster",
        "航拍": "aerial", "画面": "aerial", "视觉": "aerial", "图像": "aerial",
        "入侵": "intruder", "鸟击": "intruder",
        "障碍": "obstacle", "电线": "obstacle", "建筑遮挡": "obstacle",
    }
    for keyword, detect_type in cross_agent_map.items():
        if keyword in q:
            return {"detect_type": detect_type, "sample": None}

    # Agent-specific keywords (supplementary)
    if agent_name == "perception":
        if any(k in q for k in ["检测", "识别", "监控", "cv"]):
            return {"detect_type": "aerial", "sample": None}

    return None


# ---- Main chat function ----
def chat(agent_data: dict, question: str, force_agent: str = None) -> dict:
    """Process user question through the multi-agent system."""
    chains = agent_data["chains"]
    context = _build_context()

    # 1. Determine which agent to use
    if force_agent and force_agent in chains:
        agent_name = force_agent
    else:
        agent_name = _dispatch(agent_data, question) if chains else "auto"
    logger.info(f"[Chat] Dispatch result: agent={agent_name}, question={question[:50]}")

    # 2. If auto, use a general approach: run perception as default with full context
    if agent_name == "auto" or agent_name not in chains:
        agent_name = "perception"  # default fallback

    # 3. Decide CV call
    cv_decision = _decide_cv_call(agent_name, question)
    cv_result = None
    cv_context_text = ""
    logger.info(f"[Chat] CV decision: {cv_decision}")

    if cv_decision:
        cv_result = agent_cv_detect(
            cv_decision["detect_type"],
            sample_name=cv_decision.get("sample")
        )
        logger.info(f"[Chat] CV result: detect_type={cv_result.detect_type if cv_result else None}, threat={cv_result.threat_level if cv_result else None}, total={cv_result.summary.get('total') if cv_result else None}")
        if cv_result:
            cv_context_text = f"\n\n=== CV视觉检测结果 ===\n{cv_result.analysis_text}\n检测类型: {cv_result.detect_type}\n威胁等级: {cv_result.threat_level}\n检测到目标数: {cv_result.summary.get('total', 0)}"
            logger.info(f"[Chat] CV context text length: {len(cv_context_text)}")
        else:
            logger.warning("[Chat] CV detection returned None!")

    # 4. Build agent input with context
    full_input = f"{context}\n\n=== 用户指令 ===\n{question}{cv_context_text}"
    logger.info(f"[Chat] Full input length: {len(full_input)}, has_cv_context: {bool(cv_context_text)}")

    # 5. Execute agent
    answer = ""
    try:
        chain = chains[agent_name]
        result = chain.invoke({"input": full_input})
        answer = result.content
    except Exception as e:
        logger.error(f"Agent {agent_name} error: {e}")
        answer = f"Agent执行出错: {str(e)}"

    # 6. Build response
    response = {
        "answer": answer,
        "agent_used": agent_name,
        "cv_results": cv_result.model_dump() if cv_result else None,
    }

    # 7. Side effects: create events or update orders based on content
    _process_side_effects(question, answer, agent_name, cv_result)

    return response


def _process_side_effects(question: str, answer: str, agent_name: str, cv_result: Optional[CVResult]):
    """Process side effects based on agent output (create events, etc.)."""
    try:
        # If CV detected danger/critical, auto-create event
        if cv_result and cv_result.threat_level in ("danger", "critical"):
            db.create_event(
                event_type="cv_detection",
                description=f"CV检测[{cv_result.detect_type}]: {cv_result.summary}",
                severity=cv_result.threat_level,
                lat=settings.CITY_CENTER_LAT,
                lng=settings.CITY_CENTER_LNG,
            )

        # If emergency agent mentions specific actions, log as event
        if agent_name == "emergency" and any(k in question for k in ["紧急", "故障", "迫降", "事故"]):
            db.create_event(
                event_type="emergency_response",
                description=f"应急响应触发: {question[:50]}",
                severity="danger",
                lat=settings.CITY_CENTER_LAT,
                lng=settings.CITY_CENTER_LNG,
            )
    except Exception as e:
        logger.error(f"Side effect error: {e}")
