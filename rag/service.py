"""检索契约的 RAG 适配器：隔离 Qdrant 条件与内部 payload 格式。"""

from typing import TYPE_CHECKING

from contract.retrieval import SearchFilter, SearchHit

if TYPE_CHECKING:
    from rag.retriever import Retriever


class RagSearchAdapter:
    def __init__(self, retriever: "Retriever | None" = None):
        # 延迟初始化：纯结构化查询和工具装配不需要打开向量库。
        self._retriever = retriever

    def _get_retriever(self):
        if self._retriever is None:
            from rag.retriever import Retriever
            from rag.store import get_store

            self._retriever = Retriever(get_store())
        return self._retriever

    @staticmethod
    def _build_filter(filters: SearchFilter | None):
        if filters is None or not (filters.equals or filters.less_than_or_equal):
            return None

        from qdrant_client.models import FieldCondition, Filter, MatchValue, Range

        must = [
            FieldCondition(key=key, match=MatchValue(value=value))
            for key, value in filters.equals.items()
        ]
        must.extend(
            FieldCondition(key=key, range=Range(lte=value))
            for key, value in filters.less_than_or_equal.items()
        )
        return Filter(must=must)

    def search(
        self,
        collection: str,
        query: str,
        filters: SearchFilter | None = None,
        top_k: int = 5,
    ) -> list[SearchHit]:
        query_filter = self._build_filter(filters)
        hits = self._get_retriever().retrieve(
            collection, query, top_k=top_k,
            score_threshold=0.3, query_filter=query_filter,
        )
        return [
            SearchHit(
                id=hit["id"],
                text=hit["payload"].get("_text", ""),
                metadata={key: value for key, value in hit["payload"].items()
                          if key not in ("_text", "_cid")},
                score=float(hit["score"]),
            )
            for hit in hits
        ]
