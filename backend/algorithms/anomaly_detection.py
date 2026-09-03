"""
算法模块三：基于统计学习的异常检测
技术方向：工业数据分析与异常检测（统计过程控制SPC + 孤立森林思想）

功能：
1. 基于历史检测数据建立正常行为基线
2. 多维度异常评分（置信度异常、尺寸异常、频率异常、重量异常）
3. 滑动窗口统计分析（均值、标准差、Z-Score）
4. 异常原因诊断与分类
5. 实时异常预警
"""
import time
import math
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

from backend.config import CLASS_NAMES


@dataclass
class AnomalyResult:
    """异常检测结果"""
    is_anomaly: bool
    anomaly_score: float  # 0-1，越高越异常
    anomaly_level: str  # normal / mild / severe
    reasons: List[str] = field(default_factory=list)
    dimension_scores: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "is_anomaly": self.is_anomaly,
            "anomaly_score": round(self.anomaly_score, 4),
            "anomaly_level": self.anomaly_level,
            "anomaly_level_cn": {
                "normal": "正常",
                "mild": "轻度异常",
                "severe": "严重异常"
            }.get(self.anomaly_level, self.anomaly_level),
            "reasons": self.reasons,
            "dimension_scores": {k: round(v, 4) for k, v in self.dimension_scores.items()},
        }


