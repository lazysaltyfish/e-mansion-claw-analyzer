import os
import json
import argparse
import re
import google.generativeai as genai
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_comments(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [item['text'] for item in data]

def analyze_comments(comments, prompt):
    """分析评论并返回结果。"""

    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config=generation_config,
    )

    chat_session = model.start_chat(history=[])

    # 将评论编号添加到提示中
    numbered_comments = []
    for i, comment in enumerate(comments):
        numbered_comments.append(f"评论{i + 1}:\n{comment}\n")

    message = prompt + "".join(numbered_comments)
    logging.debug(f"Sending message to Gemini: {message}")

    response = chat_session.send_message(message)

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

    analysis_prompt = """请分析以下用户评论，提取关于该房地产项目的优缺点、价格信息、与其他楼盘的比较，以及其他有价值的信息。

请用 JSON 格式输出结果，包含以下字段：

* property_name：楼盘名称
* confidence_score：置信度得分
* information：包含以下信息的字典
    * advantages: 优点列表，每个优点包含 type（fact 或 inference）和 description
    * disadvantages: 缺点列表，每个缺点包含 type（fact 或 inference）和 description
    * price: 价格信息列表，每个信息包含 type（fact 或 inference）和 description
    * comparisons: 与其他楼盘比较的列表，每个比较包含 property_name、comparison_points 和 confidence_score
    * other_information: 其他有价值信息的列表，每个信息包含 type（fact 或 inference）和 description

请务必保证返回一个合法的json字符串，不要有任何多余的输出

示例：
```json
{
  "property_name": "楼盘 A",
  "confidence_score": 0.9,
  "information": {
    "advantages": [
      {"type": "fact", "description": "交通便利"},
      {"type": "inference", "description": "环境优美"}
    ],
    "disadvantages": [
      {"type": "fact", "description": "价格较高"}
    ],
    "price": [
      {"type": "fact", "description": "均价 500 万"}
    ],
    "comparisons": [
      {
        "property_name": "楼盘 B",
        "comparison_points": ["价格", "位置"],
        "confidence_score": 0.8
      }
    ],
    "other_information": [
       {"type": "inference", "description": "未来有升值潜力"}
    ]
  }
}
```
请只返回 JSON 数据，不要包含任何其他文本。"""


    try:
        result = analyze_comments(comments, analysis_prompt)
        if result is None:  # 处理 Gemini API 调用失败的情况
            print(f"分析失败: Gemini API 调用返回 None")
            return

        print(f"Result from Gemini: {result}")
        try:
            # 提取 JSON 部分并处理注释
            json_str = result.replace('//', '')  # 去除单行注释
            json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)  # 去除多行注释
            json_str = re.search(r'\{.*\}', json_str, re.DOTALL).group(0)  # 提取 JSON 主体, 使用group(0)获取匹配的字符串
            parsed_result = json.loads(json_str)

        except json.JSONDecodeError:
            parsed_result = []
            print(f"无法解析 JSON 结果: {result}")
        except AttributeError:  # result 为 None 时，访问 result.replace 会抛出 AttributeError
            parsed_result = []
            print(f"Gemini API 调用失败: {result}")

        print(f"Parsed Result: {parsed_result}")


        output_path = f"analysis_{os.path.basename(args.input_json)}"
        with open(output_path, 'w', encoding='utf-8') as f:  # 指定编码为 utf-8
            json.dump(parsed_result, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"分析失败: {str(e)}")



if __name__ == "__main__":
    main()

