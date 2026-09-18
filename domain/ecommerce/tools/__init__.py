"""
domain/ecommerce/tools/__init__.py

电商领域工具：技能实现集合 + 工具契约清单（TOOL_SPECS）。
"""

from domain.ecommerce.tool_args import (
    CheckInventoryArgs,
    GetProductDetailArgs,
    SearchFaqArgs,
    SearchKnowledgeArgs,
    SearchProductsArgs,
)
from domain.ecommerce.tools.faq_search import search_faq
from domain.ecommerce.tools.inventory import check_inventory
from domain.ecommerce.tools.knowledge_search import search_knowledge
from domain.ecommerce.tools.product_search import get_product_detail, search_products

TOOL_SPECS = [
    {
        "name": "search_products",
        "description": "搜索商品。按类别、预算、品牌或关键词筛选商品列表，返回精简信息（名称/品牌/价格/类别/简介）。",
        "args_model": SearchProductsArgs,
        "fn": search_products,
    },
    {
        "name": "get_product_detail",
        "description": "查询单个商品的完整硬件参数（CPU/内存/存储/屏幕/重量/电池/系统等）。当用户询问某款商品的具体配置/参数时调用。",
        "args_model": GetProductDetailArgs,
        "fn": get_product_detail,
    },
    {
        "name": "check_inventory",
        "description": "查询商品库存。可按商品ID或类别查询。",
        "args_model": CheckInventoryArgs,
        "fn": check_inventory,
    },
    {
        "name": "search_faq",
        "description": "搜索常见问题FAQ，用于回答支付、发货、运费、退换货、保修、发票、订单、产品、售后、优惠等售后问题。",
        "args_model": SearchFaqArgs,
        "fn": search_faq,
    },
    {
        "name": "search_knowledge",
        "description": "检索知识库（售后政策、选购指南、帮助文档等长文），用于回答规则、政策、流程、选购建议类问题；返回带来源的相关片段。",
        "args_model": SearchKnowledgeArgs,
        "fn": search_knowledge,
    },
]

# 各工具回填给 LLM 前保留的字段（未列出的字段丢弃，省 token）
TOOL_FIELD_MAP = {
    "search_products": ["id", "name", "brand", "price", "category", "description"],
    "get_product_detail": ["id", "name", "brand", "category", "price", "cpu", "memory",
                           "storage", "display", "weight", "battery", "os", "description"],
    "check_inventory": ["product_id", "product_name", "stock", "in_stock"],
    "search_faq": ["category", "question", "answer"],
    "search_knowledge": ["source", "title", "content", "score"],
}
