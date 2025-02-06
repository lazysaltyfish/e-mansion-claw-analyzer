import os
import json
import argparse
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ANALYSIS_PROMPT = r"""# Role: 房地产评论分析师

## Profile

房地产评论分析师能够分析用户评论,提取关于房地产项目的关键信息,包括优缺点、价格、与其他楼盘的比较以及其他有价值的信息。分析师能够区分事实陈述和推论,并为每条信息赋予置信度评分。

## Rules

1. 所有提取的description请翻译成中文再放入json。
2. 置信度评分 (confidence_score) 的值必须在 0 到 1 之间。
3. JSON 输出必须是合法且完整的 JSON 字符串,不包含任何其他信息。

## Workflow

1. 接收包含用户评论的 JSON 数据作为输入,JSON 数据至少包含评论 ID 和评论文本。
2. 分析评论文本,提取关于楼盘的关键信息。
3. 将提取的信息组织成以下结构的 JSON:

```json
{
  "property_name": "楼盘名称",
  "information": {
    "advantages": [
      {"type": "fact/inference", "description": "优点描述", "confidence_score": 0.8},
      ...
    ],
    "disadvantages": [
      {"type": "fact/inference", "description": "缺点描述", "confidence_score": 0.6},
      ...
    ],
    "price": [
      {"type": "fact/inference", "description": "价格信息", "confidence_score": 0.9},
      ...
    ],
    "other_information": [
      {"type": "fact/inference", "description": "其他信息", "confidence_score": 0.7},
      ...
    ]
  }
}

## Output

语言为中文的JSON string, 注意不是markdown格式
```
"""

MERGE_PROMPT = """请帮我合并如下JSON文件中的重复项。该文件是一个 JSON 格式的数据,其中`advantages`、`disadvantages`、`price`和`other_information`四个键值下分别对应一个数组。请合并这些数组中的重复项,判断重复的标准是`description`字段内容相同或高度相似,置信度请取平均值。请返回合并后的 JSON 数据。"""

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
        raise ValueError("需要设置GEMINI_API_KEY环境变量")

    api_key = os.environ['GEMINI_API_KEY']
    genai.configure(api_key=api_key)

    # 格式化评论
    formatted_comments = format_comments(comments)

    # 创建多个并发任务
    logging.info(f"正在启动{concurrent}个并发分析请求...")
    tasks = []
    for i in range(concurrent):
        logging.debug(f"创建第{i+1}个分析任务")
        task = analyze_comments(formatted_comments, ANALYSIS_PROMPT)
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
        final_result = await analyze_comments(merged_json_str, MERGE_PROMPT)
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

async def analyze_comments(comments, prompt):
    """
    同步分析评论函数,由异步函数调用, 增加重试机制
    """
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain"
    }

    model = genai.GenerativeModel(
        model_name="gemini-2.0-pro-exp",
        generation_config=generation_config,
    )

    input_message = {
        "instruction": prompt,
        "comments": comments,
    }

    retries = 0
    max_retries = 3
    timeout = 10  # seconds

    while retries < max_retries:
        try:
            response = await model.generate_content_async(json.dumps(input_message))
            return response.text
        except Exception as e:
            error_msg = f"Gemini API调用失败 (尝试次数: {retries + 1}/{max_retries}): {str(e)}"
            logging.error(error_msg)
            save_error_context(prompt, comments, error_msg) # 每次错误都保存上下文 # 移动到 retries += 1 之前
            if retries < max_retries - 1:
                logging.info(f"等待 {timeout} 秒后重试...")
                await asyncio.sleep(timeout)
            retries += 1
    return None # 超过最大重试次数后返回 None

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
