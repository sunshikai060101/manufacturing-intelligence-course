"""将mp4v编码的视频转码为H.264格式，兼容所有播放器"""
import os
import sys
import subprocess
import imageio_ffmpeg

INPUT_VIDEO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo_video.mp4")
OUTPUT_VIDEO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo_video_h264.mp4")

ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
print(f"ffmpeg路径: {ffmpeg_path}")
print(f"输入文件: {INPUT_VIDEO}")
print(f"输出文件: {OUTPUT_VIDEO}")

# 转码命令：H.264编码，中等质量，兼容所有播放器
cmd = [
    ffmpeg_path,
    "-y",  # 覆盖输出文件
    "-i", INPUT_VIDEO,
    "-c:v", "libx264",
    "-preset", "medium",
    "-crf", "23",
    "-pix_fmt", "yuv420p",  # 确保兼容性
    "-movflags", "+faststart",  # 优化网络播放
    OUTPUT_VIDEO
]

print(f"\n开始转码...")
print(f"命令: {' '.join(cmd)}")

result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode == 0:
    input_size = os.path.getsize(INPUT_VIDEO) / (1024 * 1024)
    output_size = os.path.getsize(OUTPUT_VIDEO) / (1024 * 1024)
    print(f"\n转码成功!")
    print(f"原文件大小: {input_size:.1f} MB (mp4v编码)")
    print(f"新文件大小: {output_size:.1f} MB (H.264编码)")
    print(f"输出文件: {OUTPUT_VIDEO}")
else:
    print(f"\n转码失败，错误码: {result.returncode}")
    print(f"stderr: {result.stderr[-2000:]}")
    sys.exit(1)
