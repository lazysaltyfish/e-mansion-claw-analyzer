import os
import json
import argparse
import re
import asyncio
import logging
from datetime import datetime

from src.api_caller import GeminiAPIKeyPool, call_gemini_api

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from src.prompt_generator import PromptGenerator

# 使用PromptGenerator生成prompt
ANALYSIS_PROMPT = PromptGenerator.create_analysis_prompt()
MERGE_PROMPT = PromptGenerator.create_merge_prompt()

def save_error_context(prompt, comments, error_msg):
    """
    保存错误上下文到文件
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    error_dir = "error_logs"
    os.makedirs(error_dir, exist_ok=True)
    
    error_file = os.path.join(error_dir, f"error_context_{timestamp}.json")
    error_context = {
        "timestamp": timestamp,
        "error_message": str(error_msg),
        "prompt": prompt,
        "comments": comments
    }
    
    try:
        with open(error_file, 'w', encoding='utf-8') as f:
            json.dump(error_context, f, ensure_ascii=False, indent=2)
        logging.info(f"错误上下文已保存至: {error_file}")
    except Exception as e:
        logging.error(f"保存错误上下文时出错: {str(e)}")

def load_comments(json_path):
    """
    加载评论,返回完整的评论对象列表
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def format_comments(comments):
    """
    格式化评论列表,将id和text合并为字符串,并按id排序
    """
    # 确保每个评论都有id和text
    valid_comments = [
        comment for comment in comments 
        if isinstance(comment, dict) and 'id' in comment and 'text' in comment
    ]
    
    # 按id排序 (转换为整数)
    sorted_comments = sorted(valid_comments, key=lambda x: int(x['id']))
    
    # 只保留最后3000条评论
    sorted_comments = sorted_comments[-3000:]
    
    # 格式化为"[评论id]:评论内容"
    formatted_comments = [
        f"[{comment['id']}]:{comment['text']}"
        for comment in sorted_comments
    ]
    
    return formatted_comments

async def analyze_comments_async(comments, concurrent=5):
    """
    异步分析评论,支持并发请求,每个请求之间间隔3秒

    Args:
        comments: 评论列表(包含id和text的字典列表)
        concurrent: 并发请求数量

    Returns:
        合并后的分析结果
    """
    # 确保API密钥已设置
    if 'GEMINI_API_KEY' not in os.environ:
        raise ValueError("需要设置GEMINI_API_KEYS环境变量")

    api_keys = os.environ['GEMINI_API_KEYS'].split(',')  # 从环境变量读取多个API密钥,以逗号分隔
    api_key_pool = GeminiAPIKeyPool(api_keys)  # 创建密钥池

    # 格式化评论
    formatted_comments = format_comments(comments)

    # 创建多个并发任务
    logging.info(f"正在启动{concurrent}个并发分析请求...")
    tasks = []
    for i in range(concurrent):
        logging.debug(f"创建第{i+1}个分析任务")
        task = analyze_comments(formatted_comments, ANALYSIS_PROMPT, api_key_pool) # 传入api_key_pool
        tasks.append(task)
        if i < concurrent - 1:  # 除了最后一个任务,每个任务之间等待3秒
            logging.debug("等待3秒...")
            await asyncio.sleep(3)

    # 并发执行所有任务
    try:
        results = await asyncio.gather(*tasks)
    except Exception as e:
        logging.error(f"并发请求过程中发生错误: {str(e)}")
        save_error_context(ANALYSIS_PROMPT, formatted_comments, e)
        raise

    # 合并结果
    merged_result = merge_results(results)
    if merged_result is None:
        error_msg = "分析失败: 所有API调用均返回None"
        logging.error(error_msg)
        save_error_context(ANALYSIS_PROMPT, formatted_comments, error_msg)
        return None

    # 将合并结果转换为字符串
    merged_json_str = json.dumps(merged_result, ensure_ascii=False)

    # 使用同步函数进行最终合并
    try:
        # 直接调用异步函数进行最终合并
        final_result = await analyze_comments(merged_json_str, MERGE_PROMPT, api_key_pool)
    except Exception as e:
        logging.error(f"最终合并请求过程中发生错误: {str(e)}")
        save_error_context(MERGE_PROMPT, merged_json_str, e)
        raise

    # 解析最终结果
    final_result_json = extract_json_from_markdown(final_result)
    if final_result_json:
        return json.dumps(final_result_json, ensure_ascii=False, indent=2)
    else:
        error_msg = "最终合并失败"
        logging.error(error_msg)
        save_error_context(MERGE_PROMPT, merged_json_str, error_msg)
        return json.dumps(merged_result, ensure_ascii=False, indent=2)

async def analyze_comments(comments, prompt, api_key_pool):
    """
    同步分析评论函数,由异步函数调用, 使用api_key_pool
    """
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain"
    }

    model_name = "gemini-2.0-pro-exp"  # 将模型名称提取出来
    input_message = {
        "instruction": prompt,
        "comments": comments,
    }

    # 调用 call_gemini_api
    response_text = await call_gemini_api(model_name, generation_config, input_message, api_key_pool, prompt, comments)
    return response_text

def extract_json_from_markdown(markdown_text):
    """
    从Markdown格式的字符串中提取第一个JSON对象。
    """
    try:
        # 使用正则表达式匹配第一个json代码块
        pattern = r'```json\n(.*?)\n```'
        match = re.search(pattern, markdown_text, re.DOTALL)
        if not match:
            return None
            
        # 提取第一个JSON块的内容
        json_text = match.group(1)
        # 解析JSON
        json_obj = json.loads(json_text)
        return json_obj
    except json.JSONDecodeError as e:
        logging.error(f"JSON解析失败: {str(e)}")
        return None

def merge_results(results):
    """
    合并多个分析结果
    """
    logging.info(f"开始合并{len(results)}个分析结果...")
    if not results:
        logging.warning("没有可合并的分析结果")
        return None
        
    # 初始化合并结果
    merged = {
        "property_name": "",
        "information": {
            "advantages": [],
            "disadvantages": [],
            "price": [],
            "other_information": []
        }
    }
    
    for i, result in enumerate(results):
        if not result:  # 跳过None结果
            logging.warning(f"第{i+1}个分析结果为空,已跳过")
            continue
            
        try:
            # 使用新函数解析JSON
            result_json = extract_json_from_markdown(result)
            if result_json is None:
                continue

            # 如果property_name为空,使用第一个非空的property_name
            if not merged["property_name"] and result_json.get("property_name"):
                merged["property_name"] = result_json["property_name"]
            
            # 合并各个类别的信息
            for category in ["advantages", "disadvantages", "price", "other_information"]:
                if category in result_json.get("information", {}):
                    merged["information"][category].extend(result_json["information"][category])
        except (KeyError) as e:
            logging.error(f"合并结果时出错: {str(e)}")
            continue
    
    return merged

async def main_async():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_json', help='输入JSON文件路径')
    parser.add_argument('--concurrent', type=int, default=5, help='并发请求数量')
    args = parser.parse_args()

    comments = load_comments(args.input_json)

    try:
        result = await analyze_comments_async(comments, args.concurrent)
        if result:
            output_path = os.path.join("output", "analysis_results", f"analysis_{os.path.basename(args.input_json)}")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result)
            logging.info(f"分析结果已保存至 {output_path}")
        else:
            logging.error("分析失败")
    except Exception as e:
        logging.error(f"分析失败: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main_async())
