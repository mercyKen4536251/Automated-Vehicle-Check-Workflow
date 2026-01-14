"""
模型客户端模块

封装模型API调用，支持多模型配置

调用方法说明：
- call_single: 单图判断（节点1-3），只传生成图
- call_multi_ref: 多参考图比对（节点4），参考图在前，生成图在后
- call_compare: 双图比对（节点5），参考图+描述+生成图
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
    
    def _send_request(self, messages):
        """
        发送请求到模型API（内部方法）
        
        Args:
            messages: 完整的消息列表
        
        Returns:
            str: 模型返回的文本内容
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                thinking={"type": self.thinking_mode}
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {e}"
    
    def call_single(self, prompt, image_url):
        """
        单图判断调用（节点1-3使用）
        
        Args:
            prompt: 提示词文本
            image_url: 生成图URL
        
        Returns:
            str: 模型返回的文本内容
        """
        messages = [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "请判断下面这张生成图"},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ]
        return self._send_request(messages)
    
    def call_multi_ref(self, prompt, ref_urls, gen_url):
        """
        多参考图比对调用（节点4使用）
        图片顺序：参考图1-N在前，生成图在后
        
        Args:
            prompt: 提示词文本
            ref_urls: 参考图URL列表
            gen_url: 生成图URL
        
        Returns:
            str: 模型返回的文本内容
        """
        # 构建参考图内容
        ref_content = [
            {"type": "text", "text": f"下面{len(ref_urls)}张图片为参考图"}
        ]
        for url in ref_urls:
            ref_content.append({"type": "image_url", "image_url": {"url": url}})
        
        # 构建生成图内容
        ref_content.append({"type": "text", "text": "下面图片为生成图，需要判断这个图片"})
        ref_content.append({"type": "image_url", "image_url": {"url": gen_url, "detail": "high"}})
        
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": ref_content}
        ]
        return self._send_request(messages)
    
    def call_compare(self, prompt, ref_url, gen_url, ref_description=""):
        """
        双图比对调用（节点5使用）
        图片顺序：参考图在前，生成图在后
        
        Args:
            prompt: 提示词文本（应包含{{cankaotumiaoshu}}占位符）
            ref_url: 参考图URL
            gen_url: 生成图URL
            ref_description: 参考图描述文本
        
        Returns:
            str: 模型返回的文本内容
        """
        # 替换描述占位符
        final_prompt = prompt
        if "{{cankaotumiaoshu}}" in prompt:
            final_prompt = prompt.replace("{{cankaotumiaoshu}}", ref_description)
        
        # 构建内容：参考图 + 生成图
        user_content = [
            {"type": "text", "text": "下面第一张图片为参考图"},
            {"type": "image_url", "image_url": {"url": ref_url}},
            {"type": "text", "text": "下面图片为生成图，需要判断这个图片"},
            {"type": "image_url", "image_url": {"url": gen_url, "detail": "high"}}
        ]
        
        messages = [
            {"role": "system", "content": final_prompt},
            {"role": "user", "content": user_content}
        ]
        return self._send_request(messages)
    
    def call(self, prompt, image_urls, system_prompt="You are a helpful assistant."):
        """
        通用调用方法（向后兼容，不推荐新代码使用）
        
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
        
        return self._send_request(messages)
    
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