class AnomalyDetector:
    """异常检测器"""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        # 每个类别的历史数据滑动窗口
        self.history = defaultdict(lambda: deque(maxlen=window_size))
        # 全局统计
        self.global_confidence_history = deque(maxlen=500)
        self.global_detection_count = 0
        self.last_detection_time = None
        # 异常阈值
        self.mild_threshold = 0.4
        self.severe_threshold = 0.7
        # Z-Score阈值
        self.zscore_warning = 2.0
        self.zscore_critical = 3.0

    def update_history(self, class_name: str, confidence: float,
                       bbox_size: float, weight: Optional[float] = None):
        """更新历史数据窗口"""
        record = {
            "confidence": confidence,
            "bbox_size": bbox_size,
            "weight": weight,
            "timestamp": time.time(),
        }
        self.history[class_name].append(record)
        self.global_confidence_history.append(confidence)
        self.global_detection_count += 1
        self.last_detection_time = time.time()

    def _calculate_zscore(self, value: float, history: List[float]) -> float:
        """计算Z-Score"""
        if len(history) < 5:
            return 0.0
        mean = sum(history) / len(history)
        variance = sum((x - mean) ** 2 for x in history) / len(history)
        std = math.sqrt(variance)
        if std == 0:
            return 0.0
        return abs((value - mean) / std)

    def _confidence_anomaly_score(self, class_name: str, confidence: float) -> Tuple[float, str]:
        """
        维度1：置信度异常检测
        置信度突然降低可能意味着图像质量差、遮挡或新类别出现
        """
        history = [r["confidence"] for r in self.history[class_name]]
        if not history:
            # 使用全局历史
            history = list(self.global_confidence_history)

        if len(history) < 10:
            # 数据不足，低置信度本身不算异常
            if confidence < 0.5:
                return 0.3, f"置信度{confidence:.2f}偏低，但历史数据不足"
            return 0.0, ""

        zscore = self._calculate_zscore(confidence, history)
        mean_conf = sum(history) / len(history)

        if confidence < 0.5:
            score = min(1.0, 0.5 + (0.5 - confidence))
            return score, f"置信度{confidence:.2f}显著低于正常水平(均值{mean_conf:.2f})"
        elif zscore > self.zscore_critical:
            return 0.8, f"置信度Z-Score={zscore:.2f}超过临界值{self.zscore_critical}"
        elif zscore > self.zscore_warning:
            return 0.4, f"置信度Z-Score={zscore:.2f}超过警告值{self.zscore_warning}"

        return 0.0, ""

    def _size_anomaly_score(self, class_name: str, bbox_size: float) -> Tuple[float, str]:
        """
        维度2：目标尺寸异常检测
        检测框尺寸异常可能意味着远距离小目标、近距离大目标或误检
        """
        history = [r["bbox_size"] for r in self.history[class_name] if r["bbox_size"] > 0]
        if len(history) < 10:
            return 0.0, ""

        zscore = self._calculate_zscore(bbox_size, history)
        mean_size = sum(history) / len(history)

        if zscore > self.zscore_critical:
            return 0.75, f"目标尺寸Z-Score={zscore:.2f}异常(均值{mean_size:.1f})"
        elif zscore > self.zscore_warning:
            return 0.35, f"目标尺寸Z-Score={zscore:.2f}偏离正常范围"

        return 0.0, ""

    def _frequency_anomaly_score(self) -> Tuple[float, str]:
        """
        维度3：检测频率异常检测
        单位时间内检测次数异常可能意味着传感器故障或重复检测
        """
        if self.last_detection_time is None:
            return 0.0, ""

        time_since_last = time.time() - self.last_detection_time

        # 极短时间内重复检测（<0.1秒）
        if time_since_last < 0.1:
            return 0.6, f"检测间隔{time_since_last*1000:.0f}ms过短，可能重复触发"
        elif time_since_last < 0.3:
            return 0.25, f"检测间隔{time_since_last*1000:.0f}ms偏短"

        return 0.0, ""

    def _weight_anomaly_score(self, class_name: str, weight: Optional[float]) -> Tuple[float, str]:
        """
        维度4：重量异常检测
        基于历史重量数据的统计异常
        """
        if weight is None:
            return 0.0, ""

        history = [r["weight"] for r in self.history[class_name] if r["weight"] is not None]
        if len(history) < 10:
            return 0.0, ""

        zscore = self._calculate_zscore(weight, history)
        mean_weight = sum(history) / len(history)

        if zscore > self.zscore_critical:
            return 0.8, f"重量Z-Score={zscore:.2f}严重异常(均值{mean_weight:.2f}kg)"
        elif zscore > self.zscore_warning:
            return 0.4, f"重量Z-Score={zscore:.2f}偏离正常范围"

        return 0.0, ""

    def detect(self, class_name: str, confidence: float,
               bbox_w: float, bbox_h: float,
               weight: Optional[float] = None) -> AnomalyResult:
        """
        执行多维度异常检测

        参数:
            class_name: 识别类别
            confidence: 识别置信度
            bbox_w: 检测框宽度（像素）
            bbox_h: 检测框高度（像素）
            weight: 重量（kg，可选）

        返回:
            AnomalyResult 异常检测结果
        """
        bbox_size = bbox_w * bbox_h
        reasons = []
        dimension_scores = {}

        # 维度1：置信度异常
        conf_score, conf_reason = self._confidence_anomaly_score(class_name, confidence)
        dimension_scores["confidence"] = conf_score
        if conf_reason:
            reasons.append(conf_reason)

        # 维度2：尺寸异常
        size_score, size_reason = self._size_anomaly_score(class_name, bbox_size)
        dimension_scores["size"] = size_score
        if size_reason:
            reasons.append(size_reason)

        # 维度3：频率异常
        freq_score, freq_reason = self._frequency_anomaly_score()
        dimension_scores["frequency"] = freq_score
        if freq_reason:
            reasons.append(freq_reason)

        # 维度4：重量异常
        weight_score, weight_reason = self._weight_anomaly_score(class_name, weight)
        dimension_scores["weight"] = weight_score
        if weight_reason:
            reasons.append(weight_reason)

        # 综合异常评分（加权平均）
        weights = {"confidence": 0.35, "size": 0.25, "frequency": 0.15, "weight": 0.25}
        total_score = sum(dimension_scores[k] * weights[k] for k in weights)

        # 判定异常等级
        if total_score >= self.severe_threshold:
            level = "severe"
            is_anomaly = True
        elif total_score >= self.mild_threshold:
            level = "mild"
            is_anomaly = True
        else:
            level = "normal"
            is_anomaly = False

        if not reasons:
            reasons.append("各维度指标均在正常范围内")

        # 更新历史数据
        self.update_history(class_name, confidence, bbox_size, weight)

        return AnomalyResult(
            is_anomaly=is_anomaly,
            anomaly_score=total_score,
            anomaly_level=level,
            reasons=reasons,
            dimension_scores=dimension_scores,
        )

    def get_statistics(self) -> Dict:
        """获取检测器统计信息"""
        class_stats = {}
        for class_name, records in self.history.items():
            if not records:
                continue
            confs = [r["confidence"] for r in records]
            class_stats[class_name] = {
                "sample_count": len(records),
                "mean_confidence": round(sum(confs) / len(confs), 4),
                "min_confidence": round(min(confs), 4),
                "max_confidence": round(max(confs), 4),
            }

        return {
            "total_detections": self.global_detection_count,
            "window_size": self.window_size,
            "class_statistics": class_stats,
            "mild_threshold": self.mild_threshold,
            "severe_threshold": self.severe_threshold,
        }


# 全局异常检测器单例
_anomaly_instance = None


def get_anomaly_detector() -> AnomalyDetector:
    """获取全局异常检测器实例"""
    global _anomaly_instance
    if _anomaly_instance is None:
        _anomaly_instance = AnomalyDetector()
    return _anomaly_instance
