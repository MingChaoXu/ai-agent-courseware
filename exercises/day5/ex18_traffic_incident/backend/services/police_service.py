"""
Police Force Distribution Service — Simulated Police System Interface

This module simulates a connection to the real police command system (警务指挥系统),
providing real-time police unit distribution data and optimal allocation algorithms.

In production, these would be replaced by actual API calls to the police system.
For training purposes, we use realistic mock data based on Chengdu's actual police districts.
"""

import math
import random
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional


# ============================================================
# Police Unit Model
# ============================================================

@dataclass
class PoliceUnit:
    """A single police force unit (中队/大队/站点)."""
    unit_id: str              # 单位编号 e.g. "CD-JJ-001"
    name: str                 # 单位名称 e.g. "交警一分局武侯大队"
    unit_type: str            # 类型: 交警/巡警/特警/派出所
    location_text: str        # 地址描述
    lng: float                # 经度 (GCJ-02)
    lat: float                # 纬度 (GCJ-02)
    personnel_count: int      # 在岗人数
    vehicles: List[str]       # 可用车辆 e.g. ["巡逻车2辆", "警用车1辆"]
    equipment: List[str]      # 特殊装备 e.g. ["破拆工具", "路障设置设备"]
    status: str               # 当前状态: 待命/执勤/已调度
    contact_phone: str        # 联系电话
    response_range_km: float  # 响应范围(km)
    avg_response_min: float   # 平均响应时间(分钟)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["vehicles"] = ",".join(d["vehicles"])
        d["equipment"] = ",".join(d["equipment"])
        return d


# ============================================================
# Mock Police Units — Chengdu Police Districts
# ============================================================

