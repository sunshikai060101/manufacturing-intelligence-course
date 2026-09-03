"""
录制系统演示视频 v7 - 全屏录制，动作连贯，减少停顿
参考视频风格：
- 全屏录制（整个屏幕）
- 开头：命令行启动服务
- 中间：浏览器快速切换各功能页面
- 结尾：回到命令行看API日志
- 动作连贯，每个页面停留短，持续滚动
- 30fps，约2分钟
"""
import time
import glob
import os
import subprocess
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
OUTPUT_VIDEO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo_v7_raw.mp4")
FPS = 30
DURATION = 120  # 2分钟
TOTAL_FRAMES = FPS * DURATION

test_images = glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "processed", "images", "test", "*.jpg"))
TEST_IMAGE = test_images[0] if test_images else None

def switch_page(driver, page_name):
    """快速切换页面"""
    try:
        nav = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f'.nav-item[data-page="{page_name}"]'))
        )
        nav.click()
        time.sleep(0.8)
    except:
        try:
            driver.execute_script(f'document.querySelector(\'.nav-item[data-page="{page_name}"]\').click();')
            time.sleep(0.8)
        except:
            pass

def scroll_smooth(driver, start_ratio, end_ratio, steps=5):
    """平滑滚动，减少停顿感"""
    for i in range(steps + 1):
        ratio = start_ratio + (end_ratio - start_ratio) * i / steps
        driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {ratio})")
        time.sleep(0.15)

