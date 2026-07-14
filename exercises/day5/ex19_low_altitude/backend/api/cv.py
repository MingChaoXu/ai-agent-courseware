"""CV detection API - direct access to YOLO inference."""
import logging
from fastapi import APIRouter, HTTPException
from models.schemas import DetectRequest, DetectResponse
from cv_service.yolo_server import get_cv_service
from cv_service.detectors import run_detection

router = APIRouter(prefix="/cv", tags=["cv"])
logger = logging.getLogger(__name__)


@router.get("/samples")
async def list_samples():
    cv = get_cv_service()
    return {"samples": cv.list_samples(), "loaded": cv.is_loaded}


@router.get("/status")
async def cv_status():
    from config import settings
    cv = get_cv_service()
    return {
        "loaded": cv.is_loaded,
        "model": settings.YOLO_MODEL,
        "device": settings.YOLO_DEVICE,
        "conf_threshold": settings.YOLO_CONF_THRESHOLD,
        "samples": cv.list_samples(),
    }


@router.post("/detect", response_model=DetectResponse)
async def detect(request: DetectRequest):
    cv = get_cv_service()
    if not cv.is_loaded:
        raise HTTPException(status_code=503, detail="CV model not loaded")

    # Load image
    image = None
    if request.image_base64:
        image = cv.decode_base64_image(request.image_base64)
    elif request.image_source and request.image_source != "sample":
        image = cv.load_sample_image(request.image_source)

    if image is None:
        # Auto-select sample based on detect_type
        sample_map = {
            "aerial": "urban_density",
            "obstacle": "construction_site",
            "intruder": "river_bridge",
            "landing": "open_field",
            "disaster": "construction_site",
            "traffic": "city_intersection",
        }
        fallback = sample_map.get(request.detect_type, "urban_density")
        image = cv.load_sample_image(fallback)

    if image is None:
        return DetectResponse(success=False, error="No image available. Place test images in backend/data/test_images/")

    result = run_detection(cv, image, request.detect_type, request.drone_id)
    return DetectResponse(success=True, result=result)
