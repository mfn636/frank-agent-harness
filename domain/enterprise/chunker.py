"""
domain/enterprise/chunker.py

企业运维领域分块：服务 / 运维手册（长文档）。
通用分块能力复用 rag/chunker.py。
"""

from rag.chunker import split_by_headings


def chunk_services(services):
    """服务：一个服务一个 chunk；payload 存可过滤字段与 doc_id。"""
    chunks = []
    for s in services:
        text = (f"{s.id} {s.name}（{s.owner} · {s.tier} · {s.runtime}）"
                f"当前状态 {s.status}，可用性 {s.uptime_pct}%。{s.description}")
        chunks.append({
            "id": f"service-{s.id}",
            "text": text,
            "payload": {
                "source": "service",
                "doc_id": s.id,
                "service_id": s.id,
                "owner": s.owner,
                "tier": s.tier,
                "status": s.status,
            },
        })
    return chunks


def chunk_runbooks(runbooks, max_len=400, overlap=60):
    """运维手册：标题感知分块——按 `##` 小节切；超长小节再按段落细切。"""
    chunks = []
    for g in runbooks:
        title = g.get("title", "")
        for j, sec in enumerate(split_by_headings(g.get("content", ""), max_len, overlap)):
            chunks.append({
                "id": f"runbook-{g['id']}-{j}",
                "text": f"{title}｜{sec}",
                "payload": {
                    "source": g.get("source", "runbook"),
                    "doc_id": g["id"],
                    "title": title,
                    "category": g.get("category", ""),
                },
            })
    return chunks
