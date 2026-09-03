"""
YOLOv8模型训练脚本（简化版）
基于SORDI数据集6类仓储物料，迁移学习训练
"""
import os
import sys
import shutil
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent.parent
DATA_YAML = BASE_DIR / "data" / "processed" / "data.yaml"
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

def main():
    print("=" * 60)
    print("YOLOv8 仓储物料检测模型训练")
    print("=" * 60)

    # 检查数据集
    if not DATA_YAML.exists():
        print(f"错误: 数据集配置文件不存在: {DATA_YAML}")
        sys.exit(1)
    print(f"数据集配置: {DATA_YAML}")

    # 统计数据集
    train_dir = DATA_YAML.parent / "images" / "train"
    val_dir = DATA_YAML.parent / "images" / "val"
    test_dir = DATA_YAML.parent / "images" / "test"
    train_count = len(list(train_dir.glob("*.jpg"))) if train_dir.exists() else 0
    val_count = len(list(val_dir.glob("*.jpg"))) if val_dir.exists() else 0
    test_count = len(list(test_dir.glob("*.jpg"))) if test_dir.exists() else 0
    print(f"训练集: {train_count} 张")
    print(f"验证集: {val_count} 张")
    print(f"测试集: {test_count} 张")
    print(f"类别数: 6 (纸箱/托盘/料架/叉车/泡沫箱/滚轮料箱)")

    # 导入YOLO
    print("\n加载YOLOv8...")
    from ultralytics import YOLO

    # 使用本地预训练权重
    local_weights = BASE_DIR / "yolov8n.pt"
    if local_weights.exists():
        model = YOLO(str(local_weights))
        print(f"模型: YOLOv8n (nano)")
        print(f"预训练权重: {local_weights}")
    else:
        model = YOLO("yolov8n.pt")
        print("模型: YOLOv8n (自动下载)")

    # 训练（只传核心参数）
    print("\n开始训练...")
    print("参数: epochs=20, imgsz=640, batch=16")

    results = model.train(
        data=str(DATA_YAML),
        epochs=20,
        imgsz=640,
        batch=16,
        device="cpu",
        pretrained=True,
        name="warehouse_yolov8n",
        exist_ok=True,
        plots=True,
        save=True,
        val=True,
    )

    print("\n" + "=" * 60)
    print("训练完成!")
    print("=" * 60)

    # 找到最佳模型
    run_dir = Path("runs/detect/warehouse_yolov8n")
    best_pt = run_dir / "weights" / "best.pt"

    if best_pt.exists():
        print(f"最佳模型: {best_pt}")
        # 复制到models目录
        target_path = MODELS_DIR / "best.pt"
        shutil.copy2(best_pt, target_path)
        print(f"已复制到: {target_path}")
        print("\n系统重启后将自动加载真实模型，检测精度将大幅提升!")
    else:
        print(f"警告: 未找到最佳模型 {best_pt}")
        # 尝试查找其他位置
        for pt in Path("runs").rglob("best.pt"):
            print(f"找到: {pt}")
            shutil.copy2(pt, MODELS_DIR / "best.pt")
            print(f"已复制到: {MODELS_DIR / 'best.pt'}")
            break

    # 打印最终指标
    print("\n最终验证指标:")
    try:
        results_dict = results.results_dict
        for k, v in results_dict.items():
            print(f"  {k}: {v:.4f}")
    except Exception as e:
        print(f"  无法获取指标: {e}")

if __name__ == "__main__":
    main()
