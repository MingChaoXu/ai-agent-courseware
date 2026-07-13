"""
AMap (高德地图) API Client - Online/Offline Dual Mode

When AMAP_API_KEY is configured, calls real AMap REST APIs:
  - Geocode (地址 → 经纬度)
  - Regeocode (经纬度 → 地址)
  - Around Search (周边搜索: 医院/消防/交警/加油站)
  - Driving Direction (驾车路径规划 → 分流路线)
  - Traffic Status (实时路况查询)

When AMAP_API_KEY is NOT configured, returns mock data for offline testing.
"""

import json
import math
import os
import urllib.parse
import urllib.request
from typing import Dict, Any, List, Optional

from config import settings


# ============================================================
# Offline Mock Data
# ============================================================

_MOCK_GEOCODE = {
    "三环路辅路与人民路交叉口": {
        "location": "104.066801,30.662932",
        "formatted_address": "四川省成都市武侯区三环路辅路与人民路交叉口",
        "city": "成都",
        "district": "武侯区",
    },
    "成华大道与建设路交叉口": {
        "location": "104.101941,30.670261",
        "formatted_address": "四川省成都市成华区成华大道与建设路交叉口",
        "city": "成都",
        "district": "成华区",
    },
    "绕城高速K35+200处": {
        "location": "104.052234,30.721145",
        "formatted_address": "四川省成都市郫都区绕城高速K35+200处",
        "city": "成都",
        "district": "郫都区",
    },
    "天府大道南段与科学城路口": {
        "location": "104.071234,30.401958",
        "formatted_address": "四川省成都市双流区天府大道南段与科学城路口",
        "city": "成都",
        "district": "双流区",
    },
    "光华大道与青羊大道交叉口": {
        "location": "104.015678,30.668901",
        "formatted_address": "四川省成都市青羊区光华大道与青羊大道交叉口",
        "city": "成都",
        "district": "青羊区",
    },
}

_MOCK_AROUND = {
    "104.066801,30.662932": {
        "hospitals": [
            {"name": "成都市第三人民医院", "address": "青龙街82号", "distance": "1200", "tel": "028-86641114"},
            {"name": "武侯区人民医院", "address": "广福桥街16号", "distance": "850", "tel": "028-85055120"},
        ],
        "fire_stations": [
            {"name": "武侯区消防大队", "address": "武侯大道288号", "distance": "1500", "tel": "028-85062119"},
        ],
        "traffic_police": [
            {"name": "交警一分局武侯大队", "address": "二环路西一段", "distance": "600", "tel": "028-85023122"},
        ],
        "gas_stations": [
            {"name": "中石化三环路加油站", "address": "三环路辅路", "distance": "300", "tel": "028-85010120"},
        ],
    },
    "104.101941,30.670261": {
        "hospitals": [
            {"name": "成都市第六人民医院", "address": "建设南街16号", "distance": "900", "tel": "028-84334280"},
        ],
        "fire_stations": [
            {"name": "成华区消防大队", "address": "建设路", "distance": "1100", "tel": "028-84322119"},
        ],
        "traffic_police": [
            {"name": "交警五分局成华大队", "address": "建设北路", "distance": "500", "tel": "028-84333122"},
        ],
        "gas_stations": [
            {"name": "中石油成华大道加油站", "address": "成华大道", "distance": "400", "tel": "028-84310120"},
        ],
    },
    "104.052234,30.721145": {
        "hospitals": [
            {"name": "郫都区人民医院", "address": "东大街156号", "distance": "3200", "tel": "028-87862120"},
        ],
        "fire_stations": [
            {"name": "郫都区消防中队", "address": "成灌路", "distance": "2800", "tel": "028-87862119"},
        ],
        "traffic_police": [
            {"name": "交警六分局绕城大队", "address": "绕城高速服务区", "distance": "1500", "tel": "028-87863122"},
        ],
        "gas_stations": [
            {"name": "中石化绕城高速加油站", "address": "绕城高速K34", "distance": "800", "tel": "028-87860120"},
        ],
    },
    "104.071234,30.401958": {
        "hospitals": [
            {"name": "天府新区人民医院", "address": "正北下街21号", "distance": "1800", "tel": "028-85672120"},
        ],
        "fire_stations": [
            {"name": "天府新区消防大队", "address": "科学城北路", "distance": "1200", "tel": "028-85672119"},
        ],
        "traffic_police": [
            {"name": "交警七分局天府大队", "address": "天府大道南段", "distance": "400", "tel": "028-85673122"},
        ],
        "gas_stations": [
            {"name": "中石油天府大道加油站", "address": "天府大道南段", "distance": "500", "tel": "028-85670120"},
        ],
    },
    "104.015678,30.668901": {
        "hospitals": [
            {"name": "四川省人民医院", "address": "一环路西二段32号", "distance": "1000", "tel": "028-87393999"},
        ],
        "fire_stations": [
            {"name": "青羊区消防大队", "address": "光华村街", "distance": "800", "tel": "028-87312119"},
        ],
        "traffic_police": [
            {"name": "交警二分局青羊大队", "address": "青羊大道", "distance": "300", "tel": "028-87313122"},
        ],
        "gas_stations": [
            {"name": "中石化光华大道加油站", "address": "光华大道", "distance": "200", "tel": "028-87310120"},
        ],
    },
}

