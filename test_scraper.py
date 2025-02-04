import pytest
from scraper import scrape_comments
import requests

# 模拟一个返回示例 HTML 的函数
@pytest.fixture
def mock_response():
    class MockResponse:
        def __init__(self, text, status_code):
            self.text = text
            self.status_code = status_code
            self.content = self.text.encode()  # 添加 content 属性

        def raise_for_status(self):
            if self.status_code != 200:
                raise requests.exceptions.HTTPError(f"HTTP error: {self.status_code}")



    def _mock_response(url, **kwargs):
        with open('test_html.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        if url == "valid_url":
            return MockResponse(html_content, 200)
        elif url == "different_html_structure_url":
            with open('test_different_html.html', 'r', encoding='utf-8') as f:
                different_html_content = f.read()
            return MockResponse(different_html_content, 200)
        elif url == "no_comments_url":
            return MockResponse("<html></html>", 200)
        elif url == "invalid_url":
            return MockResponse("", 404)
        elif url == "network_error_url":
            raise requests.exceptions.ConnectionError("Network error")
        else:
            return MockResponse("", 404)

    return _mock_response


# 测试 scrape_comments 函数在正常情况下的行为
def test_scrape_comments_success(monkeypatch, mock_response):
    monkeypatch.setattr("requests.get", mock_response)
    with open('test_html.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    comments, _ = scrape_comments("valid_url", test_mode=True, test_html=html_content)
    assert len(comments) == 20
    assert comments[0]['id'] == '10433'
    assert comments[1]['id'] == '10434'
    assert comments[2]['id'] == '10435'
    assert comments[3]['id'] == '10436'
    assert comments[4]['id'] == '10437'
    assert comments[5]['id'] == '10438'
    assert comments[19]['id'] == '10452'


# 测试 scrape_comments 函数在遇到无效 URL 时的行为
def test_scrape_comments_invalid_url(monkeypatch, mock_response):
    monkeypatch.setattr("requests.get", mock_response)
    monkeypatch.setattr("requests.get", mock_response)
    monkeypatch.setattr("requests.get", mock_response)
    comments, _ = scrape_comments("invalid_url")
    assert comments == []

# 测试 scrape_comments 函数在处理分页情况下的行为

def test_scrape_comments_pagination(monkeypatch, mock_response):
    monkeypatch.setattr("requests.get", mock_response)
    with open('test_html.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    comments, _ = scrape_comments("valid_url", test_mode=True, test_html=html_content)
    assert len(comments) == 20
    assert comments[0]['id'] == '10433'
    assert comments[1]['id'] == '10434'
    assert comments[2]['id'] == '10435'
    assert comments[3]['id'] == '10436'
    assert comments[4]['id'] == '10437'
    assert comments[5]['id'] == '10438'
    assert comments[19]['id'] == '10452'


# 测试 scrape_comments 函数在遇到没有评论的情况下的行为
def test_scrape_comments_no_comments(monkeypatch, mock_response):
    monkeypatch.setattr("requests.get", mock_response)
    comments, _ = scrape_comments("no_comments_url")
    assert comments == []



# 测试 scrape_comments 函数在遇到不同的 HTML 结构时的行为
def test_scrape_comments_different_html_structure(monkeypatch, mock_response):
    monkeypatch.setattr("requests.get", mock_response)
    with open('test_different_html.html', 'r', encoding='utf-8') as f:
        different_html_content = f.read()
    comments, _ = scrape_comments("different_html_structure_url", test_mode=True, test_html=different_html_content)
    assert len(comments) == 20
    # 检查所有评论ID是否都在结果中,不关心顺序
    expected_ids = {'10433', '10434', '3', '10436', '5', '10438', '7', '10440',
                   '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20'}
    actual_ids = {comment['id'] for comment in comments}
    assert actual_ids == expected_ids


# 测试 scrape_comments 函数在遇到网络错误时的行为
def test_scrape_comments_network_error(monkeypatch, mock_response):
    monkeypatch.setattr("requests.get", mock_response)
    comments, _ = scrape_comments("network_error_url")
    assert comments == []
