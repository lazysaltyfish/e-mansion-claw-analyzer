import pytest
import json
import os
import shutil
from datetime import datetime
from src.gemini_analyzer import (
    load_comments,
    extract_json_from_markdown,
    merge_results,
    format_comments,
    save_error_context
)

# 用于测试的模拟 JSON 数据
@pytest.fixture
def mock_json_data():
    def _mock_json_data(data):
        return json.dumps(data)
    return _mock_json_data

# 清理错误日志目录的fixture
@pytest.fixture
def clean_error_logs():
    error_dir = "error_logs"
    if os.path.exists(error_dir):
        shutil.rmtree(error_dir)
    yield
    if os.path.exists(error_dir):
        shutil.rmtree(error_dir)

# 测试错误上下文保存功能
def test_save_error_context(clean_error_logs):
    prompt = "Test prompt"
    comments = ["Test comment 1", "Test comment 2"]
    error_msg = "Test error message"
    
    save_error_context(prompt, comments, error_msg)
    
    # 验证错误日志目录是否创建
    assert os.path.exists("error_logs")
    
    # 获取创建的日志文件
    log_files = os.listdir("error_logs")
    assert len(log_files) == 1
    
    # 读取日志文件内容
    with open(os.path.join("error_logs", log_files[0]), 'r', encoding='utf-8') as f:
        error_log = json.load(f)
    
    # 验证日志内容
    assert error_log["prompt"] == prompt
    assert error_log["comments"] == comments
    assert error_log["error_message"] == error_msg
    assert "timestamp" in error_log

# 测试 load_comments 函数在正常情况下的行为
def test_load_comments_success(tmp_path, mock_json_data):
    # 创建一个临时文件并写入模拟的 JSON 数据
    test_data = [{"id": 1, "text": "Comment 1"}, {"id": 2, "text": "Comment 2"}]
    file = tmp_path / "comments.json"
    file.write_text(mock_json_data(test_data))
    # 调用 load_comments 函数加载评论数据
    comments = load_comments(str(file))
    # 断言返回了正确的评论数据
    assert len(comments) == 2
    assert comments[0]["id"] == 1
    assert comments[0]["text"] == "Comment 1"
    assert comments[1]["id"] == 2
    assert comments[1]["text"] == "Comment 2"

# 测试 format_comments 函数的行为
def test_format_comments():
    # 测试数据
    comments = [
        {"id": 3, "text": "Third comment"},
        {"id": 1, "text": "First comment"},
        {"id": 2, "text": "Second comment"}
    ]
    
    # 调用 format_comments 函数
    formatted = format_comments(comments)
    
    # 验证结果
    assert len(formatted) == 3
    assert formatted[0] == "[1]:First comment"
    assert formatted[1] == "[2]:Second comment"
    assert formatted[2] == "[3]:Third comment"

# 测试 format_comments 函数的评论限制
def test_format_comments_limit():
    # 创建3500条评论
    comments = [
        {"id": i, "text": f"Comment {i}"} 
        for i in range(1, 3501)
    ]
    
    # 调用 format_comments 函数
    formatted = format_comments(comments)
    
    # 验证结果
    assert len(formatted) == 3000  # 只保留最后3000条
    assert formatted[0] == "[501]:Comment 501"  # 第一条应该是501
    assert formatted[-1] == "[3500]:Comment 3500"  # 最后一条应该是3500

# 测试 format_comments 函数处理无效评论
def test_format_comments_invalid():
    comments = [
        {"id": 1, "text": "Valid comment"},
        {"invalid": "No id or text"},
        {"id": 2},  # 没有text
        {"text": "No id"},  # 没有id
        {"id": 3, "text": "Another valid"}
    ]
    
    formatted = format_comments(comments)
    
    # 只有有效的评论应该被包含
    assert len(formatted) == 2
    assert formatted[0] == "[1]:Valid comment"
    assert formatted[1] == "[3]:Another valid"

