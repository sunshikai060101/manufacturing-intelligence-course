"""
算法模块一：基于深度学习的目标检测
技术方向：机器视觉与深度学习（YOLO目标检测算法）

功能：
1. 加载YOLO模型进行物料目标检测
2. 图像预处理（缩放、归一化）
3. 检测结果后处理（NMS、坐标转换）
4. 支持模型不存在时的模拟检测（用于演示）
"""
import os
import time
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from backend.config import (
    CLASS_NAMES, CLASS_NAMES_CN, DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_IOU_THRESHOLD, TARGET_IMAGE_SIZE, DEFAULT_MODEL_PATH
)


class DetectionResult:
    """单个检测结果"""
    def __init__(self, class_id: int, class_name: str, confidence: float,
                 bbox: Tuple[float, float, float, float]):
        self.class_id = class_id
        self.class_name = class_name
        self.class_name_cn = CLASS_NAMES_CN.get(class_name, class_name)
        self.confidence = confidence
        self.x, self.y, self.w, self.h = bbox  # 中心点坐标和宽高（像素）

    def to_dict(self) -> Dict:
        return {
            "class_id": self.class_id,
            "class_name": self.class_name,
            "class_name_cn": self.class_name_cn,
            "confidence": round(self.confidence, 4),
            "bbox": {
                "x": round(self.x, 2),
                "y": round(self.y, 2),
                "w": round(self.w, 2),
                "h": round(self.h, 2),
            }
        }


class ObjectDetector:
    """目标检测器"""

    def __init__(self, model_path: Optional[str] = None,
                 conf_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
                 iou_threshold: float = DEFAULT_IOU_THRESHOLD):
        self.model_path = model_path or str(DEFAULT_MODEL_PATH)
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.model = None
        self.model_loaded = False
        self._load_model()

    def _load_model(self):
        """加载YOLO模型"""
        try:
            from ultralytics import YOLO
            if os.path.exists(self.model_path):
                self.model = YOLO(self.model_path)
                self.model_loaded = True
                print(f"[目标检测] 模型加载成功: {self.model_path}")
            else:
                print(f"[目标检测] 模型文件不存在，使用模拟检测模式: {self.model_path}")
                self.model_loaded = False
        except ImportError:
            print("[目标检测] ultralytics未安装，使用模拟检测模式")
            self.model_loaded = False
        except Exception as e:
            print(f"[目标检测] 模型加载失败: {e}，使用模拟检测模式")
            self.model_loaded = False

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        图像预处理
        1. 转换为RGB
        2. 等比例缩放至目标尺寸
        3. 居中填充
        """
        try:
            import cv2
            use_cv2 = True
        except ImportError:
            use_cv2 = False

        if len(image.shape) == 2:
            if use_cv2:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            else:
                image = np.stack([image] * 3, axis=-1)
        elif image.shape[2] == 4:
            image = image[:, :, :3]

        h, w = image.shape[:2]
        scale = TARGET_IMAGE_SIZE / max(h, w)
        new_h, new_w = int(h * scale), int(w * scale)

        if use_cv2:
            resized = cv2.resize(image, (new_w, new_h))
        else:
            # 使用Pillow进行缩放
            from PIL import Image
            pil_img = Image.fromarray(image)
            pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)
            resized = np.array(pil_img)

        # 居中填充
        canvas = np.zeros((TARGET_IMAGE_SIZE, TARGET_IMAGE_SIZE, 3), dtype=np.uint8)
        y_offset = (TARGET_IMAGE_SIZE - new_h) // 2
        x_offset = (TARGET_IMAGE_SIZE - new_w) // 2
        canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized

        return canvas

    def detect(self, image: np.ndarray) -> Tuple[List[DetectionResult], float]:
        """
        执行目标检测
        返回: (检测结果列表, 推理时间ms)
        """
        start_time = time.time()

        if self.model_loaded and self.model is not None:
            results = self._detect_with_model(image)
        else:
            results = self._simulate_detection(image)

        inference_time = (time.time() - start_time) * 1000
        return results, inference_time

    def _detect_with_model(self, image: np.ndarray) -> List[DetectionResult]:
        """使用真实YOLO模型检测"""
        results = self.model(
            image,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            verbose=False
        )

        detections = []
        if results and len(results) > 0:
            result = results[0]
            if result.boxes is not None:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    xywh = box.xywh[0].cpu().numpy()
                    x, y, w, h = float(xywh[0]), float(xywh[1]), float(xywh[2]), float(xywh[3])

                    if class_id < len(CLASS_NAMES):
                        class_name = CLASS_NAMES[class_id]
                    else:
                        class_name = f"class_{class_id}"

                    detections.append(DetectionResult(
                        class_id=class_id,
                        class_name=class_name,
                        confidence=confidence,
                        bbox=(x, y, w, h)
                    ))

        return detections

    def _simulate_detection(self, image: np.ndarray) -> List[DetectionResult]:
        """
        模拟检测（无模型时使用）
        基于图像特征生成合理的模拟检测结果，用于系统演示和测试
        """
        h, w = image.shape[:2] if len(image.shape) >= 2 else (480, 640)
        detections = []

        # 基于图像亮度和纹理复杂度决定检测数量
        gray = np.mean(image, axis=2) if len(image.shape) == 3 else image
        brightness = np.mean(gray) / 255.0
        texture = np.std(gray) / 255.0

        num_objects = max(1, min(5, int(texture * 6 + brightness * 2)))

        # 固定随机种子基于图像特征，保证同一张图结果一致
        seed = int(np.sum(image[:10, :10]) % 10000)
        rng = np.random.RandomState(seed)

        for i in range(num_objects):
            class_id = rng.randint(0, len(CLASS_NAMES))
            class_name = CLASS_NAMES[class_id]
            confidence = float(rng.uniform(0.65, 0.98))

            obj_w = float(rng.uniform(0.15, 0.4) * w)
            obj_h = float(rng.uniform(0.15, 0.4) * h)
            x = float(rng.uniform(obj_w / 2, w - obj_w / 2))
            y = float(rng.uniform(obj_h / 2, h - obj_h / 2))

            detections.append(DetectionResult(
                class_id=class_id,
                class_name=class_name,
                confidence=confidence,
                bbox=(x, y, obj_w, obj_h)
            ))

        # 按置信度排序
        detections.sort(key=lambda d: d.confidence, reverse=True)
        return detections

    def detect_from_file(self, image_path: str) -> Tuple[List[DetectionResult], float, tuple]:
        """从文件加载图像并检测"""
        try:
            import cv2
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"无法读取图像文件: {image_path}")
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        except ImportError:
            from PIL import Image
            pil_img = Image.open(image_path).convert("RGB")
            image_rgb = np.array(pil_img)

        results, inference_time = self.detect(image_rgb)
        return results, inference_time, image_rgb.shape[:2]


# 全局检测器单例
_detector_instance = None


def get_detector() -> ObjectDetector:
    """获取全局检测器实例"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = ObjectDetector()
    return _detector_instance
