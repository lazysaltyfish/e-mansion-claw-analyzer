import pytest
from src.caller import main
from unittest.mock import patch, mock_open, MagicMock
import json
import logging
import os
import sys
import asyncio

class MockFile:
    def __init__(self, content='', mode='r'):
        self.content = content
        self.mode = mode
        self.lines = content.splitlines(True)
        self.current_line = 0
        self.written_content = []

    def __iter__(self):
        return self

    def __next__(self):
        if self.current_line >= len(self.lines):
            raise StopIteration
        line = self.lines[self.current_line]
        self.current_line += 1
        return line

    def read(self):
        return self.content

    def write(self, content):
        if 'w' not in self.mode and 'a' not in self.mode:
            raise IOError("File not open for writing")
        self.written_content.append(content)
        return len(content)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

# 创建一个异步的mock函数
async def async_mock_analyze(*args, **kwargs):
    return json.dumps({"result": "Analysis Result"})

# 测试 caller.py 的 main 函数的集成测试
@pytest.mark.asyncio
async def test_main_integration(tmp_path, monkeypatch):
    # 设置模拟函数的返回值
    comments = [{"id": 1, "text": "Comment 1"}]
    mock_scrape = MagicMock(return_value=(comments, True))
    mock_check = MagicMock(return_value=None)

    # 创建测试文件和目录
    urls_file = tmp_path / "urls.txt"
    urls_file.write_text("http://example.com/thread/123/")

    # 设置命令行参数
    test_args = ['caller.py', str(urls_file)]
    monkeypatch.setattr(sys, 'argv', test_args)

    # 创建一个字典来存储不同文件的内容
    mock_files = {
        "urls.txt": "http://example.com/thread/123/\n",
        "comments_123.json": "[]",
        "analysis_comments_123_merged.json": "{}"
    }

    def mock_open_func(filename, mode='r', encoding=None):
        content = mock_files.get(os.path.basename(filename), '')
        return MockFile(content, mode)

    # 调用 main 函数
    with patch('builtins.open', mock_open_func), \
         patch('src.scraper.scrape_comments', mock_scrape), \
         patch('src.gemini_analyzer.analyze_comments_async', async_mock_analyze), \
         patch('src.check_comments.check_missing_ids', mock_check):
        await main(str(urls_file))

    # 验证模拟函数是否被正确调用
    expected_filename = os.path.join('.', 'comments_123.json')
    mock_scrape.assert_called_once_with(
        "http://example.com/thread/123/",
        filename=expected_filename
    )