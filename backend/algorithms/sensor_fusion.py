"""
算法模块二：多传感器数据融合
技术方向：传感器与多源数据融合技术

功能：
1. 融合视觉识别结果与重量传感器数据
2. 基于规则的一致性校验（类别-重量匹配）
3. 加权融合决策（视觉置信度 + 传感器可信度）
4. 红外传感器到位检测与触发逻辑
5. 输出融合判定结果（通过/警告/拒绝）
"""
import time
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

from backend.config import CLASS_WEIGHT_RANGE, CLASS_NAMES_CN


@dataclass
class SensorReading:
    """传感器读数"""
    sensor_type: str  # weight / infrared / photoelectric
    sensor_id: str
    value: float
    unit: str = ""
    timestamp: float = field(default_factory=time.time)
    confidence: float = 0.9  # 传感器可信度


@dataclass
class FusionResult:
    """融合判定结果"""
    status: str  # pass / warning / reject
    confidence: float
    final_class: str
    final_class_cn: str
    reasons: List[str] = field(default_factory=list)
    visual_confidence: float = 0.0
    sensor_confidence: float = 0.0
    weight_value: Optional[float] = None
    expected_weight_range: Optional[Tuple[float, float]] = None

    def to_dict(self) -> Dict:
        return {
            "status": self.status,
            "status_cn": {"pass": "通过", "warning": "警告", "reject": "拒绝"}.get(self.status, self.status),
            "confidence": round(self.confidence, 4),
            "final_class": self.final_class,
            "final_class_cn": self.final_class_cn,
            "reasons": self.reasons,
            "visual_confidence": round(self.visual_confidence, 4),
            "sensor_confidence": round(self.sensor_confidence, 4),
            "weight_value": self.weight_value,
            "expected_weight_range": self.expected_weight_range,
        }


