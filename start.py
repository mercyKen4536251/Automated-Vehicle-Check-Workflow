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
import signal

def check_port_available(port):
    """
    检查端口是否可用
    
    Check if port is available
    
    Args:
        port: 端口号
    
    Returns:
        bool: 端口是否可用
    """
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", port))
        sock.close()
        return True
    except:
        return False

def wait_for_backend(max_attempts=15):
    """
    等待后端启动
    
    Wait for backend to start
    
    Args:
        max_attempts: 最大尝试次数
    
    Returns:
        bool: 是否启动成功
    """
    import requests
    for i in range(max_attempts):
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                return True
        except:
            pass
        time.sleep(1)
    return False

def main():
    print("=" * 60)
    print("🚀 启动 VLM 自动化测试系统 v2.0.0")
    print("   Starting VLM Automated Test System v2.0.0")
    print("=" * 60)
    print()
    
    # ==================== 检查端口 ====================
    if not check_port_available(8000):
        print("❌ 端口 8000 已被占用")
        print("   Port 8000 is already in use")
        print()
        print("💡 请先关闭占用端口的进程，或使用以下命令查找：")
        if os.name == 'nt':
            print("   netstat -ano | findstr :8000")
        else:
            print("   lsof -i :8000")
        return
    
    # ==================== 启动后端 ====================
    print("📡 启动后端服务 (FastAPI)...")
    print("   Starting backend service (FastAPI)...")
    
    # 不重定向输出，让日志直接显示
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--port", "8000", "--host", "127.0.0.1"],
        creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
    )
    
    # 等待后端启动
    print("   等待后端启动（最多15秒）...")
    if wait_for_backend():
        print("✅ 后端服务启动成功")
        print("   Backend service started successfully")
        print("   API: http://localhost:8000")
        print("   Docs: http://localhost:8000/docs")
    else:
        print("❌ 后端服务启动失败")
        print("   Backend service failed to start")
        print()
        print("💡 请检查后端窗口的错误信息")
        backend.terminate()
        return
    
    print()
    
    # ==================== 启动前端 ====================
    print("🎨 启动前端界面 (Streamlit)...")
    print("   Starting frontend interface (Streamlit)...")
    
    frontend = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "pages/app.py", "--server.headless", "true"]
    )
    
    print("   等待前端启动...")
    time.sleep(3)
    
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
    print("💡 提示：")
    print("   - 后端日志在单独的窗口中显示")
    print("   - 前端日志在当前窗口中显示")
    print("   - 按 Ctrl+C 退出所有服务")
    print("=" * 60)
    print()
    
    # ==================== 注册清理函数 ====================
    def cleanup():
        print()
        print("🛑 正在关闭服务...")
        print("   Shutting down services...")
        
        # 先尝试优雅关闭
        backend.terminate()
        frontend.terminate()
        
        try:
            backend.wait(timeout=5)
            frontend.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # 强制关闭
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
