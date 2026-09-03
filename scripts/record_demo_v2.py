"""
录制2分钟系统演示视频 v2 - 确保浏览器全屏在前台
"""
import time
import glob
import os
import sys
import numpy as np
import cv2
import mss
import pyautogui
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://127.0.0.1:8000"
OUTPUT_VIDEO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo_video_raw.mp4")
FPS = 20
DURATION = 120
TOTAL_FRAMES = FPS * DURATION

test_images = glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "processed", "images", "test", "*.jpg"))
TEST_IMAGE = test_images[0] if test_images else None
print(f"测试图片: {TEST_IMAGE}")

def bring_browser_to_front(driver):
    """确保浏览器窗口在最前台"""
    try:
        # 用selenium最小化再恢复，强制窗口到前台
        driver.minimize_window()
        time.sleep(0.3)
        driver.maximize_window()
        time.sleep(0.5)
        # 点击浏览器中心位置确保焦点
        size = driver.get_window_size()
        pos = driver.get_window_position()
        center_x = pos['x'] + size['width'] // 2
        center_y = pos['y'] + size['height'] // 2
        pyautogui.click(center_x, center_y)
        time.sleep(0.3)
    except Exception as e:
        print(f"  激活浏览器窗口失败: {e}")

def navigate_to(driver, page_name):
    try:
        nav = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f'.nav-item[data-page="{page_name}"]'))
        )
        nav.click()
        time.sleep(1.5)
    except Exception as e:
        print(f"导航到 {page_name} 失败: {e}")

def main():
    # 先最小化所有窗口（Win+D），确保浏览器启动后在最前
    print("最小化所有窗口...")
    pyautogui.hotkey('win', 'd')
    time.sleep(1)
    
    # 启动Edge
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    driver = webdriver.Edge(options=options)
    driver.get(BASE_URL)
    time.sleep(3)
    
    # 确保浏览器在前台并全屏
    bring_browser_to_front(driver)
    driver.fullscreen_window()
    time.sleep(1)
    
    # 初始化录屏 - 录制主显示器
    sct = mss.mss()
    monitor = sct.monitors[1]
    width = monitor["width"]
    height = monitor["height"]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(OUTPUT_VIDEO, fourcc, FPS, (width, height))
    
    print(f"开始录屏: {width}x{height}, {FPS}fps, {DURATION}秒")
    print(f"输出文件: {OUTPUT_VIDEO}")
    
    start_time = time.time()
    frame_count = 0
    last_front_ensure = time.time()
    
    try:
        # === 0-15秒: 仪表盘 ===
        print("[0-15s] 仪表盘")
        navigate_to(driver, "dashboard")
        time.sleep(3)
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
            try:
                file_input = driver.find_element(By.ID, "image-input")
                file_input.send_keys(TEST_IMAGE)
                print("  图片已上传")
                time.sleep(3)
                
                detect_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "btn-detect"))
                )
                detect_btn.click()
                print("  开始检测")
                time.sleep(5)
                
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
    
    # 录帧循环
    while frame_count < TOTAL_FRAMES:
        elapsed = time.time() - start_time
        expected_frame = int(elapsed * FPS)
        
        # 每15秒确保浏览器在前台一次
        if time.time() - last_front_ensure > 15:
            bring_browser_to_front(driver)
            last_front_ensure = time.time()
        
        if frame_count < expected_frame:
            img = sct.grab(monitor)
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            out.write(frame)
            frame_count += 1
            
            if frame_count % (FPS * 10) == 0:
                print(f"  已录制 {frame_count // FPS}秒 / {DURATION}秒")
        else:
            time.sleep(0.001)
    
    out.release()
    driver.quit()
    sct.close()
    
    print(f"\n录屏完成! 输出文件: {OUTPUT_VIDEO}")
    print(f"总帧数: {frame_count}, 时长: {frame_count / FPS:.1f}秒")

if __name__ == "__main__":
    main()
