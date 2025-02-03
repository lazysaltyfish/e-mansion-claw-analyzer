# e-mansion claw & analyzer

## 项目简介

e-mansion claw & analyzer 是一个 Python 项目，旨在从 e-mansion 网站抓取评论数据，并使用 Gemini API 对评论进行分析，提取楼盘的优缺点、价格信息以及其他有价值的信息。

## 项目目的

该项目的目的是为了帮助用户快速了解特定楼盘的用户评价，通过抓取和分析论坛评论，提取关键信息，为购房决策提供参考。

## 文件说明

* **caller.py**: 主程序入口文件，负责调用 `scraper.py` 抓取评论，调用 `check_comments.py` 检查评论完整性，以及调用 `gemini_analyzer.py` 分析评论。
* **scraper.py**: 负责从指定 URL 抓取网页评论，并将评论数据保存为 JSON 文件。支持增量抓取，避免重复抓取已存在的评论。
* **check_comments.py**: 负责检查评论 JSON 文件中评论 ID 的连续性，找出缺失的评论 ID，用于评估抓取结果的完整性。
* **gemini_analyzer.py**: 负责加载评论 JSON 文件，调用 Google Gemini API 对评论进行分析，提取楼盘的优缺点、价格等信息，并将分析结果保存为 JSON 文件。
* **analysis_comments_*.json**: Gemini API 分析评论后生成的 JSON 结果文件，文件名包含时间戳。
* **comments_*.json**: `scraper.py` 抓取的原始评论 JSON 文件，文件名包含楼盘 ID。
* **urls.txt**:  包含待抓取 URL 列表的文件，每个 URL 占一行。

## 使用方法

1. **安装依赖**: 确保已安装以下 Python 库：

    ```bash
    pip install requests beautifulsoup4 google-generativeai
    ```

2. **配置 Gemini API 密钥**: 需要设置环境变量 `GEMINI_API_KEY` 为您的 Gemini API 密钥。

3. **运行 `caller.py`**:

    * 确保 `urls.txt` 文件位于同一目录下，并且包含要处理的 URL 列表，每个 URL 占一行。
    * 直接运行 `caller.py` 将读取 `urls.txt` 文件中的 URL 列表，抓取评论、检查缺失 ID 并进行分析。

      ```bash
      python caller.py
      ```

    * 使用 `--check-missing` 参数和文件名，可以单独检查指定评论 JSON 文件的缺失 ID。

      ```bash
      python caller.py --check-missing <filename>
      ```

## `caller.py` 参数说明

* `--check-missing`: 标志，如果设置，则只检查指定文件中的缺失 ID，而不进行抓取和分析。
* `<filename>`: 可选参数，当使用 `--check-missing` 时，指定要检查的评论 JSON 文件名。


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
├── urls.txt
└── __pycache__/
```

## 分析结果示例 (Example Analysis Result)

以下是 `analysis_comments_701418.json` 的分析结果示例，展示了 Gemini API 对楼盘评论进行分析后提取出的优点、缺点、价格和其他信息。

```json
{
  "property_name": "バウス日暮里",
  "information": {
    "advantages": [
      {
        "type": "inference",
        "description": "交通利便性が高い。日暮里駅と西日暮里駅が徒歩圏内で、山手線、京浜東北線、常磐線、千代田線など複数の路線が利用可能。",
        "confidence_score": 0.9
      },
      {
        "type": "inference",
        "description": "駅前に商業施設が多く、生活利便性が高い。",
        "confidence_score": 0.8
      },
      {
        "type": "inference",
        "description": "日暮里、西日暮里周辺の再開発により、将来的な資産価値上昇が期待できる。",
        "confidence_score": 0.7
      },
      {
        "type": "inference",
        "description": "ファミリー層にとって子育てしやすい環境。",
        "confidence_score": 0.7
      },
      {
        "type": "inference",
        "description": "全戸トランクルーム完備、ゲストルームや駐車場など共用施設が充実している。",
        "confidence_score": 0.8
      },
      {
        "type": "inference",
        "description": "静かな環境。",
        "confidence_score": 0.6
      },
      {
        "type": "inference",
        "description": "植栽や共用施設が充実している。",
        "confidence_score": 0.7
      }
    ],
    "disadvantages": [
      {
        "type": "inference",
        "description": "価格が高い。坪単価600万円以上と予想され、周辺の中古マンションと比べて割高。",
        "confidence_score": 0.9
      },
      {
        "type": "inference",
        "description": "大規模商業施設が少ない。",
        "confidence_score": 0.6
      },
      {
        "type": "inference",
        "description": "線路に近い部屋は騒音や排気ガスが気になる可能性がある。",
        "confidence_score": 0.7
      },
      {
        "type": "inference",
        "description": "ハザードマップに要注意。",
        "confidence_score": 0.7
      },
      {
        "type": "inference",
        "description": "管理費、修繕積立金、固定資産税が高い可能性がある。",
        "confidence_score": 0.7
      }
    ],
    "price": [
      {
        "type": "inference",
        "description": "坪単価600万円以上と予想される。",
        "confidence_score": 0.8
      },
      {
        "type": "inference",
        "description": "3LDK70平米で1億1千万円程度になる可能性がある。",
        "confidence_score": 0.7
      },
      {
        "type": "inference",
        "description": "75平米で1億2000万円～1億3000万円程度と予想される。",
        "confidence_score": 0.7
      },
      {
        "type": "inference",
        "description": "78平米、3LDKで1億2000万円程度になる可能性がある。",
        "confidence_score": 0.7
      }
    ],
    "other_information": [
      {
        "type": "fact",
        "description": "ルジェンテ西日暮里が坪400万円台、オープレジデンシア西日暮里ステーションフロント（中古）が1億円近くで売り出されている。",
        "confidence_score": 1.0
      },
      {
        "type": "fact",
        "description": "イニシア日暮里が坪510万円程度で販売されていた。",
        "confidence_score": 0.9
      },
      {
        "type": "inference",
        "description": "近隣築浅中古マンションで450万円前後、駅直結タワーマンションで600万円ぐらいの価格帯。",
        "confidence_score": 0.8
      },
      {
        "type": "inference",
        "description": "日暮里は駅力、都心アクセス力、周辺環境、再開発の有無などを考慮すると、割安感がある。",
        "confidence_score": 0.7
      },
      {
        "type": "fact",
        "description": "2030年に西日暮里駅再開発、2031年に東山手ルート開業予定。",
        "confidence_score": 1.0
      },
      {
        "type": "inference",
        "description": "周辺に築浅のスーパーやおしゃれなカフェ付き分譲マンションもある。",
        "confidence_score": 0.7
      },
      {
        "type": "fact",
        "description": "地下にできるのは駐車場ではなく駐輪場。",
        "confidence_score": 1.0
      },
      {
        "type": "inference",
        "description": "元々は寿屋という会社が持っていた土地で、3分の1ぐらいを中央日本土地建物が取得。寿屋は残る土地で賃貸マンション（単身世帯中心）を新たに建てる予定。バウスはファミリー世帯中心。なお、寿屋は近隣に賃貸マンションを過去に手掛けている。",
        "confidence_score": 0.8
      }
    ]
  }
}
```
