import pytest
from src.caller import main
from unittest.mock import patch, MagicMock
import json
import os
import argparse

class MockResponse:
    def __init__(self, text, status_code=200):
        self.content = text.encode('utf-8')
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code != 200:
            raise Exception(f"HTTP {self.status_code}")

class MockFile:
    def __init__(self, content='', mode='r', filename=None):
        self.content = content
        self.mode = mode
        self.filename = filename
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
        if self.filename in mock_files:
            return mock_files[self.filename]
        return self.content

    def write(self, content):
        if 'w' not in self.mode and 'a' not in self.mode:
            raise IOError("File not open for writing")
        self.written_content.append(content)
        if self.filename:
            # 总是追加内容，而不是覆盖
            mock_files[self.filename] = mock_files.get(self.filename, '') + content
        return len(content)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

# 创建一个异步的mock函数
async def async_mock_analyze(*args, **kwargs):
    return '''```json
{
  "property_name": "测试楼盘",
  "information": {
    "advantages": [{"type": "fact", "description": "位置好", "confidence_score": 0.9}],
    "disadvantages": [],
    "price": [],
    "other_information": []
  }
}
```'''

# 跟踪请求次数的全局变量
request_count = 0

def mock_requests_get(url, headers=None):
    global request_count
    request_count += 1
    
    # 第一次请求返回一个评论
    if request_count == 1:
        html_content = '''
        <html>
            <body>
                <li class="normal" value="1">
                    <div class="res-item-detail">
                        <p itemprop="commentText">Test comment 1</p>
                    </div>
                </li>
            </body>
        </html>
        '''
    else:
        # 后续请求返回空页面，这将导致循环终止
        html_content = '''
        <html>
            <body>
            </body>
        </html>
        '''
    return MockResponse(html_content)

# 全局变量来存储mock文件内容
mock_files = {}

# 测试 caller.py 的 main 函数的集成测试
@pytest.mark.asyncio
async def test_main_integration(tmp_path, monkeypatch):
    # 重置请求计数器和mock文件
    global request_count, mock_files
    request_count = 0
    mock_files.clear()

    # 创建测试文件
    urls_file = os.path.join(tmp_path, "urls.txt")
    with open(urls_file, 'w', encoding='utf-8') as f:
        f.write("http://example.com/thread/123/\n")

    # Mock ArgumentParser
    mock_args = MagicMock()
    mock_args.check_missing = False
    mock_args.filename = None
    mock_parse_args = MagicMock(return_value=mock_args)
    mock_parser = MagicMock()
    mock_parser.parse_args = mock_parse_args
    monkeypatch.setattr(argparse, 'ArgumentParser', MagicMock(return_value=mock_parser))

    def mock_open_func(filename, mode='r', encoding=None):
        # 标准化路径
        abs_path = os.path.abspath(filename)
        norm_path = abs_path.replace('\\', '/')

        if 'w' in mode:
            # 如果是写入模式, 且文件还不存在，则初始化为空字符串
            if norm_path not in mock_files:
                mock_files[norm_path] = ''
            return MockFile(mock_files.get(norm_path, ''), mode, norm_path)

        # 对于读取模式，根据文件类型返回适当的内容
        if filename == urls_file:
            return MockFile("http://example.com/thread/123/\n", mode, norm_path)
        elif norm_path.endswith('comments_123.json'):
            # 如果文件不存在，抛出FileNotFoundError
            if norm_path not in mock_files:
                raise FileNotFoundError(f"模拟文件未找到: {filename}")
            return MockFile(mock_files[norm_path], mode, norm_path)
        else:
            # 其他文件默认返回空列表的JSON字符串
            if norm_path not in mock_files:
              raise FileNotFoundError(f"模拟文件未找到: {filename}")
            return MockFile('[]', mode, norm_path)

    # 修改工作目录
    monkeypatch.chdir(tmp_path)

    # 创建必要的目录
    os.makedirs(os.path.join(tmp_path, "output", "intermediate_results"), exist_ok=True)
    os.makedirs(os.path.join(tmp_path, "output", "analysis_results"), exist_ok=True)

    # 调用 main 函数
    with patch('builtins.open', mock_open_func), \
         patch('requests.get', mock_requests_get), \
         patch('src.gemini_analyzer.analyze_comments_async', async_mock_analyze), \
         patch('os.makedirs', lambda path, exist_ok=True: None):  # Mock makedirs
        await main(str(urls_file))  # 将 urls_file 对象转换为字符串

    # 验证是否从URLs文件中读取了URL
    assert request_count > 0, "No HTTP requests were made"

    # 检查是否有任何以comments_123.json结尾的文件被写入
    comments_file_written = False
    comments_file_content = None
    for path, content in mock_files.items():
        if path.endswith('comments_123.json'):
            comments_file_written = True
            comments_file_content = content
            break

    assert comments_file_written, "No comments file was written"
    assert comments_file_content, "Comments file is empty"

    # 验证文件内容是否为有效的JSON
    json_content = json.loads(comments_file_content)
    assert isinstance(json_content, list), f"Output is not a JSON array, got: {comments_file_content}"
    assert len(json_content) > 0, "No comments were written to the output file"
    assert json_content[0]["id"] == "1", f"First comment ID is incorrect, got {json_content[0]['id']}"
    assert json_content[0]["text"] == "Test comment 1", f"First comment text is incorrect, got {json_content[0]['text']}"