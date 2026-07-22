"""防御性 JSON 解析（从旧 ai-service 的经验提炼）。

LLM 输出 JSON 的常见毛病：
1. 前后带开场白/代码块 → 提取首个 [ 或 { 到对应结束符
2. LaTeX 反斜杠未转义 → 单反斜杠会被 JSON 解析器当成转义符吃掉
3. 多余逗号 / 换行 → 提取后清理再试

策略（带坏转义检测）：
- 若存在「单反斜杠后跟非合法 JSON 转义字符」（即 LLM 漏转义），先做 LaTeX 修复再解析；
- 否则直接解析 → 提取子串解析 → 修复后解析，逐级兜底。
"""
import json
import re


def _has_bad_escapes(s: str) -> bool:
    """检测需要先修复再解析的情况：
    - 单反斜杠后跟非合法 JSON 转义字符
    - 反斜杠后跟 2 个以上字母（JSON 转义都是单字母，多字母几乎必然是
      LLM 漏转义的 LaTeX 命令，如 \\frac；单独的 \\f 是合法转义但 \\frac 不是）
    """
    if re.search('\\\\(?!["\\\\/bfnrtu])', s):
        return True
    if re.search('(?<!\\\\)\\\\[a-zA-Z]{2,}', s):
        return True
    return False



def _fix_latex_escapes(s: str) -> str:
    """把 LLM 漏转义的 LaTeX 反斜杠补上（恢复合法 JSON 转义符）。"""
    s = s.replace('\\', '\\\\')   # 单反斜杠 -> 双反斜杠
    s = s.replace('\\\\"', '\\"')   # 恢复转义引号
    s = s.replace('\\\\n', '\\n')   # 恢复换行
    s = s.replace('\\\\t', '\\t')   # 恢复制表符
    s = s.replace('\\\\u', '\\u')   # 恢复 unicode 转义
    return s


def extract_json_str(text: str) -> str:
    """从文本中截取最外层 JSON 数组/对象子串。找不到抛 ValueError。

    用括号配对扫描（而非简单 find/rfind）：对象里含数组时（如
    {"note_ids": ["x"]}），简单 find('[') 会错误地截取内部数组。
    扫描器同时尊重字符串字面量（引号内的 { } [ ] 不参与配对）。
    """
    text = text.strip()
    # 去掉 markdown 代码块围栏
    fence = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()

    start = -1
    for i, ch in enumerate(text):
        if ch in "{[":
            start = i
            break
    if start == -1:
        raise ValueError("未找到 JSON 结构")

    open_ch = text[start]
    close_ch = "}" if open_ch == "{" else "]"
    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == open_ch:
                depth += 1
            elif ch == close_ch:
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
    raise ValueError("JSON 结构不完整（可能被截断）")



def parse_json_defensive(text: str) -> object:
    """返回解析后的对象；全部尝试失败抛 ValueError。"""
    try:
        candidate = extract_json_str(text)
    except ValueError:
        candidate = text.strip()

    # 先修复再解析（LLM 漏转义时直接解析会静默吃转义符）
    if _has_bad_escapes(candidate):
        try:
            return json.loads(_fix_latex_escapes(candidate))
        except json.JSONDecodeError:
            pass

    # 逐级兜底：直接 → 提取 → 修复
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    try:
        return json.loads(_fix_latex_escapes(extract_json_str(text)))
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f'JSON 解析失败（尝试了提取与 LaTeX 修复）: {e}') from e