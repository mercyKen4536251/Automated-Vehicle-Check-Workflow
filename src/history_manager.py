import os
import json
from datetime import datetime

# 获取项目路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
HISTORY_DIR = os.path.join(PROJECT_ROOT, "data", "test_history")

# 确保目录存在
os.makedirs(HISTORY_DIR, exist_ok=True)


def generate_test_id():
    """
    生成测试ID（时间戳格式）
    
    Returns:
        str: 格式为 YYYYMMDD_HHMMSS 的测试ID
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def save_test_history(results_list):
    """
    保存测试历史到JSON文件

    Args:
        results_list: 测试结果列表，每个元素包含：
            - case_id: 用例ID
            - car: 车型
            - case_type: 用例类型（goodcase/badcase）
            - problem_tag: 问题标签
            - case_url: 图片URL
            - final_pass: 最终审核结果
            - finish_at_step: 完成到第几步
            - parse_output: 关键节点JSON输出
            - is_correct: 是否符合预期
            - prompt_versions: 提示词版本字典 {"p1": "v1.0.0", "p2": "v2.0.0", ...}
            - model_config: 模型配置 {"model_id": "...", "thinking_mode": "..."}

    Returns:
        str: 生成的测试ID
    """
    test_id = generate_test_id()
    test_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cases_total = len(results_list)
    acc_total = sum(1 for r in results_list if r.get('is_correct', False))
    acc_rate = round(acc_total / cases_total, 4) if cases_total > 0 else 0

    # 收集所有测试用例的提示词版本信息
    all_prompt_versions = {}
    for r in results_list:
        if 'prompt_versions' in r:
            # 合并所有用例的版本信息，以第一个非unknown为准
            for key, version in r['prompt_versions'].items():
                if key not in all_prompt_versions and version != 'unknown':
                    all_prompt_versions[key] = version

    # 收集模型配置信息（所有用例应该使用相同的模型）
    model_config = {}
    if results_list and 'model_config' in results_list[0]:
        model_config = results_list[0]['model_config']

    # 简化results（只保留必要字段）
    simplified_results = []
    for r in results_list:
        # 确定expected_pass
        expected_pass = "no" if r.get('case_type') == 'badcase' else "yes"

        simplified_results.append({
            "case_id": r.get('case_id'),
            "car": r.get('car'),
            "case_type": r.get('case_type'),
            "problem_tag": r.get('problem_tag'),
            "case_url": r.get('case_url'),
            "expected_pass": expected_pass,
            "final_pass": r.get('final_pass'),
            "is_correct": r.get('is_correct'),
            "finish_at_step": r.get('finish_at_step'),
            "parse_output": r.get('parse_output', {})
        })

    # 构建历史数据
    history_data = {
        "test_id": test_id,
        "test_time": test_time,
        "cases_total": cases_total,
        "acc_total": acc_total,
        "acc_rate": acc_rate,
        "prompt_versions": all_prompt_versions,  # 添加提示词版本信息
        "model_config": model_config,  # 添加模型配置信息
        "results": simplified_results
    }

    # 保存到文件
    file_path = os.path.join(HISTORY_DIR, f"{test_id}.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(history_data, f, ensure_ascii=False, indent=2)

    return test_id


def load_test_history(test_id):
    """
    加载指定测试历史
    
    Args:
        test_id: 测试ID
    
    Returns:
        dict or None: 测试历史数据，不存在返回None
    """
    file_path = os.path.join(HISTORY_DIR, f"{test_id}.json")
    if not os.path.exists(file_path):
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading test history {test_id}: {e}")
        return None


def list_test_history():
    """
    列出所有测试历史（按时间倒序）
    
    Returns:
        list: 测试历史摘要列表，每个元素包含：
            - test_id
            - test_time
            - cases_total
            - acc_total
            - acc_rate
    """
    if not os.path.exists(HISTORY_DIR):
        return []
    
    files = [f for f in os.listdir(HISTORY_DIR) if f.endswith('.json')]
    files.sort(reverse=True)  # 按文件名倒序（时间戳格式天然支持）
    
    history_list = []
    for filename in files:
        test_id = filename.replace('.json', '')
        data = load_test_history(test_id)
        if data:
            history_list.append({
                "test_id": data['test_id'],
                "test_time": data['test_time'],
                "cases_total": data['cases_total'],
                "acc_total": data['acc_total'],
                "acc_rate": data['acc_rate']
            })
    
    return history_list


def delete_test_history(test_id):
    """
    删除指定测试历史
    
    Args:
        test_id: 测试ID
    
    Returns:
        bool: 删除成功返回True，失败返回False
    """
    file_path = os.path.join(HISTORY_DIR, f"{test_id}.json")
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            return True
        except Exception as e:
            print(f"Error deleting test history {test_id}: {e}")
            return False
    return False


def get_problem_tag_stats(test_id):
    """
    获取指定测试的问题标签统计
    
    Args:
        test_id: 测试ID
    
    Returns:
        dict: 问题标签统计，格式：
            {
                "问题标签": {
                    "total": 总数,
                    "correct": 正确数,
                    "accuracy": 准确率,
                    "fail_steps": {1: 次数, 2: 次数, ...}
                }
            }
    """
    data = load_test_history(test_id)
    if not data:
        return {}
    
    stats = {}
    for result in data['results']:
        tag = result.get('problem_tag', 'unknown')
        
        if tag not in stats:
            stats[tag] = {
                "total": 0,
                "correct": 0,
                "accuracy": 0.0,
                "fail_steps": {}
            }
        
        stats[tag]["total"] += 1
        if result.get('is_correct'):
            stats[tag]["correct"] += 1
        
        # 记录失败节点
        if not result.get('is_correct'):
            step = result.get('finish_at_step', 0)
            stats[tag]["fail_steps"][step] = stats[tag]["fail_steps"].get(step, 0) + 1
    
    # 计算准确率
    for tag in stats:
        if stats[tag]["total"] > 0:
            stats[tag]["accuracy"] = round(stats[tag]["correct"] / stats[tag]["total"], 4)
    
    return stats


def get_fail_step_stats(test_id):
    """
    获取指定测试的失败节点统计
    
    Args:
        test_id: 测试ID
    
    Returns:
        dict: 失败节点统计，格式：
            {
                1: {"count": 次数, "problem_tags": {"标签": 次数}},
                2: {"count": 次数, "problem_tags": {"标签": 次数}},
                ...
            }
    """
    data = load_test_history(test_id)
    if not data:
        return {}
    
    stats = {}
    for result in data['results']:
        # 只统计失败的用例
        if not result.get('is_correct'):
            step = result.get('finish_at_step', 0)
            tag = result.get('problem_tag', 'unknown')
            
            if step not in stats:
                stats[step] = {
                    "count": 0,
                    "problem_tags": {}
                }
            
            stats[step]["count"] += 1
            stats[step]["problem_tags"][tag] = stats[step]["problem_tags"].get(tag, 0) + 1
    
    return stats
