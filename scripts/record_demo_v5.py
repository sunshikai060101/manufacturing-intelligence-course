"""
录制系统演示视频 v5 - 修复DPI缩放坐标问题
系统DPI=125%，selenium返回逻辑坐标，mss用物理坐标
需要将逻辑坐标 * 1.25 转换为物理坐标
"""
import time
import glob
import os
import ctypes
import numpy as np
import cv2
import mss
import pyautogui
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By

# 设置进程DPI感知，让pyautogui等使用物理坐标
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

BASE_URL = "http://127.0.0.1:8000"
GITHUB_URL = "https://github.com/sunshikai060101/manufacturing-intelligence-course"
OUTPUT_VIDEO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo_v5_raw.mp4")
FPS = 27
DURATION = 164
TOTAL_FRAMES = FPS * DURATION

# DPI缩放因子（125% = 1.25）
DPI_SCALE = 1.25

# 逻辑坐标下的窗口设置（会被转换为物理坐标）
LOGIC_W = 1000
LOGIC_H = 620
LOGIC_X = 40
LOGIC_Y = 20

test_images = glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "processed", "images", "test", "*.jpg"))
TEST_IMAGE = test_images[0] if test_images else None

def switch_page(driver, page_name):
    """用JS强制切换页面"""
    try:
        driver.execute_script(f"""
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            var nav = document.querySelector('.nav-item[data-page="{page_name}"]');
            if (nav) nav.classList.add('active');
            var page = document.getElementById('page-{page_name}');
            if (page) page.classList.add('active');
            window.scrollTo(0, 0);
        """)
        time.sleep(1.5)
        print(f"  已切换到: {page_name}")
    except Exception as e:
        print(f"  切换失败: {e}")

def scroll_page(driver, ratio):
    driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {ratio})")

def main():
    print(f"DPI缩放因子: {DPI_SCALE}")
    print("最小化所有窗口...")
    pyautogui.hotkey('win', 'd')
    time.sleep(1.5)
    
    options = Options()
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    # 告诉Edge使用系统DPI
    options.add_argument("--force-device-scale-factor=1")
    options.add_argument("--high-dpi-support=1")
    
    driver = webdriver.Edge(options=options)
    # selenium用逻辑坐标设置窗口
    driver.set_window_rect(LOGIC_X, LOGIC_Y, LOGIC_W, LOGIC_H)
    time.sleep(2)
    
    # 获取逻辑坐标
    logic_rect = driver.get_window_rect()
    print(f"逻辑窗口位置: {logic_rect}")
    
    # 转换为物理坐标用于mss录制
    phys_x = int(logic_rect['x'] * DPI_SCALE)
    phys_y = int(logic_rect['y'] * DPI_SCALE)
    phys_w = int(logic_rect['width'] * DPI_SCALE)
    phys_h = int(logic_rect['height'] * DPI_SCALE)
    
    # 录制区域稍微扩大以包含窗口边框
    record_region = {
        "top": phys_y - 2,
        "left": phys_x - 2,
        "width": phys_w + 4,
        "height": phys_h + 4
    }
    print(f"物理录制区域: {record_region}")
    
    REC_W = record_region['width']
    REC_H = record_region['height']
    
    driver.get(BASE_URL)
    time.sleep(4)
    
    # 打开GitHub新标签
    driver.execute_script(f"window.open('{GITHUB_URL}', '_blank');")
    time.sleep(3)
    driver.switch_to.window(driver.window_handles[0])
    time.sleep(1)
    
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
                
                driver.execute_script("document.getElementById('btn-detect').click();")
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
