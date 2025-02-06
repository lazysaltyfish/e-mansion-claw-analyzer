# Gemini 分析器 (带密钥池)

## 概要

为了提高 `gemini_analyzer.py` 的稳定性和可用性，我们引入了 API 密钥池轮询机制。由于 Gemini API 经常可能由于各种原因不可用，使用单个 API 密钥可能会导致请求失败。通过使用多个密钥并轮询它们，我们可以提高成功的机会。

## 修改内容

1.  **创建 `src/api_caller.py`:**

    *   创建了一个新文件 `src/api_caller.py` 来处理 API 调用和密钥管理。
    *   定义了 `GeminiAPIKeyPool` 类：
        *   `__init__(self, api_keys)`: 初始化密钥池，接收一个 API 密钥列表。
        *   `get_key(self)`: 获取下一个 API 密钥（循环使用）。
    *   定义了 `call_gemini_api` 函数：
        *   `call_gemini_api(model_name, generation_config, input_message, api_key_pool, prompt, comments)`:
            *   接收模型名称、生成配置、输入消息、`GeminiAPIKeyPool` 实例、prompt 和 comments 作为参数。
            *   使用 `api_key_pool.get_key()` 获取密钥。
            *   配置 `genai`。
            *   使用 `await model.generate_content_async` 发起 API 调用。
            *   实现重试逻辑（最多重试 3 次，每次间隔 10 秒）。
            *   如果所有尝试都失败，则返回 `None`。
        *   增加了 `save_error_context` 函数，用于记录错误信息，并添加了 `api_key_index` 参数来记录出错的 API 密钥索引。

2.  **修改 `src/gemini_analyzer.py`:**

    *   导入了 `GeminiAPIKeyPool` 和 `call_gemini_api`。
    *   在 `analyze_comments_async` 函数中：
        *   从环境变量 `GEMINI_API_KEYS` 中读取多个 API 密钥（以逗号分隔）。
        *   创建 `GeminiAPIKeyPool` 实例。
        *   移除 `genai.configure(api_key=api_key)`。
    *   修改了 `analyze_comments` 函数：
        *   接收 `api_key_pool` 参数。
        *   移除原有的重试逻辑。
        *   使用 `call_gemini_api` 函数进行 API 调用。
        *   修改了 `save_error_context` 函数的调用。

3.  **修改 `tests/test_gemini_analyzer.py`:**

    *   更新了 `test_analyze_comments_success`、`test_analyze_comments_retry_success` 和 `test_analyze_comments_retry_fail` 测试用例：
        *   创建了 `MockAPIKeyPool` 类来模拟密钥池。
        *   使用 `mocker.patch` 模拟 `src.api_caller.call_gemini_api` 函数。
        *   将模拟的 `api_key_pool` 实例传递给 `analyze_comments` 函数。

## 使用方法

1.  **设置环境变量:**

    *   设置 `GEMINI_API_KEYS` 环境变量，包含多个以逗号分隔的 API 密钥。
        ```bash
        export GEMINI_API_KEYS="key1,key2,key3"
        ```

2.  **运行脚本:**
    *   运行方式与之前相同。
    ```bash
    python src/gemini_analyzer.py <input_json> --concurrent <并发数>
    ```

## 注意事项
*   确保 `requirements.txt` 文件中包含所有必要的依赖项 (google-generativeai, pytest, pytest-asyncio, beautifulsoup4, requests, pytest-mock)。
*   错误日志会保存在 `error_logs` 目录下，并包含使用的 API 密钥索引。