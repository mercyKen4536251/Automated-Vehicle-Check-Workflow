"""
一键启动脚本
同时启动 FastAPI 后端和 Streamlit 前端

One-click startup script
Starts both FastAPI backend and Streamlit frontend
"""
import subprocess
import time
import sys
import os
import atexit

def main():
    print("=" * 60)
    print("🚀 启动 VLM 自动化测试系统 v2.0.0")
    print("   Starting VLM Automated Test System v2.0.0")
    print("=" * 60)
    print()
    
    # ==================== 启动后端 ====================
    print("📡 启动后端服务 (FastAPI)...")
    print("   Starting backend service (FastAPI)...")
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--port", "8000", "--host", "127.0.0.1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    )
    
    # 等待后端启动
    print("   等待后端启动...")
    time.sleep(3)
    
    # 检查后端是否启动成功
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✅ 后端服务启动成功")
            print("   Backend service started successfully")
            print("   API: http://localhost:8000")
            print("   Docs: http://localhost:8000/docs")
        else:
            print("⚠️  后端服务可能未正常启动")
            print("   Backend service may not have started properly")
    except Exception as e:
        print("⚠️  无法连接到后端服务，但继续启动前端...")
        print(f"   Cannot connect to backend: {e}")
    
    print()
    
    # ==================== 启动前端 ====================
    print("🎨 启动前端界面 (Streamlit)...")
    print("   Starting frontend interface (Streamlit)...")
    frontend = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "pages/app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print("   等待前端启动...")
    time.sleep(2)
    
    print()
    print("=" * 60)
    print("✅ 系统启动完成！")
    print("   System started successfully!")
    print("=" * 60)
    print()
    print("📡 后端 API:  http://localhost:8000")
    print("   Backend API: http://localhost:8000")
    print()
    print("🎨 前端界面:  http://localhost:8501")
    print("   Frontend UI: http://localhost:8501")
    print()
    print("📚 API 文档:  http://localhost:8000/docs")
    print("   API Docs: http://localhost:8000/docs")
    print()
    print("=" * 60)
    print("按 Ctrl+C 退出 | Press Ctrl+C to exit")
    print("=" * 60)
    print()
    
    # ==================== 注册清理函数 ====================
    def cleanup():
        print()
        print("🛑 正在关闭服务...")
        print("   Shutting down services...")
        backend.terminate()
        frontend.terminate()
        try:
            backend.wait(timeout=5)
            frontend.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend.kill()
            frontend.kill()
        print("✅ 服务已关闭")
        print("   Services stopped")
    
    atexit.register(cleanup)
    
    # ==================== 等待用户中断 ====================
    try:
        frontend.wait()
    except KeyboardInterrupt:
        cleanup()
        sys.exit(0)

if __name__ == "__main__":
    main()