MOCK_POLICE_UNITS: List[PoliceUnit] = [
    # ---- 武侯区 ----
    PoliceUnit(
        unit_id="CD-JJ-001", name="交警一分局武侯大队", unit_type="交警",
        location_text="武侯区二环路西一段128号", lng=104.048, lat=30.648,
        personnel_count=12, vehicles=["巡逻车2辆", "警用车1辆", "清障车1辆"],
        equipment=["路障设置设备", "事故勘察工具"], status="待命",
        contact_phone="028-85023122", response_range_km=8.0, avg_response_min=8,
    ),
    PoliceUnit(
        unit_id="CD-XJ-001", name="武侯区巡警中队", unit_type="巡警",
        location_text="武侯区武侯大道288号", lng=104.032, lat=30.658,
        personnel_count=8, vehicles=["巡逻车1辆", "摩托车3辆"],
        equipment=["警戒带", "急救包"], status="待命",
        contact_phone="028-85063100", response_range_km=6.0, avg_response_min=6,
    ),
    PoliceUnit(
        unit_id="CD-PC-001", name="武侯区浆洗街派出所", unit_type="派出所",
        location_text="武侯区浆洗街16号", lng=104.058, lat=30.650,
        personnel_count=6, vehicles=["警用车1辆"],
        equipment=["警戒带", "急救包"], status="执勤",
        contact_phone="028-85553110", response_range_km=3.0, avg_response_min=10,
    ),

    # ---- 青羊区 ----
    PoliceUnit(
        unit_id="CD-JJ-002", name="交警二分局青羊大队", unit_type="交警",
        location_text="青羊区青羊大道189号", lng=104.015, lat=30.670,
        personnel_count=10, vehicles=["巡逻车2辆", "警用车1辆"],
        equipment=["路障设置设备", "事故勘察工具"], status="待命",
        contact_phone="028-87313122", response_range_km=7.0, avg_response_min=7,
    ),
    PoliceUnit(
        unit_id="CD-TJ-001", name="青羊区特警中队", unit_type="特警",
        location_text="青羊区光华村街55号", lng=104.020, lat=30.662,
        personnel_count=15, vehicles=["特警车2辆", "指挥车1辆"],
        equipment=["防爆器材", "破拆工具", "急救设备"], status="待命",
        contact_phone="028-87312119", response_range_km=10.0, avg_response_min=12,
    ),
    PoliceUnit(
        unit_id="CD-PC-002", name="青羊区草市街派出所", unit_type="派出所",
        location_text="青羊区草市街8号", lng=104.062, lat=30.673,
        personnel_count=5, vehicles=["警用车1辆"],
        equipment=["警戒带", "急救包"], status="待命",
        contact_phone="028-86253110", response_range_km=3.0, avg_response_min=12,
    ),

    # ---- 成华区 ----
    PoliceUnit(
        unit_id="CD-JJ-003", name="交警五分局成华大队", unit_type="交警",
        location_text="成华区建设北路66号", lng=104.105, lat=30.672,
        personnel_count=10, vehicles=["巡逻车2辆", "警用车1辆"],
        equipment=["路障设置设备", "事故勘察工具"], status="待命",
        contact_phone="028-84333122", response_range_km=7.0, avg_response_min=7,
    ),
    PoliceUnit(
        unit_id="CD-XJ-002", name="成华区巡警中队", unit_type="巡警",
        location_text="成华区双林路38号", lng=104.110, lat=30.668,
        personnel_count=6, vehicles=["巡逻车1辆", "摩托车2辆"],
        equipment=["警戒带", "急救包"], status="执勤",
        contact_phone="028-84323100", response_range_km=5.0, avg_response_min=8,
    ),

    # ---- 高新区/天府新区 ----
    PoliceUnit(
        unit_id="CD-JJ-004", name="交警七分局高新大队", unit_type="交警",
        location_text="高新区天府大道北段1700号", lng=104.068, lat=30.560,
        personnel_count=8, vehicles=["巡逻车1辆", "警用车1辆"],
        equipment=["路障设置设备"], status="待命",
        contact_phone="028-85343122", response_range_km=8.0, avg_response_min=9,
    ),
    PoliceUnit(
        unit_id="CD-JJ-005", name="交警七分局天府大队", unit_type="交警",
        location_text="天府新区天府大道南段520号", lng=104.071, lat=30.405,
        personnel_count=8, vehicles=["巡逻车1辆", "警用车1辆"],
        equipment=["路障设置设备", "事故勘察工具"], status="待命",
        contact_phone="028-85673122", response_range_km=8.0, avg_response_min=10,
    ),
    PoliceUnit(
        unit_id="CD-XJ-003", name="天府新区巡警中队", unit_type="巡警",
        location_text="天府新区科学城北路12号", lng=104.075, lat=30.410,
        personnel_count=6, vehicles=["巡逻车1辆", "摩托车2辆"],
        equipment=["警戒带", "急救包"], status="待命",
        contact_phone="028-85673100", response_range_km=6.0, avg_response_min=8,
    ),

    # ---- 郫都区 ----
    PoliceUnit(
        unit_id="CD-JJ-006", name="交警六分局郫都大队", unit_type="交警",
        location_text="郫都区成灌路168号", lng=104.050, lat=30.720,
        personnel_count=8, vehicles=["巡逻车1辆", "警用车1辆"],
        equipment=["路障设置设备"], status="待命",
        contact_phone="028-87863122", response_range_km=8.0, avg_response_min=10,
    ),

    # ---- 市级机动 ----
    PoliceUnit(
        unit_id="CD-JJ-ZD", name="市交警支队机动大队", unit_type="交警",
        location_text="锦江区东大街100号(市局)", lng=104.080, lat=30.660,
        personnel_count=20, vehicles=["巡逻车4辆", "指挥车1辆", "清障车2辆", "摩托车6辆"],
        equipment=["路障设置设备", "事故勘察工具", "破拆工具", "指挥通讯设备"],
        status="待命", contact_phone="028-86643122",
        response_range_km=15.0, avg_response_min=15,
    ),
    PoliceUnit(
        unit_id="CD-TJ-ZD", name="市特警支队机动大队", unit_type="特警",
        location_text="锦江区东大街100号(市局)", lng=104.080, lat=30.660,
        personnel_count=30, vehicles=["特警车4辆", "指挥车1辆", "装甲车1辆"],
        equipment=["防爆器材", "破拆工具", "急救设备", "消防设备", "通讯设备"],
        status="待命", contact_phone="028-86642119",
        response_range_km=20.0, avg_response_min=20,
    ),
]


