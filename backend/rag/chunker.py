"""文档分块策略。

使用 RecursiveCharacterTextSplitter（LangChain 唯一引入的组件，可自实现替代）：
- chunk_size=500：BGE-small-zh 最大输入 512 tokens，中文约 1.5 字符/token，
  500 字符 ≈ 333 tokens，留有余量；
- chunk_overlap=100：避免关键信息恰好被切在分块边界；
- separators 按「段落 → 行 → 句号/逗号 → 字符」逐级切分，优先自然断句。
"""
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .. import config


def split_text(
    text: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[str]:
    """将文本切成若干块；空文本返回 []。"""
    if not text or not text.strip():
        return []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size or config.CHUNK_SIZE,
        chunk_overlap=chunk_overlap or config.CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", "。", ".", "，", " ", ""],
    )
    return splitter.split_text(text)
