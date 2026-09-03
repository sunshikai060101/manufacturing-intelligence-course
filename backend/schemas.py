"""Pydantic 请求/响应模型定义"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ===== 检测相关 =====
class BBox(BaseModel):
    x: float
    y: float
    w: float
    h: float


class DetectionItem(BaseModel):
    class_id: int
    class_name: str
    class_name_cn: str
    confidence: float
    bbox: BBox


class FusionInfo(BaseModel):
    status: str
    status_cn: str
    confidence: float
    final_class: str
    final_class_cn: str
    reasons: List[str]
    visual_confidence: float
    sensor_confidence: float
    weight_value: Optional[float] = None
    expected_weight_range: Optional[tuple] = None


class AnomalyInfo(BaseModel):
    is_anomaly: bool
    anomaly_score: float
    anomaly_level: str
    anomaly_level_cn: str
    reasons: List[str]
    dimension_scores: Dict[str, float]


class DetectionResponse(BaseModel):
    success: bool
    image_name: str
    image_size: Optional[tuple] = None
    detections: List[DetectionItem]
    inference_time_ms: float
    fusion_results: List[FusionInfo] = []
    anomaly_results: List[AnomalyInfo] = []
    total_objects: int
    timestamp: str


class DetectionRecordResponse(BaseModel):
    id: int
    image_name: str
    class_id: int
    class_name: str
    confidence: float
    fusion_result: Optional[str] = None
    is_anomaly: bool
    sort_status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ===== 库存相关 =====
class InventoryItemCreate(BaseModel):
    class_id: int
    class_name: str
    quantity: int = 0
    location: Optional[str] = None
    description: Optional[str] = None
    min_stock: int = 10
    max_stock: int = 1000


class InventoryItemUpdate(BaseModel):
    quantity: Optional[int] = None
    location: Optional[str] = None
    description: Optional[str] = None
    min_stock: Optional[int] = None
    max_stock: Optional[int] = None


class InventoryItemResponse(BaseModel):
    id: int
    class_id: int
    class_name: str
    quantity: int
    location: Optional[str] = None
    description: Optional[str] = None
    min_stock: int
    max_stock: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== 传感器相关 =====
class SensorDataCreate(BaseModel):
    sensor_type: str
    sensor_id: str
    value: float
    unit: Optional[str] = None
    detection_record_id: Optional[int] = None


class SensorDataResponse(BaseModel):
    id: int
    sensor_type: str
    sensor_id: str
    value: float
    unit: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ===== 统计相关 =====
class ClassStats(BaseModel):
    class_id: int
    class_name: str
    class_name_cn: str
    count: int
    avg_confidence: float
    anomaly_count: int


class DashboardStats(BaseModel):
    total_detections: int
    today_detections: int
    total_inventory: int
    anomaly_count: int
    pass_rate: float
    class_distribution: List[ClassStats]
    recent_detections: List[DetectionRecordResponse]


# ===== 通用响应 =====
class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
