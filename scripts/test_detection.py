"""测试图像上传检测功能"""
import sys
import os
import glob

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)

# 找一张处理后的图片
imgs = glob.glob('data/processed/images/*/*.jpg')
if not imgs:
    print('没有找到处理后的图片')
    sys.exit(1)

img_path = imgs[0]
print(f'使用测试图片: {img_path}')
print(f'图片大小: {os.path.getsize(img_path)} bytes')

with open(img_path, 'rb') as f:
    response = client.post(
        '/api/detection/upload',
        files={'file': ('test_image.jpg', f, 'image/jpeg')},
        data={
            'enable_fusion': 'true',
            'enable_anomaly': 'true',
            'simulate_sensors': 'true',
        }
    )

print(f'响应状态: {response.status_code}')
if response.status_code == 200:
    result = response.json()
    print(f'检测到目标数: {result["total_objects"]}')
    print(f'推理时间: {result["inference_time_ms"]}ms')
    for i, det in enumerate(result['detections']):
        print(f'  目标{i+1}: {det["class_name_cn"]} ({det["class_name"]}), 置信度: {det["confidence"]*100:.1f}%')
    for i, fr in enumerate(result.get('fusion_results', [])):
        print(f'  融合{i+1}: {fr["status_cn"]}, 置信度: {fr["confidence"]*100:.1f}%')
    for i, a in enumerate(result.get('anomaly_results', [])):
        print(f'  异常{i+1}: {a["anomaly_level_cn"]}, 分数: {a["anomaly_score"]*100:.1f}%')
    print()
    print('图像上传检测功能测试通过!')
else:
    print(f'错误: {response.text}')