class MultiSensorFusion:
    """多传感器融合引擎"""

    def __init__(self):
        # 融合权重：视觉 0.6，传感器 0.4
        self.visual_weight = 0.6
        self.sensor_weight = 0.4
        # 重量容差比例
        self.weight_tolerance = 0.3  # 允许±30%偏差
        # 传感器历史数据（用于滤波）
        self.weight_history: List[float] = []
        self.max_history = 10

    def add_weight_reading(self, weight: float):
        """添加重量读数，用于滑动平均滤波"""
        self.weight_history.append(weight)
        if len(self.weight_history) > self.max_history:
            self.weight_history.pop(0)

    def get_filtered_weight(self) -> Optional[float]:
        """获取滤波后的重量值（滑动平均）"""
        if not self.weight_history:
            return None
        # 去除最大值和最小值后取平均
        if len(self.weight_history) >= 3:
            sorted_hist = sorted(self.weight_history)
            trimmed = sorted_hist[1:-1]
            return sum(trimmed) / len(trimmed)
        return sum(self.weight_history) / len(self.weight_history)

    def check_weight_consistency(self, class_name: str, weight: float) -> Tuple[bool, str, Tuple[float, float]]:
        """
        检查重量与视觉识别类别的一致性
        返回: (是否一致, 原因描述, 期望重量范围)
        """
        if class_name not in CLASS_WEIGHT_RANGE:
            return True, "无该类别的重量参考数据", (0, 0)

        min_w, max_w = CLASS_WEIGHT_RANGE[class_name]
        # 应用容差
        tolerance = (max_w - min_w) * self.weight_tolerance
        effective_min = min_w - tolerance
        effective_max = max_w + tolerance

        if effective_min <= weight <= effective_max:
            return True, f"重量{weight:.2f}kg在预期范围[{effective_min:.2f}, {effective_max:.2f}]kg内", (min_w, max_w)
        elif weight < effective_min:
            return False, f"重量{weight:.2f}kg低于预期范围[{effective_min:.2f}, {effective_max:.2f}]kg，可能为空箱或误检", (min_w, max_w)
        else:
            return False, f"重量{weight:.2f}kg高于预期范围[{effective_min:.2f}, {effective_max:.2f}]kg，可能超载或混装", (min_w, max_w)

    def fuse(self, visual_class: str, visual_confidence: float,
             sensors: List[SensorReading]) -> FusionResult:
        """
        执行多传感器融合决策

        参数:
            visual_class: 视觉识别的类别名称
            visual_confidence: 视觉识别置信度
            sensors: 传感器读数列表

        返回:
            FusionResult 融合判定结果
        """
        reasons = []
        visual_class_cn = CLASS_NAMES_CN.get(visual_class, visual_class)

        # 提取重量传感器数据
        weight_readings = [s for s in sensors if s.sensor_type == "weight"]
        infrared_readings = [s for s in sensors if s.sensor_type == "infrared"]

        # 检查红外到位信号
        object_present = True
        if infrared_readings:
            ir_value = infrared_readings[-1].value
            object_present = ir_value > 0.5  # 红外检测到物体
            if not object_present:
                reasons.append("红外传感器未检测到物体到位")

        # 重量校验
        weight_value = None
        weight_consistent = True
        expected_range = None
        sensor_confidence = 0.8  # 默认传感器可信度

        if weight_readings:
            raw_weight = weight_readings[-1].value
            self.add_weight_reading(raw_weight)
            weight_value = self.get_filtered_weight()
            sensor_confidence = weight_readings[-1].confidence

            weight_consistent, weight_reason, expected_range = self.check_weight_consistency(
                visual_class, weight_value
            )
            reasons.append(weight_reason)
        else:
            reasons.append("无重量传感器数据，跳过重量校验")

        # 加权融合计算总置信度
        total_confidence = (
            self.visual_weight * visual_confidence +
            self.sensor_weight * sensor_confidence
        )

        # 决策逻辑
        if not object_present:
            status = "reject"
            reasons.append("物体未到位，拒绝分拣")
        elif not weight_consistent and weight_value is not None:
            if visual_confidence > 0.85:
                status = "warning"
                reasons.append(f"视觉高置信度({visual_confidence:.2f})但重量不符，标记为警告送入复检区")
            else:
                status = "reject"
                reasons.append("视觉与重量数据不一致，拒绝分拣")
        elif total_confidence >= 0.75:
            status = "pass"
            reasons.append(f"融合置信度{total_confidence:.2f}≥0.75，通过校验")
        elif total_confidence >= 0.5:
            status = "warning"
            reasons.append(f"融合置信度{total_confidence:.2f}偏低，标记为警告")
        else:
            status = "reject"
            reasons.append(f"融合置信度{total_confidence:.2f}过低，拒绝分拣")

        return FusionResult(
            status=status,
            confidence=total_confidence,
            final_class=visual_class,
            final_class_cn=visual_class_cn,
            reasons=reasons,
            visual_confidence=visual_confidence,
            sensor_confidence=sensor_confidence,
            weight_value=weight_value,
            expected_weight_range=expected_range,
        )

    def simulate_sensors(self, class_name: str, anomaly: bool = False) -> List[SensorReading]:
        """
        模拟传感器数据（无硬件时用于演示）
        根据类别生成合理的重量和红外读数
        """
        sensors = []

        # 红外传感器：检测到物体
        sensors.append(SensorReading(
            sensor_type="infrared",
            sensor_id="IR-001",
            value=1.0,
            unit="digital",
            confidence=0.95
        ))

        # 重量传感器：基于类别理论范围生成
        if class_name in CLASS_WEIGHT_RANGE:
            min_w, max_w = CLASS_WEIGHT_RANGE[class_name]
            if anomaly:
                # 异常：重量超出范围
                weight = max_w * 1.5 if random.random() > 0.5 else min_w * 0.3
            else:
                weight = random.uniform(min_w * 0.9, max_w * 1.1)
        else:
            weight = random.uniform(1.0, 10.0)

        sensors.append(SensorReading(
            sensor_type="weight",
            sensor_id="W-001",
            value=round(weight, 2),
            unit="kg",
            confidence=0.92
        ))

        return sensors


# 全局融合引擎单例
_fusion_instance = None


def get_fusion_engine() -> MultiSensorFusion:
    """获取全局多传感器融合引擎实例"""
    global _fusion_instance
    if _fusion_instance is None:
        _fusion_instance = MultiSensorFusion()
    return _fusion_instance
