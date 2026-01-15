"""
任务执行器
负责实际执行测试任务

Task executor
Responsible for actually executing test tasks
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src import data_manager as dm
from src import workflow_engine as we
from backend.tasks.manager import TaskManager

task_manager = TaskManager()

def execute_test_task(task_id: str, case_ids: list):
    """
    执行测试任务
    在后台线程中运行
    
    Execute test task
    Runs in background thread
    
    Args:
        task_id: 任务ID
        case_ids: 测试用例ID列表
    """
    try:
        # 更新状态为 running
        task_manager.update_task(task_id, {
            "status": "running",
            "started_at": datetime.now()
        })
        
        # 加载数据
        cases_df = dm.get_test_cases()
        refs_df = dm.get_refs()
        prompts = dm.get_prompts()
        tags_df = dm.get_problem_tags()
        
        # 构建标签映射
        tag_node_map = {}
        if not tags_df.empty:
            for _, row in tags_df.iterrows():
                tag_node_map[row["tag_content"]] = int(row["expected_filter_node"])
        
        results = []
        
        # 逐个执行测试用例
        for idx, case_id in enumerate(case_ids):
            # 检查是否被取消
            task = task_manager.get_task(task_id)
            if task and task["status"] == "cancelled":
                break
            
            # 更新当前进度
            task_manager.update_task(task_id, {
                "progress": {
                    "total": len(case_ids),
                    "completed": idx,
                    "failed": len([r for r in results if not r.get("is_correct", False)]),
                    "current_case_id": case_id
                }
            })
            
            # 获取用例信息
            case_row = cases_df[cases_df["case_id"] == case_id]
            if case_row.empty:
                continue
            
            case_info = case_row.iloc[0].to_dict()
            
            # 获取参考图
            ref_row = refs_df[refs_df["car"] == case_info["car"]]
            if ref_row.empty:
                continue
            
            ref_data = ref_row.iloc[0].to_dict()
            
            # 执行工作流
            result = we.run_workflow_for_case(case_info, ref_data, prompts)
            
            # 添加用例信息
            result["case_id"] = case_info["case_id"]
            result["car"] = case_info["car"]
            result["case_type"] = case_info["case_type"]
            result["problem_tag"] = case_info.get("problem_tag", "")
            result["case_url"] = case_info["case_url"]
            
            # 判断正确性
            if case_info["case_type"] == "badcase":
                is_correct = (result["final_pass"] == "no")
            else:
                is_correct = (result["final_pass"] == "yes")
            result["is_correct"] = is_correct
            
            # 计算精准度
            is_precise = False
            if case_info["case_type"] == "badcase":
                problem_tag = case_info.get("problem_tag", "")
                expected_node = tag_node_map.get(problem_tag, 0)
                actual_node = result.get("finish_at_step", 0)
                is_precise = (result["final_pass"] == "no" and expected_node == actual_node)
            else:
                is_precise = (result["final_pass"] == "yes" and result.get("finish_at_step", 0) == 5)
            result["is_precise"] = is_precise
            
            results.append(result)
        
        # 更新最终状态
        task_manager.update_task(task_id, {
            "status": "completed",
            "completed_at": datetime.now(),
            "results": results,
            "progress": {
                "total": len(case_ids),
                "completed": len(results),
                "failed": len([r for r in results if not r.get("is_correct", False)]),
                "current_case_id": None
            }
        })
        
        # 保存到历史记录
        if results:
            from src import history_manager as hm
            hm.save_test_history(results, tag_node_map)
        
    except Exception as e:
        # 更新错误状态
        task_manager.update_task(task_id, {
            "status": "failed",
            "completed_at": datetime.now(),
            "error": str(e)
        })
