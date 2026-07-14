"""Pydantic models for Low-Altitude Agent Platform."""
from pydantic import BaseModel, Field
from typing import Optional, Any
from enum import Enum


# ---- Enums ----
class DroneStatusEnum(str, Enum):
    idle = "idle"
    flying = "flying"
    charging = "charging"
    maintenance = "maintenance"
    emergency = "emergency"


class OrderStatusEnum(str, Enum):
    pending = "pending"
    assigned = "assigned"
    delivering = "delivering"
    delivered = "delivered"
    cancelled = "cancelled"


class EventSeverityEnum(str, Enum):
    info = "info"
    warning = "warning"
    danger = "danger"
    critical = "critical"


class EventStatusEnum(str, Enum):
    active = "active"
    resolved = "resolved"
    monitoring = "monitoring"


class DetectTypeEnum(str, Enum):
    aerial = "aerial"
    obstacle = "obstacle"
    intruder = "intruder"
    landing = "landing"
    disaster = "disaster"
    traffic = "traffic"


# ---- Chat ----
class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    agent: Optional[str] = Field(None, description="Force agent: perception|logistics|traffic|emergency|auto")


class ChatResponse(BaseModel):
    answer: str = Field(None)
    agent_used: Optional[str] = None
    cv_results: Optional[Any] = None
    drone_updates: Optional[list] = None
    events: Optional[list] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    llm_configured: bool
    agent_ready: bool
    cv_model_loaded: bool
    drones_count: int
    active_orders: int
    active_events: int
    agents: list
    amap_mode: str = "offline"
    amap_api_key: str = ""


# ---- Drone ----
class DroneStatus(BaseModel):
    id: int
    name: str
    status: str = "idle"
    battery: float = 100.0
    lat: float
    lng: float
    altitude: float = 0.0
    speed: float = 0.0
    payload: float = 0.0
    max_payload: float = 5.0
    order_id: Optional[int] = None
    model_type: str = "multirotor"
    range_km: float = 30.0


class DroneControl(BaseModel):
    drone_id: int
    action: str = Field(..., description="takeoff|land|return|hover|goto")
    lat: Optional[float] = None
    lng: Optional[float] = None
    altitude: Optional[float] = None


# ---- Order ----
class OrderInfo(BaseModel):
    id: int
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: float
    dropoff_lng: float
    pickup_name: str = ""
    dropoff_name: str = ""
    cargo_type: str = "general"
    weight: float = 1.0
    priority: int = 1  # 1=normal, 2=high, 3=urgent
    status: str = "pending"
    drone_id: Optional[int] = None
    description: str = ""


class CreateOrder(BaseModel):
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: float
    dropoff_lng: float
    pickup_name: str = ""
    dropoff_name: str = ""
    cargo_type: str = "general"
    weight: float = 1.0
    priority: int = 1
    description: str = ""


# ---- Event ----
class EventInfo(BaseModel):
    id: int
    type: str
    description: str
    severity: str = "info"
    lat: float
    lng: float
    status: str = "active"
    drone_id: Optional[int] = None


# ---- CV Detection ----
class DetectRequest(BaseModel):
    image_source: str = Field("sample", description="sample name or base64")
    image_base64: Optional[str] = None
    detect_type: str = "aerial"
    drone_id: Optional[int] = None


class Detection(BaseModel):
    class_name: str
    confidence: float
    bbox: list  # [x1, y1, x2, y2]
    category: str = ""  # human/vehicle/obstacle/animal/other


class CVResult(BaseModel):
    detect_type: str
    detections: list[Detection] = []
    summary: dict = {}
    threat_level: str = "normal"  # normal|warning|danger
    annotated_image: Optional[str] = None  # base64
    analysis_text: str = ""
    drone_id: Optional[int] = None


class DetectResponse(BaseModel):
    success: bool
    result: Optional[CVResult] = None
    error: Optional[str] = None


# ---- Route ----
class RoutePlan(BaseModel):
    drone_id: int
    waypoints: list[dict] = []  # [{lat, lng, altitude, action}]
    total_distance_km: float = 0.0
    est_time_min: float = 0.0
    avoid_zones: list = []


class FlightPath(BaseModel):
    id: int
    drone_id: int
    waypoints: list = []
    status: str = "planned"
    created_at: str = ""


# ---- Dashboard ----
class DashboardData(BaseModel):
    drones: list[DroneStatus] = []
    orders: list[OrderInfo] = []
    events: list[EventInfo] = []
    flight_paths: list[FlightPath] = []
    cv_model_status: dict = {}
    stats: dict = {}
