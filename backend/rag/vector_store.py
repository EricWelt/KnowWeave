"""ChromaDB 操作封装。

关键点：
- 必须用 PersistentClient（持久化到目录），不要用 Client()（内存模式，重启丢数据）；
- collection 元数据 hnsw:space=cosine，与归一化向量配合；
- document id 格式 {note_id}_{chunk_index}，与 note_chunks 表 chroma_id 对应。
"""
from .. import config

_client = None
_collection = None


def get_collection():
    global _client, _collection
    if _collection is None:
        import chromadb

        _client = chromadb.PersistentClient(path=config.CHROMA_PATH)
        _collection = _client.get_or_create_collection(
            name=config.CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def add_chunks(
    note_id: str,
    note_title: str,
    chunks: list[str],
    embeddings: list[list[float]],
    source_type: str,
) -> list[str]:
    """入库一批分块，返回 chroma_id 列表。"""
    collection = get_collection()
    ids = [f"{note_id}_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "note_id": note_id,
            "note_title": note_title,
            "chunk_index": i,
            "source_type": source_type,
        }
        for i in range(len(chunks))
    ]
    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    return ids


def query_chunks(query_embedding: list[float], n_results: int = 5) -> list[dict]:
    """向量检索，返回 [{note_id, note_title, chunk_index, content, score}]。"""
    collection = get_collection()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )
    out = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]
    for i, doc in enumerate(docs):
        meta = metas[i] or {}
        out.append(
            {
                "note_id": meta.get("note_id", ""),
                "note_title": meta.get("note_title", ""),
                "chunk_index": meta.get("chunk_index", 0),
                "source_type": meta.get("source_type", ""),
                "content": doc,
                "score": float(dists[i]) if i < len(dists) else 0.0,
            }
        )
    return out


def delete_by_note(note_id: str) -> None:
    """按笔记删除全部相关分块。"""
    collection = get_collection()
    existing = collection.get(where={"note_id": note_id})
    if existing["ids"]:
        collection.delete(ids=existing["ids"])
