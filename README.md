# e-mansion claw & analyzer

## 项目简介

e-mansion claw & analyzer 是一个 Python 项目，旨在从e-mansion网站抓取评论数据，并使用 Gemini API 对评论进行分析，提取楼盘的优缺点、价格信息以及其他有价值的信息。

## 项目目的

该项目的目的是为了帮助用户快速了解特定楼盘的用户评价，通过抓取和分析论坛评论，提取关键信息，为购房决策提供参考。

## 文件说明

* **caller.py**:  主程序入口文件，负责调用 `scraper.py` 抓取评论，调用 `check_comments.py` 检查评论完整性，以及调用 `gemini_analyzer.py` 分析评论。
* **scraper.py**:  负责从指定 URL 抓取网页评论，并将评论数据保存为 JSON 文件。支持增量抓取，避免重复抓取已存在的评论。
* **check_comments.py**:  负责检查评论 JSON 文件中评论 ID 的连续性，找出缺失的评论 ID，用于评估抓取结果的完整性。
* **gemini_analyzer.py**:  负责加载评论 JSON 文件，调用 Google Gemini API 对评论进行分析，提取楼盘的优缺点、价格等信息，并将分析结果保存为 JSON 文件。
* **analysis_comments_*.json**:  Gemini API 分析评论后生成的 JSON 结果文件，文件名包含时间戳。
* **comments_*.json**:  `scraper.py` 抓取的原始评论 JSON 文件，文件名包含楼盘 ID。

## 使用方法

1. **安装依赖**: 确保已安装以下 Python 库：
    ```bash
    pip install requests beautifulsoup4 google-generativeai
    ```
2. **配置 Gemini API 密钥**:  需要设置环境变量 `GEMINI_API_KEY` 为您的 Gemini API 密钥。
3. **运行 `caller.py`**:
    * URL 列表现在从 `urls.txt` 文件中读取。确保 `urls.txt` 文件位于同一目录下，并且包含要处理的 URL 列表，每个 URL 占一行。
    * 直接运行 `caller.py` 将读取 `urls.txt` 文件中的 URL 列表，抓取评论、检查缺失 ID 并进行分析。
      ```bash
      python caller.py
      ```
    * 使用 `--check-missing` 参数和文件名，可以单独检查指定评论 JSON 文件的缺失 ID。
      ```bash
      python caller.py --check-missing <filename>
      ```

## `caller.py` 参数说明

* `--check-missing`:  标志，如果设置，则只检查指定文件中的缺失 ID，而不进行抓取和分析。
* `filename`:  可选参数，当使用 `--check-missing` 时，指定要检查的评论 JSON 文件名。

## 注意事项

* 确保网络连接正常，以便程序可以访问目标论坛网站和 Gemini API。
* Gemini API 的使用可能需要付费，请注意您的 API 使用额度。
* 抓取频率不宜过高，避免对目标网站造成过大压力。

## 项目结构

```
property_claw/
├── analysis_comments_*.json
├── caller.py
├── check_comments.py
├── comments_*.json
├── gemini_analyzer.py
├── scraper.py
├── README.md
└── __pycache__/
```

请根据您的实际项目情况进行修改和完善 README 文件。
