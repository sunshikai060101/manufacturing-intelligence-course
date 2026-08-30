import os
import csv
import random
from PIL import Image

# 目录配置
RAW_DIR = "../原始"
PROCESSED_DIR = "."
IMAGE_DIR = os.path.join(PROCESSED_DIR, "images")
LABEL_DIR = os.path.join(PROCESSED_DIR, "labels")
INDEX_FILE = os.path.join(PROCESSED_DIR, "processed_index.csv")
CLASSES_FILE = os.path.join(PROCESSED_DIR, "classes.txt")

# 数据集划分比例
TRAIN_RATIO = 0.7
VAL_RATIO = 0.2
TEST_RATIO = 0.1

# 支持的图像格式
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


def load_classes():
    """加载类别定义"""
    classes = []
    if os.path.exists(CLASSES_FILE):
        with open(CLASSES_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    classes.append(line)
    return classes


def is_image_file(filename):
    """判断是否为图像文件"""
    return filename.lower().endswith(IMAGE_EXTENSIONS)


def check_image(image_path):
    """检查图像是否能正常读取"""
    try:
        with Image.open(image_path) as img:
            img.verify()
        return True
    except Exception:
        return False


def convert_image(image_path, output_path):
    """统一图像格式为JPG"""
    try:
        with Image.open(image_path) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(output_path, "JPEG", quality=95)
        return True
    except Exception as e:
        print(f"转换失败 {image_path}: {e}")
        return False


def find_label_file(image_name, raw_dir):
    """查找对应的标注文件"""
    base_name = os.path.splitext(image_name)[0]
    for ext in (".txt",):
        label_path = os.path.join(raw_dir, base_name + ext)
        if os.path.exists(label_path):
            return label_path
    return None


def split_dataset(image_list):
    """划分训练集、验证集、测试集"""
    random.shuffle(image_list)
    total = len(image_list)
    train_end = int(total * TRAIN_RATIO)
    val_end = train_end + int(total * VAL_RATIO)

    train_set = image_list[:train_end]
    val_set = image_list[train_end:val_end]
    test_set = image_list[val_end:]

    return train_set, val_set, test_set


def generate_index(processed_data, index_file):
    """生成数据索引CSV文件"""
    with open(index_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["image_path", "label_path", "split", "status"])
        for item in processed_data:
            writer.writerow([
                item["image_path"],
                item["label_path"],
                item["split"],
                item["status"]
            ])


def main():
    print("=" * 50)
    print("数据预处理程序启动")
    print("=" * 50)

    # 加载类别
    classes = load_classes()
    print(f"加载类别: {classes}")

    # 创建输出目录
    os.makedirs(IMAGE_DIR, exist_ok=True)
    os.makedirs(LABEL_DIR, exist_ok=True)

    # 扫描原始数据目录
    raw_images = []
    if os.path.exists(RAW_DIR):
        for filename in os.listdir(RAW_DIR):
            if is_image_file(filename):
                raw_images.append(filename)
    print(f"扫描到原始图像: {len(raw_images)} 张")

    # 处理每张图像
    processed_data = []
    valid_count = 0
    invalid_count = 0

    for idx, image_name in enumerate(raw_images, 1):
        raw_image_path = os.path.join(RAW_DIR, image_name)
        base_name = os.path.splitext(image_name)[0]
        output_image_name = f"{base_name}.jpg"
        output_image_path = os.path.join(IMAGE_DIR, output_image_name)

        print(f"处理中 [{idx}/{len(raw_images)}]: {image_name}")

        # 检查图像有效性
        if not check_image(raw_image_path):
            print(f"  图像无效，跳过: {image_name}")
            invalid_count += 1
            processed_data.append({
                "image_path": f"images/{output_image_name}",
                "label_path": "",
                "split": "unused",
                "status": "invalid"
            })
            continue

        # 转换图像格式
        if convert_image(raw_image_path, output_image_path):
            valid_count += 1
        else:
            invalid_count += 1
            processed_data.append({
                "image_path": f"images/{output_image_name}",
                "label_path": "",
                "split": "unused",
                "status": "convert_failed"
            })
            continue

        # 查找标注文件
        label_path = find_label_file(image_name, RAW_DIR)
        label_output_path = ""
        if label_path:
            label_output_name = f"{base_name}.txt"
            label_output_path = os.path.join(LABEL_DIR, label_output_name)
            import shutil
            shutil.copy2(label_path, label_output_path)

        processed_data.append({
            "image_path": f"images/{output_image_name}",
            "label_path": f"labels/{base_name}.txt" if label_path else "",
            "split": "pending",
            "status": "processed"
        })

    # 划分数据集
    valid_items = [item for item in processed_data if item["status"] == "processed"]
    train_set, val_set, test_set = split_dataset(valid_items)

    for item in train_set:
        item["split"] = "train"
    for item in val_set:
        item["split"] = "val"
    for item in test_set:
        item["split"] = "test"

    # 生成索引文件
    generate_index(processed_data, INDEX_FILE)

    # 输出统计信息
    print("\n" + "=" * 50)
    print("预处理完成")
    print("=" * 50)
    print(f"总图像数: {len(raw_images)}")
    print(f"有效图像: {valid_count}")
    print(f"无效图像: {invalid_count}")
    print(f"训练集: {len(train_set)} 张")
    print(f"验证集: {len(val_set)} 张")
    print(f"测试集: {len(test_set)} 张")
    print(f"索引文件: {INDEX_FILE}")
    print("=" * 50)


if __name__ == "__main__":
    main()
