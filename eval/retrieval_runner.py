"""
eval/retrieval_runner.py

检索评测：黄金集 → hit rate @1/@3/@5。
运行：python -m eval.retrieval_runner [vector|hybrid|hybrid_rerank]
"""

import json
import sys
from datetime import datetime
from pathlib import Path

from domain.registry import get_domain
from rag.retriever import Retriever
from rag.store import get_store

REPORT = Path("eval/retrieval_report.md")
KS = (1, 3, 5)


def _doc_id_of(hit) -> str:
    p = hit["payload"]
    return p.get("doc_id") or p.get("_cid") or ""


def evaluate(mode="hybrid", rerank=False, retriever=None, reranker=None, pack=None):
    """跑一遍黄金集，返回 {total, hits:{1,3,5}, rows}。"""
    pack = pack or get_domain()
    golden = json.loads(Path(pack.retrieval_golden_path).read_text(encoding="utf-8"))
    retriever = retriever or Retriever(get_store())
    if rerank and retriever.reranker is None:
        if reranker is None:
            from rag.rerank import CrossEncoderReranker
            reranker = CrossEncoderReranker()
        retriever.set_reranker(reranker)

    hits_stat = {k: 0 for k in KS}
    rows = []
    for g in golden:
        expected = (g.get("expected_ids") or [None])[0]
        if not expected:
            continue
        collection = pack.collection_for_doc(expected)
        hits = retriever.retrieve(collection, g["query"], top_k=max(KS),
                                  score_threshold=0.0, mode=mode, rerank=rerank)
        seen, ranked = set(), []
        for h in hits:
            did = _doc_id_of(h)
            if did and did not in seen:
                seen.add(did)
                ranked.append(did)

        row = {"query": g["query"], "expected": expected, "rank": None}
        for k in KS:
            if expected in ranked[:k]:
                hits_stat[k] += 1
        if expected in ranked:
            row["rank"] = ranked.index(expected) + 1
        rows.append(row)

    return {"mode": mode, "rerank": rerank, "total": len(rows), "hits": hits_stat, "rows": rows}


def _render(result):
    total = result["total"]
    hits = result["hits"]
    rows = result["rows"]
    name = "hybrid + rerank" if (result["mode"] == "hybrid" and result["rerank"]) else result["mode"]
    lines = [
        "# 检索评测报告",
        "",
        f"> 时间：{datetime.now():%Y-%m-%d %H:%M} · 配置：**{name}** · 黄金查询数：{total}",
        "",
        "| 指标 | 命中 / 总数 | 命中率 |",
        "|---|---|---|",
    ]
    for k in KS:
        lines.append(f"| hit@{k} | {hits[k]} / {total} | {hits[k] / total * 100:.1f}% |")
    lines += ["", "## 未命中样例（前 10）", "", "| 查询 | 期望命中 | 名次 |", "|---|---|---|"]
    miss = [r for r in rows if r["rank"] is None][:10]
    for r in miss or [{"query": "-", "expected": "全部命中"}]:
        lines.append(f"| {r['query']} | {r['expected']} | {'未命中' if r['rank'] is None else '-'} |")
    return "\n".join(lines)


def run(mode="hybrid", pack=None):
    result = evaluate(mode=mode, pack=pack)
    report = _render(result)
    REPORT.write_text(report, encoding="utf-8")
    print(report)
    print(f"\n报告已写入：{REPORT}")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "hybrid"
    if arg == "hybrid_rerank":
        r = evaluate(mode="hybrid", rerank=True)
        print(_render(r))
    else:
        run(arg)