# ============================================================
# Allocation Algorithm
# ============================================================

def haversine_km(lng1: float, lat1: float, lng2: float, lat2: float) -> float:
    """Haversine formula: compute distance between two GCJ-02 points in km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def estimate_arrival_time(distance_km: float, unit: PoliceUnit) -> float:
    """Estimate arrival time in minutes.
    
    Model: base response time + distance / avg_speed
    Avg speed assumptions:
      - 交警/巡警/派出所 on urban roads: 25-35 km/h
      - 特警 with priority: 40 km/h
    """
    speed_map = {"交警": 30, "巡警": 28, "派出所": 25, "特警": 40}
    speed = speed_map.get(unit.unit_type, 28)
    travel_time = (distance_km / speed) * 60  # minutes
    # Add base dispatch time (call processing, crew assembly, departure)
    base_time = 2 + random.uniform(0, 2)  # 2-4 min base
    return round(base_time + travel_time, 1)


def allocate_police(
    incident_lng: float,
    incident_lat: float,
    incident_severity: str = "一般",
    required_types: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Optimal police allocation algorithm for an incident.

    Strategy:
      1. Filter: only consider units within response range AND available (待命/执勤)
      2. Rank: sort by distance → arrival time
      3. Determine need: severity → minimum personnel & required unit types
      4. Greedy select: pick units closest first until personnel requirement met
      5. Verify coverage: ensure each required type has at least 1 unit

    Returns allocation plan with:
      - recommended_units: list of recommended units with distance & ETA
      - total_personnel: total people allocated
      - estimated_earliest_arrival: fastest unit ETA
      - estimated_full_deployment: when all units arrive
      - coverage_check: whether all required types are covered
    """
    # Severity → minimum personnel & required type matrix
    severity_config = {
        "轻微": {"min_personnel": 3, "required_types": ["交警"], "max_units": 1},
        "一般": {"min_personnel": 6, "required_types": ["交警"], "max_units": 2},
        "严重": {"min_personnel": 12, "required_types": ["交警", "巡警"], "max_units": 3},
        "特重大": {"min_personnel": 20, "required_types": ["交警", "特警", "巡警"], "max_units": 4},
    }

    config = severity_config.get(incident_severity, severity_config["一般"])
    min_personnel = config["min_personnel"]
    req_types = required_types or config["required_types"]
    max_units = config["max_units"]

    # Step 1: Filter eligible units
    eligible = []
    for unit in MOCK_POLICE_UNITS:
        if unit.status in ("已调度",):
            continue  # Skip already dispatched units
        dist = haversine_km(incident_lng, incident_lat, unit.lng, unit.lat)
        if dist > unit.response_range_km * 1.3:  # Allow 30% over nominal range for urgent
            continue
        eta = estimate_arrival_time(dist, unit)
        eligible.append({
            "unit": unit,
            "distance_km": round(dist, 2),
            "eta_min": eta,
            "type_match": unit.unit_type in req_types,
        })

    # Step 2: Sort — primary: type match > distance > eta
    eligible.sort(key=lambda x: (-x["type_match"], x["distance_km"], x["eta_min"]))

    # Step 3: Greedy selection
    selected = []
    total_personnel = 0
    covered_types = set()

    for e in eligible:
        if len(selected) >= max_units and total_personnel >= min_personnel and covered_types >= set(req_types):
            break  # Requirement met
        if len(selected) >= max_units + 2:  # Hard cap to avoid over-dispatch
            break
        selected.append(e)
        total_personnel += e["unit"].personnel_count
        covered_types.add(e["unit"].unit_type)

    # Step 4: Build result
    recommended = []
    for e in selected:
        u = e["unit"]
        recommended.append({
            "unit_id": u.unit_id,
            "name": u.name,
            "unit_type": u.unit_type,
            "personnel_count": u.personnel_count,
            "vehicles": u.vehicles,
            "equipment": u.equipment,
            "location_text": u.location_text,
            "lng": u.lng,
            "lat": u.lat,
            "distance_km": e["distance_km"],
            "eta_min": e["eta_min"],
            "contact_phone": u.contact_phone,
            "status": u.status,
        })

    coverage_ok = covered_types >= set(req_types)
    etas = [e["eta_min"] for e in selected] if selected else []

    return {
        "incident_location": {"lng": incident_lng, "lat": incident_lat},
        "incident_severity": incident_severity,
        "recommended_units": recommended,
        "total_personnel": total_personnel,
        "min_personnel_needed": min_personnel,
        "personnel_satisfied": total_personnel >= min_personnel,
        "estimated_earliest_arrival": min(etas) if etas else None,
        "estimated_full_deployment": max(etas) if etas else None,
        "covered_types": list(covered_types),
        "required_types": req_types,
        "coverage_complete": coverage_ok,
        "allocation_summary": _build_summary(recommended, total_personnel, coverage_ok, etas),
    }


