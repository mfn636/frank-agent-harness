"""
domain/ecommerce/tools/__init__.py

电商领域工具：由工厂绑定检索服务，生成工具契约清单。
- 商品 / 库存：实时读真实 Shopify
- 知识库：真实店铺 pages / 政策（RAG）
"""

from functools import partial

from contract.retrieval import SearchService
from domain.ecommerce.tool_args import (
    CheckInventoryArgs,
    GetProductDetailArgs,
    SearchKnowledgeArgs,
    SearchProductsArgs,
)
from domain.ecommerce.tools.inventory import check_inventory
from domain.ecommerce.tools.knowledge_search import search_knowledge
from domain.ecommerce.tools.product_search import get_product_detail, search_products


def build_tool_specs(search_service: SearchService) -> list[dict]:
    """每次装配独立绑定依赖；服务不会成为暴露给模型的工具参数。"""
    return [
        {
            "name": "search_products",
            "description": "搜索店铺商品。按类别、预算、品牌或关键词筛选，返回商品列表（名称/类型/品牌/价格/状态）。",
            "args_model": SearchProductsArgs,
            "fn": search_products,
        },
        {
            "name": "get_product_detail",
            "description": "查询单个商品的完整信息（详情、标签、全部变体与价格/库存）。当用户询问某款商品的具体信息时调用。",
            "args_model": GetProductDetailArgs,
            "fn": get_product_detail,
        },
        {
            "name": "check_inventory",
            "description": "查询商品库存（按商品 ID 或商品类型），逐变体返回可售数量。",
            "args_model": CheckInventoryArgs,
            "fn": check_inventory,
        },
        {
            "name": "search_knowledge",
            "description": "检索店铺知识库（隐私政策、配送/售后等政策、帮助页面），用于回答规则、政策、流程类问题；返回带来源的相关片段。",
            "args_model": SearchKnowledgeArgs,
            "fn": partial(search_knowledge, search_service=search_service),
        },
    ]


# 各工具回填给 LLM 前保留的字段（未列出的字段丢弃，省 token）
TOOL_FIELD_MAP = {
    "search_products": ["id", "title", "product_type", "vendor", "price", "status"],
    "get_product_detail": ["id", "title", "vendor", "product_type", "status",
                           "price", "tags", "description", "variants"],
    "check_inventory": ["product_id", "product_title", "variant_title", "sku", "available"],
    "search_knowledge": ["source", "title", "content", "score"],
}
