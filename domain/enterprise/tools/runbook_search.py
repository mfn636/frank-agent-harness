"""
domain/enterprise/tools/runbook_search.py

运维手册语义检索（RAG）：排障步骤 / 流程规范。
"""

from typing import List, Optional

from contract.retrieval import SearchFilter, SearchService

from domain.enterprise.collections import COLLECTION_RUNBOOKS
from domain.enterprise.models.runbook import RunbookItem


def search_runbook(
    query: str,
    category: Optional[str] = None,
    top_k: int = 5,
    *,
    search_service: SearchService,
) -> List[RunbookItem]:
    """运维手册语义检索。"""
    filters = SearchFilter(equals={"category": category}) if category else None
    hits = search_service.search(COLLECTION_RUNBOOKS, query, filters=filters, top_k=top_k)

    items = []
    for h in hits:
        p = h.metadata
        items.append(RunbookItem(
            source=p.get("source", "runbook"),
            title=p.get("title", ""),
            content=h.text,
            score=round(h.score, 4),
        ))
    return items
