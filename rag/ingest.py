"""
rag/ingest.py

数据管道（领域无关）：领域包 → 逐集合 build chunk → embed → upsert（幂等，可重复跑）。
CLI：python -m rag.ingest
"""

from rag.embedder import EMBED_DIM, Embedder
from rag.store import VectorStore


def ingest(pack=None) -> dict:
    if pack is None:
        from domain.registry import get_domain
        pack = get_domain()

    store = VectorStore()
    embedder = Embedder()

    result = {}
    for col in pack.collections:
        chunks = col.build_chunks()
        store.recreate_collection(col.name, EMBED_DIM)
        store.upsert(col.name, chunks, embedder.embed([c["text"] for c in chunks]))
        result[col.name] = store.count(col.name)

    store.close()
    return result


if __name__ == "__main__":
    print("ingest ->", ingest())
