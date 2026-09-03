"""系统配置模块"""
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent.parent

# 数据目录
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
DATABASE_DIR = DATA_DIR / "database"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

# 数据库配置
DATABASE_URL = f"sqlite:///{DATABASE_DIR / 'warehouse.db'}"

# 模型配置
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_MODEL_PATH = MODEL_DIR / "best.pt"

# 检测类别（与数据集一致）
CLASS_NAMES = [
    "cardboard_box",   # 0: 纸箱
    "pallet",          # 1: 托盘
    "stillage",        # 2: 料架
    "forklift",        # 3: 叉车
    "eps_box",         # 4: 泡沫箱
    "wheelie_bin",     # 5: 滚轮料箱
]

CLASS_NAMES_CN = {
    "cardboard_box": "纸箱",
    "pallet": "托盘",
    "stillage": "料架",
    "forklift": "叉车",
    "eps_box": "泡沫箱",
    "wheelie_bin": "滚轮料箱",
}

# 各类物料理论重量范围（kg），用于多传感器融合校验
CLASS_WEIGHT_RANGE = {
    "cardboard_box": (0.5, 25.0),
    "pallet": (15.0, 30.0),
    "stillage": (30.0, 80.0),
    "forklift": (1000.0, 5000.0),
    "eps_box": (0.2, 5.0),
    "wheelie_bin": (5.0, 25.0),
}

# 检测参数
DEFAULT_CONFIDENCE_THRESHOLD = 0.5
DEFAULT_IOU_THRESHOLD = 0.45
TARGET_IMAGE_SIZE = 640

# 上传文件保存目录
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 传感器模拟参数
SENSOR_SAMPLING_RATE = 10  # Hz
