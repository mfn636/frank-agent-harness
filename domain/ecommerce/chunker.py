"""
domain/ecommerce/chunker.py

电商领域分块：把知识条目（真实店铺 pages / 政策）切成带元数据的 chunk。
通用分块能力（按标题 / 段落切）复用 rag/chunker.py。
"""

from rag.chunker import split_by_headings


def chunk_knowledge(items, max_len=400, overlap=60):
    """知识条目（{id,title,source,content}）→ 标题感知分块。"""
    chunks = []
    for it in items:
        for j, sec in enumerate(split_by_headings(it.get("content", ""), max_len, overlap)):
            chunks.append({
                "id": f"{it['id']}-{j}",
                "text": f"{it['title']}｜{sec}",
                "payload": {
                    "source": it.get("source", "knowledge"),
                    "doc_id": it["id"],
                    "title": it.get("title", ""),
                },
            })
    return chunks
