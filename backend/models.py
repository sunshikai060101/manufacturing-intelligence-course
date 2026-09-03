"""数据库模型定义"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from backend.database import Base


class DetectionRecord(Base):
    """检测记录表 - 存储每次物料识别的结果"""
    __tablename__ = "detection_records"

    id = Column(Integer, primary_key=True, index=True)
    image_name = Column(String(255), nullable=False)
    image_path = Column(String(500), nullable=True)
    class_id = Column(Integer, nullable=False)
    class_name = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)
    bbox_x = Column(Float, nullable=True)
    bbox_y = Column(Float, nullable=True)
    bbox_w = Column(Float, nullable=True)
    bbox_h = Column(Float, nullable=True)
    # 多传感器融合结果
    sensor_weight = Column(Float, nullable=True)
    fusion_result = Column(String(50), nullable=True)  # pass / warning / reject
    fusion_confidence = Column(Float, nullable=True)
    # 异常检测
    is_anomaly = Column(Boolean, default=False)
    anomaly_score = Column(Float, default=0.0)
    anomaly_reason = Column(String(255), nullable=True)
    # 分拣状态
    sort_status = Column(String(50), default="pending")  # pending / sorting / sorted / failed
    target_location = Column(String(100), nullable=True)
    # 时间
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class InventoryItem(Base):
    """库存物料表 - 管理仓库中的物料库存"""
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, nullable=False)
    class_name = Column(String(100), nullable=False)
    quantity = Column(Integer, default=0)
    location = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    min_stock = Column(Integer, default=10)
    max_stock = Column(Integer, default=1000)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class SensorData(Base):
    """传感器数据表 - 记录重量、红外等传感器读数"""
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, index=True)
    sensor_type = Column(String(50), nullable=False)  # weight / infrared / photoelectric
    sensor_id = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=True)
    detection_record_id = Column(Integer, ForeignKey("detection_records.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    detection_record = relationship("DetectionRecord", backref="sensor_data")


class SystemLog(Base):
    """系统日志表"""
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), default="info")  # info / warning / error
    module = Column(String(100), nullable=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)


class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(Text, nullable=True)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
