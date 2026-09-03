"""
录制系统演示视频 v6 - 用selenium截图直接录制
优点：不受DPI缩放、窗口位置影响，录制的就是浏览器内容
页面切换用真实点击，确保前端JS响应
"""
import time
import glob
import os
import numpy as np
import cv2
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import io

BASE_URL = "http://127.0.0.1:8000"
GITHUB_URL = "https://github.com/sunshikai060101/manufacturing-intelligence-course"
OUTPUT_VIDEO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo_v6_raw.mp4")
FPS = 27
DURATION = 164
TOTAL_FRAMES = FPS * DURATION

# 输出视频尺寸（参考视频标准）
OUT_W = 960
OUT_H = 576

test_images = glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "processed", "images", "test", "*.jpg"))
TEST_IMAGE = test_images[0] if test_images else None

def get_screenshot_frame(driver):
    """获取浏览器截图，转换为BGR numpy数组"""
    png = driver.get_screenshot_as_png()
    img = Image.open(io.BytesIO(png))
    frame = np.array(img)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    frame = cv2.resize(frame, (OUT_W, OUT_H))
    return frame

def switch_page(driver, page_name):
    """用真实点击切换页面"""
    try:
        nav = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f'.nav-item[data-page="{page_name}"]'))
        )
        nav.click()
        time.sleep(2)
        # 验证页面标题是否变化
        title = driver.find_element(By.ID, "page-title").text
        print(f"  已切换到: {page_name} (标题: {title})")
    except Exception as e:
        print(f"  点击切换失败，尝试JS: {e}")
        try:
            driver.execute_script(f"""
                document.querySelector('.nav-item[data-page="{page_name}"]').click();
            """)
            time.sleep(2)
            print(f"  JS切换到: {page_name}")
        except Exception as e2:
            print(f"  JS切换也失败: {e2}")

def scroll_page(driver, ratio):
    driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {ratio})")

def main():
    # 启动Edge，窗口大小设为输出尺寸的比例
    options = Options()
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    driver = webdriver.Edge(options=options)
    # 设置窗口大小为 960x600（内容区约960x576）
    driver.set_window_size(960, 620)
    driver.set_window_position(0, 0)
    time.sleep(2)
    
    driver.get(BASE_URL)
    time.sleep(4)
    
    # 打开GitHub新标签
    driver.execute_script(f"window.open('{GITHUB_URL}', '_blank');")
    time.sleep(3)
    driver.switch_to.window(driver.window_handles[0])
    time.sleep(1)
    
    # 初始化视频写入
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(OUTPUT_VIDEO, fourcc, FPS, (OUT_W, OUT_H))
    
    print(f"开始录屏: {OUT_W}x{OUT_H}, {FPS}fps, {DURATION}秒")
    print(f"用selenium截图方式录制")
    
    start_time = time.time()
    frame_count = 0
    last_action_time = 0
    
    # 定义动作序列：(时间点, 动作函数, 参数)
    # 用独立线程执行动作，主线程负责录帧
    import threading
    
    def action_worker():
        nonlocal last_action_time
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
                    
                    detect_btn = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.ID, "btn-detect"))
                    )
                    detect_btn.click()
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
                    links[0].click()
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
                frame = get_screenshot_frame(driver)
                out.write(frame)
            except Exception as e:
                print(f"  截图错误: {e}")
                # 写一帧黑色画面
                frame = np.zeros((OUT_H, OUT_W, 3), dtype=np.uint8)
                out.write(frame)
            frame_count += 1
            
            if frame_count % (FPS * 20) == 0:
                print(f"  已录制 {frame_count // FPS}秒 / {DURATION}秒")
        else:
            time.sleep(0.001)
    
    out.release()
    driver.quit()
    
    print(f"\n录屏完成! {OUTPUT_VIDEO}")
    print(f"总帧数: {frame_count}, 时长: {frame_count / FPS:.1f}秒")

if __name__ == "__main__":
    main()
