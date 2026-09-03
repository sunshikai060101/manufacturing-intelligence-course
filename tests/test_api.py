"""API接口集成测试"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from backend.app import app
from backend.database import init_db, SessionLocal
from backend.models import DetectionRecord, InventoryItem

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """每个测试前初始化数据库"""
    init_db()
    yield
    # 清理测试数据
    db = SessionLocal()
    db.query(DetectionRecord).delete()
    db.query(InventoryItem).delete()
    db.commit()
    db.close()


class TestHealthCheck:
    """健康检查测试"""

    def test_health_check(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "智能仓储" in data["system"]

    def test_api_root(self):
        response = client.get("/api")
        assert response.status_code == 200
        data = response.json()
        assert "endpoints" in data


class TestStatsAPI:
    """统计API测试"""

    def test_dashboard_stats(self):
        response = client.get("/api/stats/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "total_detections" in data
        assert "today_detections" in data
        assert "total_inventory" in data
        assert "anomaly_count" in data
        assert "pass_rate" in data
        assert "class_distribution" in data
        assert "recent_detections" in data

    def test_detection_trend(self):
        response = client.get("/api/stats/trend?days=7")
        assert response.status_code == 200
        data = response.json()
        assert data["days"] == 7
        assert len(data["data"]) == 7

    def test_class_info(self):
        response = client.get("/api/stats/classes")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 6
        assert len(data["classes"]) == 6
        assert data["classes"][0]["class_name"] == "cardboard_box"

    def test_system_info(self):
        response = client.get("/api/stats/system")
        assert response.status_code == 200
        data = response.json()
        assert "system_name" in data
        assert "version" in data
        assert "num_classes" in data


class TestInventoryAPI:
    """库存管理API测试"""

    def test_create_inventory(self):
        response = client.post("/api/inventory", json={
            "class_id": 0,
            "class_name": "cardboard_box",
            "quantity": 100,
            "location": "A-01",
            "description": "纸箱",
            "min_stock": 10,
            "max_stock": 500,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["class_id"] == 0
        assert data["quantity"] == 100

    def test_get_inventory_list(self):
        # 先创建一条
        client.post("/api/inventory", json={
            "class_id": 1, "class_name": "pallet", "quantity": 50
        })
        response = client.get("/api/inventory")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_inbound_stock(self):
        # 创建
        create_resp = client.post("/api/inventory", json={
            "class_id": 2, "class_name": "stillage", "quantity": 10
        })
        item_id = create_resp.json()["id"]
        # 入库
        response = client.post(f"/api/inventory/{item_id}/inbound?quantity=5")
        assert response.status_code == 200
        assert "入库5件成功" in response.json()["message"]

    def test_outbound_stock(self):
        create_resp = client.post("/api/inventory", json={
            "class_id": 3, "class_name": "forklift", "quantity": 20
        })
        item_id = create_resp.json()["id"]
        response = client.post(f"/api/inventory/{item_id}/outbound?quantity=5")
        assert response.status_code == 200
        assert "出库5件成功" in response.json()["message"]

    def test_outbound_insufficient_stock(self):
        create_resp = client.post("/api/inventory", json={
            "class_id": 4, "class_name": "eps_box", "quantity": 5
        })
        item_id = create_resp.json()["id"]
        response = client.post(f"/api/inventory/{item_id}/outbound?quantity=100")
        assert response.status_code == 400

    def test_delete_inventory(self):
        create_resp = client.post("/api/inventory", json={
            "class_id": 5, "class_name": "wheelie_bin", "quantity": 10
        })
        item_id = create_resp.json()["id"]
        response = client.delete(f"/api/inventory/{item_id}")
        assert response.status_code == 200


class TestSensorAPI:
    """传感器API测试"""

    def test_create_sensor_data(self):
        response = client.post("/api/sensor", json={
            "sensor_type": "weight",
            "sensor_id": "W-001",
            "value": 15.5,
            "unit": "kg",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["sensor_type"] == "weight"
        assert data["value"] == 15.5

    def test_get_sensor_data(self):
        client.post("/api/sensor", json={
            "sensor_type": "infrared", "sensor_id": "IR-001", "value": 1.0
        })
        response = client.get("/api/sensor")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_sensor_stats(self):
        for i in range(5):
            client.post("/api/sensor", json={
                "sensor_type": "weight", "sensor_id": "W-001",
                "value": 10.0 + i, "unit": "kg"
            })
        response = client.get("/api/sensor/stats?sensor_type=weight&hours=24")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 5
        assert data["mean"] > 0


class TestDetectionAPI:
    """检测API测试"""

    def test_get_detection_records_empty(self):
        response = client.get("/api/detection/records")
        assert response.status_code == 200
        assert response.json() == []

    def test_update_sort_status(self):
        # 先创建一条检测记录
        from backend.database import SessionLocal
        from backend.models import DetectionRecord
        db = SessionLocal()
        record = DetectionRecord(
            image_name="test.jpg", class_id=0, class_name="cardboard_box",
            confidence=0.95, sort_status="pending"
        )
        db.add(record)
        db.commit()
        record_id = record.id
        db.close()

        response = client.put(f"/api/detection/records/{record_id}/sort?status=sorted")
        assert response.status_code == 200
        assert "已更新" in response.json()["message"]

    def test_invalid_sort_status(self):
        response = client.put("/api/detection/records/999/sort?status=invalid")
        assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
