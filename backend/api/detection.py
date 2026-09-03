"""检测API路由 - 物料识别、多传感器融合、异常检测"""
import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import DetectionRecord, SensorData, InventoryItem
from backend.schemas import DetectionResponse, DetectionRecordResponse, ApiResponse
from backend.algorithms.object_detection import get_detector
from backend.algorithms.sensor_fusion import get_fusion_engine, SensorReading
from backend.algorithms.anomaly_detection import get_anomaly_detector
from backend.config import UPLOAD_DIR, CLASS_NAMES_CN

router = APIRouter(prefix="/api/detection", tags=["检测管理"])


@router.post("/upload", response_model=DetectionResponse)
async def upload_and_detect(
    file: UploadFile = File(...),
    enable_fusion: bool = Form(True),
    enable_anomaly: bool = Form(True),
    simulate_sensors: bool = Form(True),
    db: Session = Depends(get_db)
):
    """上传图像并执行完整检测流程（目标检测 + 多传感器融合 + 异常检测）"""
    # 保存上传文件
    file_ext = os.path.splitext(file.filename)[1]
    saved_name = f"{uuid.uuid4().hex}{file_ext}"
    saved_path = os.path.join(UPLOAD_DIR, saved_name)

    with open(saved_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # 目标检测
    detector = get_detector()
    try:
        detections, inference_time, img_shape = detector.detect_from_file(saved_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"图像检测失败: {str(e)}")

    detection_items = []
    fusion_results = []
    anomaly_results = []

    fusion_engine = get_fusion_engine()
    anomaly_detector = get_anomaly_detector()

    for det in detections:
        detection_items.append(det.to_dict())

        # 多传感器融合
        if enable_fusion:
            if simulate_sensors:
                sensors = fusion_engine.simulate_sensors(det.class_name)
            else:
                sensors = []
            fusion_result = fusion_engine.fuse(det.class_name, det.confidence, sensors)
            fusion_results.append(fusion_result.to_dict())

            # 保存传感器数据
            for s in sensors:
                db_sensor = SensorData(
                    sensor_type=s.sensor_type,
                    sensor_id=s.sensor_id,
                    value=s.value,
                    unit=s.unit,
                )
                db.add(db_sensor)
        else:
            fusion_result = None

        # 异常检测
        if enable_anomaly:
            weight_val = None
            if fusion_result and fusion_result.weight_value is not None:
                weight_val = fusion_result.weight_value
            anomaly_result = anomaly_detector.detect(
                class_name=det.class_name,
                confidence=det.confidence,
                bbox_w=det.w,
                bbox_h=det.h,
                weight=weight_val,
            )
            anomaly_results.append(anomaly_result.to_dict())
        else:
            anomaly_result = None

        # 保存检测记录到数据库
        record = DetectionRecord(
            image_name=file.filename,
            image_path=saved_path,
            class_id=det.class_id,
            class_name=det.class_name,
            confidence=det.confidence,
            bbox_x=det.x,
            bbox_y=det.y,
            bbox_w=det.w,
            bbox_h=det.h,
            sensor_weight=fusion_result.weight_value if fusion_result else None,
            fusion_result=fusion_result.status if fusion_result else None,
            fusion_confidence=fusion_result.confidence if fusion_result else None,
            is_anomaly=anomaly_result.is_anomaly if anomaly_result else False,
            anomaly_score=anomaly_result.anomaly_score if anomaly_result else 0.0,
            anomaly_reason="; ".join(anomaly_result.reasons) if anomaly_result else None,
            sort_status="pending",
        )
        db.add(record)

        # 更新库存
        if fusion_result and fusion_result.status == "pass":
            inventory = db.query(InventoryItem).filter(
                InventoryItem.class_id == det.class_id
            ).first()
            if inventory:
                inventory.quantity += 1
            else:
                new_item = InventoryItem(
                    class_id=det.class_id,
                    class_name=det.class_name,
                    quantity=1,
                    location=f"A-{det.class_id:02d}",
                    description=CLASS_NAMES_CN.get(det.class_name, det.class_name),
                )
                db.add(new_item)

    db.commit()

    return DetectionResponse(
        success=True,
        image_name=file.filename,
        image_size=img_shape,
        detections=detection_items,
        inference_time_ms=round(inference_time, 2),
        fusion_results=fusion_results,
        anomaly_results=anomaly_results,
        total_objects=len(detections),
        timestamp=datetime.now().isoformat(),
    )


@router.get("/records", response_model=list[DetectionRecordResponse])
def get_detection_records(
    skip: int = 0,
    limit: int = 50,
    class_id: Optional[int] = None,
    fusion_result: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取检测记录列表"""
    query = db.query(DetectionRecord)
    if class_id is not None:
        query = query.filter(DetectionRecord.class_id == class_id)
    if fusion_result:
        query = query.filter(DetectionRecord.fusion_result == fusion_result)
    records = query.order_by(DetectionRecord.created_at.desc()).offset(skip).limit(limit).all()
    return records


@router.get("/records/{record_id}", response_model=DetectionRecordResponse)
def get_detection_record(record_id: int, db: Session = Depends(get_db)):
    """获取单条检测记录详情"""
    record = db.query(DetectionRecord).filter(DetectionRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="检测记录不存在")
    return record


@router.put("/records/{record_id}/sort", response_model=ApiResponse)
def update_sort_status(record_id: int, status: str, db: Session = Depends(get_db)):
    """更新分拣状态"""
    valid_statuses = ["pending", "sorting", "sorted", "failed"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"无效状态，可选: {valid_statuses}")
    record = db.query(DetectionRecord).filter(DetectionRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="检测记录不存在")
    record.sort_status = status
    db.commit()
    return ApiResponse(success=True, message=f"分拣状态已更新为: {status}")


@router.delete("/records/{record_id}", response_model=ApiResponse)
def delete_detection_record(record_id: int, db: Session = Depends(get_db)):
    """删除检测记录"""
    record = db.query(DetectionRecord).filter(DetectionRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="检测记录不存在")
    db.delete(record)
    db.commit()
    return ApiResponse(success=True, message="检测记录已删除")
