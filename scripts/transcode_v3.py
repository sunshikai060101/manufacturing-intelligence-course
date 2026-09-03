"""转码v3录屏为参考视频标准：H.264, 960x576, 27fps"""
import os
import subprocess
import imageio_ffmpeg

INPUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo_v3_raw.mp4")
OUTPUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo_video_final.mp4")

ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

cmd = [
    ffmpeg, "-y",
    "-i", INPUT,
    "-c:v", "libx264",
    "-preset", "medium",
    "-crf", "23",
    "-pix_fmt", "yuv420p",
    "-vf", "scale=960:576",
    "-r", "27",
    "-movflags", "+faststart",
    "-an",  # 无音频（后期配音）
    OUTPUT
]

print(f"输入: {INPUT}")
print(f"输出: {OUTPUT}")
print(f"目标: 960x576, H.264, 27fps, 无声")
print("开始转码...")

result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode == 0:
    in_size = os.path.getsize(INPUT) / (1024*1024)
    out_size = os.path.getsize(OUTPUT) / (1024*1024)
    print(f"\n转码成功!")
    print(f"原文件: {in_size:.1f} MB (1000x650 mp4v)")
    print(f"新文件: {out_size:.1f} MB (960x576 H.264)")
    print(f"输出: {OUTPUT}")
else:
    print(f"转码失败: {result.returncode}")
    print(result.stderr[-2000:])
