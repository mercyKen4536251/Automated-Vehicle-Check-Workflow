"""
测试任务相关 API

Test task related API
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import Optional
from backend.api.models import (
    TestSubmitRequest, 
    TestSubmitResponse, 
    TaskStatusResponse,
    TaskListItem
)
from backend.tasks.manager import TaskManager
from backend.tasks.executor import execute_test_task
from datetime import datetime

router = APIRouter()
task_manager = TaskManager()

# ==================== 提交测试任务 ====================

@router.post("/submit", response_model=TestSubmitResponse)
async def submit_test(request: TestSubmitRequest, background_tasks: BackgroundTasks):
    """
    提交测试任务
    
    Submit test task
    
    Args:
        request: 测试任务请求
        background_tasks: FastAPI 后台任务
    
    Returns:
        TestSubmitResponse: 任务提交响应
    """
    # 创建任务
    task_id = task_manager.create_task(request.case_ids)
    
    # 添加后台任务
    background_tasks.add_task(execute_test_task, task_id, request.case_ids)
    
    return TestSubmitResponse(
        task_id=task_id,
        status="pending",
        submitted_at=datetime.now(),
        total_cases=len(request.case_ids)
    )

# ==================== 查询任务状态 ====================

@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    获取任务状态
    
    Get task status
    
    Args:
        task_id: 任务ID
    
    Returns:
        TaskStatusResponse: 任务状态响应
    
    Raises:
        HTTPException: 任务不存在时抛出 404
    """
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

# ==================== 取消任务 ====================

@router.post("/cancel/{task_id}")
async def cancel_task(task_id: str):
    """
    取消任务
    
    Cancel task
    
    Args:
        task_id: 任务ID
    
    Returns:
        dict: 取消结果
    
    Raises:
        HTTPException: 任务不存在时抛出 404
    """
    success = task_manager.cancel_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task cancelled successfully", "task_id": task_id}

# ==================== 获取任务列表 ====================

@router.get("/tasks")
async def list_tasks(status: Optional[str] = None, limit: int = 10):
    """
    获取任务列表
    
    Get task list
    
    Args:
        status: 筛选状态（可选）
        limit: 返回数量限制
    
    Returns:
        dict: 任务列表
    """
    tasks = task_manager.list_tasks(status=status, limit=limit)
    
    # 转换为简化格式
    task_list = []
    for task in tasks:
        task_list.append({
            "task_id": task["task_id"],
            "status": task["status"],
            "total_cases": task["progress"]["total"],
            "completed_cases": task["progress"]["completed"],
            "submitted_at": task["submitted_at"],
            "completed_at": task.get("completed_at")
        })
    
    return {
        "tasks": task_list,
        "total": len(task_list)
    }

# ==================== 获取任务统计 ====================

@router.get("/stats")
async def get_stats():
    """
    获取任务统计信息
    
    Get task statistics
    
    Returns:
        dict: 统计信息
    """
    all_tasks = task_manager.list_tasks(limit=1000)
    
    stats = {
        "total": len(all_tasks),
        "pending": len([t for t in all_tasks if t["status"] == "pending"]),
        "running": len([t for t in all_tasks if t["status"] == "running"]),
        "completed": len([t for t in all_tasks if t["status"] == "completed"]),
        "failed": len([t for t in all_tasks if t["status"] == "failed"]),
        "cancelled": len([t for t in all_tasks if t["status"] == "cancelled"])
    }
    
    return stats
