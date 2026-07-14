"""YOLOv8 inference service for low-altitude CV detection."""
import base64
import io
import logging
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# COCO class category mapping
HUMAN_CLASSES = {"person"}
VEHICLE_CLASSES = {"car", "truck", "bus", "motorcycle", "bicycle"}
ANIMAL_CLASSES = {"bird", "cat", "dog", "horse", "cow", "sheep"}
OBSTACLE_CLASSES = {"traffic light", "fire hydrant", "stop sign", "parking meter", "bench"}
BUILDING_CLASSES = set()  # COCO doesn't have building class directly

# Sample image mapping
SAMPLE_IMAGES = {
    "city_intersection": "Aerial view of a busy city intersection with many cars and trucks",
    "open_field": "Aerial view of an open field near a residential area",
    "urban_density": "Aerial view of dense urban area with buildings and streets",
    "parking_lot": "Aerial view of a parking lot full of cars",
    "construction_site": "Aerial view of a construction site with cranes and trucks",
    "river_bridge": "Aerial view of a river with a bridge and vehicles",
    "stadium_crowd": "Aerial view of a stadium area with crowds of people",
    "highway_traffic": "Aerial view of highway with heavy traffic",
}


class YOLOService:
    """YOLOv8 inference service wrapping ultralytics model."""

    def __init__(self, model_path: str = "yolov8n.pt", device: str = "cpu", conf: float = 0.25):
        self.model_path = model_path
        self.device = device
        self.conf_threshold = conf
        self._model = None
        self._class_names = None

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def load(self):
        """Load YOLO model. Downloads weights on first run."""
        try:
            from ultralytics import YOLO
            logger.info(f"Loading YOLO model: {self.model_path}")
            self._model = YOLO(self.model_path)
            self._class_names = self._model.names
            logger.info(f"YOLO model loaded. {len(self._class_names)} classes.")
            # Warm up
            dummy = np.zeros((640, 640, 3), dtype=np.uint8)
            self._model(dummy, verbose=False)
            logger.info("YOLO warm-up done.")
            return True
        except Exception as e:
            logger.error(f"Failed to load YOLO: {e}")
            self._model = None
            return False

    def infer(self, image: np.ndarray) -> list:
        """Run detection, return raw results list."""
        if not self.is_loaded:
            return []
        results = self._model(image, conf=self.conf_threshold, verbose=False)
        return results

    def parse_detections(self, results) -> list:
        """Parse YOLO results into structured detections."""
        if not results:
            return []
        r = results[0]
        detections = []
        boxes = r.boxes
        for i in range(len(boxes)):
            cls_id = int(boxes.cls[i].item())
            conf = float(boxes.conf[i].item())
            xyxy = boxes.xyxy[i].tolist()
            cls_name = self._class_names.get(cls_id, str(cls_id))
            category = self._get_category(cls_name)
            detections.append({
                "class_name": cls_name,
                "confidence": round(conf, 3),
                "bbox": [round(v, 1) for v in xyxy],
                "category": category,
            })
        return detections

    def get_annotated_image(self, results) -> Optional[str]:
        """Return base64 encoded annotated image."""
        if not results:
            return None
        try:
            annotated = results[0].plot()  # numpy BGR image
            return self._encode_image(annotated)
        except Exception as e:
            logger.error(f"Annotation error: {e}")
            return None

    @staticmethod
    def _encode_image(img_array: np.ndarray) -> str:
        """Encode numpy image to base64 JPEG."""
        try:
            import cv2
            _, buffer = cv2.imencode('.jpg', img_array, [cv2.IMWRITE_JPEG_QUALITY, 85])
            return base64.b64encode(buffer).decode('utf-8')
        except ImportError:
            from PIL import Image
            img = Image.fromarray(img_array[..., ::-1])
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=85)
            return base64.b64encode(buf.getvalue()).decode('utf-8')

    @staticmethod
    def _get_category(cls_name: str) -> str:
        if cls_name in HUMAN_CLASSES:
            return "human"
        if cls_name in VEHICLE_CLASSES:
            return "vehicle"
        if cls_name in ANIMAL_CLASSES:
            return "animal"
        if cls_name in OBSTACLE_CLASSES:
            return "obstacle"
        return "other"

    @staticmethod
    def decode_base64_image(b64_str: str) -> Optional[np.ndarray]:
        """Decode base64 image to numpy array."""
        try:
            import cv2
            img_bytes = base64.b64decode(b64_str)
            img_array = np.frombuffer(img_bytes, dtype=np.uint8)
            return cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        except ImportError:
            from PIL import Image
            img_bytes = base64.b64decode(b64_str)
            img = Image.open(io.BytesIO(img_bytes))
            return np.array(img)[..., ::-1]
        except Exception as e:
            logger.error(f"Image decode error: {e}")
            return None

    def load_sample_image(self, name: str) -> Optional[np.ndarray]:
        """Load a sample test image by name."""
        from config import settings
        img_dir = Path(settings.TEST_IMAGES_DIR)
        # Try common extensions
        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            path = img_dir / f"{name}{ext}"
            if path.exists():
                try:
                    import cv2
                    return cv2.imread(str(path))
                except ImportError:
                    from PIL import Image
                    img = Image.open(str(path))
                    return np.array(img)[..., ::-1]
                except Exception as e:
                    logger.error(f"Error loading {path}: {e}")
        logger.warning(f"Sample image not found: {name}")
        return None

    def list_samples(self) -> list:
        """List available sample images."""
        from config import settings
        img_dir = Path(settings.TEST_IMAGES_DIR)
        samples = []
        if img_dir.exists():
            for f in sorted(img_dir.iterdir()):
                if f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp'):
                    samples.append(f.stem)
        return samples


# Singleton
_cv_service: Optional[YOLOService] = None


def get_cv_service() -> YOLOService:
    global _cv_service
    if _cv_service is None:
        from config import settings
        _cv_service = YOLOService(
            model_path=settings.YOLO_MODEL,
            device=settings.YOLO_DEVICE,
            conf=settings.YOLO_CONF_THRESHOLD,
        )
    return _cv_service