def main():
    print("=== 全屏录制 v7 ===")
    
    # 最小化所有窗口，从干净桌面开始
    pyautogui.hotkey('win', 'd')
    time.sleep(1)
    
    # 1. 打开命令行，启动服务（模拟参考视频开头）
    print("[0-12s] 命令行启动服务")
    # 用cmd打开一个窗口，进入项目目录
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cmd_process = subprocess.Popen(
        ['cmd', '/k', f'cd /d {project_dir} && echo 正在启动智能仓储系统... && python run.py'],
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    time.sleep(5)
    
    # 2. 启动Edge浏览器，最大化
    print("[12-110s] 浏览器功能展示")
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    driver = webdriver.Edge(options=options)
    driver.maximize_window()
    time.sleep(1)
    
    driver.get(BASE_URL)
    time.sleep(3)
    
    # 初始化全屏录屏
    sct = mss.mss()
    monitor = sct.monitors[1]
    width = monitor["width"]
    height = monitor["height"]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(OUTPUT_VIDEO, fourcc, FPS, (width, height))
    
    print(f"录屏参数: {width}x{height}, {FPS}fps, {DURATION}秒")
    start_time = time.time()
    frame_count = 0
    
    # 动作线程函数
    import threading
    
    def action_worker():
        try:
            # 前12秒已经在命令行启动服务了
            time.sleep(12)
            
            # === 12-22秒: 仪表盘概览 ===
            print("[12-22s] 仪表盘")
            switch_page(driver, "dashboard")
            time.sleep(1)
            scroll_smooth(driver, 0, 0.5, 4)
            time.sleep(1)
            scroll_smooth(driver, 0.5, 1, 4)
            time.sleep(1)
            scroll_smooth(driver, 1, 0, 4)
            time.sleep(1)
            
            # === 22-45秒: 物料检测（核心功能，多停留） ===
            print("[22-45s] 物料检测")
            switch_page(driver, "detection")
            time.sleep(1)
            
            if TEST_IMAGE and os.path.exists(TEST_IMAGE):
                try:
                    file_input = driver.find_element(By.ID, "image-input")
                    file_input.send_keys(TEST_IMAGE)
                    time.sleep(2)
                    
                    detect_btn = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.ID, "btn-detect"))
                    )
                    detect_btn.click()
                    time.sleep(4)
                    
                    # 滚动展示检测结果
                    scroll_smooth(driver, 0, 0.3, 3)
                    time.sleep(1)
                    scroll_smooth(driver, 0.3, 0.6, 3)
                    time.sleep(1)
                    scroll_smooth(driver, 0.6, 0.9, 3)
                    time.sleep(1)
                    scroll_smooth(driver, 0.9, 0, 3)
                    time.sleep(2)
                except Exception as e:
                    print(f"  检测失败: {e}")
                    time.sleep(10)
            else:
                time.sleep(15)
            
            # === 45-55秒: 库存管理 ===
            print("[45-55s] 库存管理")
            switch_page(driver, "inventory")
            time.sleep(1)
            scroll_smooth(driver, 0, 0.5, 3)
            time.sleep(1)
            scroll_smooth(driver, 0.5, 1, 3)
            time.sleep(1)
            scroll_smooth(driver, 1, 0, 3)
            time.sleep(1)
            
            # === 55-63秒: 传感器数据 ===
            print("[55-63s] 传感器数据")
            switch_page(driver, "sensor")
            time.sleep(1)
            scroll_smooth(driver, 0, 0.5, 3)
            time.sleep(1)
            scroll_smooth(driver, 0.5, 0, 3)
            time.sleep(1)
            
            # === 63-72秒: 检测记录 ===
            print("[63-72s] 检测记录")
            switch_page(driver, "records")
            time.sleep(1)
            scroll_smooth(driver, 0, 0.5, 3)
            time.sleep(1)
            scroll_smooth(driver, 0.5, 1, 3)
            time.sleep(1)
            scroll_smooth(driver, 1, 0, 3)
            time.sleep(1)
            
            # === 72-80秒: 系统设置 ===
            print("[72-80s] 系统设置")
            switch_page(driver, "settings")
            time.sleep(1)
            scroll_smooth(driver, 0, 0.5, 3)
            time.sleep(1)
            scroll_smooth(driver, 0.5, 0, 3)
            time.sleep(1)
            
            # === 80-95秒: GitHub仓库 ===
            print("[80-95s] GitHub仓库")
            driver.execute_script("window.open('https://github.com/sunshikai060101/manufacturing-intelligence-course', '_blank');")
            time.sleep(2)
            driver.switch_to.window(driver.window_handles[1])
            time.sleep(2)
            scroll_smooth(driver, 0, 0.4, 4)
            time.sleep(1)
            scroll_smooth(driver, 0.4, 0.8, 4)
            time.sleep(1)
            scroll_smooth(driver, 0.8, 0, 4)
            time.sleep(2)
            
            # === 95-105秒: 回到仪表盘 ===
            print("[95-105s] 回到仪表盘")
            driver.switch_to.window(driver.window_handles[0])
            switch_page(driver, "dashboard")
            time.sleep(1)
            scroll_smooth(driver, 0, 0.5, 3)
            time.sleep(1)
            scroll_smooth(driver, 0.5, 0, 3)
            time.sleep(1)
            
            # === 105-120秒: 最小化浏览器，展示命令行日志 ===
            print("[105-120s] 命令行日志")
            driver.minimize_window()
            time.sleep(2)
            # 点击任务栏的cmd窗口，或用Alt+Tab
            pyautogui.hotkey('alt', 'tab')
            time.sleep(10)
            
        except Exception as e:
            print(f"动作线程出错: {e}")
            import traceback
            traceback.print_exc()
    
    # 启动动作线程
    action_thread = threading.Thread(target=action_worker, daemon=True)
    action_thread.start()
    
    # 主线程录帧
    while frame_count < TOTAL_FRAMES:
        elapsed = time.time() - start_time
        expected_frame = int(elapsed * FPS)
        
        if frame_count < expected_frame:
            try:
                img = sct.grab(monitor)
                frame = np.array(img)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                out.write(frame)
            except Exception as e:
                print(f"  录帧错误: {e}")
            frame_count += 1
            
            if frame_count % (FPS * 10) == 0:
                print(f"  已录制 {frame_count // FPS}秒 / {DURATION}秒")
        else:
            time.sleep(0.001)
    
    out.release()
    try:
        driver.quit()
    except:
        pass
    sct.close()
    
    # 关闭cmd进程
    try:
        cmd_process.terminate()
    except:
        pass
    
    print(f"\n录屏完成! {OUTPUT_VIDEO}")
    print(f"总帧数: {frame_count}, 时长: {frame_count / FPS:.1f}秒")

if __name__ == "__main__":
    main()
