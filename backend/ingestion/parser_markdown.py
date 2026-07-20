"""Markdown → 纯文本：直接读取，保留原始格式。"""


def parse_markdown(file_bytes: bytes, filename: str) -> tuple[str, str]:
    """返回 (文本, 标题=文件名)。"""
    text = file_bytes.decode("utf-8", errors="replace")
    return text, filename
