"""
数据集准备脚本
从SORDI工业数据集中抽取仓储相关类别子集，将JSON标签转换为YOLO格式，
并按7:2:1划分训练集、验证集、测试集。
"""
import os
import sys
import json
import zipfile
import random
import shutil
from pathlib import Path
from collections import defaultdict

# 配置
ZIP_PATH = r"C:\Users\ssk28\Desktop\archive.zip"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "processed"
IMAGES_DIR = OUTPUT_DIR / "images"
LABELS_DIR = OUTPUT_DIR / "labels"

# 选择的仓储物料类别（YOLO class_id 从0开始）
SELECTED_CLASSES = {
    "cardboard_box": 0,   # 纸箱
    "pallet": 1,           # 托盘
    "stillage": 2,         # 料架/笼车
    "forklift": 3,         # 叉车
    "eps_box": 4,          # 泡沫箱
    "wheelie_bin": 5,      # 滚轮料箱
}

# 每类抽取的图片数量
SAMPLES_PER_CLASS = 400

# 数据集划分比例
TRAIN_RATIO = 0.7
VAL_RATIO = 0.2
TEST_RATIO = 0.1

# 图像尺寸（用于坐标归一化）
IMG_WIDTH = 1280
IMG_HEIGHT = 720

random.seed(42)


def get_image_size_from_zip(zf, image_path):
    """从zip中读取图片尺寸"""
    try:
        from PIL import Image
        import io
        with zf.open(image_path) as f:
            img = Image.open(io.BytesIO(f.read()))
            return img.size  # (width, height)
    except Exception:
        return IMG_WIDTH, IMG_HEIGHT


def json_to_yolo(json_data, img_width, img_height):
    """将JSON标签转换为YOLO格式行列表"""
    yolo_lines = []
    for obj in json_data:
        class_name = obj.get("ObjectClassName", "")
        if class_name not in SELECTED_CLASSES:
            continue
        class_id = SELECTED_CLASSES[class_name]
        left = obj.get("Left", 0)
        top = obj.get("Top", 0)
        right = obj.get("Right", 0)
        bottom = obj.get("Bottom", 0)

        # 边界检查
        left = max(0, min(left, img_width))
        right = max(0, min(right, img_width))
        top = max(0, min(top, img_height))
        bottom = max(0, min(bottom, img_height))

        if right <= left or bottom <= top:
            continue

        # 转换为YOLO归一化格式
        x_center = ((left + right) / 2) / img_width
        y_center = ((top + bottom) / 2) / img_height
        width = (right - left) / img_width
        height = (bottom - top) / img_height

        # 确保在0-1范围内
        x_center = max(0, min(1, x_center))
        y_center = max(0, min(1, y_center))
        width = max(0, min(1, width))
        height = max(0, min(1, height))

        yolo_lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

    return yolo_lines


