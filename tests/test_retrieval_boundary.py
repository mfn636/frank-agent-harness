"""检索边界回归：不调用模型 API、Ollama 或已有向量库。"""

import subprocess
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from bootstrap import build_agent, build_tools
from contract.retrieval import SearchFilter, SearchHit
from domain.ecommerce import PACK
from domain.ecommerce.collections import COLLECTION_KNOWLEDGE, COLLECTION_PRODUCTS
from domain.ecommerce.tools.faq_search import FAQ
from domain.ecommerce.tools.product_search import PRODUCTS
from rag.service import RagSearchAdapter


class FakeSearchService:
    def __init__(self, hits=(), error=None):
        self.hits = list(hits)
        self.error = error
        self.calls = []

    def search(self, collection, query, filters=None, top_k=5):
        self.calls.append((collection, query, filters, top_k))
        if self.error is not None:
            raise self.error
        return self.hits[:top_k]


def knowledge_hit(text="七天内可申请退货"):
    return SearchHit(
        id="policy-1", text=text,
        metadata={"source": "policy", "title": "退货政策"}, score=0.876543,
    )


class DomainSearchTests(unittest.TestCase):
    def test_product_filters_and_result_mapping(self):
        product = PRODUCTS[0]
        hit = SearchHit("product-1", "简介", {"product_id": product.id}, 0.8)
        service = FakeSearchService([hit])
        tools = build_tools(PACK, service)
        result = tools.call("search_products", {
            "query": "适合办公", "budget": product.price,
            "brand": product.brand, "category": product.category,
        })
        self.assertEqual(result, [product])
        self.assertEqual(service.calls, [(
            COLLECTION_PRODUCTS, "适合办公",
            SearchFilter(
                equals={"source": "product", "brand": product.brand,
                        "category": product.category},
                less_than_or_equal={"price": product.price},
            ), 8,
        )])

    def test_product_fallback_on_empty_error_or_unknown_product(self):
        product = PRODUCTS[0]
        unknown = SearchHit("missing", "", {"product_id": "missing"}, 1.0)
        for service in (FakeSearchService(), FakeSearchService([unknown]),
                        FakeSearchService(error=RuntimeError("offline"))):
            with self.subTest(service=service):
                result = build_tools(PACK, service).call("search_products", {
                    "keyword": product.name, "budget": product.price,
                    "brand": product.brand, "category": product.category,
                })
                self.assertIn(product, result)
                self.assertTrue(all(p.price <= product.price for p in result))

    def test_structured_search_detail_and_inventory_do_not_retrieve(self):
        service = FakeSearchService(error=AssertionError("不应检索"))
        tools = build_tools(PACK, service)
        result = tools.call("search_products", {"budget": 5000})
        self.assertTrue(result)
        self.assertTrue(all(p.price <= 5000 for p in result))
        product = PRODUCTS[0]
        self.assertEqual(tools.call("get_product_detail", {"product_id": product.id}),
                         [product])
        self.assertTrue(tools.call("check_inventory", {"product_id": product.id}))
        self.assertEqual(service.calls, [])

    def test_faq_filters_and_mapping(self):
        faq = FAQ[0]
        service = FakeSearchService([
            SearchHit("faq-1", "", faq.model_dump(), 0.9),
        ])
        result = build_tools(PACK, service).call("search_faq", {
            "query": "怎么处理", "category": faq.category,
        })
        self.assertEqual(result, [faq])
        self.assertEqual(service.calls, [(
            COLLECTION_KNOWLEDGE, "怎么处理",
            SearchFilter(equals={"source": "faq", "category": faq.category}), 5,
        )])

    def test_faq_fallback_on_empty_or_error(self):
        faq = FAQ[0]
        for service in (FakeSearchService(), FakeSearchService(error=RuntimeError("offline"))):
            with self.subTest(service=service):
                result = build_tools(PACK, service).call("search_faq", {
                    "query": faq.question, "category": faq.category,
                })
                self.assertIn(faq, result)
                self.assertTrue(all(item.category == faq.category for item in result))

    def test_knowledge_mapping_filters_and_default_limit(self):
        service = FakeSearchService([knowledge_hit()])
        tools = build_tools(PACK, service)
        result = tools.call("search_knowledge", {
            "query": "怎么退货", "category": "退换货", "top_k": 2,
        })
        self.assertEqual(result[0].model_dump(), {
            "source": "policy", "title": "退货政策",
            "content": "七天内可申请退货", "score": 0.8765,
        })
        self.assertEqual(service.calls[0], (
            COLLECTION_KNOWLEDGE, "怎么退货",
            SearchFilter(equals={"category": "退换货"}), 2,
        ))
        tools.call("search_knowledge", {"query": "怎么退货"})
        self.assertEqual(service.calls[1], (COLLECTION_KNOWLEDGE, "怎么退货", None, 5))

    def test_knowledge_errors_are_not_silently_hidden(self):
        tools = build_tools(PACK, FakeSearchService(error=RuntimeError("offline")))
        with self.assertRaisesRegex(RuntimeError, "offline"):
            tools.call("search_knowledge", {"query": "怎么退货"})

    def test_separate_tool_instances_keep_separate_services(self):
        first = FakeSearchService([knowledge_hit("服务一")])
        second = FakeSearchService([knowledge_hit("服务二")])
        first_tools = build_tools(PACK, first)
        second_tools = build_tools(PACK, second)
        for tools, expected in ((first_tools, "服务一"), (second_tools, "服务二"),
                                (first_tools, "服务一")):
            result = tools.call("search_knowledge", {"query": "政策"})
            self.assertEqual(result[0].content, expected)
        self.assertEqual(len(first.calls), 2)
        self.assertEqual(len(second.calls), 1)

    def test_dependency_is_not_exposed_in_tool_schema(self):
        schemas = build_tools(PACK, FakeSearchService()).list_tools()
        self.assertEqual({s["function"]["name"] for s in schemas}, {
            "search_products", "get_product_detail", "check_inventory",
            "search_faq", "search_knowledge",
        })
        for schema in schemas:
            self.assertNotIn("search_service", schema["function"]["parameters"]["properties"])

    def test_agent_uses_injected_search_through_full_turn(self):
        service = FakeSearchService([knowledge_hit()])
        tool_call = SimpleNamespace(
            id="call-1", type="function",
            function=SimpleNamespace(name="search_knowledge", arguments='{"query":"退货"}'),
        )
        llm = Mock(usage_log=[])
        # Reflection 默认关闭：主循环 2 次（工具调用 + 最终回复）+ 记忆更新 1 次
        llm.chat.side_effect = [
            SimpleNamespace(content=None, tool_calls=[tool_call]),
            SimpleNamespace(content="七天内可申请退货", tool_calls=None),
            SimpleNamespace(content="用户咨询退货政策"),
        ]
        with patch("agent.core.loop.load_snapshot", return_value=(None, None)), \
                patch("agent.core.loop.save_snapshot") as save:
            agent = build_agent(llm=llm, search_service=service)
            result = agent.run("怎么退货")
        self.assertEqual(result.replies, ["七天内可申请退货"])
        self.assertEqual(result.tool_calls, [{"name": "search_knowledge", "args": {"query": "退货"}}])
        self.assertEqual(len(service.calls), 1)
        self.assertEqual(llm.chat.call_count, 3)
        save.assert_called_once()

    def test_injected_service_works_without_rag_backend_imports(self):
        # 新进程避免已缓存模块掩盖意外的后端依赖；分块原语仍允许复用。
        code = '''
import importlib.abc
import sys
class BlockBackend(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith("qdrant_client") or (
            fullname.startswith("rag.") and fullname != "rag.chunker"
        ):
            raise AssertionError("Unexpected backend import: " + fullname)
sys.meta_path.insert(0, BlockBackend())
from bootstrap import build_tools
from domain.ecommerce import PACK
from contract.retrieval import SearchHit
class Search:
    def search(self, collection, query, filters=None, top_k=5):
        return [SearchHit("1", "policy", {"source": "policy", "title": "title"}, 1.0)]
tools = build_tools(PACK, Search())
assert tools.call("search_knowledge", {"query": "policy"})[0].content == "policy"
'''
        result = subprocess.run(
            [sys.executable, "-c", code], cwd=Path(__file__).resolve().parents[1],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class AdapterTests(unittest.TestCase):
    def test_adapter_translates_filters_and_normalizes_results(self):
        retriever = Mock()
        retriever.retrieve.return_value = [{
            "id": "chunk-1", "score": 0.75,
            "payload": {"_cid": "chunk-1", "_text": "正文", "source": "guide", "title": "标题"},
        }]
        filters = SearchFilter(equals={"brand": "Apex"}, less_than_or_equal={"price": 5000})
        result = RagSearchAdapter(retriever).search("products", "办公", filters, top_k=3)
        self.assertEqual(result, [SearchHit(
            "chunk-1", "正文", {"source": "guide", "title": "标题"}, 0.75,
        )])
        args, kwargs = retriever.retrieve.call_args
        self.assertEqual(args, ("products", "办公"))
        self.assertEqual(kwargs["top_k"], 3)
        must = kwargs["query_filter"].must
        self.assertEqual((must[0].key, must[0].match.value), ("brand", "Apex"))
        self.assertEqual((must[1].key, must[1].range.lte), ("price", 5000))

    def test_empty_filters_and_empty_results(self):
        retriever = Mock()
        retriever.retrieve.return_value = []
        adapter = RagSearchAdapter(retriever)
        for filters in (None, SearchFilter()):
            self.assertEqual(adapter.search("knowledge", "query", filters), [])
            self.assertIsNone(retriever.retrieve.call_args.kwargs["query_filter"])

    def test_default_tool_assembly_is_lazy(self):
        with patch.object(RagSearchAdapter, "_get_retriever", side_effect=AssertionError("eager init")):
            tools = build_tools(PACK)
            self.assertEqual(len(tools.list_tools()), 5)
            self.assertTrue(tools.call("search_products", {"budget": 5000}))


if __name__ == "__main__":
    unittest.main()
