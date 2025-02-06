import os
import json
import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content
import asyncio
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def save_error_context(prompt, comments, error_msg, api_key_index=None):
    """
    保存错误上下文到文件,增加api_key_index参数
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    error_dir = "error_logs"
    os.makedirs(error_dir, exist_ok=True)
    
    error_file = os.path.join(error_dir, f"error_context_{timestamp}.json")
    error_context = {
        "timestamp": timestamp,
        "error_message": str(error_msg),
        "prompt": prompt,
        "comments": comments,
        "api_key_index": api_key_index  # 保存出错的key的索引
    }
    
    try:
        with open(error_file, 'w', encoding='utf-8') as f:
            json.dump(error_context, f, ensure_ascii=False, indent=2)
        logging.info(f"错误上下文已保存至: {error_file}")
    except Exception as e:
        logging.error(f"保存错误上下文时出错: {str(e)}")

class GeminiAPIKeyPool:
    """
    Gemini API 密钥池
    """
    def __init__(self, api_keys):
        """
        初始化密钥池

        Args:
            api_keys: API 密钥列表
        """
        if not api_keys:
            raise ValueError("API 密钥列表不能为空")
        self.api_keys = api_keys
        self.index = 0

    def get_key(self):
        """
        获取下一个 API 密钥

        Returns:
            API 密钥
        """
        key = self.api_keys[self.index]
        self.index = (self.index + 1) % len(self.api_keys)  # 循环
        return key

async def call_gemini_api(model_name, generation_config, input_message, api_key_pool, prompt, comments):
    """
    调用 Gemini API,并处理重试

    Args:
        model_name: 模型名称
        generation_config: 生成配置
        input_message: 输入消息
        api_key_pool: GeminiAPIKeyPool 实例
        prompt: prompt内容,用于错误记录
        comments: 评论内容,用于错误记录

    Returns:
        API 响应文本,如果所有尝试都失败则返回 None
    """
    max_retries = 3
    timeout = 10

    for attempt in range(max_retries):
        api_key = api_key_pool.get_key()
        api_key_index = api_key_pool.index -1  # 获取当前key的索引, 因为get_key已经+1了
        if api_key_index < 0:
            api_key_index = len(api_key_pool.api_keys) - 1
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config,
        )
        try:
            response = await model.generate_content_async(json.dumps(input_message))
            return response.text
        except Exception as e:
            error_msg = f"Gemini API调用失败 (尝试次数: {attempt + 1}/{max_retries}, 使用的Key索引: {api_key_index}): {str(e)}"
            logging.error(error_msg)
            save_error_context(prompt, comments, error_msg, api_key_index)  # 传入api_key_index
            if attempt < max_retries - 1:
                logging.info(f"等待 {timeout} 秒后重试...")
                await asyncio.sleep(timeout)
    return None