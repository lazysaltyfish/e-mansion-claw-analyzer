import os
import json
import argparse
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_comments(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [item['text'] for item in data]

async def analyze_comments_async(comments, prompt):
    """
    异步包装器函数,使用线程池执行同步的analyze_comments
    """
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, analyze_comments, comments, prompt)

def analyze_comments(comments, prompt):
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
    }

    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config=generation_config,
    )

    input_message = {
        "instruction": prompt,
        "comments": comments,
    }

    response = model.generate_content(json.dumps(input_message))
    try:
        return response.text
    except AttributeError as e:
        logging.error(f"Gemini API调用失败: {response} {str(e)}")
        return None

def extract_json_from_markdown(markdown_text):
    """
    从Markdown格式的字符串中提取JSON对象。

    Args:
        markdown_text: 包含Markdown标记的字符串。

    Returns:
        解析后的JSON对象, 如果解析失败则返回None。
    """
    try:
        # 移除markdown代码块标记
        text = re.sub(r'```json\n?', '', markdown_text)
        text = re.sub(r'```', '', text)
        # 解析JSON
        json_obj = json.loads(text)
        return json_obj
    except json.JSONDecodeError as e:
        logging.error(f"JSON解析失败: {str(e)}")
        return None

def merge_results(results):
    """
    合并多个分析结果
    
    Args:
        results: 包含多个分析结果的列表
        
    Returns:
        合并后的结果字典
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

    api_key = os.environ['GEMINI_API_KEY']
    genai.configure(api_key=api_key)

    comments = load_comments(args.input_json)
    # 最近的2000条评论
    comments = comments[-2000:]

    analysis_prompt = r"""# Role: 房地产评论分析师

## Profile

房地产评论分析师能够分析用户评论，提取关于房地产项目的关键信息，包括优缺点、价格、与其他楼盘的比较以及其他有价值的信息。分析师能够区分事实陈述和推论，并为每条信息赋予置信度评分。

## Rules

1. 所有提取的description请翻译成中文再放入json。
2. 置信度评分 (confidence\_score) 的值必须在 0 到 1 之间。
3. JSON 输出必须是合法且完整的 JSON 字符串，不包含任何其他信息。

## Workflow

1. 接收包含用户评论的 JSON 数据作为输入，JSON 数据至少包含评论 ID 和评论文本。
2. 分析评论文本，提取关于楼盘的关键信息。
3. 将提取的信息组织成以下结构的 JSON：

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
```
"""

    merge_prompt = "请帮我合并`analysis_comments_683455.json`文件中的重复项。该文件是一个 JSON 格式的数据，其中`advantages`、`disadvantages`、`price`和`other_information`四个键值下分别对应一个数组。请合并这些数组中的重复项，判断重复的标准是`description`字段内容相同或高度相似。请返回合并后的 JSON 数据。"

    try:
        # 创建多个并发任务
        logging.info(f"正在启动{args.concurrent}个并发分析请求...")
        tasks = []
        for i in range(args.concurrent):
            logging.debug(f"创建第{i+1}个分析任务")
            task = analyze_comments_async(comments, analysis_prompt)
            tasks.append(task)
        
        # 并发执行所有任务
        results = await asyncio.gather(*tasks)
        
        # 合并结果
        merged_result = merge_results(results)
        if merged_result is None:
            print(f"分析失败: 所有API调用均返回None")
            return

        # 保存合并后的结果
        output_path = f"analysis_{os.path.basename(args.input_json)}"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged_result, f, ensure_ascii=False, indent=2)
            logging.info(f"Write the merged results to {output_path}")

        # 使用merge_prompt合并结果
        logging.info("使用merge_prompt合并结果")
        merge_input_path = output_path
        merge_output_path = output_path.replace(".json", "_merged.json")
        with open(merge_input_path, 'r', encoding='utf-8') as f:
            analysis_comments = f.read()

        merge_result = analyze_comments(analysis_comments, merge_prompt)
        
        # 使用新函数解析JSON
        merge_result_json = extract_json_from_markdown(merge_result)

        if merge_result_json:
            logging.info(f"合并结果:\n{json.dumps(merge_result_json, ensure_ascii=False, indent=2)}")
            with open(merge_output_path, 'w', encoding='utf-8') as f:
                json.dump(merge_result_json, f, ensure_ascii=False, indent=2)
            logging.info(f"合并后的结果已保存至 {merge_output_path}")
        else:
            logging.error("合并失败")

    except Exception as e:
        print(f"分析失败: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main_async())
