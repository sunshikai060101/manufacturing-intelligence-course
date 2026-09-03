"""
录制2分钟系统演示视频（无声，后期配音）
自动操作浏览器展示系统各功能模块
"""
import time
import glob
import os
import sys
import numpy as np
import cv2
import mss
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 配置
BASE_URL = "http://127.0.0.1:8000"
OUTPUT_VIDEO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo_video.mp4")
FPS = 20
DURATION = 120  # 2分钟
TOTAL_FRAMES = FPS * DURATION

# 找一张测试图片
test_images = glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "processed", "images", "test", "*.jpg"))
TEST_IMAGE = test_images[0] if test_images else None
print(f"测试图片: {TEST_IMAGE}")

def navigate_to(driver, page_name):
    """点击侧边栏导航切换页面"""
    try:
        nav = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f'.nav-item[data-page="{page_name}"]'))
        )
        nav.click()
        time.sleep(1.5)
    except Exception as e:
        print(f"导航到 {page_name} 失败: {e}")

def main():
    # 启动Edge
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    driver = webdriver.Edge(options=options)
    driver.get(BASE_URL)
    time.sleep(3)
    
    # 初始化录屏
    sct = mss.mss()
    monitor = sct.monitors[1]  # 主显示器
    width = monitor["width"]
    height = monitor["height"]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(OUTPUT_VIDEO, fourcc, FPS, (width, height))
    
    print(f"开始录屏: {width}x{height}, {FPS}fps, {DURATION}秒")
    print(f"输出文件: {OUTPUT_VIDEO}")
    
    start_time = time.time()
    frame_count = 0
    
    try:
        # === 0-15秒: 仪表盘 ===
        print("[0-15s] 仪表盘")
        navigate_to(driver, "dashboard")
        time.sleep(3)
        # 滚动展示
        driver.execute_script("window.scrollTo(0, 0)")
        time.sleep(4)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.5)")
        time.sleep(4)
        driver.execute_script("window.scrollTo(0, 0)")
        time.sleep(4)
        
        # === 15-50秒: 物料检测 ===
        print("[15-50s] 物料检测")
        navigate_to(driver, "detection")
        time.sleep(2)
        
        if TEST_IMAGE and os.path.exists(TEST_IMAGE):
            # 上传图片
            try:
                file_input = driver.find_element(By.ID, "image-input")
                file_input.send_keys(TEST_IMAGE)
                print("  图片已上传")
                time.sleep(3)
                
                # 点击检测按钮
                detect_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "btn-detect"))
                )
                detect_btn.click()
                print("  开始检测")
                time.sleep(5)
                
                # 滚动查看检测结果
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.3)")
                time.sleep(5)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.6)")
                time.sleep(5)
                driver.execute_script("window.scrollTo(0, 0)")
                time.sleep(5)
            except Exception as e:
                print(f"  检测操作失败: {e}")
                time.sleep(15)
        else:
            print("  无测试图片，跳过上传")
            time.sleep(20)
        
        # === 50-65秒: 库存管理 ===
        print("[50-65s] 库存管理")
        navigate_to(driver, "inventory")
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.3)")
        time.sleep(4)
        driver.execute_script("window.scrollTo(0, 0)")
        time.sleep(3)
        
        # === 65-80秒: 传感器数据 ===
        print("[65-80s] 传感器数据")
        navigate_to(driver, "sensor")
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.4)")
        time.sleep(4)
        driver.execute_script("window.scrollTo(0, 0)")
        time.sleep(3)
        
        # === 80-95秒: 检测记录 ===
        print("[80-95s] 检测记录")
        navigate_to(driver, "records")
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.4)")
        time.sleep(4)
        driver.execute_script("window.scrollTo(0, 0)")
        time.sleep(3)
        
        # === 95-110秒: 系统设置 ===
        print("[95-110s] 系统设置")
        navigate_to(driver, "settings")
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.5)")
        time.sleep(4)
        driver.execute_script("window.scrollTo(0, 0)")
        time.sleep(3)
        
        # === 110-120秒: 回到仪表盘 ===
        print("[110-120s] 回到仪表盘")
        navigate_to(driver, "dashboard")
        time.sleep(10)
        
    except Exception as e:
        print(f"操作过程出错: {e}")
    
    # 录帧循环（持续到达到目标时长）
    while frame_count < TOTAL_FRAMES:
        elapsed = time.time() - start_time
        expected_frame = int(elapsed * FPS)
        
        if frame_count < expected_frame:
            # 捕获屏幕
            img = sct.grab(monitor)
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            out.write(frame)
            frame_count += 1
            
            if frame_count % (FPS * 10) == 0:
                print(f"  已录制 {frame_count // FPS}秒 / {DURATION}秒")
        else:
            time.sleep(0.001)
    
    # 清理
    out.release()
    driver.quit()
    sct.close()
    
    print(f"\n录屏完成! 输出文件: {OUTPUT_VIDEO}")
    print(f"总帧数: {frame_count}, 时长: {frame_count / FPS:.1f}秒")
    file_size = os.path.getsize(OUTPUT_VIDEO) / (1024 * 1024)
    print(f"文件大小: {file_size:.1f} MB")

if __name__ == "__main__":
    main()