_MOCK_TRAFFIC = {
    "104.066801,30.662932": {"status": "拥堵", "description": "三环路辅路双向严重拥堵，平均车速<15km/h", "direction": "南北双向"},
    "104.101941,30.670261": {"status": "缓行", "description": "成华大道北向南方向缓行，平均车速25km/h", "direction": "北向南"},
    "104.052234,30.721145": {"status": "畅通", "description": "绕城高速该路段畅通，平均车速80km/h", "direction": "双向"},
    "104.071234,30.401958": {"status": "缓行", "description": "天府大道南段北向南缓行，平均车速30km/h", "direction": "北向南"},
    "104.015678,30.668901": {"status": "拥堵", "description": "光华大道双向拥堵，平均车速<20km/h", "direction": "东西双向"},
}

_MOCK_DRIVING = {
    "default": [
        {"route": "方案1: 经三环路主路 → 人民南路 → 二环路", "distance": "5.2km", "duration": "15分钟", "tolls": "0元"},
        {"route": "方案2: 经三环路辅路 → 武侯大道 → 二环路", "distance": "6.8km", "duration": "22分钟", "tolls": "0元"},
        {"route": "方案3: 经绕城高速 → 成雅高速出口", "distance": "12.5km", "duration": "18分钟", "tolls": "5元"},
    ],
}


# ============================================================
# AMap Client
# ============================================================

AMAP_BASE = "https://restapi.amap.com/v3"

# POI type codes for around search
POI_TYPES = {
    "hospitals": "090100",      # 综合医院
    "fire_stations": "050301",   # 消防
    "traffic_police": "050300",  # 交通管理
    "gas_stations": "010100",    # 加油站
}

POI_LABELS = {
    "hospitals": "医院",
    "fire_stations": "消防站",
    "traffic_police": "交警队",
    "gas_stations": "加油站",
}


