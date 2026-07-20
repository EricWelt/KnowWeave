"""文件解析入口：按扩展名分发。"""
from .parser_markdown import parse_markdown
from .parser_pdf import parse_pdf
from .parser_pptx import parse_pptx

PARSERS = {
    ".pdf": parse_pdf,
    ".pptx": parse_pptx,
    ".md": parse_markdown,
}


def parse_file(ext: str, file_bytes: bytes, filename: str) -> tuple[str, str]:
    """返回 (text, title)；不支持的扩展名抛 ValueError。"""
    parser = PARSERS.get(ext.lower())
    if parser is None:
        raise ValueError(f"不支持的文件类型: {ext}")
    return parser(file_bytes, filename)
