"""
domain/ecommerce/tools/knowledge_search.py

知识库语义检索（RAG）：FAQ / 指南 / 政策 / 帮助 统一检索。
"""

from typing import List, Optional

from contract.retrieval import SearchFilter, SearchService

from domain.ecommerce.collections import COLLECTION_KNOWLEDGE
from domain.ecommerce.models.knowledge import KnowledgeItem


def search_knowledge(
    query: str,
    category: Optional[str] = None,
    top_k: int = 5,
    *,
    search_service: SearchService,
) -> List[KnowledgeItem]:
    """
    知识库语义检索工具。

    Args:
        query: 用户问题（自然语言）
        category: 可选，按知识类别过滤（如 退换货、支付）
        top_k: 返回条数上限

    Returns:
        List[KnowledgeItem]
    """
    query_filter = None
    if category:
        query_filter = SearchFilter(equals={"category": category})

    hits = search_service.search(
        COLLECTION_KNOWLEDGE, query, top_k=top_k,
        filters=query_filter,
    )

    items = []
    for h in hits:
        p = h.metadata
        items.append(KnowledgeItem(
            source=p.get("source", "knowledge"),
            title=p.get("question") or p.get("title") or "",
            content=h.text,
            score=round(h.score, 4),
        ))
    return items
