"""
工作流引擎模块

实现5节点审图工作流逻辑，使用模块化的模型客户端

工作流最终结果说明：
- final_pass="yes": 生成图通过所有审核，质量合格
- final_pass="no": 生成图在某个节点被明确判定为不合格
- final_pass="unknown": 无法判定（如节点4找不到匹配视角，或节点5返回unknown）
"""
from . import model_client as mc
from . import config_manager as cm


def run_workflow_for_case(case_data, ref_data, prompts):
    """
    执行5节点审图工作流

    工作流逻辑：
    1. Node1: 判断是否有车且可用 -> car="yes"才继续
    2. Node2: 判断是否裁切 -> cropping="no"才继续
    3. Node3: 判断车牌有字/无人驾驶 -> match="yes"才继续
    4. Node4: 判断视角一致 -> match="yes"才继续到Node5，match="no"返回unknown
    5. Node5: 判断细节一致 -> match="yes"返回yes，match="no"返回no，match="unknown"返回unknown

    Args:
        case_data: 测试用例数据（dict）
        ref_data: 参考图数据（dict）
        prompts: 提示词字典 {1: {...}, 2: {...}, ...}

    Returns:
        dict: {
            "final_pass": "yes" | "no" | "unknown" | "error",
            "finish_at_step": 1-5,
            "parse_output": {...},
            "reason": "失败原因或成功信息",
            "prompt_versions": {"p1": "v1.0.0", ...},
            "model_config": {"model_id": "...", "thinking_mode": "..."}
        }
    """
    case_url = case_data['case_url']

    # 获取模型客户端（使用激活的配置）
    client = mc.get_client()

    # 获取当前激活的模型配置
    active_config = cm.get_active_config()
    model_config = {
        "model_id": active_config.get('model_id', 'unknown'),
        "thinking_mode": active_config.get('thinking_mode', 'unknown')
    }

    # 收集提示词版本信息
    prompt_versions = {}

    # ==================== Node 1: 判断是否存在汽车 ====================
    p1_data = prompts.get(1, {})
    p1 = p1_data.get('prompt_content', "")
    prompt_versions["p1"] = p1_data.get('prompt_version', "unknown")

    if not p1:
        return {
            "final_pass": "error",
            "finish_at_step": 1,
            "parse_output": {"error": "Prompt 1 not found"},
            "reason": "缺少Node1提示词",
            "prompt_versions": prompt_versions,
            "model_config": model_config
        }

    resp1_text = client.call_single(p1, case_url)
    resp1_json = client.parse_json_response(resp1_text)

    if not resp1_json:
        return {
            "final_pass": "error",
            "finish_at_step": 1,
            "parse_output": {"error": "Failed to parse JSON", "raw_response": resp1_text[:200]},
            "reason": "Node1 JSON解析失败",
            "prompt_versions": prompt_versions,
            "model_config": model_config
        }

    if resp1_json.get('car') != 'yes':
        return {
            "final_pass": "no",
            "finish_at_step": 1,
            "parse_output": resp1_json,
            "reason": "图片中未检测到可用汽车",
            "prompt_versions": prompt_versions,
            "model_config": model_config
        }

    # ==================== Node 2: 判断车身是否被裁切 ====================
    p2_data = prompts.get(2, {})
    p2 = p2_data.get('prompt_content', "")
    prompt_versions["p2"] = p2_data.get('prompt_version', "unknown")

    if not p2:
        return {
            "final_pass": "error",
            "finish_at_step": 2,
            "parse_output": {"error": "Prompt 2 not found"},
            "reason": "缺少Node2提示词",
            "prompt_versions": prompt_versions,
            "model_config": model_config
        }

    resp2_text = client.call_single(p2, case_url)
    resp2_json = client.parse_json_response(resp2_text)

    if not resp2_json:
        return {
            "final_pass": "error",
            "finish_at_step": 2,
            "parse_output": {"error": "Failed to parse JSON", "raw_response": resp2_text[:200]},
            "reason": "Node2 JSON解析失败",
            "prompt_versions": prompt_versions,
            "model_config": model_config
        }

    if resp2_json.get('cropping') == 'yes':
        return {
            "final_pass": "no",
            "finish_at_step": 2,
            "parse_output": resp2_json,
            "reason": "车身被裁切，不完整",
            "prompt_versions": prompt_versions,
            "model_config": model_config
        }

    # ==================== Node 3: 判断车牌有字/无人驾驶 ====================
    p3_data = prompts.get(3, {})
    p3 = p3_data.get('prompt_content', "")
    prompt_versions["p3"] = p3_data.get('prompt_version', "unknown")

    if not p3:
        return {
            "final_pass": "error",
            "finish_at_step": 3,
            "parse_output": {"error": "Prompt 3 not found"},
            "reason": "缺少Node3提示词",
            "prompt_versions": prompt_versions,
            "model_config": model_config
        }

    resp3_text = client.call_single(p3, case_url)
    resp3_json = client.parse_json_response(resp3_text)

    if not resp3_json:
        return {
            "final_pass": "error",
            "finish_at_step": 3,
            "parse_output": {"error": "Failed to parse JSON", "raw_response": resp3_text[:200]},
            "reason": "Node3 JSON解析失败",
            "prompt_versions": prompt_versions,
            "model_config": model_config
        }

    if resp3_json.get('match') == 'no':
        return {
            "final_pass": "no",
            "finish_at_step": 3,
            "parse_output": resp3_json,
            "reason": resp3_json.get('reason', '检测到车牌有字或无人驾驶'),
            "prompt_versions": prompt_versions,
            "model_config": model_config
        }

    # ==================== Node 4: 判断视角是否一致 ====================
    ordered_ref_urls = []
    for i in range(1, 6):
        u = ref_data.get(f'ref_url_{i}')
        if u and str(u).strip() and str(u).startswith('http'):
            ordered_ref_urls.append(u)

    if not ordered_ref_urls:
        return {
            "final_pass": "error",
            "finish_at_step": 4,
            "parse_output": {"error": "No valid reference images"},
            "reason": f"缺少{case_data.get('car', 'unknown')}的参考图",
            "prompt_versions": prompt_versions,
            "model_config": model_config
        }

    p4_data = prompts.get(4, {})
    p4 = p4_data.get('prompt_content', "")
    prompt_versions["p4"] = p4_data.get('prompt_version', "unknown")

    if not p4:
        return {
            "final_pass": "error",
            "finish_at_step": 4,
            "parse_output": {"error": "Prompt 4 not found"},
            "reason": "缺少Node4提示词",
            "prompt_versions": prompt_versions,
            "model_config": model_config
        }

    # 使用call_multi_ref：参考图在前，生成图在后
    resp4_text = client.call_multi_ref(p4, ordered_ref_urls, case_url)
    resp4_json = client.parse_json_response(resp4_text)

    if not resp4_json:
        return {
            "final_pass": "error",
            "finish_at_step": 4,
            "parse_output": {"error": "Failed to parse JSON", "raw_response": resp4_text[:200]},
            "reason": "Node4 JSON解析失败",
            "prompt_versions": prompt_versions,
            "model_config": model_config
        }

    # 节点4的match="no"表示没有找到匹配的参考图视角，返回unknown
    if resp4_json.get('match') == 'no':
        return {
            "final_pass": "unknown",
            "finish_at_step": 4,
            "parse_output": resp4_json,
            "reason": "未找到与生成图视角匹配的参考图，无法判定",
            "prompt_versions": prompt_versions,
            "model_config": model_config
        }

    # 解析匹配的参考图索引
    # 图片传递顺序：[参考图1, 参考图2, ..., 参考图N, 生成图]
    # 模型返回的match_image应该是参考图的顺序值（1-N）
    matched_ref_url = None
    match_image_value = resp4_json.get('match_image', '')

    try:
        idx = int(match_image_value)
        # 模型返回1-N，对应ordered_ref_urls[0-(N-1)]
        if 1 <= idx <= len(ordered_ref_urls):
            matched_ref_url = ordered_ref_urls[idx - 1]
        else:
            return {
                "final_pass": "error",
                "finish_at_step": 4,
                "parse_output": resp4_json,
                "reason": f"match_image索引超出范围: {idx} (期望1-{len(ordered_ref_urls)})",
                "prompt_versions": prompt_versions,
                "model_config": model_config
            }
    except (ValueError, TypeError):
        # 尝试作为URL处理（兼容性）
        if str(match_image_value).startswith('http'):
            matched_ref_url = match_image_value
        else:
            return {
                "final_pass": "error",
                "finish_at_step": 4,
                "parse_output": resp4_json,
                "reason": f"无法解析match_image: {match_image_value}",
                "prompt_versions": prompt_versions,
                "model_config": model_config
            }

    description = resp4_json.get('reference_vehicle_description', '')

    # ==================== Node 5: 判断细节是否一致 ====================
    p5_data = prompts.get(5, {})
    p5 = p5_data.get('prompt_content', "")
    prompt_versions["p5"] = p5_data.get('prompt_version', "unknown")

    if not p5:
        return {
            "final_pass": "error",
            "finish_at_step": 5,
            "parse_output": {"error": "Prompt 5 not found"},
            "reason": "缺少Node5提示词",
            "prompt_versions": prompt_versions,
            "model_config": model_config
        }

    # 使用call_compare：参考图+描述+生成图
    resp5_text = client.call_compare(p5, matched_ref_url, case_url, description)
    resp5_json = client.parse_json_response(resp5_text)

    if not resp5_json:
        return {
            "final_pass": "error",
            "finish_at_step": 5,
            "parse_output": {"error": "Failed to parse JSON", "raw_response": resp5_text[:200]},
            "reason": "Node5 JSON解析失败",
            "prompt_versions": prompt_versions,
            "model_config": model_config
        }

    # 节点5的match结果直接映射到final_pass
    match_result = resp5_json.get('match', 'unknown')
    
    if match_result == 'yes':
        return {
            "final_pass": "yes",
            "finish_at_step": 5,
            "parse_output": resp5_json,
            "reason": "所有审核节点通过",
            "prompt_versions": prompt_versions,
            "model_config": model_config
        }
    elif match_result == 'no':
        return {
            "final_pass": "no",
            "finish_at_step": 5,
            "parse_output": resp5_json,
            "reason": resp5_json.get('reason', '细节不一致'),
            "prompt_versions": prompt_versions,
            "model_config": model_config
        }
    else:
        # match="unknown" 或其他情况
        return {
            "final_pass": "unknown",
            "finish_at_step": 5,
            "parse_output": resp5_json,
            "reason": resp5_json.get('reason', '无法判定细节是否一致'),
            "prompt_versions": prompt_versions,
            "model_config": model_config
        }
