"""
录制系统演示视频 v3 - 按参考视频标准
- 浏览器窗口录屏（非全屏，960x576内容区）
- 系统页面 + GitHub仓库切换
- 时长约2分44秒（164秒）
- 无声，后期配音
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
from selenium.webdriver.common.keys import Keys

BASE_URL = "http://127.0.0.1:8000"
GITHUB_URL = "https://github.com/sunshikai060101/manufacturing-intelligence-course"
OUTPUT_VIDEO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo_v3_raw.mp4")
FPS = 27
DURATION = 164  # 2分44秒
TOTAL_FRAMES = FPS * DURATION

# 浏览器窗口设置（内容区960x576，加上边框和标题栏约1000x650）
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 650
WINDOW_X = 100
WINDOW_Y = 50

test_images = glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "processed", "images", "test", "*.jpg"))
TEST_IMAGE = test_images[0] if test_images else None
print(f"测试图片: {TEST_IMAGE}")

def navigate_to(driver, page_name):
    try:
        nav = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f'.nav-item[data-page="{page_name}"]'))
        )
        nav.click()
        time.sleep(1.5)
    except Exception as e:
        print(f"导航到 {page_name} 失败: {e}")

def scroll_page(driver, ratio):
    driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {ratio})")

def main():
    # 最小化所有窗口
    print("最小化所有窗口...")
    pyautogui.hotkey('win', 'd')
    time.sleep(1)
    
    # 启动Edge
    options = Options()
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    driver = webdriver.Edge(options=options)
    driver.set_window_size(WINDOW_WIDTH, WINDOW_HEIGHT)
    driver.set_window_position(WINDOW_X, WINDOW_Y)
    time.sleep(1)
    
    # 打开系统页面
    driver.get(BASE_URL)
    time.sleep(3)
    
    # 打开GitHub仓库新标签页
    driver.execute_script(f"window.open('{GITHUB_URL}', '_blank');")
    time.sleep(3)
    
    # 切回系统页面（第一个标签）
    driver.switch_to.window(driver.window_handles[0])
    time.sleep(1)
    
    # 计算录制区域（浏览器窗口位置和大小）
    # Edge窗口边框约8px，标题栏约35px
    record_region = {
        "top": WINDOW_Y,
        "left": WINDOW_X,
        "width": WINDOW_WIDTH,
        "height": WINDOW_HEIGHT
    }
    print(f"录制区域: {record_region}")
    
    # 初始化录屏
    sct = mss.mss()
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(OUTPUT_VIDEO, fourcc, FPS, (WINDOW_WIDTH, WINDOW_HEIGHT))
    
    print(f"开始录屏: {WINDOW_WIDTH}x{WINDOW_HEIGHT}, {FPS}fps, {DURATION}秒")
    start_time = time.time()
    frame_count = 0
    
    try:
        # === 0-25秒: 仪表盘 ===
        print("[0-25s] 仪表盘")
        navigate_to(driver, "dashboard")
        time.sleep(3)
        scroll_page(driver, 0)
        time.sleep(5)
        scroll_page(driver, 0.4)
        time.sleep(5)
        scroll_page(driver, 0.7)
        time.sleep(5)
        scroll_page(driver, 0)
        time.sleep(7)
        
        # === 25-60秒: 物料检测（核心功能） ===
        print("[25-60s] 物料检测")
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
                
                scroll_page(driver, 0.25)
                time.sleep(6)
                scroll_page(driver, 0.5)
                time.sleep(6)
                scroll_page(driver, 0.75)
                time.sleep(6)
                scroll_page(driver, 0)
                time.sleep(7)
            except Exception as e:
                print(f"  检测操作失败: {e}")
                time.sleep(25)
        else:
            time.sleep(30)
        
        # === 60-75秒: 库存管理 ===
        print("[60-75s] 库存管理")
        navigate_to(driver, "inventory")
        time.sleep(3)
        scroll_page(driver, 0.3)
        time.sleep(5)
        scroll_page(driver, 0.6)
        time.sleep(4)
        scroll_page(driver, 0)
        time.sleep(3)
        
        # === 75-85秒: 传感器数据 ===
        print("[75-85s] 传感器数据")
        navigate_to(driver, "sensor")
        time.sleep(3)
        scroll_page(driver, 0.4)
        time.sleep(4)
        scroll_page(driver, 0)
        time.sleep(3)
        
        # === 85-100秒: 检测记录 ===
        print("[85-100s] 检测记录")
        navigate_to(driver, "records")
        time.sleep(3)
        scroll_page(driver, 0.3)
        time.sleep(5)
        scroll_page(driver, 0.6)
        time.sleep(4)
        scroll_page(driver, 0)
        time.sleep(3)
        
        # === 100-110秒: 系统设置 ===
        print("[100-110s] 系统设置")
        navigate_to(driver, "settings")
        time.sleep(3)
        scroll_page(driver, 0.4)
        time.sleep(4)
        scroll_page(driver, 0)
        time.sleep(3)
        
        # === 110-140秒: 切换到GitHub仓库 ===
        print("[110-140s] GitHub仓库")
        driver.switch_to.window(driver.window_handles[1])
        time.sleep(3)
        
        # 滚动展示仓库文件列表
        driver.execute_script("window.scrollTo(0, 300)")
        time.sleep(5)
        driver.execute_script("window.scrollTo(0, 600)")
        time.sleep(5)
        driver.execute_script("window.scrollTo(0, 0)")
        time.sleep(5)
        
        # 点击进入backend目录展示代码结构
        try:
            backend_link = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "backend"))
            )
            backend_link.click()
            time.sleep(3)
            driver.execute_script("window.scrollTo(0, 200)")
            time.sleep(5)
            driver.back()
            time.sleep(3)
        except:
            time.sleep(8)
        
        # 滚动到README展示
        driver.execute_script("window.scrollTo(0, 800)")
        time.sleep(5)
        driver.execute_script("window.scrollTo(0, 0)")
        time.sleep(4)
        
        # === 140-164秒: 回到系统仪表盘 ===
        print("[140-164s] 回到仪表盘")
        driver.switch_to.window(driver.window_handles[0])
        navigate_to(driver, "dashboard")
        time.sleep(5)
        scroll_page(driver, 0.3)
        time.sleep(5)
        scroll_page(driver, 0)
        time.sleep(14)
        
    except Exception as e:
        print(f"操作过程出错: {e}")
    
    # 录帧循环
    while frame_count < TOTAL_FRAMES:
        elapsed = time.time() - start_time
        expected_frame = int(elapsed * FPS)
        
        if frame_count < expected_frame:
            img = sct.grab(record_region)
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            # 调整大小到精确尺寸
            frame = cv2.resize(frame, (WINDOW_WIDTH, WINDOW_HEIGHT))
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
