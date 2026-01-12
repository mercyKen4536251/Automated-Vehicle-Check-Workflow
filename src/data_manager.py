import os
import pandas as pd
import uuid

# Get directory of the current file (src/)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Data dir is one level up
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path)
    # 读取后处理：将转义的换行符还原
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(
                lambda x: x.replace('\\n', '\n').replace('\\r', '\r') if pd.notna(x) and isinstance(x, str) else x
            )
    return df

def save_csv(filename, df):
    path = os.path.join(DATA_DIR, filename)
    # 保存前处理：将换行符转换为转义字符
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(
                lambda x: x.replace('\n', '\\n').replace('\r', '\\r') if pd.notna(x) and isinstance(x, str) else x
            )
    df.to_csv(path, index=False, quoting=1)  # quoting=1 确保所有字段都被引号包裹

def get_test_cases():
    return load_csv("test_cases.csv")

def save_test_case(data):
    df = load_csv("test_cases.csv")
    new_row = pd.DataFrame([data])
    df = pd.concat([df, new_row], ignore_index=True)
    save_csv("test_cases.csv", df)

def get_refs():
    return load_csv("ref.csv")

def get_prompts():
    prompts = {}
    for i in range(1, 6):
        filename = f"prompt_0{i}.csv"
        df = load_csv(filename)
        if not df.empty:
            # Get the active one or the last one
            active = df[df['is_active'] == True]
            if not active.empty:
                 prompts[i] = active.iloc[0].to_dict()
            else:
                 prompts[i] = df.iloc[-1].to_dict()
    return prompts

def get_prompt_versions(node_index):
    """
    获取指定节点的所有版本记录

    Args:
        node_index: 节点索引 (1-5)

    Returns:
        DataFrame: 包含所有版本记录的数据框
    """
    filename = f"prompt_0{node_index}.csv"
    df = load_csv(filename)
    if not df.empty:
        return df.sort_index(ascending=False)  # 最新的在前
    return pd.DataFrame()

def update_prompt(node_index, content, version):
    """
    更新提示词

    如果版本号已存在 → 更新该版本的内容（修改操作）
    如果版本号不存在 → 创建新版本并激活（新增操作）

    Args:
        node_index: 节点索引 (1-5)
        content: 提示词内容
        version: 用户指定的版本号

    Returns:
        tuple: (operation_type, version)
            operation_type: 'update' (修改) 或 'create' (新增)
            version: 最终的版本号
    """
    filename = f"prompt_0{node_index}.csv"
    df = load_csv(filename)

    # 检查版本号是否已存在
    existing_version = df[df['prompt_version'] == version]

    if not existing_version.empty:
        # 版本号已存在 → 更新该版本的内容（修改操作）
        idx = existing_version.index[0]
        df.loc[idx, 'prompt_content'] = content
        df['is_active'] = False  # 先全部停用
        df.loc[idx, 'is_active'] = True  # 只激活当前版本
        operation_type = 'update'
    else:
        # 版本号不存在 → 创建新版本（新增操作）
        df['is_active'] = False  # 先全部停用
        new_row = {
            "prompt_id": str(uuid.uuid4())[:8],
            "prompt_version": version,
            "prompt_content": content,
            "is_active": True
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        operation_type = 'create'

    save_csv(filename, df)
    return (operation_type, version)

def activate_prompt_version(node_index, version):
    """
    激活指定版本的提示词

    Args:
        node_index: 节点索引 (1-5)
        version: 要激活的版本号
    """
    filename = f"prompt_0{node_index}.csv"
    df = load_csv(filename)

    if df.empty:
        return False

    # Deactivate all
    df['is_active'] = False

    # Activate the specified version
    idx = df[df['prompt_version'] == version].index
    if len(idx) > 0:
        df.loc[idx[0], 'is_active'] = True
        save_csv(filename, df)
        return True
    return False

def get_problem_tags():
    return load_csv("problem_tags.csv")

def add_problem_tag(tag_content):
    """添加新标签"""
    df = load_csv("problem_tags.csv")
    # 生成新的标签ID（自动递增）
    if df.empty:
        new_id = 1
    else:
        new_id = df['tag_id'].max() + 1
    
    new_row = {
        "tag_id": new_id,
        "tag_content": tag_content
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_csv("problem_tags.csv", df)
    return new_id

def update_problem_tag(tag_id, new_content):
    """更新标签内容"""
    df = load_csv("problem_tags.csv")
    # 查找标签
    idx = df[df['tag_id'] == tag_id].index
    if len(idx) == 0:
        return False
    
    df.loc[idx[0], 'tag_content'] = new_content
    save_csv("problem_tags.csv", df)
    return True

def delete_problem_tag(tag_id):
    """删除标签"""
    df = load_csv("problem_tags.csv")
    # 不允许删除最后一个标签
    if len(df) <= 1:
        return False
    
    # 删除标签
    df = df[df['tag_id'] != tag_id]
    save_csv("problem_tags.csv", df)
    return True
