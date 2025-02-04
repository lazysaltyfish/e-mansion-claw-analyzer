# e-mansion claw & analyzer

## 项目简介

e-mansion claw & analyzer 是一个 Python 项目，旨在从 e-mansion 网站抓取评论数据，并使用 Gemini API 对评论进行分析，提取楼盘的优缺点、价格信息以及其他有价值的信息。

## 项目目的

该项目的目的是为了帮助用户快速了解特定楼盘的用户评价，通过抓取和分析论坛评论，提取关键信息，为购房决策提供参考。

## 文件说明

*   **caller.py**: 主程序入口文件，负责调用  `scraper.py`  抓取评论，调用  `check_comments.py`  检查评论完整性，以及调用  `gemini_analyzer.py`  分析评论。
*   **scraper.py**: 负责从指定 URL 抓取网页评论，并将评论数据保存为 JSON 文件。支持增量抓取，避免重复抓取已存在的评论。文件名现在包含从 URL 中提取的楼盘 ID。
*   **check_comments.py**: 负责检查评论 JSON 文件中评论 ID 的连续性，找出缺失的评论 ID，用于评估抓取结果的完整性。
*   **gemini_analyzer.py**: 负责加载评论 JSON 文件，调用 Google Gemini API 对评论进行分析，提取楼盘的优缺点、价格等信息，并将分析结果保存为 JSON 文件。现在还使用合并提示合并分析结果。
*   **analysis_comments_*.json**: Gemini API 分析评论后生成的 JSON 结果文件，文件名包含时间戳。
*   **comments_*.json**:  `scraper.py`  抓取的原始评论 JSON 文件，文件名包含楼盘 ID。
*   **urls.txt**: 包含待抓取 URL 列表的文件，每个 URL 占一行。

## 使用方法

1. **安装依赖**: 确保已安装以下 Python 库：

    ```bash
    pip install requests beautifulsoup4 google-generativeai
    ```

2. **配置 Gemini API 密钥**: 需要设置环境变量  `GEMINI_API_KEY`  为您的 Gemini API 密钥。

3. **运行  `caller.py`**

    *   确保 `urls.txt` 文件位于项目的根目录 (即 `property_claw` 文件夹) 下，并且包含要处理的 URL 列表，每个 URL 占一行。
    *   从项目的根目录运行 `caller.py`，它将读取 `urls.txt` 文件中的 URL 列表，抓取评论、检查缺失 ID 并进行分析。

        ```bash
        python src/caller.py
        ```

    *   使用 `--check-missing` 参数和文件名，可以单独检查指定评论 JSON 文件的缺失 ID。

        ```bash
        python src/caller.py --check-missing <filename>
        ```

## `caller.py` 参数说明

*   `--check-missing`: 标志，如果设置，则只检查指定文件中的缺失 ID，而不进行抓取和分析。
*   `<filename>`: 可选参数，当使用  `--check-missing`  时，指定要检查的评论 JSON 文件名。

## 运行测试

要运行测试，请使用以下命令：

```bash
pytest tests
```

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

以下是 `analysis_comments_683455_merged.json` 的分析结果示例，展示了 Gemini API 对楼盘评论进行分析后提取出的优点、缺点、价格和其他信息。

