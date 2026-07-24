"""RAG 管线测试：分块策略 + ChromaDB 增删查。

不加载真实 BGE 模型：vector_store.add_chunks 直接接收向量，
测试用确定性假向量即可验证检索行为（真实 embedding 质量在冒烟脚本验证）。
"""
import pytest

from backend.rag.chunker import split_text
from backend.rag import vector_store


# ============ 分块器 ============

def test_split_empty_text():
    assert split_text("") == []
    assert split_text("   \n  ") == []


def test_split_short_text_single_chunk():
    chunks = split_text("这是一个很短的内容。")
    assert len(chunks) == 1
    assert chunks[0] == "这是一个很短的内容。"


def test_split_long_text_into_multiple_chunks():
    text = "操作系统是管理计算机硬件与软件资源的系统软件。\n" * 50  # 约 800 字符
    chunks = split_text(text)
    assert len(chunks) >= 2
    for c in chunks:
        assert len(c) <= 500  # 每块不超过 chunk_size


def test_split_has_overlap():
    text = "段落A内容" + "，" * 30 + "段" + "B" * 500 + "结尾内容"
    chunks = split_text(text, chunk_size=100, chunk_overlap=20)
    assert len(chunks) >= 2
    # 存在重叠 ⟺ 各块长度之和 > 原文长度（否则只是无重叠切分）
    assert sum(len(c) for c in chunks) > len(text)


def test_split_chinese_punctuation_boundary():
    # 中文句号应优先于字符级切分
    text = "第一句。" + "第二句。" + "第三句。" + "很长的第四句" * 200
    chunks = split_text(text)
    assert len(chunks) >= 2


# ============ ChromaDB ============

def _fake_embedding(text: str, dim: int = 8) -> list[float]:
    """确定性假向量：按文本哈希生成，同文本同向量。"""
    import hashlib
    h = hashlib.md5(text.encode("utf-8")).digest()
    vec = [0.0] * dim
    for i, b in enumerate(h[:dim]):
        vec[i] = b / 255.0
    return vec


def test_vector_add_and_query():
    chunks = ["进程调度算法包括先来先服务", "虚拟内存管理", "死锁的四个必要条件"]
    embeddings = [_fake_embedding(c) for c in chunks]
    ids = vector_store.add_chunks(
        note_id="n1",
        note_title="操作系统",
        chunks=chunks,
        embeddings=embeddings,
        source_type="manual",
    )
    assert len(ids) == 3
    assert ids[0] == "n1_0"

    # 用第一个块的向量查询 → 应返回它自己且最相似
    results = vector_store.query_chunks(embeddings[0], n_results=1)
    assert len(results) == 1
    assert results[0]["note_id"] == "n1"
    assert results[0]["chunk_index"] == 0
    assert "进程调度" in results[0]["content"]


def test_vector_delete_by_note():
    vector_store.add_chunks(
        note_id="n2",
        note_title="笔记2",
        chunks=["内容A", "内容B"],
        embeddings=[_fake_embedding("内容A"), _fake_embedding("内容B")],
        source_type="md",
    )
    vector_store.delete_by_note("n2")
    results = vector_store.query_chunks(_fake_embedding("内容A"), n_results=3)
    assert all(r["note_id"] != "n2" for r in results)


def test_vector_query_returns_metadata():
    vector_store.add_chunks(
        note_id="n3",
        note_title="计算机网络",
        chunks=["TCP 三次握手"],
        embeddings=[_fake_embedding("TCP 三次握手")],
        source_type="pdf",
    )
    results = vector_store.query_chunks(_fake_embedding("TCP 三次握手"), n_results=1)
    assert results[0]["note_title"] == "计算机网络"
    assert results[0]["source_type"] == "pdf"
