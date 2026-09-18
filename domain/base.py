"""
domain/base.py

领域包接口：把「某个行业/场景」所需的一切（人设、工具、数据集合、评测用例）
打包成一个 DomainPack，供核心、检索与评测引擎按接口消费。

核心（agent / rag / eval 引擎）不依赖任何具体领域，只认这个接口。
"""

from dataclasses import dataclass
from typing import Callable, List


@dataclass
class CollectionSpec:
    """一个向量集合：集合名 + 如何从领域数据构建 chunk。"""

    name: str
    build_chunks: Callable[[], list]


@dataclass
class DomainPack:
    """一个领域的完整配置。新增领域 = 新增一个包并注册，核心零改动。"""

    name: str
    system_prompt: str
    tool_specs: List[dict]                      # {name, description, args_model, fn}
    tool_field_map: dict                        # {工具名: [压缩时保留的字段]}
    reflection_prompt: str                      # 自检 Prompt（领域相关的判定维度）
    state_update_prompt: str                    # 长期记忆提炼 Prompt（领域相关规则）
    collections: List[CollectionSpec]
    eval_cases: List[dict]
    retrieval_golden_path: str
    collection_for_doc: Callable[[str], str]    # doc_id -> 集合名（检索评测用）