def _build_summary(units: list, total: int, coverage: bool, etas: list) -> str:
    """Generate a human-readable allocation summary."""
    if not units:
        return "⚠ 无可用警力单元，需手动调度"
    lines = [
        f"共调度 {len(units)} 个警力单元，合计 {total} 人",
    ]
    for u in units:
        lines.append(f"  → {u['name']}({u['unit_type']}) {u['personnel_count']}人, "
                     f"距离{u['distance_km']}km, 预计{u['eta_min']}分钟到达")
    if coverage:
        lines.append("✓ 所有必要警力类型已覆盖")
    else:
        lines.append("⚠ 部分警力类型未覆盖，建议补充调度")
    if etas:
        lines.append(f"最快到达: {min(etas)}分钟 | 全部到位: {max(etas)}分钟")
    return "\n".join(lines)


# ============================================================
# API-facing functions
# ============================================================

def get_all_units() -> List[Dict[str, Any]]:
    """Return all police units (simulated real-time data from police system)."""
    # Simulate slight status changes for realism
    for unit in MOCK_POLICE_UNITS:
        if unit.status == "待命" and random.random() < 0.05:
            unit.status = "执勤"  # 5% chance a unit becomes busy
        elif unit.status == "执勤" and random.random() < 0.15:
            unit.status = "待命"  # 15% chance a busy unit becomes free
    return [u.to_dict() for u in MOCK_POLICE_UNITS]


def get_unit_by_id(unit_id: str) -> Optional[Dict[str, Any]]:
    """Return a specific unit by ID."""
    for u in MOCK_POLICE_UNITS:
        if u.unit_id == unit_id:
            return u.to_dict()
    return None


# ============================================================
# Personnel Model — Individual Officers (OA System Data)
# ============================================================

@dataclass
class Personnel:
    """A single police officer from the OA system (警务人事系统)."""
    officer_id: str           # 警号 e.g. "CD-JJ-001-01"
    name: str                 # 姓名
    rank: str                 # 警衔: 警员/三级警司/二级警司/一级警司/三级警督/二级警督/一级警督
    unit_id: str              # 所属单位编号
    unit_name: str            # 所属单位名称
    unit_type: str            # 单位类型: 交警/巡警/特警/派出所
    role: str                 # 岗位: 指挥员/巡逻员/勘察员/通讯员/驾驶员/安全员/急救员
    phone: str                # 手机号
    status: str               # 状态: 待命/执勤/休假
    skills: List[str]         # 专业技能 e.g. ["事故勘察", "伤员急救"]
    certifications: List[str] # 资质证书 e.g. ["交通事故处理资格证"]
    gender: str               # 性别
    age: int                  # 年龄
    years_of_service: int     # 从警年限

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["skills"] = ", ".join(d["skills"])
        d["certifications"] = ", ".join(d["certifications"])
        return d


# ============================================================
# Mock Personnel Generator — Realistic OA Data
# ============================================================

# Surnames and given names for generating realistic Chinese names
_SURNAMES = ["王", "李", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴",
             "徐", "孙", "胡", "朱", "高", "林", "何", "郭", "马", "罗",
             "梁", "宋", "郑", "谢", "韩", "唐", "冯", "于", "董", "萧"]
