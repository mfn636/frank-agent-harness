"""
eval/retrieval_ablation.py

检索消融：vector / hybrid / hybrid+rerank 的 hit@k 对比（验证混合检索与 rerank 的增益）。
运行：python -m eval.retrieval_ablation
"""

from eval.retrieval_runner import KS, evaluate
from rag.retriever import Retriever
from rag.store import get_store


def main(pack=None):
    retriever = Retriever(get_store())
    configs = [("vector", False), ("hybrid", False), ("hybrid", True)]
    print("| 配置 | hit@1 | hit@3 | hit@5 |")
    print("|---|---|---|---|")
    for mode, rerank in configs:
        r = evaluate(mode=mode, rerank=rerank, retriever=retriever, pack=pack)
        h, t = r["hits"], r["total"]
        name = "hybrid + rerank" if (mode == "hybrid" and rerank) else mode
        print(f"| {name} | {h[1] / t * 100:.1f}% | {h[3] / t * 100:.1f}% | {h[5] / t * 100:.1f}% |")


if __name__ == "__main__":
    main()
