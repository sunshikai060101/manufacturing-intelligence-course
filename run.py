"""系统启动脚本"""
import uvicorn
import sys
import os

# 确保项目根目录在Python路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("正在启动智能仓储物料识别与分拣系统...")
    print("访问地址: http://127.0.0.1:8000")
    print("API文档: http://127.0.0.1:8000/docs")
    print("=" * 60)

    uvicorn.run(
        "backend.app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info",
    )
