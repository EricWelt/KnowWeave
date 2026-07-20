"""Embedding 模型封装。

- 模型：BAAI/bge-small-zh-v1.5，输出 512 维，中文效果好、体积小（~200MB）CPU 可跑；
- 惰性加载（lazy）：首次 embed 时才下载/加载模型，避免拖慢应用启动；
- normalize_embeddings=True：L2 归一化后，L2 距离等价于余弦相似度；
- 国内下载失败：设置环境变量 HF_ENDPOINT=https://hf-mirror.com。
"""
from .. import config

_model = None


def get_model():
    """单例加载 SentenceTransformer（线程安全由库内部保证）。"""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(config.EMBEDDING_MODEL)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """批量文本 → 归一化向量。"""
    if not texts:
        return []
    vectors = get_model().encode(texts, normalize_embeddings=True)
    return vectors.tolist()


def embed_query(query: str) -> list[float]:
    """单条查询向量（BGE v1.5 查询侧不强求 prefix）。"""
    return embed_texts([query])[0]
