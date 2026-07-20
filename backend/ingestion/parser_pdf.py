"""PDF → 文本（，PyMuPDF）。

要点：
- page.get_text() 原生支持中文 UTF-8；
- 不清除空白（留给 chunker 处理连续空行）；
- 不提取图片；扫描版 PDF（图片型）get_text 返回空 → 上层报友好错误；
- 加密 PDF：needs_pass 为 True → 抛 ValueError。
"""
import fitz


def parse_pdf(file_bytes: bytes, filename: str) -> tuple[str, str]:
    """返回 (纯文本, 标题)。解析失败抛 ValueError。"""
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        raise ValueError(f"无法解析 PDF 文件: {e}") from e

    if doc.needs_pass:
        raise ValueError("该 PDF 已加密，无法解析")

    text_parts = [page.get_text() for page in doc]
    text = "\n".join(text_parts)

    # 元数据 title 优先，空则用文件名
    meta_title = (doc.metadata or {}).get("title") or ""
    title = meta_title.strip() if meta_title.strip() else filename
    return text, title
