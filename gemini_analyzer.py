import os
import json
import argparse
import re
import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_comments(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [item['text'] for item in data]

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

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('input_json', help='输入JSON文件路径')
    args = parser.parse_args()

    api_key = os.environ['GEMINI_API_KEY']
    logging.info(f"API Key: {api_key}")
    genai.configure(api_key=api_key)

    comments = load_comments(args.input_json)
    # 最近的2000条评论
    comments = comments[-2000:]

    analysis_prompt = """
请分析以下用户评论(用json格式化给出，包含评论id，由于来源是帖子，所以有一些回复和聊天的存在）。
    
你需要提取关于该房地产项目的优缺点、价格信息、与其他楼盘的比较，以及其他有价值的信息。

请用 JSON 格式输出结果，包含以下字段：

* property_name：楼盘名称
* information：包含以下信息的字典
    * advantages: 优点列表，每个优点包含 type（fact 或 inference）和 description 和置信度 confidence_score
    * disadvantages: 缺点列表，每个缺点包含 type（fact 或 inference）和 description 和置信度 confidence_score
    * price: 价格信息列表，每个信息包含 type（fact 或 inference）和 description 和置信度 confidence_score
    * other_information: 其他有价值信息的列表，每个信息包含 type（fact 或 inference）和 description 和置信度 confidence_score

你的所有的分析结果一定一定要使用中文进行并显示，并且 confidence_score 的值在 0 到 1 之间。

请用JSON格式来输出结果，分析出来的结论一定要用中文，一定要保证JSON字符串是合法的，并且不包含其他的信息。

"""

    try:
        result = analyze_comments(comments, analysis_prompt)
        if result is None:  # 处理 Gemini API 调用失败的情况
            print(f"分析失败: Gemini API 调用返回 None")
            return
        from pprint import pprint
        pprint(result)

        output_path = f"analysis_{os.path.basename(args.input_json)}"
        with open(output_path, 'w', encoding='utf-8') as f:  # 指定编码为 utf-8
            try:
                # 移除 markdown 标记
                result_text = re.sub(r'```json\n?', '', result)
                result_text = re.sub(r'```', '', result_text)

                # 尝试将 result (response.text) 解析为 JSON 对象
                json_object = json.loads(result_text)
                # 将 JSON 对象以标准 JSON 格式写入文件
                json.dump(json_object, f, ensure_ascii=False, indent=2)
            except json.JSONDecodeError as e:
                logging.error(f"JSON decoding error: {e}, result text: {result}")
                print(f"分析失败: JSON decoding error: {e}")

    except Exception as e:
        print(f"分析失败: {str(e)}")


if __name__ == "__main__":
    main()
