"""
domain/ecommerce/__init__.py

电商领域包：人设 + 工具 + 知识集合 + 评测用例，组装成 DomainPack。
- 商品 / 库存：实时读真实 Shopify（shopify_source）
- 知识库：真实店铺 pages / 政策（RAG）
"""

from pathlib import Path

from domain.base import CollectionSpec, DomainPack
from domain.ecommerce.chunker import chunk_knowledge
from domain.ecommerce.collections import COLLECTION_KNOWLEDGE
from domain.ecommerce.eval_cases import CASES
from domain.ecommerce.prompt import SYSTEM_PROMPT
from domain.ecommerce.reflection_prompt import REFLECTION_PROMPT
from domain.ecommerce.shopify_source import fetch_pages, fetch_policies
from domain.ecommerce.state_prompt import STATE_UPDATE_PROMPT
from domain.ecommerce.tools import TOOL_FIELD_MAP, build_tool_specs


def _knowledge_items():
    return fetch_pages() + fetch_policies()


def _collection_for_doc(doc_id: str) -> str:
    return COLLECTION_KNOWLEDGE


PACK = DomainPack(
    name="ecommerce",
    system_prompt=SYSTEM_PROMPT,
    build_tool_specs=build_tool_specs,
    tool_field_map=TOOL_FIELD_MAP,
    reflection_prompt=REFLECTION_PROMPT,
    state_update_prompt=STATE_UPDATE_PROMPT,
    collections=[
        CollectionSpec(COLLECTION_KNOWLEDGE, lambda: chunk_knowledge(_knowledge_items())),
    ],
    eval_cases=CASES,
    retrieval_golden_path=str(Path(__file__).parent / "data" / "retrieval_golden.json"),
    collection_for_doc=_collection_for_doc,
)