def main():
    print("=" * 60)
    print("数据集准备：SORDI工业数据集 -> 仓储物料YOLO数据集")
    print("=" * 60)

    # 创建输出目录
    for split in ["train", "val", "test"]:
        (IMAGES_DIR / split).mkdir(parents=True, exist_ok=True)
        (LABELS_DIR / split).mkdir(parents=True, exist_ok=True)

    # 第一步：扫描zip，建立类别到图片的映射
    print("\n[1/4] 扫描数据集，建立类别索引...")
    class_to_images = defaultdict(list)

    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        all_files = zf.namelist()
        label_files = [f for f in all_files if f.endswith(".json") and "labels/json/" in f]
        print(f"  总标签文件数: {len(label_files)}")

        for i, lf in enumerate(label_files):
            try:
                content = zf.read(lf)
                data = json.loads(content)
                img_name = Path(lf).stem  # 如 "0"
                dataset_prefix = lf.split("/")[0]  # DR-1 或 DR-2

                # 检查图片是否存在
                img_path_in_zip = f"{dataset_prefix}/images/{img_name}.jpg"
                if img_path_in_zip not in all_files:
                    continue

                # 统计该图片包含的目标类别
                classes_in_img = set()
                for obj in data:
                    cname = obj.get("ObjectClassName", "")
                    if cname in SELECTED_CLASSES:
                        classes_in_img.add(cname)

                for cname in classes_in_img:
                    class_to_images[cname].append((dataset_prefix, img_name, img_path_in_zip, lf))

            except Exception as e:
                continue

            if (i + 1) % 10000 == 0:
                print(f"  已扫描 {i+1}/{len(label_files)}...")

    print("\n  各类别可用图片数:")
    for cname, cid in sorted(SELECTED_CLASSES.items(), key=lambda x: x[1]):
        print(f"    [{cid}] {cname}: {len(class_to_images.get(cname, []))} 张")

    # 第二步：抽样选择图片
    print("\n[2/4] 按类别抽样...")
    selected_images = {}  # key: (dataset_prefix, img_name) -> (img_path, label_path)

    for cname, cid in SELECTED_CLASSES.items():
        candidates = class_to_images.get(cname, [])
        random.shuffle(candidates)
        selected = candidates[:SAMPLES_PER_CLASS]
        for dataset_prefix, img_name, img_path, label_path in selected:
            key = (dataset_prefix, img_name)
            if key not in selected_images:
                selected_images[key] = (img_path, label_path)
        print(f"  {cname}: 选择 {len(selected)} 张")

    print(f"  去重后总图片数: {len(selected_images)}")

    # 第三步：转换标签并复制图片
    print("\n[3/4] 转换标签格式并提取图片...")
    all_samples = []  # (img_filename, label_filename, has_objects)

    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        for idx, ((dataset_prefix, img_name), (img_path, label_path)) in enumerate(selected_images.items()):
            try:
                # 读取JSON标签
                content = zf.read(label_path)
                data = json.loads(content)

                # 获取图片实际尺寸
                img_width, img_height = get_image_size_from_zip(zf, img_path)

                # 转换为YOLO格式
                yolo_lines = json_to_yolo(data, img_width, img_height)

                if not yolo_lines:
                    continue

                # 新文件名（避免冲突）
                new_name = f"{dataset_prefix}_{img_name}"
                img_filename = f"{new_name}.jpg"
                label_filename = f"{new_name}.txt"

                # 提取图片到临时目录
                temp_img_path = IMAGES_DIR / img_filename
                with zf.open(img_path) as src, open(temp_img_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)

                # 写入YOLO标签
                temp_label_path = LABELS_DIR / label_filename
                with open(temp_label_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(yolo_lines) + "\n")

                all_samples.append((img_filename, label_filename))

            except Exception as e:
                print(f"  处理失败 {img_name}: {e}")
                continue

            if (idx + 1) % 500 == 0:
                print(f"  已处理 {idx+1}/{len(selected_images)}...")

    print(f"  成功处理: {len(all_samples)} 张")

    # 第四步：划分数据集
    print("\n[4/4] 划分训练集/验证集/测试集...")
    random.shuffle(all_samples)
    total = len(all_samples)
    train_end = int(total * TRAIN_RATIO)
    val_end = train_end + int(total * VAL_RATIO)

    splits = {
        "train": all_samples[:train_end],
        "val": all_samples[train_end:val_end],
        "test": all_samples[val_end:],
    }

    for split_name, samples in splits.items():
        split_img_dir = IMAGES_DIR / split_name
        split_label_dir = LABELS_DIR / split_name

        for img_filename, label_filename in samples:
            # 移动图片
            src_img = IMAGES_DIR / img_filename
            dst_img = split_img_dir / img_filename
            if src_img.exists():
                shutil.move(str(src_img), str(dst_img))

            # 移动标签
            src_label = LABELS_DIR / label_filename
            dst_label = split_label_dir / label_filename
            if src_label.exists():
                shutil.move(str(src_label), str(dst_label))

        print(f"  {split_name}: {len(samples)} 张")

    # 生成data.yaml
    yaml_path = OUTPUT_DIR / "data.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(f"path: {OUTPUT_DIR.absolute()}\n")
        f.write(f"train: images/train\n")
        f.write(f"val: images/val\n")
        f.write(f"test: images/test\n\n")
        f.write(f"names:\n")
        for cname, cid in sorted(SELECTED_CLASSES.items(), key=lambda x: x[1]):
            f.write(f"  {cid}: {cname}\n")

    # 生成类别名称文件
    classes_path = OUTPUT_DIR / "classes.txt"
    with open(classes_path, "w", encoding="utf-8") as f:
        for cname, cid in sorted(SELECTED_CLASSES.items(), key=lambda x: x[1]):
            f.write(f"{cname}\n")

    # 生成数据集索引CSV
    import csv
    index_path = OUTPUT_DIR / "dataset_index.csv"
    with open(index_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["split", "image_file", "label_file", "class_ids"])
        for split_name, samples in splits.items():
            for img_filename, label_filename in samples:
                label_path = LABELS_DIR / split_name / label_filename
                class_ids = set()
                if label_path.exists():
                    with open(label_path, "r") as lf:
                        for line in lf:
                            if line.strip():
                                class_ids.add(line.split()[0])
                writer.writerow([split_name, img_filename, label_filename, ";".join(sorted(class_ids))])

    print("\n" + "=" * 60)
    print("数据集准备完成!")
    print("=" * 60)
    print(f"  输出目录: {OUTPUT_DIR}")
    print(f"  类别数: {len(SELECTED_CLASSES)}")
    print(f"  总样本数: {len(all_samples)}")
    print(f"  训练集: {len(splits['train'])}")
    print(f"  验证集: {len(splits['val'])}")
    print(f"  测试集: {len(splits['test'])}")
    print(f"  配置文件: {yaml_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