# 测试 load_comments 函数在处理不存在的文件时的行为
def test_load_comments_file_not_found():
    # 调用 load_comments 函数加载一个不存在的文件,预期会抛出 FileNotFoundError 异常
    with pytest.raises(FileNotFoundError):
        load_comments("nonexistent_file.json")

# 测试 load_comments 函数在处理非 JSON 文件时的行为
def test_load_comments_invalid_json(tmp_path):
    # 创建一个临时文件并写入非 JSON 格式的数据
    file = tmp_path / "comments.json"
    file.write_text("This is not a JSON file.")
    # 调用 load_comments 函数加载评论数据,预期会抛出 json.JSONDecodeError 异常
    with pytest.raises(json.JSONDecodeError):
        load_comments(str(file))

# 测试 extract_json_from_markdown 函数在正常情况下的行为
def test_extract_json_from_markdown_success():
    # 定义一个包含 JSON 数据的 Markdown 文本
    markdown_text = """
```json
{"key": "value"}
```
    """
    # 调用 extract_json_from_markdown 函数提取 JSON 数据
    json_data = extract_json_from_markdown(markdown_text)
    # 断言返回了正确的 JSON 对象
    assert json_data == {"key": "value"}

# 测试 extract_json_from_markdown 函数在处理不包含 JSON 数据的 Markdown 文本时的行为
def test_extract_json_from_markdown_no_json():
    # 定义一个不包含 JSON 数据的 Markdown 文本
    markdown_text = "This is a plain text."
    # 调用 extract_json_from_markdown 函数提取 JSON 数据
    json_data = extract_json_from_markdown(markdown_text)
    # 断言返回了 None
    assert json_data is None

# 测试 extract_json_from_markdown 函数在处理包含多个 JSON 块的 Markdown 文本时的行为
def test_extract_json_from_markdown_multiple_json():
    # 定义一个包含多个 JSON 块的 Markdown 文本
    markdown_text = """
```json
{"key1": "value1"}
```
```json
{"key2": "value2"}
```
    """
    # 调用 extract_json_from_markdown 函数提取 JSON 数据
    json_data = extract_json_from_markdown(markdown_text)
    # 断言返回了第一个 JSON 对象
    assert json_data == {"key1": "value1"}

# 测试 merge_results 函数在正常情况下的行为
def test_merge_results_success(mock_json_data):
    # 模拟两个不同的分析结果,每个都是Markdown格式,内嵌JSON
    result1 = """
```json
{
  "property_name": "Property A",
  "information": {
    "advantages": [{"type": "fact", "description": "Good location", "confidence_score": 0.9}],
    "disadvantages": [],
    "price": [],
    "other_information": []
  }
}
```"""
    result2 = """
```json
{
  "property_name": "Property B",
  "information": {
    "advantages": [],
    "disadvantages": [{"type": "fact", "description": "High price", "confidence_score": 0.8}],
    "price": [{"type": "fact", "description": "1000 USD", "confidence_score": 0.9}],
    "other_information": []
  }
}
```"""
    # 调用 merge_results 函数合并结果
    merged_results = merge_results([result1, result2])
    # 验证合并后的结果是否符合预期
    assert merged_results["property_name"] == "Property A"  # 第一个非空property_name
    assert {"type": "fact", "description": "Good location", "confidence_score": 0.9} in merged_results["information"]["advantages"]
    assert {"type": "fact", "description": "High price", "confidence_score": 0.8} in merged_results["information"]["disadvantages"]
    assert {"type": "fact", "description": "1000 USD", "confidence_score": 0.9} in merged_results["information"]["price"]

# 测试 merge_results 函数在处理空列表时的行为
def test_merge_results_empty_list():
    # 调用 merge_results 函数合并一个空列表
    merged_results = merge_results([])
    # 断言返回了一个None
    assert merged_results is None