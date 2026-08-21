"""本地知识库：用 LanceDB 做向量存储 + 余弦检索（RAG 的检索侧）。"""
import os
import re
import uuid

import numpy as np
import pyarrow as pa

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "lancedb")
TABLE = "kb"


def get_db():
    os.makedirs(DB_PATH, exist_ok=True)
    import lancedb

    return lancedb.connect(DB_PATH)


def table_exists() -> bool:
    return TABLE in get_db().table_names()


def ensure_table(embedder):
    db = get_db()
    if TABLE in db.table_names():
        return db.open_table(TABLE)
    dim = embedder.dim
    schema = pa.schema(
        [
            pa.field("id", pa.string()),
            pa.field("doc", pa.string()),
            pa.field("chunk", pa.string()),
            pa.field("vector", pa.list_(pa.float32(), dim)),
        ]
    )
    return db.create_table(TABLE, schema=schema)


def get_table():
    db = get_db()
    if TABLE in db.table_names():
        return db.open_table(TABLE)
    return None


def chunk_text(text: str, size: int = 400, overlap: int = 50):
    text = re.sub(r"\s+", " ", text).strip()
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        chunks.append(text[start : start + size])
        start += size - overlap
    return [c for c in chunks if c.strip()]


def ingest_file(filename: str, text: str, embedder) -> int:
    return ingest_text(filename, text, embedder)


def ingest_text(doc_name: str, text: str, embedder) -> int:
    """把一段文本（来自文件或外部接入）切分、向量化并入知识库。"""
    chunks = chunk_text(text)
    if not chunks:
        return 0
    vecs = embedder.embed_batch(chunks)
    table = ensure_table(embedder)
    rows = [
        {
            "id": str(uuid.uuid4()),
            "doc": doc_name,
            "chunk": chunks[i],
            "vector": vecs[i].tolist(),
        }
        for i in range(len(chunks))
    ]
    table.add(rows)
    return len(chunks)


def query(question: str, embedder, top_k: int = 4):
    table = get_table()
    if table is None:
        return None
    qv = embedder.embed(question)
    return table.search(qv.tolist()).limit(top_k).to_list()


def list_docs():
    table = get_table()
    if table is None:
        return []
    rows = table.to_arrow().to_pylist()
    if not rows:
        return []
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["doc"]] = counts.get(r["doc"], 0) + 1
    return [{"doc": k, "chunks": v} for k, v in counts.items()]


def delete_doc(name: str):
    table = get_table()
    if table is None:
        return {"deleted": name, "note": "知识库为空"}
    safe = name.replace("'", "''")
    table.delete(f"doc = '{safe}'")
    return {"deleted": name}
