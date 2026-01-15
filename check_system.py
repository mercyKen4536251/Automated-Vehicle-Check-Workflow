"""
系统诊断脚本
检查项目环境和依赖

System diagnostic script
Check project environment and dependencies
"""
import sys
import subprocess

def check_python_version():
    """检查 Python 版本"""
    print("=" * 60)
    print("🐍 Python 版本检查")
    print("=" * 60)
    version = sys.version_info
    print(f"Python 版本: {version.major}.{version.minor}.{version.micro}")
    if version.major >= 3 and version.minor >= 10:
        print("✅ Python 版本符合要求 (>= 3.10)")
    else:
        print("❌ Python 版本过低，需要 >= 3.10")
    print()

def check_dependencies():
    """检查依赖包"""
    print("=" * 60)
    print("📦 依赖包检查")
    print("=" * 60)
    
    required_packages = {
        "streamlit": "1.30.0",
        "pandas": "2.0.0",
        "fastapi": "0.104.0",
        "uvicorn": "0.24.0",
        "pydantic": "2.5.0",
        "requests": "2.31.0"
    }
    
    for package, min_version in required_packages.items():
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", package],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                # 提取版本号
                for line in result.stdout.split("\n"):
                    if line.startswith("Version:"):
                        version = line.split(":")[1].strip()
                        print(f"✅ {package}: {version}")
                        break
            else:
                print(f"❌ {package}: 未安装")
        except Exception as e:
            print(f"❌ {package}: 检查失败 ({e})")
    print()

def check_ports():
    """检查端口占用"""
    print("=" * 60)
    print("🔌 端口检查")
    print("=" * 60)
    
    import socket
    
    ports = {
        8000: "后端 API (FastAPI)",
        8501: "前端界面 (Streamlit)"
    }
    
    for port, desc in ports.items():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("127.0.0.1", port))
            sock.close()
            print(f"✅ 端口 {port} 可用 ({desc})")
        except:
            print(f"❌ 端口 {port} 已被占用 ({desc})")
    print()

def check_backend():
    """检查后端服务"""
    print("=" * 60)
    print("📡 后端服务检查")
    print("=" * 60)
    
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✅ 后端服务正在运行")
            print(f"   响应: {response.json()}")
        else:
            print(f"❌ 后端服务响应异常: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务（未启动）")
    except Exception as e:
        print(f"❌ 后端服务检查失败: {e}")
    print()

def check_file_structure():
    """检查文件结构"""
    print("=" * 60)
    print("📁 文件结构检查")
    print("=" * 60)
    
    required_files = [
        "start.py",
        "requirements.txt",
        "backend/main.py",
        "backend/api/routes/test.py",
        "backend/tasks/manager.py",
        "backend/tasks/executor.py",
        "pages/app.py",
        "pages/test/run_test.py",
        "src/data_manager.py",
        "src/workflow_engine.py",
        "data/prompts/prompt_01.csv"
    ]
    
    import os
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} (缺失)")
    print()

def main():
    print()
    print("🔍 VLM 自动化测试系统 - 系统诊断")
    print("   System Diagnostic Tool")
    print()
    
    check_python_version()
    check_dependencies()
    check_file_structure()
    check_ports()
    check_backend()
    
    print("=" * 60)
    print("✅ 诊断完成")
    print("=" * 60)
    print()
    print("💡 如果发现问题：")
    print("   1. 缺少依赖 → pip install -r requirements.txt")
    print("   2. 端口被占用 → 关闭占用端口的进程")
    print("   3. 后端未启动 → python start.py")
    print()

if __name__ == "__main__":
    main()