_GIVEN_NAMES = ["伟", "芳", "秀英", "敏", "强", "磊", "军", "洋", "艳", "静",
                "娜", "勇", "涛", "明", "超", "秀兰", "霞", "平", "刚", "桂英",
                "文", "华", "建国", "建军", "志强", "志明", "国强", "海涛", "天宇", "鹏飞",
                "晓峰", "雪梅", "春华", "东升", "永刚", "学军", "德明", "立新", "卫东", "庆华"]

_RANKS_BY_UNIT_TYPE = {
    "交警": ["警员", "三级警司", "二级警司", "一级警司", "三级警督"],
    "巡警": ["警员", "三级警司", "二级警司", "一级警司", "三级警督"],
    "特警": ["三级警司", "二级警司", "一级警司", "三级警督", "二级警督"],
    "派出所": ["警员", "三级警司", "二级警司", "一级警司", "三级警督"],
}

_ROLES_BY_UNIT_TYPE = {
    "交警": ["指挥员", "巡逻员", "勘察员", "通讯员", "驾驶员", "安全员"],
    "巡警": ["指挥员", "巡逻员", "通讯员", "驾驶员", "安全员"],
    "特警": ["指挥员", "突击手", "狙击手", "爆破手", "急救员", "通讯员"],
    "派出所": ["值班员", "巡逻员", "调解员", "通讯员", "驾驶员"],
}

_SKILLS_BY_ROLE = {
    "指挥员": ["现场指挥", "通讯调度", "应急决策"],
    "巡逻员": ["路面管控", "交通疏导", "群众沟通"],
    "勘察员": ["事故现场勘察", "证据采集", "轨迹分析"],
    "通讯员": ["通讯设备操作", "信息报送", "视频监控"],
    "驾驶员": ["特种驾驶", "车辆维护", "紧急运输"],
    "安全员": ["警戒设置", "现场保护", "驱离疏导"],
    "急救员": ["伤员急救", "医疗转运", "心肺复苏"],
    "突击手": ["突击攻坚", "近身格斗", "战术突入"],
    "狙击手": ["远程精确射击", "观察侦察", "阵地构建"],
    "爆破手": ["爆破作业", "排爆处置", "危险品识别"],
    "值班员": ["接警处理", "信息登记", "首问负责"],
    "调解员": ["纠纷调解", "法律宣讲", "社区联络"],
}

_CERTS_BY_ROLE = {
    "指挥员": ["指挥员资格证"],
    "巡逻员": ["交通管理执法证"],
    "勘察员": ["交通事故处理资格证", "现场勘察资格证"],
    "通讯员": ["通讯设备操作证"],
    "驾驶员": ["特种车辆驾驶证", "警用车辆驾驶证"],
    "安全员": ["安全员资格证"],
    "急救员": ["急救员证", "AED操作证"],
    "突击手": ["突击手资格认证"],
    "狙击手": ["射击资格证"],
    "爆破手": ["爆破作业许可证", "排爆资格证"],
    "值班员": ["执法资格证"],
    "调解员": ["调解员资格证"],
}


