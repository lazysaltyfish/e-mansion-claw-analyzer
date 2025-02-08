from typing import List, Dict, Optional

class PromptTemplate:
    def __init__(self, 
                 role: str,
                 profile: str,
                 rules: List[str],
                 input_format: Dict[str, str],
                 workflow: List[str],
                 output_format: str,
                 output_language: str = "中文"):
        self.role = role
        self.profile = profile
        self.rules = rules
        self.input_format = input_format
        self.workflow = workflow
        self.output_format = output_format
        self.output_language = output_language

    def generate(self) -> str:
        """生成完整的prompt字符串"""
        prompt_parts = [
            f"# Role: {self.role}\n",
            f"\n## Profile\n\n{self.profile}\n",
            "\n## Rules\n\n" + "\n".join(f"{i+1}. {rule}" for i, rule in enumerate(self.rules)),
            "\n## Input\n\n" + self._format_input_structure(),
            "\n## Workflow\n\n" + "\n".join(f"{i+1}. {step}" for i, step in enumerate(self.workflow)),
            f"\n## Output\n\n{self.output_format}"
        ]
        return "\n".join(prompt_parts)

    def _format_input_structure(self) -> str:
        """格式化输入结构说明"""
        lines = ["JSON 数据，包含以下字段：\n"]
        for field, desc in self.input_format.items():
            lines.append(f"- {field}: {desc}")
        return "\n".join(lines)

class PromptGenerator:
    @staticmethod
    def create_analysis_prompt() -> str:
        """创建分析评论的prompt"""
        template = PromptTemplate(
            role="房地产评论分析师",
            profile="房地产评论分析师能够分析用户评论,提取关于房地产项目的关键信息,包括优缺点、价格、与其他楼盘的比较以及其他有价值的信息。分析师能够区分事实陈述和推论,并为每条信息赋予置信度评分。",
            rules=[
                "所有提取的description请翻译成中文再放入json。",
                "置信度评分 (confidence_score) 的值必须在 0 到 1 之间。",
                "JSON 输出必须是合法且完整的 JSON 字符串,不包含任何其他信息。"
            ],
            input_format={
                "id": "评论 ID (字符串)",
                "text": "评论文本 (字符串)",
                "timestamp": "评论时间戳 (字符串, ISO 8601 格式)",
                "replies": "回复的评论 ID 列表 (字符串列表)",
                "images": "图片链接列表 (字符串列表)"
            },
            workflow=[
                "接收包含用户评论的 JSON 数据作为输入。",
                "分析评论文本，并结合 timestamp, replies, images 字段，提取关于楼盘的关键信息。\n    - 特别注意分析 replies 字段，理解评论之间的回复关系，这有助于理解上下文。\n    - 如果有 images 字段, 分析图片内容, 提取相关信息 (例如, 图片展示了房间的内部装修, 周围环境等)。",
                """将提取的信息组织成以下结构的 JSON:

```json
{
  "property_name": "楼盘名称",
  "information": {
    "advantages": [
      {"type": "fact/inference", "description": "优点描述", "confidence_score": 0.8},
      ...
    ],
    "disadvantages": [
      {"type": "fact/inference", "description": "缺点描述", "confidence_score": 0.6},
      ...
    ],
    "price": [
      {"type": "fact/inference", "description": "价格信息", "confidence_score": 0.9},
      ...
    ],
    "other_information": [
      {"type": "fact/inference", "description": "其他信息", "confidence_score": 0.7},
      ...
    ]
  }
}
```"""
            ],
            output_format="语言为中文的JSON string, 注意不是markdown格式"
        )
        return template.generate()

    @staticmethod
    def create_merge_prompt() -> str:
        """创建合并结果的prompt"""
        template = PromptTemplate(
            role="数据合并分析师",
            profile="数据合并分析师负责合并和去重分析结果，确保最终输出的数据准确且无重复。分析师能够识别相似内容，计算置信度平均值，并保持数据结构的完整性。",
            rules=[
                "合并时需要保持原有的JSON结构不变。",
                "检测并合并description字段内容相同或高度相似的项。",
                "合并项的confidence_score取平均值。",
                "合并后的JSON必须保持合法且完整。"
            ],
            input_format={
                "property_name": "楼盘名称 (字符串)",
                "information": "包含advantages、disadvantages、price和other_information的对象，每个字段都是数组"
            },
            workflow=[
                "接收包含分析结果的JSON数据作为输入。",
                "分别处理advantages、disadvantages、price和other_information四个数组。",
                "在每个数组中识别相似项：\n    - 通过比较description字段内容\n    - 计算相似项的confidence_score平均值",
                "保持type字段不变，合并相似的description项。",
                "将处理后的结果重新组织为原有的JSON结构。"
            ],
            output_format="语言为中文的JSON string，必须包含完整的property_name和information字段结构"
        )
        return template.generate()

    @staticmethod
    def customize_prompt(base_prompt: str, custom_rules: Optional[List[str]] = None) -> str:
        """基于基础prompt模板自定义新的prompt"""
        if not custom_rules:
            return base_prompt
            
        # 在Rules部分添加自定义规则
        rules_start = base_prompt.find("## Rules")
        rules_end = base_prompt.find("##", rules_start + 2)
        if rules_start == -1 or rules_end == -1:
            return base_prompt
            
        current_rules = base_prompt[rules_start:rules_end]
        new_rules = current_rules + "\n" + "\n".join(f"{len(current_rules.split('\n'))+i}. {rule}" for i, rule in enumerate(custom_rules))
        
        return base_prompt[:rules_start] + new_rules + base_prompt[rules_end:]