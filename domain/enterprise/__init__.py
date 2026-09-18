"""
domain/enterprise/__init__.py

企业内部运营 / 运维领域包：人设 + 工具 + 数据集合 + 评测用例，组装成 DomainPack。
"""

from pathlib import Path

from domain.base import CollectionSpec, DomainPack
from domain.enterprise.chunker import chunk_runbooks, chunk_services
from domain.enterprise.collections import COLLECTION_RUNBOOKS, COLLECTION_SERVICES
from domain.enterprise.eval_cases import CASES
from domain.enterprise.loader import load_runbooks, load_services
from domain.enterprise.prompt import SYSTEM_PROMPT
from domain.enterprise.reflection_prompt import REFLECTION_PROMPT
from domain.enterprise.state_prompt import STATE_UPDATE_PROMPT
from domain.enterprise.tools import TOOL_FIELD_MAP, build_tool_specs


def _collection_for_doc(doc_id: str) -> str:
    return COLLECTION_RUNBOOKS if doc_id.startswith("rb-") else COLLECTION_SERVICES


PACK = DomainPack(
    name="enterprise",
    system_prompt=SYSTEM_PROMPT,
    build_tool_specs=build_tool_specs,
    tool_field_map=TOOL_FIELD_MAP,
    reflection_prompt=REFLECTION_PROMPT,
    state_update_prompt=STATE_UPDATE_PROMPT,
    collections=[
        CollectionSpec(COLLECTION_SERVICES, lambda: chunk_services(load_services())),
        CollectionSpec(COLLECTION_RUNBOOKS, lambda: chunk_runbooks(load_runbooks())),
    ],
    eval_cases=CASES,
    retrieval_golden_path=str(Path(__file__).parent / "data" / "retrieval_golden.json"),
    collection_for_doc=_collection_for_doc,
)
