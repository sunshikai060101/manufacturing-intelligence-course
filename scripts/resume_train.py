"""
YOLOv8模型断点续训脚本
从last.pt恢复训练，不需要从头开始
使用方法: python scripts/resume_train.py
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

# 训练输出目录
RUN_DIR = BASE_DIR / "runs" / "detect" / "warehouse_yolov8n"
LAST_PT = RUN_DIR / "weights" / "last.pt"
BEST_PT = RUN_DIR / "weights" / "best.pt"


def main():
    print("=" * 60)
    print("YOLOv8 断点续训")
    print("=" * 60)

    # 检查检查点
    if not LAST_PT.exists():
        print(f"错误: 未找到检查点文件: {LAST_PT}")
        print("请先运行 train_yolo.py 进行初始训练")
        sys.exit(1)

    print(f"检查点文件: {LAST_PT}")
    print(f"文件大小: {LAST_PT.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"最后修改: {LAST_PT.stat().st_mtime}")

    # 检查数据集
    if not DATA_YAML.exists():
        print(f"错误: 数据集配置文件不存在: {DATA_YAML}")
        sys.exit(1)
    print(f"数据集配置: {DATA_YAML}")

    # 导入YOLO
    print("\n加载YOLOv8（从检查点恢复）...")
    from ultralytics import YOLO

    # 从last.pt加载模型（包含优化器状态、epoch等）
    model = YOLO(str(LAST_PT))
    print(f"模型已从检查点加载: {LAST_PT}")

    # 断点续训
    print("\n开始断点续训（resume=True）...")
    print("将从上次中断的epoch继续训练，直到完成20个epoch")

    results = model.train(
        resume=True,  # 关键：断点续训
    )

    print("\n" + "=" * 60)
    print("训练完成!")
    print("=" * 60)

    # 找到最佳模型
    if BEST_PT.exists():
        print(f"最佳模型: {BEST_PT}")
        print(f"文件大小: {BEST_PT.stat().st_size / 1024 / 1024:.2f} MB")
        # 复制到models目录
        target_path = MODELS_DIR / "best.pt"
        shutil.copy2(BEST_PT, target_path)
        print(f"已复制到: {target_path}")
        print("\n系统重启后将自动加载真实模型，检测精度将大幅提升!")
    else:
        print(f"警告: 未找到最佳模型 {BEST_PT}")
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
