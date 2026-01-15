import streamlit as st
import sys
import os
import requests
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

# ==================== 配置 ====================
BACKEND_URL = "http://localhost:8000"

# ==================== 辅助函数 ====================

def check_backend_connection():
    """检查后端连接"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=3)
        return response.status_code == 200
    except:
        return False

def get_tasks_by_status(status, limit=10):
    """
    获取指定状态的任务
    
    Get tasks by status
    
    Args:
        status: 任务状态
        limit: 返回数量限制
    
    Returns:
        list: 任务列表
    """
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/test/tasks?status={status}&limit={limit}",
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("tasks", [])
    except:
        pass
    return []

def get_task_detail(task_id):
    """
    获取任务详情
    
    Get task detail
    
    Args:
        task_id: 任务ID
    
    Returns:
        dict: 任务详情
    """
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/test/status/{task_id}",
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def format_duration(start_time, end_time=None):
    """
    格式化时长
    
    Format duration
    
    Args:
        start_time: 开始时间
        end_time: 结束时间（可选）
    
    Returns:
        str: 格式化的时长
    """
    if not start_time:
        return "N/A"
    
    try:
        start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        if end_time:
            end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        else:
            end = datetime.now(start.tzinfo)
        
        duration = (end - start).total_seconds()
        
        if duration < 60:
            return f"{duration:.0f}秒"
        elif duration < 3600:
            return f"{duration/60:.1f}分钟"
        else:
            return f"{duration/3600:.1f}小时"
    except:
        return "N/A"

def calculate_avg_time_per_case(start_time, end_time, total_cases):
    """
    计算平均每个用例的耗时
    
    Calculate average time per case
    
    Args:
        start_time: 开始时间
        end_time: 结束时间
        total_cases: 总用例数
    
    Returns:
        str: 平均耗时
    """
    if not start_time or not end_time or total_cases == 0:
        return "N/A"
    
    try:
        start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        duration = (end - start).total_seconds()
        avg = duration / total_cases
        return f"{avg:.1f}秒/用例"
    except:
        return "N/A"

# ==================== 页面标题 ====================
st.header("📋 任务队列")
st.markdown("---")

# ==================== 检查后端连接 ====================
backend_available = check_backend_connection()

if not backend_available:
    st.error("❌ 无法连接到后端服务")
    st.info("💡 请确保后端已启动：`python start.py` 或 `uvicorn backend.main:app --port 8000`")
    st.stop()

# ==================== 模块1: 运行中的任务 ====================
running_tasks = get_tasks_by_status("running", limit=10)
st.subheader(f"🔄 运行中的任务 ({len(running_tasks)})")

with st.container(border=True):
    if not running_tasks:
        st.info("💡 当前没有运行中的任务")
    else:
        for task in running_tasks:
            # 获取详细信息
            detail = get_task_detail(task["task_id"])
            
            if detail:
                progress = detail.get("progress", {})
                total = progress.get("total", 0)
                completed = progress.get("completed", 0)
                current_case = progress.get("current_case_id")
                
                # 计算进度百分比
                progress_pct = (completed / total * 100) if total > 0 else 0
                
                # 计算已用时间
                elapsed_time = format_duration(detail.get("started_at"))
                
                # 显示任务信息
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**任务ID:** `{task['task_id']}`")
                    st.write(f"**进度:** {completed}/{total} ({progress_pct:.0f}%)")
                    if current_case:
                        st.write(f"**当前执行:** Case {current_case}")
                
                with col2:
                    st.write(f"**状态:** 🟢 运行中")
                    st.write(f"**已用时间:** {elapsed_time}")
                
                # 进度条
                st.progress(progress_pct / 100)
                
                st.markdown("---")

st.write("")

# ==================== 模块2: 最近完成的任务 ====================
completed_tasks = get_tasks_by_status("completed", limit=10)
st.subheader(f"✅ 最近完成的任务 ({len(completed_tasks)})")

with st.container(border=True):
    if not completed_tasks:
        st.info("💡 暂无已完成的任务")
    else:
        for task in completed_tasks:
            # 获取详细信息
            detail = get_task_detail(task["task_id"])
            
            if detail:
                total_cases = task.get("total_cases", 0)
                
                # 计算总耗时
                total_time = format_duration(
                    detail.get("started_at"),
                    detail.get("completed_at")
                )
                
                # 计算平均耗时
                avg_time = calculate_avg_time_per_case(
                    detail.get("started_at"),
                    detail.get("completed_at"),
                    total_cases
                )
                
                # 格式化完成时间
                completed_at = detail.get("completed_at", "")
                if completed_at:
                    try:
                        dt = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                        completed_time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        completed_time_str = "N/A"
                else:
                    completed_time_str = "N/A"
                
                # 显示任务信息
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**任务ID:** `{task['task_id']}`")
                    st.write(f"**用例数:** {total_cases}")
                    st.write(f"**完成时间:** {completed_time_str}")
                
                with col2:
                    st.write(f"**状态:** ✅ 完成")
                    st.write(f"**总耗时:** {total_time}")
                    st.write(f"**平均耗时:** {avg_time}")
                
                st.write("")

st.info("💡 前往【结果面板】查看详细测试结果和准确率")