"""
domain/ecommerce/tools/product_search.py

商品检索：语义检索（RAG）+ 结构化过滤（预算/品牌/类别），保留关键词兜底。
"""

from typing import List, Optional

from contract.retrieval import SearchFilter, SearchService

from domain.ecommerce.collections import COLLECTION_PRODUCTS
from domain.ecommerce.loader import load_products
from domain.ecommerce.models.product import Product

# Agent启动时加载一次商品数据
PRODUCTS: List[Product] = load_products()
# ID -> Product 映射（供详情查询 / 语义结果还原）
PRODUCT_MAP = {p.id: p for p in PRODUCTS}


def _build_filter(category, budget, brand) -> SearchFilter:
    filters = SearchFilter(equals={"source": "product"})
    if category:
        filters.equals["category"] = category
    if brand:
        filters.equals["brand"] = brand
    if budget is not None:
        filters.less_than_or_equal["price"] = budget
    return filters


def search_products(
    category: Optional[str] = None,
    budget: Optional[int] = None,
    brand: Optional[str] = None,
    keyword: Optional[str] = None,
    query: Optional[str] = None,
    *,
    search_service: SearchService,
) -> List[Product]:
    """
    商品搜索：有自由文本时走语义检索（叠加结构化过滤），否则结构化过滤；
    失败/空则回退关键词。
    """
    text_query = keyword or query
    if text_query:
        try:
            hits = search_service.search(
                COLLECTION_PRODUCTS, text_query, top_k=8,
                filters=_build_filter(category, budget, brand),
            )
            products = [PRODUCT_MAP[h.metadata["product_id"]]
                        for h in hits if h.metadata.get("product_id") in PRODUCT_MAP]
            if products:
                return products
        except Exception:  # noqa: BLE001
            pass
    return _keyword(category, budget, brand, keyword or query)


def _keyword(category, budget, brand, keyword) -> List[Product]:
    results = []
    for product in PRODUCTS:
        if category and category not in product.category:
            continue
        if budget and product.price > budget:
            continue
        if brand and brand.lower() not in product.brand.lower():
            continue
        if keyword:
            text = product.name + product.category + product.description
            if keyword.lower() not in text.lower():
                continue
        results.append(product)
    return results


def get_product_detail(product_id: Optional[str] = None) -> List[Product]:
    """按商品 ID 查询单个商品的完整信息（含硬件参数）。"""
    product = PRODUCT_MAP.get(product_id) if product_id else None
    return [product] if product else []
