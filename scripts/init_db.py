"""数据库初始化脚本 - 创建表并插入初始数据"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import init_db, SessionLocal
from backend.models import InventoryItem, SystemConfig
from backend.config import CLASS_NAMES, CLASS_NAMES_CN


def init_sample_data():
    """初始化示例数据"""
    db = SessionLocal()
    try:
        # 初始化库存类别
        for idx, class_name in enumerate(CLASS_NAMES):
            existing = db.query(InventoryItem).filter(
                InventoryItem.class_id == idx
            ).first()
            if not existing:
                item = InventoryItem(
                    class_id=idx,
                    class_name=class_name,
                    quantity=0,
                    location=f"A-{idx:02d}",
                    description=CLASS_NAMES_CN.get(class_name, class_name),
                    min_stock=10,
                    max_stock=1000,
                )
                db.add(item)

        # 初始化系统配置
        configs = [
            ("confidence_threshold", "0.5", "目标检测置信度阈值"),
            ("iou_threshold", "0.45", "NMS IOU阈值"),
            ("fusion_visual_weight", "0.6", "多传感器融合-视觉权重"),
            ("fusion_sensor_weight", "0.4", "多传感器融合-传感器权重"),
            ("anomaly_mild_threshold", "0.4", "异常检测-轻度阈值"),
            ("anomaly_severe_threshold", "0.7", "异常检测-严重阈值"),
        ]
        for key, value, desc in configs:
            existing = db.query(SystemConfig).filter(
                SystemConfig.config_key == key
            ).first()
            if not existing:
                config = SystemConfig(
                    config_key=key,
                    config_value=value,
                    description=desc,
                )
                db.add(config)

        db.commit()
        print("示例数据初始化完成")
    except Exception as e:
        db.rollback()
        print(f"初始化失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("初始化数据库...")
    init_db()
    print("数据库表创建完成")
    init_sample_data()
    print("数据库初始化完成!")
