"""
模型客户端模块

封装模型API调用，支持多模型配置
"""
import json
from volcenginesdkarkruntime import Ark
from . import config_manager as cm

class ModelClient:
    """模型客户端类"""
    def __init__(self, config=None):
        """
        初始化模型客户端
        
        Args:
            config: 配置字典，如果为None则使用激活的配置
        """
        if config is None:
            config = cm.get_active_config()
        
        self.config = config
        self.client = Ark(
            base_url=config['base_url'],
            api_key=config['api_key']
        )
        self.model_id = config['model_id']
        self.thinking_mode = config.get('thinking_mode', 'disabled')
    
    def call(self, prompt, image_urls, system_prompt="You are a helpful assistant."):
        """
        调用模型API
        
        Args:
            prompt: 提示词文本
            image_urls: 图片URL列表
            system_prompt: 系统提示词
        
        Returns:
            str: 模型返回的文本内容
        """
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        
        user_content = [{"type": "text", "text": prompt}]
        
        for url in image_urls:
            user_content.append({"type": "image_url", "image_url": {"url": url}})
        
        messages.append({"role": "user", "content": user_content})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                thinking={"type": self.thinking_mode}
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {e}"
    
    def parse_json_response(self, response_text):
        """
        解析模型返回的JSON内容
        支持处理Markdown代码块包裹的JSON
        
        Args:
            response_text: 模型返回的原始文本
        
        Returns:
            dict or None: 解析后的JSON对象，失败返回None
        """
        try:
            # 清理Markdown代码块
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            return json.loads(response_text.strip())
        except Exception:
            return None
    
    def get_config_info(self):
        """
        获取当前配置信息
        
        Returns:
            dict: 配置信息
        """
        return {
            "config_id": self.config.get('config_id'),
            "model_id": self.model_id,
            "thinking_mode": self.thinking_mode,
            "description": self.config.get('description', '')
        }

# 全局单例客户端（用于向后兼容）
_global_client = None

def get_client(force_reload=False):
    """
    获取全局模型客户端实例
    
    Args:
        force_reload: 是否强制重新加载配置
    
    Returns:
        ModelClient: 模型客户端实例
    """
    global _global_client
    
    if _global_client is None or force_reload:
        _global_client = ModelClient()
    
    return _global_client

def call_vlm(prompt, image_urls, system_prompt="You are a helpful assistant."):
    """
    便捷函数：调用VLM模型（向后兼容）
    
    Args:
        prompt: 提示词文本
        image_urls: 图片URL列表
        system_prompt: 系统提示词
    
    Returns:
        str: 模型返回的文本内容
    """
    client = get_client()
    return client.call(prompt, image_urls, system_prompt)

def parse_json_response(response_text):
    """
    便捷函数：解析JSON响应（向后兼容）
    
    Args:
        response_text: 模型返回的原始文本
    
    Returns:
        dict or None: 解析后的JSON对象
    """
    client = get_client()
    return client.parse_json_response(response_text)
