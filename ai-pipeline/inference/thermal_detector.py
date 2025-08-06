import cv2
import numpy as np
import torch
import torchvision.transforms as transforms
from PIL import Image
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

# YOLO-NAS imports (install with: pip install super-gradients)
from super_gradients.training import models

# MobileNetV3 imports
import torchvision.models as models

@dataclass
class Detection:
    """Single object detection result"""
    component_type: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)
    max_temperature: float
    hotspot_classification: str
    center_point: Tuple[int, int]

@dataclass
class AnalysisResult:
    """Complete analysis result for a thermal image"""
    image_id: str
    image_path: str
    is_good_quality: bool
    quality_score: float
    detections: List[Detection]
    ambient_temperature: float
    processing_time: float
    model_version: str

class ThermalDetector:
    """Main AI pipeline for thermal image analysis"""
    
    def __init__(
        self,
        yolo_model_path: str,
        mobilenet_model_path: str,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.device = device
        self.logger = logging.getLogger(__name__)
        
        # Temperature thresholds
        self.ambient_temp = 34.0
        self.potential_threshold = 20.0  # +20°C
        self.critical_threshold = 40.0   # +40°C
        
        # Component classes
        self.component_classes = {
            0: "nuts_bolts",
            1: "mid_span_joint", 
            2: "polymer_insulator"
        }
        
        # Load models
        self.yolo_model = self._load_yolo_model(yolo_model_path)
        self.quality_model = self._load_quality_model(mobilenet_model_path)
        
        # Image preprocessing
        self.quality_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        self.logger.info(f"ThermalDetector initialized on {device}")
    
    def _load_yolo_model(self, model_path: str):
        """Load YOLO-NAS model for object detection"""
        try:
            # Load pre-trained YOLO-NAS model
            model = models.get('yolo_nas_s', pretrained_weights="coco")
            
            # If custom weights exist, load them
            if Path(model_path).exists():
                checkpoint = torch.load(model_path, map_location=self.device)
                model.load_state_dict(checkpoint)
                self.logger.info(f"Loaded custom YOLO weights from {model_path}")
            else:
                self.logger.warning(f"Custom weights not found at {model_path}, using pre-trained")
            
            model.to(self.device)
            model.eval()
            return model
        except Exception as e:
            self.logger.error(f"Failed to load YOLO model: {e}")
            raise
    
    def _load_quality_model(self, model_path: str):
        """Load MobileNetV3 model for image quality assessment"""
        try:
            # Load MobileNetV3 for binary classification (good/bad quality)
            model = models.mobilenet_v3_small(pretrained=True)
            model.classifier[3] = torch.nn.Linear(model.classifier[3].in_features, 2)
            
            # Load custom weights if available
            if Path(model_path).exists():
                checkpoint = torch.load(model_path, map_location=self.device)
                model.load_state_dict(checkpoint)
                self.logger.info(f"Loaded custom MobileNet weights from {model_path}")
            else:
                self.logger.warning(f"Custom weights not found at {model_path}, using pre-trained")
            
            model.to(self.device)
            model.eval()
            return model
        except Exception as e:
            self.logger.error(f"Failed to load quality model: {e}")
            raise
    
    def assess_image_quality(self, image: np.ndarray) -> Tuple[bool, float]:
        """Assess if thermal image is good quality for analysis"""
        try:
            # Convert to PIL Image
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            
            # Preprocess
            input_tensor = self.quality_transform(pil_image).unsqueeze(0).to(self.device)
            
            # Inference
            with torch.no_grad():
                outputs = self.quality_model(input_tensor)
                probabilities = torch.softmax(outputs, dim=1)
                confidence = probabilities[0][1].item()  # Probability of "good quality"
            
            is_good_quality = confidence > 0.7  # Threshold for good quality
            return is_good_quality, confidence
            
        except Exception as e:
            self.logger.error(f"Quality assessment failed: {e}")
            return False, 0.0
    
    def detect_components(self, image: np.ndarray) -> List[Detection]:
        """Detect components in thermal image using YOLO-NAS"""
        try:
            detections = []
            
            # YOLO-NAS inference
            results = self.yolo_model.predict(image, conf=0.5)
            
            for result in results:
                if hasattr(result, 'prediction'):
                    pred = result.prediction
                    
                    # Extract bounding boxes, classes, and confidences
                    boxes = pred.bboxes_xyxy.cpu().numpy()
                    classes = pred.labels.cpu().numpy()
                    confidences = pred.confidence.cpu().numpy()
                    
                    for box, cls, conf in zip(boxes, classes, confidences):
                        x1, y1, x2, y2 = map(int, box)
                        width = x2 - x1
                        height = y2 - y1
                        center_x = x1 + width // 2
                        center_y = y1 + height // 2
                        
                        # Extract temperature from the detected region
                        roi = image[y1:y2, x1:x2]
                        max_temp = self._extract_max_temperature(roi)
                        
                        # Classify hotspot
                        hotspot_class = self._classify_hotspot(max_temp)
                        
                        # Get component type
                        component_type = self.component_classes.get(int(cls), "unknown")
                        
                        detection = Detection(
                            component_type=component_type,
                            confidence=float(conf),
                            bbox=(x1, y1, width, height),
                            max_temperature=max_temp,
                            hotspot_classification=hotspot_class,
                            center_point=(center_x, center_y)
                        )
                        
                        detections.append(detection)
            
            return detections
            
        except Exception as e:
            self.logger.error(f"Component detection failed: {e}")
            return []
    
    def _extract_max_temperature(self, roi: np.ndarray) -> float:
        """Extract maximum temperature from region of interest"""
        try:
            # For thermal images, temperature is often encoded in pixel intensity
            # This is a simplified approach - real FLIR images have metadata
            
            if len(roi.shape) == 3:
                # Convert to grayscale if colored thermal image
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            else:
                gray = roi
            
            # Find maximum intensity
            max_intensity = np.max(gray)
            
            # Convert intensity to temperature (this mapping depends on FLIR calibration)
            # Simplified linear mapping: 0-255 intensity -> 20-80°C
            max_temp = 20 + (max_intensity / 255.0) * 60
            
            return round(max_temp, 2)
            
        except Exception as e:
            self.logger.error(f"Temperature extraction failed: {e}")
            return self.ambient_temp
    
    def _classify_hotspot(self, temperature: float) -> str:
        """Classify hotspot based on temperature thresholds"""
        if temperature >= (self.ambient_temp + self.critical_threshold):
            return "critical"
        elif temperature >= (self.ambient_temp + self.potential_threshold):
            return "potential"
        else:
            return "normal"
    
    def analyze_image(
        self, 
        image_path: str, 
        image_id: str,
        ambient_temperature: Optional[float] = None
    ) -> AnalysisResult:
        """Complete analysis pipeline for a thermal image"""
        import time
        start_time = time.time()
        
        try:
            # Update ambient temperature if provided
            if ambient_temperature:
                self.ambient_temp = ambient_temperature
            
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Step 1: Quality assessment
            is_good_quality, quality_score = self.assess_image_quality(image)
            
            detections = []
            if is_good_quality:
                # Step 2: Component detection
                detections = self.detect_components(image)
            
            processing_time = time.time() - start_time
            
            result = AnalysisResult(
                image_id=image_id,
                image_path=image_path,
                is_good_quality=is_good_quality,
                quality_score=quality_score,
                detections=detections,
                ambient_temperature=self.ambient_temp,
                processing_time=processing_time,
                model_version="yolo_nas_s_mobilenet_v3"
            )
            
            self.logger.info(
                f"Processed {image_id}: "
                f"Quality={quality_score:.2f}, "
                f"Detections={len(detections)}, "
                f"Time={processing_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Analysis failed for {image_id}: {e}")
            
            # Return failed result
            return AnalysisResult(
                image_id=image_id,
                image_path=image_path,
                is_good_quality=False,
                quality_score=0.0,
                detections=[],
                ambient_temperature=self.ambient_temp,
                processing_time=time.time() - start_time,
                model_version="error"
            )
    
    def batch_analyze(self, image_paths: List[str]) -> List[AnalysisResult]:
        """Analyze multiple images in batch"""
        results = []
        
        for i, image_path in enumerate(image_paths):
            image_id = f"batch_{i}_{Path(image_path).stem}"
            result = self.analyze_image(image_path, image_id)
            results.append(result)
        
        return results

# Factory function for easy initialization
def create_thermal_detector(config: dict) -> ThermalDetector:
    """Create and initialize thermal detector with configuration"""
    return ThermalDetector(
        yolo_model_path=config.get("yolo_model_path"),
        mobilenet_model_path=config.get("mobilenet_model_path"),
        device=config.get("device", "cuda" if torch.cuda.is_available() else "cpu")
    ) 