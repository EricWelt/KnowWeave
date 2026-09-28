"""Prompt 文本的集中管理。

设计：
- 所有会进入模型上下文的自然语言文本集中在此，按语言分文件；
- 每个语言文件导出一个 TEXTS 字典（键相同、值不同），便于对照翻译与测试校验；
- 需要填值的地方使用 string.Template 的 $name 占位符，这样文本里的 JSON 花括号无需转义；
- **不在此列**的内容：JSON 结构、字段名、action 取值、工具名，以及 [工具 X 返回]
  这类前后端共用的协议常量——它们必须与语言无关。

语言标识遵循 BCP 47：`en` / `zh-Hans`（简繁之别是书写脚本之别，故用脚本子标签）。
"""
from collections.abc import Mapping

from . import en, zh_hans

# 未指定语言时使用的键
DEFAULT_LANG = "zh-Hans"
# 英文键（工具描述等按语言选择文本的地方使用）
EN_LANG = "en"
# 英文键（工具描述等按语言选择文本的地方使用）
EN_LANG = "en"

# 语言键 -> 文本表。新增语言时在此登记。
_PACKS: dict[str, Mapping[str, str]] = {
    "zh-Hans": zh_hans.TEXTS,
    "en": en.TEXTS,
}

SUPPORTED_LANGS: tuple[str, ...] = tuple(_PACKS)


def normalize_lang(tag: str | None) -> str | None:
    """把 BCP 47 标签归一化为受支持的键；无法识别返回 None。

    Accept-Language 可能形如 `en-US,en;q=0.9,zh-Hans;q=0.8`，因此逐个候选匹配，
    取第一个受支持的。任何以 zh 开头（zh、zh-CN、zh-TW、zh-Hant……）的标签
    都归一到 zh-Hans：当前只有简体资源，繁体与其它中文变体同样回落到它。
    """
    for candidate in (tag or "").split(","):
        primary = candidate.split(";")[0].strip().lower()
        if not primary:
            continue
        if primary.startswith("zh"):
            return "zh-Hans"
        if primary.startswith("en"):
            return "en"
    return None


def resolve_lang(
    explicit: str | None = None,
    accept_language: str | None = None,
    default: str | None = None,
) -> str:
    """按「请求显式字段 > Accept-Language > 配置默认值」决定本次请求的语言。"""
    return (
        normalize_lang(explicit)
        or normalize_lang(accept_language)
        or normalize_lang(default)
        or DEFAULT_LANG
    )


def get_texts(lang: str | None = None) -> Mapping[str, str]:
    """取某语言的文本表；未收录的语言回落到默认语言。"""
    key = normalize_lang(lang) or lang
    if key and key in _PACKS:
        return _PACKS[key]
    return _PACKS[DEFAULT_LANG]
