"""
工作流引擎模块

实现5节点审图工作流逻辑，使用模块化的模型客户端
"""
from . import model_client as mc
from . import config_manager as cm

def run_workflow_for_case(case_data, ref_data, prompts):
    """
    执行5节点审图工作流（一票否决机制）

    工作流逻辑：
    1. Agent1: 判断是否有车 -> car="yes"才通过
    2. Agent2: 判断是否裁切 -> cropping="no"才通过
    3. Agent3: 判断运动无人驾驶 -> match="yes"才通过（过滤运动+无人驾驶）
    4. Agent4: 判断视角一致 -> match="yes"才通过，返回匹配的参考图索引
    5. Agent5: 判断细节一致 -> match="yes"才通过

    任意节点失败，立即返回 final_pass="no"，并记录失败节点

    Args:
        case_data: 测试用例数据（dict）
        ref_data: 参考图数据（dict）
        prompts: 提示词字典 {1: {...}, 2: {...}, ...}

    Returns:
        dict: {
            "final_pass": "yes" | "no" | "error",
            "finish_at_step": 1-5,
            "parse_output": {...},  # 关键节点的JSON输出
            "reason": "失败原因或成功信息",
            "prompt_versions": {"p1": "v1.0.0", "p2": "v2.0.0", ...},  # 各节点使用的提示词版本
            "model_config": {"model_id": "...", "thinking_mode": "..."}  # 使用的模型配置
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

    resp1_text = client.call(p1, [case_url])
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
            "reason": "图片中未检测到汽车",
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

    resp2_text = client.call(p2, [case_url])
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

    # ==================== Node 3: 判断运动状态无人驾驶 ====================
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

    resp3_text = client.call(p3, [case_url])
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
            "reason": "检测到运动状态无人驾驶",
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

    # 构建提示词：明确说明图片顺序和索引规则
    prompt_with_context = f"""{p4}

重要说明：
- 第1张图片：生成图（待判定的图片）
- 第2-{len(ordered_ref_urls)+1}张图片：参考图1-{len(ordered_ref_urls)}（用于比对）
- 如果匹配，请在match_image字段中返回匹配的参考图索引（2-{len(ordered_ref_urls)+1}，对应参考图1-{len(ordered_ref_urls)}）
"""

    resp4_text = client.call(prompt_with_context, [case_url] + ordered_ref_urls)
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

    if resp4_json.get('match') == 'no':
        return {
            "final_pass": "no",
            "finish_at_step": 4,
            "parse_output": resp4_json,
            "reason": "生成图与参考图视角不一致",
            "prompt_versions": prompt_versions,
            "model_config": model_config
        }

    # 解析匹配的参考图索引
    matched_ref_url = None
    match_image_value = resp4_json.get('match_image', '')

    # 尝试解析为整数索引
    # 传递顺序：[生成图(1), 参考图1(2), 参考图2(3), ..., 参考图5(6)]
    # 模型返回2-6，对应ordered_ref_urls[0-4]
    try:
        idx = int(match_image_value)
        # 模型返回的索引是2-6（对应参考图1-5）
        if 2 <= idx <= len(ordered_ref_urls) + 1:
            matched_ref_url = ordered_ref_urls[idx - 2]  # idx=2 -> ordered_ref_urls[0]
        # 兼容旧逻辑：如果模型返回1-5（直接对应参考图）
        elif 1 <= idx <= len(ordered_ref_urls):
            matched_ref_url = ordered_ref_urls[idx - 1]
        else:
            return {
                "final_pass": "error",
                "finish_at_step": 4,
                "parse_output": resp4_json,
                "reason": f"match_image索引超出范围: {idx} (期望2-{len(ordered_ref_urls)+1}或1-{len(ordered_ref_urls)})",
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

    if "{{cankaotumiaoshu}}" in p5:
        final_prompt = p5.replace("{{cankaotumiaoshu}}", description)
    else:
        final_prompt = f"{p5}\n\n参考图描述:\n{description}"

    resp5_text = client.call(final_prompt, [matched_ref_url, case_url])
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

    if resp5_json.get('match') != 'yes':
        return {
            "final_pass": "no",
            "finish_at_step": 5,
            "parse_output": resp5_json,
            "reason": resp5_json.get('reason', '细节不一致或无法判断'),
            "prompt_versions": prompt_versions,
            "model_config": model_config
        }

    # ==================== 全部通过 ====================
    return {
        "final_pass": "yes",
        "finish_at_step": 5,
        "parse_output": resp5_json,
        "reason": "所有审核节点通过",
        "prompt_versions": prompt_versions,
        "model_config": model_config
    }