```json
{
  "property_name": "ザ・パークハウス 武蔵小杉タワー",
  "information": {
    "advantages": [
      {
        "type": "fact",
        "description": "都心へのアクセスが非常に良い。横須賀線は武蔵小杉に停車しないため、他の多くの駅と比べて片道12～15分短縮できる。",
        "confidence_score": 1.0
      },
      {
        "type": "fact",
        "description": "武蔵小杉は再開発によりさらに発展しており、将来性も高い。",
        "confidence_score": 0.8
      },
      {
        "type": "fact",
        "description": "武蔵小杉は、東横線沿線の中でも特に治安が良い駅が多い。",
        "confidence_score": 0.9
      },
      {
        "type": "fact",
        "description": "武蔵小杉駅周辺には、グランツリーなどの大型商業施設があり、買い物にも便利。",
        "confidence_score": 0.9
      },
      {
        "type": "fact",
        "description": "駅前にグランツリーなどの大型商業施設があり、日用品の買い物にも不自由しない。",
        "confidence_score": 1.0
      },
      {
        "type": "inference",
        "description": "通勤/通学の利便性が高い。目的地までの所要時間が短く、多方面への路線が充実している。",
        "confidence_score": 0.9
      },
      {
        "type": "inference",
        "description": "生活の利便性が高い。駅に近いと街全体を徒歩5分圏内で利用できる。",
        "confidence_score": 0.9
      },
      {
        "type": "inference",
        "description": "子育て環境が良い。習い事の充実など。",
        "confidence_score": 0.8
      },
      {
        "type": "fact",
        "description": "タワーマンションとして高級感があり、設備も良い。",
        "confidence_score": 1.0
      },
      {
        "type": "fact",
        "description": "共有部の高級感はパークタワー品川天王洲以上。",
        "confidence_score": 0.8
      },
      {
        "type": "fact",
        "description": "武蔵小杉は、2050年の東京23区への人口増加率で8位に入るエリアとして、将来性も高い。",
        "confidence_score": 0.9
      },
      {
        "type": "fact",
        "description": "2025年10月完成予定の三井不動産の新築タワーマンション（小杉町一丁目計画）も控えている。",
        "confidence_score": 0.9
      },
      {
        "type": "fact",
        "description": "川崎市は、2024年4月から第二子以降の保育料を無償化している。",
        "confidence_score": 1
      },
      {
        "type": "fact",
        "description": "駅前の再開発で公園整備や商業施設の建設なども計画されている。",
        "confidence_score": 0.8
      },
      {
        "type": "fact",
        "description": "武蔵小杉は災害時のリスクも指摘されるが、タワーマンションは水害などの被害を受けにくく、比較的安全。",
        "confidence_score": 0.7
      },      
      {
        "type": "fact",
        "description": "免震構造で耐震性が高い。",
        "confidence_score": 1.0
      },
      {
        "type": "fact",
        "description": "タワーマンションは共用施設が充実している。",
        "confidence_score": 0.9
      },
      {
        "type": "fact",
        "description": "武蔵小杉周辺には大きな公園があり、子育て環境が良い。",
        "confidence_score": 0.8
      },
      {
        "type": "fact",
        "description": "タワーマンションは高層階からの眺望が良い。",
        "confidence_score": 0.9
      },
      {
        "type": "fact",
        "description": "川崎市は子育て支援に力を入れている。",
        "confidence_score": 0.8
      },
      {
        "type": "fact",
        "description": "免震構造である。",
        "confidence_score": 1.0
      },
      {
        "type": "fact",
        "description": "全熱交換システムで快適。",
        "confidence_score": 0.9
      },
      {
        "type": "fact",
        "description": "アウトフレーム設計のため、部屋が広く感じられる。",
        "confidence_score": 1.0
      },
      {
        "type": "fact",
        "description": "武蔵小杉周辺には大きな病院があり、医療環境も充実している。",
        "confidence_score": 0.8
      },
      {
        "type": "fact",
        "description": "小学校の学区が良い。",
        "confidence_score": 1.0
      },
      {
        "type": "fact",
        "description": "共有部が高級である。",
        "confidence_score": 0.9
      }
    ],
    "disadvantages": [
      {
        "type": "fact",
        "description": "駅から動線上（駅前の道）の信号待ちが結構長い。",
        "confidence_score": 1.0
      },
      {
        "type": "fact",
        "description": "武蔵小杉駅周辺は、土日は人で混雑しやすい。",
        "confidence_score": 0.9
      },
      {
        "type": "fact",
        "description": "駅前のパチンコ屋が景観が悪い。",
        "confidence_score": 0.7
      },
      {
        "type": "fact",
        "description": "南武線沿道は、工場に囲まれた土地で、生活感が強い。",
        "confidence_score": 0.9
      },
      {
        "type": "inference",
        "description": "小学校が遠い。",
        "confidence_score": 0.8
      },
      {
        "type": "fact",
        "description": "新築価格は周辺中古よりも高い。",
        "confidence_score": 0.9
      },
      {
        "type": "fact",
        "description": "エレベーターホールの天井が低い。",
        "confidence_score": 0.8
      },
      {
        "type": "fact",
        "description": "低層階（43階まで）は低層階扱い、44階以上のデラックス・エグゼクティブフロア。",
        "confidence_score": 1.0
      },
      {
        "type": "fact",
        "description": "駐車場がタワーマンションにしては狭い。",
        "confidence_score": 0.7
      },
      {
        "type": "fact",
        "description": "2019年の台風で浸水被害があった。",
        "confidence_score": 1.0
      },
      {
        "type": "fact",
        "description": "北口に駅ビルがなく、買い物利便性が低い。",
        "confidence_score": 1.0
      },
      {
        "type": "fact",
        "description": "低層階は目の前に建物があり眺望が悪い。",
        "confidence_score": 1.0
      },
      {
        "type": "fact",
        "description": "全熱交換ではない部屋もある。",
        "confidence_score": 1.0
      }      
    ],
    "price": [
      {
        "type": "fact",
        "description": "販売価格は平均坪単価600万円～800万円程度。",
        "confidence_score": 0.8
      },
      {
        "type": "fact",
        "description": "70m2で1億2,500万円ほど。",
        "confidence_score": 0.9
      },
      {
        "type": "fact",
        "description": "1LDKは7000万円前後、2LDKは9000万円台から、3LDKは1億円台から。",
        "confidence_score": 0.9
      },
      {
        "type": "fact",
        "description": "1期1次は700m2平均くらい。",
        "confidence_score": 0.9
      },
      {
        "type": "fact",
        "description": "デラックス44階77m2で1.3億円くらい。",
        "confidence_score": 0.9
      },
      {
        "type": "fact",
        "description": "デラックスフロア44階77m2で1.3億円くらい。",
        "confidence_score": 0.9
      },
      {
        "type": "fact",
        "description": "1LDKは45m2で7,000万円弱、60m2で8,000万円台です。",
        "confidence_score": 0.9
      },
      {
        "type": "fact",
        "description": "3LDKで70m2台の物件が1億2,580万円で成約しています。",
        "confidence_score": 1.0
      }
    ],
    "other_information": [
      {
        "type": "inference",
        "description": "湾岸エリアと比較して割高。",
        "confidence_score": 0.8
      },
      {
        "type": "fact",
        "description": "武蔵小杉は、都心主要駅へのダイレクトアクセスカバー率が首都圏随一。",
        "confidence_score": 1.0
      },
      {
        "type": "fact",
        "description": "タワーマンションは地震に強い。",
        "confidence_score": 0.9
      },
      {
        "type": "fact",
        "description": "武蔵小杉は、日本医科大学付属病院や関東労災病院など、大きな病院も多い。",
        "confidence_score": 0.8
      },
      {
        "type": "fact",
        "description": "売主は三井地所レジデンシャル。",
        "confidence_score": 1.0
      },
      {
        "type": "inference",
        "description": "武蔵小杉タワーの共用施設の充実度は武蔵小杉のマンションの中でも最高クラス。",
        "confidence_score": 0.9
      },
      {
        "type": "fact",
        "description": "武蔵小杉は子育てファミリーからDINKS、高齢者まで幅広い層に人気。",
        "confidence_score": 0.9
      },
      {
        "type": "fact",
        "description": "武蔵小杉は再開発が進んでおり、将来的な発展が期待される。",
        "confidence_score": 0.8
      },
      {
        "type": "fact",
        "description": "武蔵小杉周辺には病院が多い。",
        "confidence_score": 0.7
      },
      {
        "type": "fact",
        "description": "2024年3月築。",
        "confidence_score": 1.0
      },
      {
        "type": "fact",
        "description": "総戸数1,400戸を超える大規模タワーマンション。",
        "confidence_score": 1.0
      },
      {
        "type": "fact",
        "description": "武蔵小杉小学校区。",
        "confidence_score": 1.0
      },
      {
        "type": "fact",
        "description": "新築マンションの建設コストは坪300万円くらいです。",
        "confidence_score": 0.9
      },
      {
        "type": "fact",
        "description": "一部の部屋は床暖房が設置されています。",
        "confidence_score": 0.9
      },
      {
        "type": "fact",
        "description": "全熱交換器は設置されていません。",
        "confidence_score": 0.95
      },
      {
        "type": "fact",
        "description": "新空港線の延伸計画があります。",
        "confidence_score": 0.8
      }
    ]
  }
}