class AMapClient:
    """AMap API client with online/offline dual mode."""

    def __init__(self, api_key: str = "", data_dir: str = ""):
        self.api_key = api_key or settings.AMAP_API_KEY
        self.data_dir = data_dir or settings.DATA_DIR
        self.is_online = bool(self.api_key)

    # ---- Helper: HTTP GET ----

    def _get(self, url: str, params: dict) -> dict:
        """Make HTTP GET request to AMap API."""
        params["key"] = self.api_key
        query = urllib.parse.urlencode(params)
        full_url = f"{url}?{query}"
        try:
            req = urllib.request.Request(full_url)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("status") != "1":
                    return {"error": data.get("info", "AMap API error"), "raw": data}
                return data
        except Exception as e:
            return {"error": str(e)}

    # ---- Geocode ----

    def geocode(self, address: str) -> Dict[str, Any]:
        """地址 → 经纬度 (地理编码)"""
        if not self.is_online:
            return self._mock_geocode(address)

        data = self._get(f"{AMAP_BASE}/geocode/geo", {"address": address})
        if "error" in data:
            return data
        geocodes = data.get("geocodes", [])
        if not geocodes:
            return {"error": "未找到该地址的坐标"}
        geo = geocodes[0]
        return {
            "location": geo.get("location", ""),
            "formatted_address": geo.get("formatted_address", address),
            "city": geo.get("city", "") or data.get("city", ""),
            "district": geo.get("district", ""),
            "province": geo.get("province", ""),
        }

    def _mock_geocode(self, address: str) -> Dict[str, Any]:
        for key, val in _MOCK_GEOCODE.items():
            if key in address or address in key:
                return dict(val)
        return {
            "location": "104.066801,30.662932",
            "formatted_address": f"四川省成都市{address}",
            "city": "成都",
            "district": "武侯区",
        }

    # ---- Around Search ----

    def around_search(self, location: str, categories: List[str] = None,
                      radius: int = 3000) -> Dict[str, List[Dict]]:
        """周边搜索 (医院/消防/交警/加油站)"""
        if categories is None:
            categories = list(POI_TYPES.keys())

        if not self.is_online:
            return self._mock_around(location, categories)

        result = {}
        for cat in categories:
            types = POI_TYPES.get(cat, "")
            data = self._get(f"{AMAP_BASE}/place/around", {
                "location": location,
                "types": types,
                "radius": radius,
                "offset": 5,
                "sortrule": "distance",
            })
            if "error" in data:
                result[cat] = []
                continue
            pois = data.get("pois", [])
            result[cat] = [
                {
                    "name": p.get("name", ""),
                    "address": p.get("address", ""),
                    "distance": p.get("distance", ""),
                    "tel": p.get("tel", ""),
                }
                for p in pois[:3]
            ]
        return result

    def _mock_around(self, location: str, categories: List[str]) -> Dict[str, List[Dict]]:
        mock = _MOCK_AROUND.get(location, {})
        result = {}
        for cat in categories:
            result[cat] = mock.get(cat, [])
        return result

    # ---- Traffic Status ----

    def traffic_status(self, location: str, radius: int = 1000) -> Dict[str, Any]:
        """实时路况查询 (圆形区域)"""
        if not self.is_online:
            return self._mock_traffic(location)

        # AMap traffic API requires level 5+ key
        data = self._get(f"{AMAP_BASE}/traffic/status/circle", {
            "location": location,
            "radius": radius,
            "level": 5,
        })
        if "error" in data:
            return {"status": "未知", "description": str(data["error"]), "direction": ""}

        traffic = data.get("trafficinfo", {})
        evaluation = traffic.get("evaluation", {})
        return {
            "status": evaluation.get("description", "未知"),
            "description": evaluation.get("expedite", "") + " " + evaluation.get("congested", ""),
            "direction": traffic.get("description", ""),
        }

    def _mock_traffic(self, location: str) -> Dict[str, Any]:
        mock = _MOCK_TRAFFIC.get(location, {
            "status": "缓行",
            "description": "该路段车流量较大，平均车速30km/h",
            "direction": "双向",
        })
        return dict(mock)

    # ---- Driving Direction ----

    def driving_direction(self, origin: str, destination: str) -> Dict[str, Any]:
        """驾车路径规划 (分流路线方案)"""
        if not self.is_online:
            return self._mock_driving(origin, destination)

        data = self._get(f"{AMAP_BASE}/direction/driving", {
            "origin": origin,
            "destination": destination,
            "strategy": 2,  # 距离最短
        })
        if "error" in data:
            return {"routes": []}

        route = data.get("route", {})
        paths = route.get("paths", [])
        routes = []
        for path in paths[:3]:
            routes.append({
                "route": path.get("steps", [{}])[0].get("instruction", ""),
                "distance": str(int(path.get("distance", 0)) / 1000) + "km",
                "duration": str(int(int(path.get("duration", 0)) / 60)) + "分钟",
                "tolls": path.get("tolls", "0") + "元",
            })
        return {"routes": routes}

    def _mock_driving(self, origin: str, destination: str) -> Dict[str, Any]:
        return {"routes": list(_MOCK_DRIVING["default"])}

    # ---- Comprehensive Query ----

    def query_location_info(self, address: str) -> Dict[str, Any]:
        """一键查询: 地理编码 + 周边设施 + 实时路况"""
        geo = self.geocode(address)
        if "error" in geo:
            return {"error": geo["error"], "address": address, "mode": self._mode_str()}

        location = geo["location"]
        around = self.around_search(location)
        traffic = self.traffic_status(location)
        detour = self.driving_direction(location, location)  # 自环→分流路线

        return {
            "mode": self._mode_str(),
            "address": address,
            "geocode": geo,
            "around": around,
            "traffic": traffic,
            "detour_routes": detour.get("routes", []),
        }

    def _mode_str(self) -> str:
        return "online (高德实时API)" if self.is_online else "offline (模拟数据)"
