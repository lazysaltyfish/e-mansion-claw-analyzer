import pytest
from src.prompt_generator import PromptGenerator, PromptTemplate

def test_prompt_template_generation():
    template = PromptTemplate(
        role="测试角色",
        profile="这是一个测试角色描述",
        rules=["规则1", "规则2"],
        input_format={"field1": "描述1", "field2": "描述2"},
        workflow=["步骤1", "步骤2"],
        output_format="输出格式说明"
    )
    
    prompt = template.generate()
    
    # 验证生成的prompt包含所有必要部分
    assert "# Role: 测试角色" in prompt
    assert "## Profile" in prompt
    assert "这是一个测试角色描述" in prompt
    assert "## Rules" in prompt
    assert "1. 规则1" in prompt
    assert "2. 规则2" in prompt
    assert "## Input" in prompt
    assert "field1: 描述1" in prompt
    assert "field2: 描述2" in prompt
    assert "## Workflow" in prompt
    assert "1. 步骤1" in prompt
    assert "2. 步骤2" in prompt
    assert "## Output" in prompt
    assert "输出格式说明" in prompt

def test_analysis_prompt_generation():
    prompt = PromptGenerator.create_analysis_prompt()
    
    # 验证分析prompt包含关键字段
    assert "房地产评论分析师" in prompt
    assert "置信度评分" in prompt
    assert "property_name" in prompt
    assert "advantages" in prompt
    assert "disadvantages" in prompt
    assert "price" in prompt
    assert "other_information" in prompt
    assert "replies" in prompt
    assert "images" in prompt

def test_merge_prompt_generation():
    prompt = PromptGenerator.create_merge_prompt()
    
    # 验证合并prompt包含关键字段
    assert "合并" in prompt
    assert "advantages" in prompt
    assert "disadvantages" in prompt
    assert "price" in prompt
    assert "other_information" in prompt
    assert "description" in prompt
    assert "置信度" in prompt

def test_customize_prompt():
    base_prompt = PromptGenerator.create_analysis_prompt()
    custom_rules = ["新规则1", "新规则2"]
    
    customized_prompt = PromptGenerator.customize_prompt(base_prompt, custom_rules)
    
    # 验证自定义prompt包含原有内容和新规则
    assert "房地产评论分析师" in customized_prompt
    assert "新规则1" in customized_prompt
    assert "新规则2" in customized_prompt

def test_prompt_template_with_empty_rules():
    template = PromptTemplate(
        role="测试角色",
        profile="描述",
        rules=[],
        input_format={},
        workflow=["步骤1"],
        output_format="输出"
    )
    
    prompt = template.generate()
    assert "# Role: 测试角色" in prompt
    assert "## Rules" in prompt

def test_customize_prompt_with_no_rules():
    base_prompt = PromptGenerator.create_analysis_prompt()
    result = PromptGenerator.customize_prompt(base_prompt)
    assert result == base_prompt