def _generate_personnel() -> List[Personnel]:
    """Generate mock personnel data for all police units from the OA system."""
    random.seed(42)  # Deterministic for consistent demo
    personnel_list = []
    used_names = set()

    for unit in MOCK_POLICE_UNITS:
        count = unit.personnel_count
        for idx in range(count):
            # Generate unique name
            while True:
                surname = random.choice(_SURNAMES)
                given = random.choice(_GIVEN_NAMES)
                full_name = surname + given
                if full_name not in used_names:
                    used_names.add(full_name)
                    break

            # Rank distribution: higher ranks are less common
            ranks = _RANKS_BY_UNIT_TYPE.get(unit.unit_type, _RANKS_BY_UNIT_TYPE["交警"])
            rank_weights = [4, 3, 2, 1, 0.3][:len(ranks)]
            rank = random.choices(ranks, weights=rank_weights, k=1)[0]

            # Role
            roles = _ROLES_BY_UNIT_TYPE.get(unit.unit_type, _ROLES_BY_UNIT_TYPE["交警"])
            # First person in each unit is the commander
            role = "指挥员" if idx == 0 else random.choice(roles)

            # Skills and certifications
            skills = _SKILLS_BY_ROLE.get(role, ["综合执法"])
            # Add 0-2 random extra skills
            extra_skill_pool = ["夜间巡逻", "外语沟通", "无人机操作", "心理疏导", "数据录入"]
            extra_count = random.randint(0, 2)
            all_skills = skills + random.sample(extra_skill_pool, min(extra_count, len(extra_skill_pool)))

            certs = _CERTS_BY_ROLE.get(role, ["执法资格证"])
            # All officers have basic law enforcement cert
            if "执法资格证" not in certs:
                certs = ["执法资格证"] + certs

            # Status: mostly available
            if idx == 0:
                status = "执勤"  # Commander is always on duty
            else:
                status = random.choices(["待命", "执勤", "休假"], weights=[6, 3, 1], k=1)[0]

            # Phone number (Chengdu format)
            phone_prefix = random.choice(["138", "139", "136", "158", "159", "188", "199", "177"])
            phone = phone_prefix + "".join([str(random.randint(0, 9)) for _ in range(8)])

            # Age and years of service
            if rank in ("警员",):
                age = random.randint(22, 28)
                years = random.randint(1, 5)
            elif rank in ("三级警司", "二级警司"):
                age = random.randint(26, 38)
                years = random.randint(4, 15)
            elif rank in ("一级警司",):
                age = random.randint(32, 45)
                years = random.randint(10, 22)
            else:  # 警督
                age = random.randint(38, 52)
                years = random.randint(16, 32)

            officer_id = f"{unit.unit_id}-{idx + 1:02d}"

            personnel_list.append(Personnel(
                officer_id=officer_id,
                name=full_name,
                rank=rank,
                unit_id=unit.unit_id,
                unit_name=unit.name,
                unit_type=unit.unit_type,
                role=role,
                phone=phone,
                status=status,
                skills=all_skills,
                certifications=certs,
                gender=random.choices(["男", "女"], weights=[7, 3], k=1)[0],
                age=age,
                years_of_service=years,
            ))

    return personnel_list


# Generate once at module load time (simulating OA system query)
MOCK_PERSONNEL: List[Personnel] = _generate_personnel()


def search_personnel(
    keyword: Optional[str] = None,
    unit_type: Optional[str] = None,
    status: Optional[str] = None,
    role: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Search personnel in the OA system with filters.

    Args:
        keyword: Search in name, officer_id, unit_name, phone
        unit_type: Filter by unit type (交警/巡警/特警/派出所)
        status: Filter by status (待命/执勤/休假)
        role: Filter by role (指挥员/巡逻员/... etc)
    
    Returns:
        List of personnel dicts matching the criteria.
    """
    results = MOCK_PERSONNEL

    if keyword:
        kw = keyword.lower()
        results = [p for p in results if
                   kw in p.name.lower() or
                   kw in p.officer_id.lower() or
                   kw in p.unit_name.lower() or
                   kw in p.phone or
                   any(kw in s.lower() for s in p.skills)]

    if unit_type:
        results = [p for p in results if p.unit_type == unit_type]

    if status:
        results = [p for p in results if p.status == status]

    if role:
        results = [p for p in results if p.role == role]

    return [p.to_dict() for p in results]


def get_personnel_stats() -> Dict[str, Any]:
    """Get summary statistics of the personnel database."""
    total = len(MOCK_PERSONNEL)
    by_type = {}
    by_status = {}
    by_role = {}
    for p in MOCK_PERSONNEL:
        by_type[p.unit_type] = by_type.get(p.unit_type, 0) + 1
        by_status[p.status] = by_status.get(p.status, 0) + 1
        by_role[p.role] = by_role.get(p.role, 0) + 1
    return {
        "total": total,
        "by_type": by_type,
        "by_status": by_status,
        "by_role": by_role,
    }
