"""
domain/ecommerce/__init__.py

电商客服领域包：人设 + 工具 + 数据集合 + 评测用例，组装成 DomainPack。
"""

from pathlib import Path

from domain.base import CollectionSpec, DomainPack
from domain.ecommerce.chunker import chunk_faq, chunk_guides, chunk_products
from domain.ecommerce.collections import COLLECTION_KNOWLEDGE, COLLECTION_PRODUCTS
from domain.ecommerce.eval_cases import CASES
from domain.ecommerce.loader import load_faq, load_guides, load_products
from domain.ecommerce.prompt import SYSTEM_PROMPT
from domain.ecommerce.reflection_prompt import REFLECTION_PROMPT
from domain.ecommerce.state_prompt import STATE_UPDATE_PROMPT
from domain.ecommerce.tools import TOOL_FIELD_MAP, build_tool_specs


def _collection_for_doc(doc_id: str) -> str:
    return COLLECTION_PRODUCTS if doc_id.startswith("product-") else COLLECTION_KNOWLEDGE


PACK = DomainPack(
    name="ecommerce",
    system_prompt=SYSTEM_PROMPT,
    build_tool_specs=build_tool_specs,
    tool_field_map=TOOL_FIELD_MAP,
    reflection_prompt=REFLECTION_PROMPT,
    state_update_prompt=STATE_UPDATE_PROMPT,
    collections=[
        CollectionSpec(COLLECTION_PRODUCTS, lambda: chunk_products(load_products())),
        CollectionSpec(
            COLLECTION_KNOWLEDGE,
            lambda: chunk_faq(load_faq()) + chunk_guides(load_guides()),
        ),
    ],
    eval_cases=CASES,
    retrieval_golden_path=str(Path(__file__).parent / "data" / "retrieval_golden.json"),
    collection_for_doc=_collection_for_doc,
)
