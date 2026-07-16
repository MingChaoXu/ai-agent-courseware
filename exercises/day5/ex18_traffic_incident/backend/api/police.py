"""
Police Force API — Real-time distribution + optimal allocation + personnel database
"""

from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter(tags=["police"])


@router.get("/police/units")
async def get_police_units():
    """Get all police force units (simulated real-time data from police command system).
    
    In production, this would connect to the actual 警务指挥系统 via secure API.
    """
    from services.police_service import get_all_units
    units = get_all_units()
    return {"units": units, "total": len(units), "source": "模拟警务指挥系统接口"}


@router.get("/police/allocate")
async def allocate_police(
    lng: float = Query(..., description="事故经度(GCJ-02)"),
    lat: float = Query(..., description="事故纬度(GCJ-02)"),
    severity: str = Query("一般", description="严重程度: 轻微/一般/严重/特重大"),
):
    """Optimal police allocation for an incident at the given location.
    
    Algorithm: 
    1. Filter units within response range
    2. Rank by distance and type-match
    3. Greedy select until personnel requirement met
    4. Verify type coverage (交警/巡警/特警)
    
    Returns recommended units with distance, ETA, and allocation summary.
    """
    from services.police_service import allocate_police
    result = allocate_police(incident_lng=lng, incident_lat=lat, incident_severity=severity)
    return result


@router.get("/police/personnel")
async def get_personnel(
    keyword: Optional[str] = Query(None, description="搜索关键词(姓名/警号/单位/电话/技能)"),
    unit_type: Optional[str] = Query(None, description="单位类型: 交警/巡警/特警/派出所"),
    status: Optional[str] = Query(None, description="状态: 待命/执勤/休假"),
    role: Optional[str] = Query(None, description="岗位: 指挥员/巡逻员/勘察员/..."),
):
    """Search police personnel from the OA system (警务人事系统).
    
    Supports keyword search across name, officer_id, unit_name, phone, skills.
    Also supports filtering by unit_type, status, and role.
    
    In production, this would connect to the actual OA system via secure API.
    """
    from services.police_service import search_personnel
    results = search_personnel(keyword=keyword, unit_type=unit_type, status=status, role=role)
    return {"personnel": results, "total": len(results), "source": "模拟警务人事系统接口"}


@router.get("/police/personnel/stats")
async def get_personnel_stats():
    """Get personnel database summary statistics."""
    from services.police_service import get_personnel_stats
    return get_personnel_stats()
