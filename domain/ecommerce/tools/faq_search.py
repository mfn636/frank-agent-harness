"""
domain/ecommerce/tools/faq_search.py

FAQ 检索：语义检索（RAG，source=faq），保留关键词兜底。
"""

from typing import List, Optional

from contract.retrieval import SearchFilter, SearchService

from domain.ecommerce.collections import COLLECTION_KNOWLEDGE
from domain.ecommerce.loader import load_faq
from domain.ecommerce.models.faq import FaqItem

FAQ: List[FaqItem] = load_faq()


def search_faq(
    query: Optional[str] = None,
    category: Optional[str] = None,
    *,
    search_service: SearchService,
) -> List[FaqItem]:
    """FAQ 搜索：优先语义检索，失败/空则回退关键词。"""
    if query:
        try:
            items = _semantic(query, category, search_service)
            if items:
                return items
        except Exception:  # noqa: BLE001
            pass
    return _keyword(query, category)


def _semantic(query, category, search_service: SearchService) -> List[FaqItem]:
    filters = SearchFilter(equals={"source": "faq"})
    if category:
        filters.equals["category"] = category
    hits = search_service.search(
        COLLECTION_KNOWLEDGE, query, top_k=5,
        filters=filters,
    )
    return [
        FaqItem(category=h.metadata.get("category", ""),
                question=h.metadata.get("question", ""),
                answer=h.metadata.get("answer", ""))
        for h in hits
    ]


def _keyword(query, category) -> List[FaqItem]:
    results = []
    for entry in FAQ:
        if category and category not in entry.category:
            continue
        if query:
            text = entry.question + entry.answer
            keywords = _extract_keywords(query)
            if not any(kw in text for kw in keywords):
                continue
        results.append(entry)
    return results


def _extract_keywords(text: str) -> List[str]:
    result = [text]
    for i in range(len(text) - 1):
        chunk = text[i:i + 2]
        chunk = chunk.strip(" ?？！!，,。.")
        if chunk and len(chunk) == 2:
            result.append(chunk)
    return result
