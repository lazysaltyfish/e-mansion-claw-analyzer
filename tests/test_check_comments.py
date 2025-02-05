import pytest
import json
import logging
from src.check_comments import check_missing_ids

# 用于测试的模拟 JSON 数据
@pytest.fixture
def mock_json_data():
    def _mock_json_data(data):
        return json.dumps(data)
    return _mock_json_data

@pytest.fixture(autouse=True)
def setup_logging(caplog):
    caplog.set_level(logging.INFO)

# 测试 check_missing_ids 函数在正常情况下的行为
def test_check_missing_ids_success(tmp_path, mock_json_data, caplog):
    # 创建一个临时文件并写入模拟的 JSON 数据
    file = tmp_path / "test.json"
    file.write_text(mock_json_data([{"id": "1"}, {"id": "2"}, {"id": "3"}]))
    # 调用 check_missing_ids 函数检查缺失的 ID
    check_missing_ids(str(file))
    # 断言没有缺失的 ID
    assert "未发现缺失的 ID" in caplog.text

# 测试 check_missing_ids 函数在有缺失 ID 的情况下的行为
def test_check_missing_ids_missing(tmp_path, mock_json_data, caplog):
    # 创建一个临时文件并写入模拟的 JSON 数据,其中包含缺失的 ID
    file = tmp_path / "test.json"
    file.write_text(mock_json_data([{"id": "1"}, {"id": "3"}]))
    # 调用 check_missing_ids 函数检查缺失的 ID
    check_missing_ids(str(file))
    # 断言返回了缺失的 ID 列表
    assert "发现以下缺失的 ID: [2]" in caplog.text

# 测试 check_missing_ids 函数在处理空文件时的行为
def test_check_missing_ids_empty_file(tmp_path, caplog):
    # 创建一个临时空文件
    file = tmp_path / "test.json"
    file.write_text("")
    # 调用 check_missing_ids 函数检查缺失的 ID
    with pytest.raises(json.JSONDecodeError):
        check_missing_ids(str(file))

# 测试 check_missing_ids 函数在处理非 JSON 文件时的行为
def test_check_missing_ids_invalid_json(tmp_path, caplog):
    # 创建一个临时文件并写入非 JSON 格式的数据
    file = tmp_path / "test.json"
    file.write_text("This is not a JSON file.")
    # 调用 check_missing_ids 函数,预期会抛出 json.JSONDecodeError 异常
    with pytest.raises(json.JSONDecodeError):
        check_missing_ids(str(file))

# 测试 check_missing_ids 函数在文件不存在的行为
def test_check_missing_ids_file_not_found(caplog):
    # 调用 check_missing_ids 函数检查缺失的 ID
    check_missing_ids("nonexistent_file.json")
    # 断言返回了缺失的 ID 列表
    assert "文件 nonexistent_file.json 未找到，跳过缺失 ID 检查。" in caplog.text

# 测试 check_missing_ids 函数在评论中缺失id key时的行为
def test_check_missing_ids_missing_id_key(tmp_path, mock_json_data, caplog):
    # 创建一个临时文件并写入模拟的 JSON 数据,其中包含缺失的 ID
    file = tmp_path / "test.json"
    file.write_text(mock_json_data([{"id": "1"}, {"not_id": "3"}]))
    # 调用 check_missing_ids 函数检查缺失的 ID
    with pytest.raises(KeyError):
        check_missing_ids(str(file))