"""
domain/ecommerce/tools/product_search.py

商品检索 / 详情：读真实 Shopify 店铺（里程碑 2，只读）。
"""

from typing import List, Optional

from domain.ecommerce import shopify_source
from domain.ecommerce.models.shopify import ShopifyProduct


def search_products(
    category: Optional[str] = None,
    budget: Optional[int] = None,
    brand: Optional[str] = None,
    keyword: Optional[str] = None,
    query: Optional[str] = None,
) -> List[ShopifyProduct]:
    """搜索真实店铺商品（类别 / 预算 / 品牌 / 关键词过滤）。"""
    return shopify_source.search_products(
        category=category, budget=budget, brand=brand, keyword=keyword or query,
    )


def get_product_detail(product_id: Optional[str] = None) -> List[ShopifyProduct]:
    """按商品 ID 查询单个商品的完整信息（含全部变体）。"""
    return shopify_source.fetch_product(product_id)
