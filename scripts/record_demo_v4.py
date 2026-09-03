"""
录制系统演示视频 v4 - 修复窗口定位和导航问题
- 精确录制浏览器窗口区域
- 用JS强制切换页面确保导航生效
- 2分44秒，960x576，无声
"""
import time
import glob
import os
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
GITHUB_URL = "https://github.com/sunshikai060101/manufacturing-intelligence-course"
OUTPUT_VIDEO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo_v4_raw.mp4")
FPS = 27
DURATION = 164
TOTAL_FRAMES = FPS * DURATION

WINDOW_WIDTH = 1020
WINDOW_HEIGHT = 640
WINDOW_X = 50
WINDOW_Y = 30

test_images = glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "processed", "images", "test", "*.jpg"))
TEST_IMAGE = test_images[0] if test_images else None

def switch_page(driver, page_name):
    """用JS强制切换页面，确保导航生效"""
    try:
        # 先尝试点击
        nav = driver.find_element(By.CSS_SELECTOR, f'.nav-item[data-page="{page_name}"]')
        driver.execute_script("arguments[0].click();", nav)
        time.sleep(2)
        # 验证页面是否切换（检查对应page区域是否可见）
        visible = driver.execute_script(f"""
            var el = document.getElementById('page-{page_name}');
            return el ? getComputedStyle(el).display !== 'none' : false;
        """)
        if not visible:
            # 备用方案：手动隐藏所有页面，显示目标页面
            driver.execute_script(f"""
                document.querySelectorAll('.page').forEach(p => p.style.display = 'none');
                document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
                var target = document.getElementById('page-{page_name}');
                if (target) target.style.display = 'block';
                var nav = document.querySelector('.nav-item[data-page=\"{page_name}\"]');
                if (nav) nav.classList.add('active');
            """)
            time.sleep(1)
        print(f"  已切换到: {page_name}")
    except Exception as e:
        print(f"  切换到 {page_name} 失败: {e}")

def scroll_page(driver, ratio):
    driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {ratio})")

