"""
任务管理器
负责任务的创建、状态管理、查询

Task manager
Responsible for task creation, status management, and querying
"""
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from threading import Lock

class TaskManager:
    """
    任务管理器（内存存储）
    
    Task manager (in-memory storage)
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.tasks = {}
                    cls._instance.task_lock = Lock()
        return cls._instance
    
    def create_task(self, case_ids: List[int]) -> str:
        """
        创建新任务
        
        Create new task
        
        Args:
            case_ids: 测试用例ID列表
        
        Returns:
            str: 任务ID
        """
        task_id = str(uuid.uuid4())[:8]
        
        with self.task_lock:
            self.tasks[task_id] = {
                "task_id": task_id,
                "status": "pending",
                "progress": {
                    "total": len(case_ids),
                    "completed": 0,
                    "failed": 0,
                    "current_case_id": None
                },
                "results": [],
                "submitted_at": datetime.now(),
                "started_at": None,
                "completed_at": None,
                "error": None,
                "case_ids": case_ids
            }
        
        return task_id
    
    def get_task(self, task_id: str) -> Optional[dict]:
        """
        获取任务信息
        
        Get task information
        
        Args:
            task_id: 任务ID
        
        Returns:
            dict: 任务信息，不存在返回 None
        """
        with self.task_lock:
            return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, updates: dict):
        """
        更新任务信息
        
        Update task information
        
        Args:
            task_id: 任务ID
            updates: 要更新的字段
        """
        with self.task_lock:
            if task_id in self.tasks:
                self.tasks[task_id].update(updates)
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Cancel task
        
        Args:
            task_id: 任务ID
        
        Returns:
            bool: 是否成功取消
        """
        with self.task_lock:
            if task_id in self.tasks:
                self.tasks[task_id]["status"] = "cancelled"
                return True
        return False
    
    def list_tasks(self, status: Optional[str] = None, limit: int = 10) -> List[dict]:
        """
        获取任务列表
        
        Get task list
        
        Args:
            status: 筛选状态（可选）
            limit: 返回数量限制
        
        Returns:
            List[dict]: 任务列表
        """
        with self.task_lock:
            tasks = list(self.tasks.values())
            if status:
                tasks = [t for t in tasks if t["status"] == status]
            # 按提交时间倒序
            tasks.sort(key=lambda x: x["submitted_at"], reverse=True)
            return tasks[:limit]
    
    def get_task_count(self) -> int:
        """
        获取任务总数
        
        Get total task count
        
        Returns:
            int: 任务总数
        """
        with self.task_lock:
            return len(self.tasks)
