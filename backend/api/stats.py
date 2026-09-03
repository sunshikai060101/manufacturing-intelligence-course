"""统计与仪表盘API路由"""
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models import DetectionRecord, InventoryItem, SensorData
from backend.schemas import DashboardStats, ClassStats, ApiResponse
from backend.config import CLASS_NAMES, CLASS_NAMES_CN

router = APIRouter(prefix="/api/stats", tags=["统计仪表盘"])


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """获取仪表盘综合统计数据"""
    # 总检测数
    total_detections = db.query(func.count(DetectionRecord.id)).scalar() or 0

    # 今日检测数
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_detections = db.query(func.count(DetectionRecord.id)).filter(
        DetectionRecord.created_at >= today_start
    ).scalar() or 0

    # 总库存
    total_inventory = db.query(func.sum(InventoryItem.quantity)).scalar() or 0

    # 异常数
    anomaly_count = db.query(func.count(DetectionRecord.id)).filter(
        DetectionRecord.is_anomaly == True
    ).scalar() or 0

    # 通过率
    pass_count = db.query(func.count(DetectionRecord.id)).filter(
        DetectionRecord.fusion_result == "pass"
    ).scalar() or 0
    pass_rate = (pass_count / total_detections * 100) if total_detections > 0 else 0.0

    # 各类别分布
    class_counts = db.query(
        DetectionRecord.class_id,
        DetectionRecord.class_name,
        func.count(DetectionRecord.id).label("count"),
        func.avg(DetectionRecord.confidence).label("avg_conf"),
        func.sum(DetectionRecord.is_anomaly.cast(Integer)).label("anomaly_count")
    ).group_by(DetectionRecord.class_id, DetectionRecord.class_name).all()

    class_distribution = []
    for cc in class_counts:
        class_distribution.append(ClassStats(
            class_id=cc.class_id,
            class_name=cc.class_name,
            class_name_cn=CLASS_NAMES_CN.get(cc.class_name, cc.class_name),
            count=cc.count or 0,
            avg_confidence=round(cc.avg_conf or 0, 4),
            anomaly_count=cc.anomaly_count or 0,
        ))

    # 最近检测记录
    recent = db.query(DetectionRecord).order_by(
        DetectionRecord.created_at.desc()
    ).limit(10).all()

    return DashboardStats(
        total_detections=total_detections,
        today_detections=today_detections,
        total_inventory=total_inventory,
        anomaly_count=anomaly_count,
        pass_rate=round(pass_rate, 2),
        class_distribution=class_distribution,
        recent_detections=recent,
    )


@router.get("/trend")
def get_detection_trend(days: int = 7, db: Session = Depends(get_db)):
    """获取检测趋势数据（按天统计）"""
    since = datetime.now() - timedelta(days=days)
    records = db.query(DetectionRecord).filter(
        DetectionRecord.created_at >= since
    ).all()

    daily_stats = defaultdict(lambda: {"total": 0, "pass": 0, "warning": 0, "reject": 0, "anomaly": 0})
    for r in records:
        day = r.created_at.strftime("%Y-%m-%d")
        daily_stats[day]["total"] += 1
        if r.fusion_result:
            daily_stats[day][r.fusion_result] = daily_stats[day].get(r.fusion_result, 0) + 1
        if r.is_anomaly:
            daily_stats[day]["anomaly"] += 1

    # 填充没有数据的日期
    result = []
    for i in range(days):
        day = (datetime.now() - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
        stats = daily_stats.get(day, {"total": 0, "pass": 0, "warning": 0, "reject": 0, "anomaly": 0})
        result.append({"date": day, **stats})

    return {"days": days, "data": result}


@router.get("/classes")
def get_class_info():
    """获取所有检测类别信息"""
    classes = []
    for idx, name in enumerate(CLASS_NAMES):
        classes.append({
            "class_id": idx,
            "class_name": name,
            "class_name_cn": CLASS_NAMES_CN.get(name, name),
        })
    return {"classes": classes, "total": len(classes)}


@router.get("/system")
def get_system_info():
    """获取系统信息"""
    from backend.algorithms.object_detection import get_detector
    from backend.algorithms.anomaly_detection import get_anomaly_detector

    detector = get_detector()
    anomaly_det = get_anomaly_detector()

    return {
        "system_name": "智能仓储物料识别与分拣系统",
        "version": "1.0.0",
        "model_loaded": detector.model_loaded,
        "model_path": detector.model_path,
        "confidence_threshold": detector.conf_threshold,
        "iou_threshold": detector.iou_threshold,
        "num_classes": len(CLASS_NAMES),
        "anomaly_detector_stats": anomaly_det.get_statistics(),
        "database_status": "connected",
    }


# 需要导入Integer
from sqlalchemy import Integer
