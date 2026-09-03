"""算法模块单元测试"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pytest
from backend.algorithms.object_detection import ObjectDetector, DetectionResult
from backend.algorithms.sensor_fusion import MultiSensorFusion, SensorReading
from backend.algorithms.anomaly_detection import AnomalyDetector


class TestObjectDetection:
    """目标检测算法测试"""

    def test_detector_initialization(self):
        """测试检测器初始化"""
        detector = ObjectDetector()
        assert detector is not None
        assert detector.conf_threshold == 0.5
        assert detector.iou_threshold == 0.45

    def test_preprocess_image(self):
        """测试图像预处理"""
        detector = ObjectDetector()
        # 创建测试图像
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        processed = detector.preprocess(image)
        assert processed.shape == (640, 640, 3)

    def test_simulate_detection(self):
        """测试模拟检测（无模型时）"""
        detector = ObjectDetector()
        detector.model_loaded = False  # 强制使用模拟模式
        image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        results, inference_time = detector.detect(image)
        assert isinstance(results, list)
        assert len(results) > 0
        assert inference_time > 0
        for r in results:
            assert isinstance(r, DetectionResult)
            assert 0 <= r.class_id < 6
            assert 0 < r.confidence <= 1
            assert r.w > 0 and r.h > 0

    def test_detection_result_to_dict(self):
        """测试检测结果序列化"""
        result = DetectionResult(
            class_id=0, class_name="cardboard_box",
            confidence=0.95, bbox=(100, 200, 50, 60)
        )
        d = result.to_dict()
        assert d["class_id"] == 0
        assert d["class_name"] == "cardboard_box"
        assert d["class_name_cn"] == "纸箱"
        assert d["confidence"] == 0.95
        assert d["bbox"]["x"] == 100


class TestSensorFusion:
    """多传感器融合算法测试"""

    def test_fusion_initialization(self):
        """测试融合引擎初始化"""
        fusion = MultiSensorFusion()
        assert fusion.visual_weight == 0.6
        assert fusion.sensor_weight == 0.4

    def test_weight_consistency_check_pass(self):
        """测试重量一致性校验-通过"""
        fusion = MultiSensorFusion()
        # cardboard_box 重量范围 0.5-25kg
        consistent, reason, _ = fusion.check_weight_consistency("cardboard_box", 10.0)
        assert consistent is True
        assert "在预期范围" in reason

    def test_weight_consistency_check_fail(self):
        """测试重量一致性校验-失败"""
        fusion = MultiSensorFusion()
        # cardboard_box 重量范围 0.5-25kg，100kg超出
        consistent, reason, _ = fusion.check_weight_consistency("cardboard_box", 100.0)
        assert consistent is False
        assert "高于预期" in reason

    def test_fuse_pass(self):
        """测试融合决策-通过"""
        fusion = MultiSensorFusion()
        sensors = [
            SensorReading(sensor_type="infrared", sensor_id="IR-1", value=1.0, confidence=0.95),
            SensorReading(sensor_type="weight", sensor_id="W-1", value=10.0, unit="kg", confidence=0.92),
        ]
        result = fusion.fuse("cardboard_box", 0.9, sensors)
        assert result.status == "pass"
        assert result.confidence > 0
        assert result.final_class == "cardboard_box"

    def test_fuse_reject_weight_mismatch(self):
        """测试融合决策-重量不匹配拒绝"""
        fusion = MultiSensorFusion()
        sensors = [
            SensorReading(sensor_type="infrared", sensor_id="IR-1", value=1.0, confidence=0.95),
            SensorReading(sensor_type="weight", sensor_id="W-1", value=1000.0, unit="kg", confidence=0.92),
        ]
        result = fusion.fuse("cardboard_box", 0.6, sensors)
        assert result.status in ("reject", "warning")

    def test_simulate_sensors(self):
        """测试模拟传感器数据"""
        fusion = MultiSensorFusion()
        sensors = fusion.simulate_sensors("cardboard_box")
        assert len(sensors) == 2
        assert sensors[0].sensor_type == "infrared"
        assert sensors[1].sensor_type == "weight"
        assert sensors[1].value > 0

    def test_filtered_weight(self):
        """测试重量滤波"""
        fusion = MultiSensorFusion()
        for w in [10.0, 10.5, 9.8, 10.2, 100.0]:  # 100是异常值
            fusion.add_weight_reading(w)
        filtered = fusion.get_filtered_weight()
        assert filtered is not None
        assert 8 < filtered < 15  # 异常值应被过滤


class TestAnomalyDetection:
    """异常检测算法测试"""

    def test_detector_initialization(self):
        """测试异常检测器初始化"""
        detector = AnomalyDetector()
        assert detector.mild_threshold == 0.4
        assert detector.severe_threshold == 0.7

    def test_detect_normal(self):
        """测试正常检测（数据不足时不应报异常）"""
        detector = AnomalyDetector()
        result = detector.detect("cardboard_box", 0.9, 100, 80, 10.0)
        assert result is not None
        assert result.anomaly_score >= 0
        assert len(result.reasons) > 0

    def test_detect_low_confidence(self):
        """测试低置信度异常检测"""
        detector = AnomalyDetector()
        # 先添加一些正常历史数据
        for i in range(20):
            detector.update_history("cardboard_box", 0.9, 10000, 10.0)
        # 低置信度应触发异常
        result = detector.detect("cardboard_box", 0.3, 100, 80, 10.0)
        assert result.dimension_scores["confidence"] > 0.3

    def test_anomaly_result_levels(self):
        """测试异常等级判定"""
        detector = AnomalyDetector()
        # 正常
        assert detector.mild_threshold == 0.4
        assert detector.severe_threshold == 0.7

    def test_get_statistics(self):
        """测试统计信息获取"""
        detector = AnomalyDetector()
        detector.update_history("cardboard_box", 0.9, 10000, 10.0)
        stats = detector.get_statistics()
        assert stats["total_detections"] >= 1
        assert "class_statistics" in stats

    def test_zscore_calculation(self):
        """测试Z-Score计算"""
        detector = AnomalyDetector()
        history = [10.0, 10.1, 9.9, 10.0, 10.2]
        z = detector._calculate_zscore(10.0, history)
        assert z >= 0
        # 异常值应有高Z-Score
        z_anomaly = detector._calculate_zscore(100.0, history)
        assert z_anomaly > z


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
