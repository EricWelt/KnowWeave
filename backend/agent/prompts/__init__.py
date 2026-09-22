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

from . import zh_hans

# 未指定语言时使用的键
DEFAULT_LANG = "zh-Hans"

# 语言键 -> 文本表。新增语言时在此登记。
_PACKS: dict[str, Mapping[str, str]] = {
    "zh-Hans": zh_hans.TEXTS,
}

SUPPORTED_LANGS: tuple[str, ...] = tuple(_PACKS)


def get_texts(lang: str | None = None) -> Mapping[str, str]:
    """取某语言的文本表；未收录的语言回落到默认语言。"""
    if lang and lang in _PACKS:
        return _PACKS[lang]
    return _PACKS[DEFAULT_LANG]
