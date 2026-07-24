"""防御性 JSON 解析单元测试（LLM 输出不可靠的兜底策略）。"""
import pytest

from backend.agent.json_utils import parse_json_defensive


def test_parse_plain_json():
    assert parse_json_defensive('{"a": 1}') == {"a": 1}


def test_parse_with_code_fence():
    text = '好的，以下是结果：\n```json\n[{"q": 1}]\n```'
    assert parse_json_defensive(text) == [{"q": 1}]


def test_parse_with_preamble():
    text = '下面是为您生成的题目：[{"question": "x"}]，请查收'
    assert parse_json_defensive(text) == [{"question": "x"}]


def test_parse_object_embedded():
    text = '结果 {\"key\": \"value\"} 完毕'
    assert parse_json_defensive(text) == {"key": "value"}


def test_latex_escape_repair():
    # LLM 漏转义 LaTeX 反斜杠 → 修复后仍可解析
    raw = '[{"question": "求 \\frac{1}{2}", "options": ["A. 1", "B. 2"]}]'
    result = parse_json_defensive(raw)
    assert result[0]["question"] == "求 \\frac{1}{2}"


def test_garbage_raises():
    with pytest.raises(ValueError):
        parse_json_defensive("完全没有 JSON 的内容")

def test_extract_object_containing_array():
    # 回归：对象里含数组时，不能误提取内部数组（冒烟发现的 bug）
    text = '{"thought": "分析", "action": "generate_summary", "params": {"note_ids": ["x"]}}'
    data = parse_json_defensive(text)
    assert isinstance(data, dict)
    assert data["action"] == "generate_summary"
    assert data["params"]["note_ids"] == ["x"]


def test_extract_top_level_array_still_works():
    text = '[{"q": 1}, {"q": 2}] 完毕'
    assert parse_json_defensive(text) == [{"q": 1}, {"q": 2}]


def test_extract_respects_string_braces():
    # 引号内的花括号不参与配对
    text = '{"msg": "结果是 {x}"}'
    assert parse_json_defensive(text) == {"msg": "结果是 {x}"}


def test_extract_truncated_raises():
    # 被截断的 JSON（缺闭合括号）应报错而非静默成功
    with pytest.raises(ValueError):
        parse_json_defensive('{"a": [1, 2')
