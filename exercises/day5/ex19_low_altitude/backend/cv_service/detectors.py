"""Detection logic for different low-altitude CV scenarios."""
import logging
from typing import Optional
from models.schemas import CVResult, Detection

logger = logging.getLogger(__name__)

# Category thresholds per detect type
DETECT_CONFIG = {
    "aerial": {
        "description": "航拍目标全量检测",
        "include_categories": None,  # all
        "threat_rules": {"person": (20, "warning"), "car": (30, "warning")},
    },
    "obstacle": {
        "description": "飞行障碍物识别",
        "include_categories": {"obstacle", "vehicle"},
        "include_classes": {"traffic light", "fire hydrant", "stop sign", "bench",
                           "car", "truck", "bus"},
        "threat_rules": {"traffic light": (1, "warning")},
    },
    "intruder": {
        "description": "空域入侵检测",
        "include_categories": {"animal"},
        "include_classes": {"bird", "airplane", "kite"},
        "threat_rules": {"bird": (3, "warning"), "airplane": (1, "danger")},
    },
    "landing": {
        "description": "降落点安全评估",
        "include_categories": {"human", "vehicle", "obstacle"},
        "include_classes": {"person", "car", "truck", "bus", "motorcycle", "bicycle",
                           "fire hydrant", "bench"},
        "threat_rules": {"person": (5, "danger"), "car": (3, "warning")},
    },
    "disaster": {
        "description": "灾害场景分析",
        "include_categories": None,
        "include_classes": {"fire hydrant", "person", "car", "truck"},
        "threat_rules": {"person": (10, "danger")},
    },
    "traffic": {
        "description": "地面交通监控",
        "include_categories": {"vehicle"},
        "include_classes": {"car", "truck", "bus", "motorcycle", "bicycle"},
        "threat_rules": {"car": (25, "warning")},
    },
}


def filter_detections(detections: list, detect_type: str) -> list:
    """Filter detections based on detect type config."""
    config = DETECT_CONFIG.get(detect_type, DETECT_CONFIG["aerial"])
    include_cats = config.get("include_categories")
    include_classes = config.get("include_classes")

    filtered = []
    for d in detections:
        if include_cats and d["category"] not in include_cats:
            if not include_classes or d["class_name"] not in include_classes:
                continue
        if include_classes and d["class_name"] not in include_classes:
            if not include_cats or d["category"] not in include_cats:
                continue
        filtered.append(d)
    return filtered


def assess_threat_level(filtered: list, detect_type: str) -> str:
    """Assess threat level based on detection counts."""
    config = DETECT_CONFIG.get(detect_type, DETECT_CONFIG["aerial"])
    rules = config.get("threat_rules", {})

    # Count by class
    class_counts = {}
    for d in filtered:
        cn = d["class_name"]
        class_counts[cn] = class_counts.get(cn, 0) + 1

    threat = "normal"
    for cls_name, (threshold, level) in rules.items():
        count = class_counts.get(cls_name, 0)
        if count >= threshold:
            if level == "danger" or (level == "warning" and threat == "normal"):
                threat = level

    return threat


def build_summary(filtered: list) -> dict:
    """Build summary dict from detections."""
    summary = {}
    category_counts = {}
    for d in filtered:
        cn = d["class_name"]
        cat = d["category"]
        summary[cn] = summary.get(cn, 0) + 1
        category_counts[cat] = category_counts.get(cat, 0) + 1
    summary["total"] = len(filtered)
    summary["by_category"] = category_counts
    return summary


def build_analysis_text(detect_type: str, summary: dict, threat_level: str,
                        drone_id: Optional[int] = None) -> str:
    """Generate natural language analysis from detection results."""
    config = DETECT_CONFIG.get(detect_type, DETECT_CONFIG["aerial"])
    desc = config["description"]
    total = summary.get("total", 0)

    parts = [f"[{desc}]"]
    if drone_id:
        parts.append(f"无人机 UAV-{drone_id:03d} 视觉报告：")
    parts.append(f"共检测到 {total} 个目标。")

    # Detail breakdown
    details = []
    for key in sorted(summary.keys()):
        if key in ("total", "by_category"):
            continue
        details.append(f"{key}({summary[key]})")
    if details:
        parts.append("目标分布：" + "、".join(details))

    # Category breakdown
    cats = summary.get("by_category", {})
    if cats:
        cat_str = "、".join(f"{k}{v}" for k, v in sorted(cats.items(), key=lambda x: -x[1]))
        parts.append(f"类别统计：{cat_str}")

    # Threat assessment
    threat_map = {
        "normal": "威胁等级：正常，空域安全。",
        "warning": "威胁等级：警告，需关注异常目标密度。",
        "danger": "威胁等级：危险，建议立即采取应对措施！",
    }
    parts.append(threat_map.get(threat_level, threat_map["normal"]))

    # Type-specific suggestions
    suggestions = {
        "landing": "建议：降落区人员/车辆密度过高，请选择备用降落点。" if threat_level != "normal" else "建议：降落区安全，可以执行降落。",
        "intruder": "建议：发现空域入侵目标，建议调整航线避让。" if threat_level != "normal" else "建议：空域无入侵目标，飞行安全。",
        "disaster": "建议：发现潜在灾害迹象，建议立即上报应急中心。" if threat_level != "normal" else "建议：未发现明显灾害迹象。",
        "traffic": "建议：交通流量较大，空域航线下方需注意。" if threat_level != "normal" else "建议：交通流量正常。",
        "obstacle": "建议：航线前方检测到障碍物，建议调整高度。" if threat_level != "normal" else "建议：航线前方无障碍物。",
        "aerial": "建议：空域态势正常，持续监控中。" if threat_level == "normal" else "建议：发现异常密度目标，加强监控。",
    }
    parts.append(suggestions.get(detect_type, ""))

    return "\n".join(parts)


def run_detection(cv_service, image, detect_type: str,
                  drone_id: Optional[int] = None) -> CVResult:
    """Execute full detection pipeline and return CVResult."""
    # Run YOLO inference
    results = cv_service.infer(image)

    # Parse all detections
    all_detections = cv_service.parse_detections(results)

    # Filter by detect type
    filtered = filter_detections(all_detections, detect_type)

    # Assess threat
    threat = assess_threat_level(filtered, detect_type)

    # Build summary
    summary = build_summary(filtered)

    # Build analysis text
    analysis = build_analysis_text(detect_type, summary, threat, drone_id)

    # Get annotated image
    annotated = cv_service.get_annotated_image(results)

    return CVResult(
        detect_type=detect_type,
        detections=[Detection(**d) for d in filtered],
        summary=summary,
        threat_level=threat,
        annotated_image=annotated,
        analysis_text=analysis,
        drone_id=drone_id,
    )
