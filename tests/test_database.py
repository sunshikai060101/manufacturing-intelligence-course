"""数据库模型测试"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import datetime
from backend.database import init_db, SessionLocal
from backend.models import DetectionRecord, InventoryItem, SensorData, SystemLog, SystemConfig


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield
    db = SessionLocal()
    db.query(DetectionRecord).delete()
    db.query(InventoryItem).delete()
    db.query(SensorData).delete()
    db.query(SystemLog).delete()
    db.query(SystemConfig).delete()
    db.commit()
    db.close()


class TestDetectionRecord:
    """检测记录模型测试"""

    def test_create_detection_record(self):
        db = SessionLocal()
        record = DetectionRecord(
            image_name="test_001.jpg",
            image_path="/tmp/test_001.jpg",
            class_id=0,
            class_name="cardboard_box",
            confidence=0.95,
            bbox_x=100.0,
            bbox_y=200.0,
            bbox_w=50.0,
            bbox_h=60.0,
            fusion_result="pass",
            fusion_confidence=0.88,
            is_anomaly=False,
            anomaly_score=0.1,
            sort_status="pending",
        )
        db.add(record)
        db.commit()
        assert record.id is not None
        assert record.class_name == "cardboard_box"
        assert record.confidence == 0.95
        db.close()

    def test_query_detection_records(self):
        db = SessionLocal()
        for i in range(5):
            db.add(DetectionRecord(
                image_name=f"test_{i}.jpg",
                class_id=i % 6,
                class_name=f"class_{i}",
                confidence=0.8 + i * 0.02,
            ))
        db.commit()
        records = db.query(DetectionRecord).all()
        assert len(records) == 5
        db.close()

    def test_filter_by_class(self):
        db = SessionLocal()
        db.add(DetectionRecord(image_name="a.jpg", class_id=0, class_name="cardboard_box", confidence=0.9))
        db.add(DetectionRecord(image_name="b.jpg", class_id=1, class_name="pallet", confidence=0.85))
        db.commit()
        records = db.query(DetectionRecord).filter(DetectionRecord.class_id == 0).all()
        assert len(records) == 1
        assert records[0].class_name == "cardboard_box"
        db.close()


class TestInventoryItem:
    """库存模型测试"""

    def test_create_inventory(self):
        db = SessionLocal()
        item = InventoryItem(
            class_id=0,
            class_name="cardboard_box",
            quantity=100,
            location="A-01",
            description="纸箱物料",
            min_stock=10,
            max_stock=500,
        )
        db.add(item)
        db.commit()
        assert item.id is not None
        assert item.quantity == 100
        db.close()

    def test_update_quantity(self):
        db = SessionLocal()
        item = InventoryItem(class_id=1, class_name="pallet", quantity=50)
        db.add(item)
        db.commit()
        item.quantity += 20
        db.commit()
        db.refresh(item)
        assert item.quantity == 70
        db.close()


class TestSensorData:
    """传感器数据模型测试"""

    def test_create_sensor_data(self):
        db = SessionLocal()
        data = SensorData(
            sensor_type="weight",
            sensor_id="W-001",
            value=15.5,
            unit="kg",
        )
        db.add(data)
        db.commit()
        assert data.id is not None
        assert data.value == 15.5
        db.close()

    def test_sensor_data_with_detection(self):
        db = SessionLocal()
        record = DetectionRecord(
            image_name="test.jpg", class_id=0, class_name="box", confidence=0.9
        )
        db.add(record)
        db.commit()
        sensor = SensorData(
            sensor_type="weight", sensor_id="W-1", value=10.0,
            detection_record_id=record.id
        )
        db.add(sensor)
        db.commit()
        assert sensor.detection_record_id == record.id
        db.close()


class TestSystemConfig:
    """系统配置模型测试"""

    def test_create_config(self):
        db = SessionLocal()
        config = SystemConfig(
            config_key="test_key",
            config_value="test_value",
            description="测试配置",
        )
        db.add(config)
        db.commit()
        assert config.id is not None
        db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
