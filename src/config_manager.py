"""
模型配置管理模块

负责模型配置的增删改查操作
"""
import os
import pandas as pd
import uuid

# 获取项目路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
CONFIG_FILE = os.path.join(DATA_DIR, "model_config.csv")


def _ensure_config_file():
    """确保配置文件存在，不存在则创建默认配置"""
    if not os.path.exists(CONFIG_FILE):
        default_config = pd.DataFrame([{
            "config_id": "default",
            "model_id": "your-model-id-here",
            "api_key": "YOUR_API_KEY_HERE",
            "thinking_mode": "disabled"
        }])
        default_config.to_csv(CONFIG_FILE, index=False)


def get_all_configs():
    """
    获取所有模型配置
    
    Returns:
        pd.DataFrame: 配置列表
    """
    _ensure_config_file()
    return pd.read_csv(CONFIG_FILE)


def get_active_config():
    """
    获取当前激活的配置（简化版：直接返回第一个配置）
    
    Returns:
        dict: 配置字典，包含 config_id, model_id, api_key, thinking_mode
    """
    _ensure_config_file()
    configs = pd.read_csv(CONFIG_FILE)
    
    if configs.empty:
        raise ValueError("No model configuration found")
    
    # 简化逻辑：直接返回第一个配置
    config = configs.iloc[0].to_dict()
    
    # 添加固定的 base_url（火山引擎）
    config['base_url'] = "https://ark.cn-beijing.volces.com/api/v3"
    
    return config


def add_config(model_id, api_key, thinking_mode="disabled"):
    """
    添加新的模型配置
    
    Args:
        model_id: 模型ID
        api_key: API密钥
        thinking_mode: 思考模式（enabled/disabled）
    
    Returns:
        str: 新配置的ID
    """
    _ensure_config_file()
    configs = pd.read_csv(CONFIG_FILE)
    
    # 生成新的配置ID
    config_id = str(uuid.uuid4())[:8]
    
    new_config = {
        "config_id": config_id,
        "model_id": model_id,
        "api_key": api_key,
        "thinking_mode": thinking_mode
    }
    
    configs = pd.concat([configs, pd.DataFrame([new_config])], ignore_index=True)
    configs.to_csv(CONFIG_FILE, index=False)
    
    return config_id


def update_config(config_id, **kwargs):
    """
    更新配置
    
    Args:
        config_id: 配置ID
        **kwargs: 要更新的字段
    
    Returns:
        bool: 是否更新成功
    """
    _ensure_config_file()
    configs = pd.read_csv(CONFIG_FILE)
    
    # 查找配置
    idx = configs[configs['config_id'] == config_id].index
    
    if len(idx) == 0:
        return False
    
    # 更新字段
    for key, value in kwargs.items():
        if key in configs.columns:
            configs.loc[idx[0], key] = value
    
    configs.to_csv(CONFIG_FILE, index=False)
    return True


def delete_config(config_id):
    """
    删除配置
    
    Args:
        config_id: 配置ID
    
    Returns:
        bool: 是否删除成功
    """
    _ensure_config_file()
    configs = pd.read_csv(CONFIG_FILE)
    
    # 不允许删除最后一个配置
    if len(configs) <= 1:
        return False
    
    # 删除配置
    configs = configs[configs['config_id'] != config_id]
    configs.to_csv(CONFIG_FILE, index=False)
    return True


def set_active_config(config_id):
    """
    设置激活的配置（简化版：将指定配置移到第一行）
    
    Args:
        config_id: 配置ID
    
    Returns:
        bool: 是否设置成功
    """
    _ensure_config_file()
    configs = pd.read_csv(CONFIG_FILE)
    
    # 查找配置
    if config_id not in configs['config_id'].values:
        return False
    
    # 将指定配置移到第一行
    target_row = configs[configs['config_id'] == config_id]
    other_rows = configs[configs['config_id'] != config_id]
    
    configs = pd.concat([target_row, other_rows], ignore_index=True)
    configs.to_csv(CONFIG_FILE, index=False)
    return True


def get_thinking_mode_options():
    """
    获取思考模式选项
    
    Returns:
        list: 思考模式选项列表
    """
    return ["disabled", "enabled"]
