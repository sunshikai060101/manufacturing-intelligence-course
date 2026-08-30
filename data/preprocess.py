import os
import csv
from PIL import Image


# 原始数据目录
RAW_DIR = "raw"

# 预处理数据目录
PROCESSED_DIR = "processed"

# 索引文件
INDEX_FILE = "processed_index.csv"


def is_image_file(filename):
    """判断文件是否为常见图像格式"""
    return filename.lower().endswith(
        (".jpg", ".jpeg", ".png", ".bmp", ".webp")
    )


def check_image(image_path):
    """检查图像是否能够正常读取"""
    try:
        with Image.open(image_path) as img:
            img.verify()
        return True
    except Exception:
        return False


def build_index():
    """扫描数据集并建立数据索引"""

    records = []

    if not os.path.exists(RAW_DIR):
        print("未找到 raw 数据目录，请先准备原始数据。")
        return

    for root, _, files in os.walk(RAW_DIR):

        for filename in files:

            if not is_image_file(filename):
                continue

            image_path = os.path.join(root, filename)

            status = "valid" if check_image(image_path) else "invalid"

            # 根据文件路径确定数据划分
            lower_path = image_path.lower()

            if "train" in lower_path:
                split = "train"
            elif "val" in lower_path or "valid" in lower_path:
                split = "val"
            elif "test" in lower_path:
                split = "test"
            else:
                split = "unknown"

            # 查找对应标注文件
            label_path = ""

            base_name = os.path.splitext(image_path)[0]

            for ext in [".txt", ".xml", ".json"]:
                possible_label = base_name + ext

                if os.path.exists(possible_label):
                    label_path = possible_label
                    break

            records.append([
                image_path,
                label_path,
                split,
                status
            ])

    with open(
        INDEX_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.writer(f)

        writer.writerow([
            "image_path",
            "label_path",
            "split",
            "status"
        ])

        writer.writerows(records)

    print("数据索引建立完成。")
    print("共发现图像：", len(records))


if __name__ == "__main__":
    build_index()
