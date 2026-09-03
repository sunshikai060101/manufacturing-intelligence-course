"""传感器数据API路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from backend.database import get_db
from backend.models import SensorData
from backend.schemas import SensorDataCreate, SensorDataResponse, ApiResponse

router = APIRouter(prefix="/api/sensor", tags=["传感器数据"])


@router.get("", response_model=list[SensorDataResponse])
def get_sensor_data(
    skip: int = 0,
    limit: int = 100,
    sensor_type: Optional[str] = None,
    sensor_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取传感器数据列表"""
    query = db.query(SensorData)
    if sensor_type:
        query = query.filter(SensorData.sensor_type == sensor_type)
    if sensor_id:
        query = query.filter(SensorData.sensor_id == sensor_id)
    data = query.order_by(SensorData.created_at.desc()).offset(skip).limit(limit).all()
    return data


@router.post("", response_model=SensorDataResponse)
def create_sensor_data(data: SensorDataCreate, db: Session = Depends(get_db)):
    """上报传感器数据"""
    db_data = SensorData(**data.model_dump())
    db.add(db_data)
    db.commit()
    db.refresh(db_data)
    return db_data


@router.get("/stats")
def get_sensor_stats(
    sensor_type: str = "weight",
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """获取传感器统计数据"""
    since = datetime.now() - timedelta(hours=hours)
    data = db.query(SensorData).filter(
        SensorData.sensor_type == sensor_type,
        SensorData.created_at >= since
    ).all()

    if not data:
        return {
            "sensor_type": sensor_type,
            "count": 0,
            "mean": 0,
            "min": 0,
            "max": 0,
            "std": 0,
            "time_range_hours": hours,
        }

    values = [d.value for d in data]
    mean_val = sum(values) / len(values)
    variance = sum((v - mean_val) ** 2 for v in values) / len(values)
    std_val = variance ** 0.5

    return {
        "sensor_type": sensor_type,
        "count": len(values),
        "mean": round(mean_val, 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
        "std": round(std_val, 4),
        "time_range_hours": hours,
        "unit": data[0].unit,
    }


@router.get("/{data_id}", response_model=SensorDataResponse)
def get_sensor_data_by_id(data_id: int, db: Session = Depends(get_db)):
    """获取单条传感器数据"""
    data = db.query(SensorData).filter(SensorData.id == data_id).first()
    if not data:
        raise HTTPException(status_code=404, detail="传感器数据不存在")
    return data
