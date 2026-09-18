"""使用临时 Qdrant 库和固定向量，验证真实检索链路的过滤语义。"""

import tempfile
import unittest

from contract.retrieval import SearchFilter
from rag.retriever import Retriever
from rag.service import RagSearchAdapter
from rag.store import VectorStore


class FixedEmbedder:
    def embed(self, query):
        return [1.0, 0.0]


class RagServiceIntegrationTests(unittest.TestCase):
    def test_hybrid_search_applies_all_filters_and_includes_budget_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            store = VectorStore(directory)
            try:
                store.ensure_collection("products", 2)
                rows = [
                    ("match", "product", "Apex", 5000),
                    ("too-expensive", "product", "Apex", 5001),
                    ("wrong-brand", "product", "Nova", 4000),
                    ("wrong-source", "faq", "Apex", 4000),
                ]
                chunks = [{
                    "id": cid, "text": "办公 laptop",
                    "payload": {"source": source, "brand": brand, "price": price},
                } for cid, source, brand, price in rows]
                store.upsert("products", chunks, [[1.0, 0.0]] * len(chunks))
                adapter = RagSearchAdapter(Retriever(store, embedder=FixedEmbedder()))
                hits = adapter.search("products", "办公 laptop", SearchFilter(
                    equals={"source": "product", "brand": "Apex"},
                    less_than_or_equal={"price": 5000},
                ))
                self.assertEqual([hit.id for hit in hits], ["match"])
                self.assertEqual(hits[0].text, "办公 laptop")
                self.assertEqual(hits[0].metadata["price"], 5000)
                self.assertNotIn("_text", hits[0].metadata)
                self.assertEqual(adapter.search("products", "办公 laptop", SearchFilter(
                    equals={"brand": "missing"},
                )), [])
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
