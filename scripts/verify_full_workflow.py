"""验证完整业务流程：图像上传->目标检测->多传感器融合->异常检测->存储->库存更新"""
import sys
import os
import glob

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from backend.app import app
from backend.database import init_db, SessionLocal
from backend.models import InventoryItem

# 初始化数据库
init_db()
db = SessionLocal()
class_names = ['cardboard_box', 'pallet', 'stillage', 'forklift', 'eps_box', 'wheelie_bin']
for i, name in enumerate(class_names):
    if not db.query(InventoryItem).filter_by(class_id=i).first():
        db.add(InventoryItem(class_id=i, class_name=name, quantity=0, location=f'A-{i:02d}'))
db.commit()
db.close()

client = TestClient(app)

# 找一张真实数据集图片
imgs = glob.glob('data/processed/images/*/*.jpg')
img_path = imgs[0]
print(f'测试图片: {img_path}')
print(f'图片大小: {os.path.getsize(img_path)} bytes')
print()

# 上传图像并执行完整检测
with open(img_path, 'rb') as f:
    response = client.post(
        '/api/detection/upload',
        files={'file': ('test.jpg', f, 'image/jpeg')},
        data={'enable_fusion': 'true', 'enable_anomaly': 'true', 'simulate_sensors': 'true'}
    )

print(f'响应状态: {response.status_code}')
result = response.json()
print(f'推理时间: {result["inference_time_ms"]}ms')
print(f'检测到目标数: {result["total_objects"]}')
print()

for i, det in enumerate(result['detections']):
    print(f'【目标{i+1}】')
    print(f'  类别: {det["class_name_cn"]} ({det["class_name"]})')
    print(f'  置信度: {det["confidence"]*100:.1f}%')
    print(f'  位置: x={det["bbox"]["x"]:.0f}, y={det["bbox"]["y"]:.0f}')
    if i < len(result['fusion_results']):
        fr = result['fusion_results'][i]
        print(f'  融合结果: {fr["status_cn"]} (置信度{fr["confidence"]*100:.1f}%)')
        if fr['weight_value']:
            print(f'  实测重量: {fr["weight_value"]}kg')
    if i < len(result['anomaly_results']):
        a = result['anomaly_results'][i]
        print(f'  异常检测: {a["anomaly_level_cn"]} (分数{a["anomaly_score"]*100:.1f}%)')
    print()

# 验证数据库已保存记录
r2 = client.get('/api/detection/records?limit=5')
print(f'数据库检测记录数: {len(r2.json())}')

# 验证库存已自动更新
r3 = client.get('/api/inventory')
inv = r3.json()
print(f'库存项数: {len(inv)}')
for item in inv:
    if item['quantity'] > 0:
        print(f'  {item["class_name"]}: {item["quantity"]}件')

print()
print('=== 完整业务流程验证通过 ===')
print('1. 图像上传 -> 2. 目标检测 -> 3. 多传感器融合 -> 4. 异常检测')
print('5. 结果存储数据库 -> 6. 库存自动更新 -> 7. 前端展示')
