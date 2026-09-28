"""Prompt 文本包与请求语言解析的测试。

覆盖三层：
1. 两份语言包的一致性（键、占位符），防止运行期 KeyError/缺参数；
2. BCP 47 标签的归一化与优先级（显式字段 > Accept-Language > 默认值）；
3. 接口层：错误信息确实按请求语言返回。
"""
import re

import pytest

from backend.agent.prompts import (
    DEFAULT_LANG,
    EN_LANG,
    SUPPORTED_LANGS,
    en,
    get_texts,
    normalize_lang,
    resolve_lang,
    zh_hans,
)
from backend.tools.base import BaseTool, ToolRegistry

_PLACEHOLDER = re.compile(r"\$([a-z_]+)")


# ==================== 语言包一致性 ====================


def test_language_packs_have_identical_keys():
    """两种语言的键集合必须完全相同，否则某条路径会 KeyError。"""
    assert set(en.TEXTS) == set(zh_hans.TEXTS)


def test_placeholders_match_between_languages():
    """同一文案的占位符集合必须一致，否则 substitute 会缺参数。"""
    for key, zh_text in zh_hans.TEXTS.items():
        assert set(_PLACEHOLDER.findall(zh_text)) == set(
            _PLACEHOLDER.findall(en.TEXTS[key])
        ), key


def test_no_text_is_empty():
    for key, value in zh_hans.TEXTS.items():
        assert value.strip(), key
    for key, value in en.TEXTS.items():
        assert value.strip(), key


def test_english_pack_has_no_cjk():
    """英文包不应残留中文。"""
    for key, value in en.TEXTS.items():
        assert not re.search(r"[\u4e00-\u9fa5]", value), key


def test_language_constants():
    assert DEFAULT_LANG == "zh-Hans"
    assert EN_LANG == "en"
    assert set(SUPPORTED_LANGS) == {"zh-Hans", "en"}


# ==================== 语言标签归一化 ====================


@pytest.mark.parametrize(
    "tag,expected",
    [
        ("zh-Hans", "zh-Hans"),
        ("zh", "zh-Hans"),
        ("zh-CN", "zh-Hans"),
        ("zh-SG", "zh-Hans"),
        ("zh-TW", "zh-Hans"),  # 只有简体资源，繁体同样回落
        ("zh-Hant", "zh-Hans"),
        ("EN", "en"),
        ("en-US", "en"),
        ("en-GB", "en"),
        ("fr", None),
        ("", None),
        (None, None),
    ],
)
def test_normalize_lang(tag, expected):
    assert normalize_lang(tag) == expected


def test_normalize_lang_reads_accept_language_list():
    assert normalize_lang("fr-FR,en;q=0.9,zh-Hans;q=0.8") == "en"
    assert normalize_lang("fr-FR,zh-CN;q=0.9") == "zh-Hans"
    assert normalize_lang("fr-FR,de;q=0.9") is None


def test_resolve_lang_priority():
    # 请求体显式字段优先
    assert resolve_lang("en", "zh-Hans", "zh-Hans") == "en"
    # 显式字段无法识别时改用请求头
    assert resolve_lang("fr", "en", "zh-Hans") == "en"
    # 两者都无法识别时用配置默认值
    assert resolve_lang("fr", "de", "en") == "en"
    # 全都没有时回落默认语言
    assert resolve_lang(None, None, None) == DEFAULT_LANG


def test_get_texts_falls_back_to_default():
    assert get_texts("en") is en.TEXTS
    assert get_texts("zh-TW") is zh_hans.TEXTS
    assert get_texts("fr") is zh_hans.TEXTS
    assert get_texts(None) is zh_hans.TEXTS


# ==================== 工具描述双语 ====================


class _DemoTool(BaseTool):
    name = "demo"
    description = "中文描述"
    description_en = "English description"
    parameters = {"type": "object", "properties": {}}


class _ChineseOnlyTool(BaseTool):
    name = "chinese_only"
    description = "仅中文描述"
    parameters = {"type": "object", "properties": {}}


def test_tool_descriptions_follow_language():
    registry = ToolRegistry()
    registry.register(_DemoTool())
    registry.register(_ChineseOnlyTool())

    zh_desc = registry.descriptions("zh-Hans")
    en_desc = registry.descriptions(EN_LANG)

    assert "中文描述" in zh_desc
    assert "English description" in en_desc
    # 工具名与参数是代码常量，两种语言下都在
    assert "demo(" in zh_desc and "demo(" in en_desc
    # 缺英文描述时回落中文，而不是给出空描述
    assert "仅中文描述" in en_desc


# ==================== 接口层：错误信息按请求语言返回 ====================


async def test_api_error_message_follows_accept_language(client, auth_headers):
    resp = await client.post(
        "/agent/sessions",
        json={"goal": "   "},
        headers={**auth_headers, "Accept-Language": "en-US,en;q=0.9"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "The learning goal cannot be empty"


async def test_api_error_message_defaults_to_chinese(client, auth_headers):
    resp = await client.post(
        "/agent/sessions", json={"goal": ""}, headers=auth_headers
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "学习目标不能为空"


async def test_session_not_found_message_is_localized(client, auth_headers):
    resp = await client.get(
        "/agent/sessions/does-not-exist",
        headers={**auth_headers, "Accept-Language": "en"},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Session not found"


async def test_explicit_lang_field_overrides_header(client, auth_headers):
    """请求体里的 lang 优先于 Accept-Language。"""
    resp = await client.post(
        "/agent/sessions",
        json={"goal": "", "lang": "zh-Hans"},
        headers={**auth_headers, "Accept-Language": "en"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "学习目标不能为空"
