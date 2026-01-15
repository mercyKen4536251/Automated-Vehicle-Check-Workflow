"""
API 数据模型定义

API data models definition
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

# ==================== 请求模型 ====================

class TestSubmitRequest(BaseModel):
    """
    提交测试任务请求
    
    Submit test task request
    """
    case_ids: List[int]
    config_id: Optional[int] = None

# ==================== 响应模型 ====================

class TestSubmitResponse(BaseModel):
    """
    提交测试任务响应
    
    Submit test task response
    """
    task_id: str
    status: str
    submitted_at: datetime
    total_cases: int

class TaskProgress(BaseModel):
    """
    任务进度
    
    Task progress
    """
    total: int
    completed: int
    failed: int
    current_case_id: Optional[int] = None

class TaskStatusResponse(BaseModel):
    """
    任务状态响应
    
    Task status response
    """
    task_id: str
    status: str  # pending/running/completed/failed/cancelled
    progress: TaskProgress
    results: List[Dict[str, Any]]
    submitted_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

class TaskListItem(BaseModel):
    """
    任务列表项
    
    Task list item
    """
    task_id: str
    status: str
    total_cases: int
    completed_cases: int
    submitted_at: datetime
    completed_at: Optional[datetime] = None