def main():
    print("最小化所有窗口...")
    pyautogui.hotkey('win', 'd')
    time.sleep(1.5)
    
    options = Options()
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    driver = webdriver.Edge(options=options)
    # 同时设置位置和大小
    driver.set_window_rect(WINDOW_X, WINDOW_Y, WINDOW_WIDTH, WINDOW_HEIGHT)
    time.sleep(2)
    
    driver.get(BASE_URL)
    time.sleep(4)
    
    # 打开GitHub新标签
    driver.execute_script(f"window.open('{GITHUB_URL}', '_blank');")
    time.sleep(3)
    driver.switch_to.window(driver.window_handles[0])
    time.sleep(1)
    
    # 获取实际窗口位置用于录制
    actual_rect = driver.get_window_rect()
    print(f"实际窗口位置: {actual_rect}")
    
    # 录制区域用实际窗口位置，稍微扩大以包含边框
    record_region = {
        "top": actual_rect['y'] - 2,
        "left": actual_rect['x'] - 2,
        "width": actual_rect['width'] + 4,
        "height": actual_rect['height'] + 4
    }
    print(f"录制区域: {record_region}")
    
    REC_W = record_region['width']
    REC_H = record_region['height']
    
    sct = mss.mss()
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(OUTPUT_VIDEO, fourcc, FPS, (REC_W, REC_H))
    
    print(f"开始录屏: {REC_W}x{REC_H}, {FPS}fps, {DURATION}秒")
    start_time = time.time()
    frame_count = 0
    
    try:
        # === 0-20秒: 仪表盘 ===
        print("[0-20s] 仪表盘")
        switch_page(driver, "dashboard")
        time.sleep(2)
        scroll_page(driver, 0); time.sleep(4)
        scroll_page(driver, 0.35); time.sleep(4)
        scroll_page(driver, 0.7); time.sleep(4)
        scroll_page(driver, 0); time.sleep(6)
        
        # === 20-55秒: 物料检测 ===
        print("[20-55s] 物料检测")
        switch_page(driver, "detection")
        time.sleep(2)
        
        if TEST_IMAGE and os.path.exists(TEST_IMAGE):
            try:
                file_input = driver.find_element(By.ID, "image-input")
                file_input.send_keys(TEST_IMAGE)
                print("  图片已上传")
                time.sleep(3)
                
                # 用JS点击检测按钮
                detect_btn = driver.find_element(By.ID, "btn-detect")
                driver.execute_script("arguments[0].click();", detect_btn)
                print("  开始检测")
                time.sleep(6)
                
                scroll_page(driver, 0.2); time.sleep(6)
                scroll_page(driver, 0.45); time.sleep(6)
                scroll_page(driver, 0.7); time.sleep(5)
                scroll_page(driver, 0); time.sleep(6)
            except Exception as e:
                print(f"  检测失败: {e}")
                time.sleep(25)
        else:
            time.sleep(30)
        
        # === 55-68秒: 库存管理 ===
        print("[55-68s] 库存管理")
        switch_page(driver, "inventory")
        time.sleep(2)
        scroll_page(driver, 0.3); time.sleep(4)
        scroll_page(driver, 0.6); time.sleep(4)
        scroll_page(driver, 0); time.sleep(3)
        
        # === 68-78秒: 传感器数据 ===
        print("[68-78s] 传感器数据")
        switch_page(driver, "sensor")
        time.sleep(2)
        scroll_page(driver, 0.4); time.sleep(4)
        scroll_page(driver, 0); time.sleep(4)
        
        # === 78-92秒: 检测记录 ===
        print("[78-92s] 检测记录")
        switch_page(driver, "records")
        time.sleep(2)
        scroll_page(driver, 0.3); time.sleep(4)
        scroll_page(driver, 0.6); time.sleep(4)
        scroll_page(driver, 0); time.sleep(4)
        
        # === 92-102秒: 系统设置 ===
        print("[92-102s] 系统设置")
        switch_page(driver, "settings")
        time.sleep(2)
        scroll_page(driver, 0.4); time.sleep(4)
        scroll_page(driver, 0); time.sleep(4)
        
        # === 102-140秒: GitHub仓库 ===
        print("[102-140s] GitHub仓库")
        driver.switch_to.window(driver.window_handles[1])
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, 200)"); time.sleep(5)
        driver.execute_script("window.scrollTo(0, 500)"); time.sleep(5)
        driver.execute_script("window.scrollTo(0, 0)"); time.sleep(4)
        
        # 尝试进入backend目录
        try:
            links = driver.find_elements(By.LINK_TEXT, "backend")
            if links:
                driver.execute_script("arguments[0].click();", links[0])
                time.sleep(3)
                driver.execute_script("window.scrollTo(0, 150)"); time.sleep(5)
                driver.back(); time.sleep(3)
            else:
                time.sleep(8)
        except:
            time.sleep(8)
        
        driver.execute_script("window.scrollTo(0, 700)"); time.sleep(5)
        driver.execute_script("window.scrollTo(0, 0)"); time.sleep(5)
        
        # === 140-164秒: 回到仪表盘 ===
        print("[140-164s] 回到仪表盘")
        driver.switch_to.window(driver.window_handles[0])
        switch_page(driver, "dashboard")
        time.sleep(4)
        scroll_page(driver, 0.3); time.sleep(5)
        scroll_page(driver, 0); time.sleep(15)
        
    except Exception as e:
        print(f"操作出错: {e}")
        import traceback
        traceback.print_exc()
    
    # 录帧循环
    while frame_count < TOTAL_FRAMES:
        elapsed = time.time() - start_time
        expected_frame = int(elapsed * FPS)
        
        if frame_count < expected_frame:
            try:
                img = sct.grab(record_region)
                frame = np.array(img)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                frame = cv2.resize(frame, (REC_W, REC_H))
                out.write(frame)
            except Exception as e:
                print(f"  录帧错误: {e}")
            frame_count += 1
            
            if frame_count % (FPS * 20) == 0:
                print(f"  已录制 {frame_count // FPS}秒 / {DURATION}秒")
        else:
            time.sleep(0.001)
    
    out.release()
    driver.quit()
    sct.close()
    
    print(f"\n录屏完成! {OUTPUT_VIDEO}")
    print(f"总帧数: {frame_count}, 时长: {frame_count / FPS:.1f}秒")

if __name__ == "__main__":
    main()
