"""
eval/benchmarks/scifact.py

BEIR scifact 检索评测（RAG 层外部测试）：
公开语料 → bge-m3(Ollama) 嵌入 → Qdrant → 现有 Retriever（vector / hybrid / hybrid+rerank）
→ nDCG@10 / Recall@10 / MRR@10。

数据：eval/benchmarks/scifact_data/scifact（BEIR 官方 JSONL）
运行：python -m eval.benchmarks.scifact [vector|hybrid|hybrid_rerank|all] [limit]
"""

import csv
import json
import math
import shutil
import sys
from datetime import datetime
from pathlib import Path

from rag.embedder import EMBED_DIM, Embedder
from rag.retriever import Retriever
from rag.store import VectorStore

DATA = Path(__file__).parent / "scifact_data" / "scifact"
QDRANT = Path(__file__).parent / "scifact_qdrant"
COLLECTION = "scifact"
REPORT = Path(__file__).parent / "scifact_report.md"
KS = (10,)


def load():
    corpus = [json.loads(l) for l in (DATA / "corpus.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    queries = {q["_id"]: q["text"] for q in
               (json.loads(l) for l in (DATA / "queries.jsonl").read_text(encoding="utf-8").splitlines() if l.strip())}
    qrels = {}
    with open(DATA / "qrels" / "test.tsv", encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            qrels.setdefault(row["query-id"], {})[row["corpus-id"]] = int(row["score"])
    return corpus, queries, qrels


def build_chunks(corpus):
    chunks = []
    for d in corpus:
        text = (d.get("title", "") + "\n" + d.get("text", "")).strip()
        chunks.append({"id": f"scifact-{d['_id']}", "text": text, "payload": {"doc_id": d["_id"]}})
    return chunks


def ensure_store(chunks):
    """集合不存在 / 数量不符时，删除本地路径后全量重建并嵌入。"""
    def _fresh():
        if QDRANT.exists():
            shutil.rmtree(QDRANT)
        st = VectorStore(path=str(QDRANT))
        st.recreate_collection(COLLECTION, EMBED_DIM)
        emb = Embedder()
        st.upsert(COLLECTION, chunks, emb.embed([c["text"] for c in chunks]))
        return st

    store = VectorStore(path=str(QDRANT))
    if not store.client.collection_exists(COLLECTION) or store.count(COLLECTION) != len(chunks):
        store.close()
        store = _fresh()
    return store


# ---------- 指标 ----------

def _dcg(rels):
    return sum((2 ** r - 1) / math.log2(i + 2) for i, r in enumerate(rels))


def ndcg_at_k(ranked, rel_map, k=10):
    rels = [rel_map.get(d, 0) for d in ranked[:k]]
    idcg = _dcg(sorted(rel_map.values(), reverse=True)[:k])
    return _dcg(rels) / idcg if idcg > 0 else 0.0


def recall_at_k(ranked, rel_set, k=10):
    return len(set(ranked[:k]) & rel_set) / len(rel_set) if rel_set else 0.0


def mrr_at_k(ranked, rel_set, k=10):
    for i, d in enumerate(ranked[:k]):
        if d in rel_set:
            return 1.0 / (i + 1)
    return 0.0


def _retrieve_ids(retriever, mode, rerank, query, k=10):
    hits = retriever.retrieve(COLLECTION, query, top_k=k, score_threshold=0.0,
                              mode=mode, rerank=rerank)
    ids = []
    for h in hits:
        did = h["payload"].get("doc_id")
        if did and did not in ids:
            ids.append(did)
    return ids


def evaluate(mode="hybrid", rerank=False, limit=None, retriever=None):
    _, queries, qrels = load()
    retriever = retriever or Retriever(ensure_store(build_chunks(load()[0])))
    if rerank and retriever.reranker is None:
        from rag.rerank import CrossEncoderReranker
        retriever.set_reranker(CrossEncoderReranker())

    qids = list(qrels.keys())
    if limit:
        qids = qids[:limit]

    n, nd, rc, mr = 0, 0.0, 0.0, 0.0
    for qid in qids:
        if qid not in queries:
            continue
        ranked = _retrieve_ids(retriever, mode, rerank, queries[qid])
        rel_map = qrels[qid]
        rel_set = set(rel_map)
        nd += ndcg_at_k(ranked, rel_map)
        rc += recall_at_k(ranked, rel_set)
        mr += mrr_at_k(ranked, rel_set)
        n += 1
    return {"mode": mode, "rerank": rerank, "total": n,
            "ndcg@10": nd / n * 100 if n else 0.0,
            "recall@10": rc / n * 100 if n else 0.0,
            "mrr@10": mr / n * 100 if n else 0.0}


def run_all(limit=None):
    store = ensure_store(build_chunks(load()[0]))
    retriever = Retriever(store)
    configs = [("vector", False), ("hybrid", False), ("hybrid", True)]
    results = [evaluate(mode=m, rerank=r, limit=limit, retriever=retriever) for m, r in configs]

    lines = [
        "# BEIR scifact 检索评测报告（RAG 层外部测试）",
        "",
        f"> 时间：{datetime.now():%Y-%m-%d %H:%M} · 嵌入：bge-m3(Ollama) · "
        f"查询数：{results[0]['total']}",
        "",
        "| 配置 | nDCG@10 | Recall@10 | MRR@10 |",
        "|---|---|---|---|",
    ]
    for r in results:
        name = "hybrid + rerank" if (r["mode"] == "hybrid" and r["rerank"]) else r["mode"]
        lines.append(f"| {name} | {r['ndcg@10']:.1f}% | {r['recall@10']:.1f}% | {r['mrr@10']:.1f}% |")
    lines += [
        "",
        "> 数据：BEIR 官方 scifact（公开基准）；指标基于 qrels/test.tsv。",
    ]
    report = "\n".join(lines)
    REPORT.write_text(report, encoding="utf-8")
    print(report)
    print(f"\n报告已写入：{REPORT}")
    return results


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    lim = int(sys.argv[2]) if len(sys.argv) > 2 else None
    if arg == "all":
        run_all(lim)
    else:
        mode = "hybrid"
        rerank = False
        if arg == "hybrid_rerank":
            mode, rerank = "hybrid", True
        elif arg == "vector":
            mode = "vector"
        print(evaluate(mode=mode, rerank=rerank, limit=lim))
