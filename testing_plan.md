# 测试计划

## 概述

本项目包含四个 Python 文件：`caller.py`、`check_comments.py`、`gemini_analyzer.py` 和 `scraper.py`。本计划旨在为这些文件添加单元测试和端到端测试，以提高代码质量和可靠性。

## 测试范围

### 单元测试

*   **`check_comments.py`**:
    *   `check_missing_ids` 函数：检查 JSON 文件中缺失的 ID。
*   **`gemini_analyzer.py`**:
    *   `load_comments` 函数：加载 JSON 文件中的评论数据。
    *   `extract_json_from_markdown` 函数：从 Markdown 文本中提取 JSON 数据。
    *   `merge_results` 函数：合并多个分析结果。
*   **`scraper.py`**:
    *   `scrape_comments` 函数：从指定 URL 抓取评论数据。

### 端到端测试

*   **`caller.py`**:
    *   `main` 函数：模拟整个流程，包括调用 `scraper.py` 和 `gemini_analyzer.py`。

## 测试框架

使用 `pytest` 作为测试框架。

## 测试用例

### 单元测试

#### `check_comments.py`

*   **`check_missing_ids`**:
    *   正常情况：提供一个包含有效 ID 的 JSON 文件，预期没有缺失 ID。
    *   边界情况：提供一个空文件，预期没有缺失 ID。
    *   异常情况：提供一个包含缺失 ID 的 JSON 文件，预期返回缺失 ID 列表。
    *   异常情况：提供一个非 JSON 格式的文件，预期抛出异常。

#### `gemini_analyzer.py`

*   **`load_comments`**:
    *   正常情况：提供一个有效的 JSON 文件路径，预期返回正确的评论数据。
    *   异常情况：提供一个不存在的文件路径，预期抛出异常。
    *   异常情况：提供一个非 JSON 格式的文件路径，预期抛出异常。
*   **`extract_json_from_markdown`**:
    *   正常情况：提供一个包含有效 JSON 数据的 Markdown 文本，预期返回正确的 JSON 对象。
    *   边界情况：提供一个空的 Markdown 文本，预期返回 None 或空 JSON 对象。
    *   异常情况：提供一个不包含 JSON 数据的 Markdown 文本，预期返回 None 或抛出异常。
*   **`merge_results`**:
    *   正常情况：提供一个包含多个结果的列表，预期返回合并后的结果。
    *   边界情况：提供一个空列表，预期返回空结果。
    *   边界情况：提供一个只包含一个结果的列表，预期返回该结果。

#### `scraper.py`

*   **`scrape_comments`**:
    *   正常情况：提供一个有效的 URL，预期返回正确的评论数据并保存到文件。
    *   异常情况：提供一个无效的 URL，预期抛出异常或返回空数据。
    *   边界情况：测试分页功能，确保能够正确抓取所有页面的评论。

### 端到端测试

#### `caller.py`

*   **`main`**:
    *   正常情况：模拟整个流程，包括调用 `scraper.py` 抓取评论，调用 `gemini_analyzer.py` 分析评论，预期最终生成正确的分析结果文件。
    *   异常情况：模拟 `scraper.py` 抓取失败的情况，预期程序能够正确处理异常。
    *   异常情况：模拟 `gemini_analyzer.py` 分析失败的情况，预期程序能够正确处理异常。

## 测试数据

*   单元测试可以使用模拟数据或小型真实数据。
*   端到端测试可以使用模拟数据或预先准备好的测试网页。

## 持续集成

*   将测试添加到 `.gitignore` 文件中，以避免将测试文件提交到代码仓库。
*   在代码仓库中添加一个 `requirements.txt` 文件，列出项目依赖，包括 `pytest`。
*   配置持续集成服务（如 GitHub Actions），在每次代码提交时自动运行测试。