"""
domain/ecommerce/tools/inventory.py

库存查询：读真实 Shopify 店铺（里程碑 2，只读）。
"""

from typing import List, Optional

from domain.ecommerce import shopify_source
from domain.ecommerce.models.shopify import ShopifyInventory


def check_inventory(
    product_id: Optional[str] = None,
    category: Optional[str] = None,
) -> List[ShopifyInventory]:
    """按商品 ID 或商品类型查询库存（逐变体返回可售数量）。"""
    return shopify_source.inventory(product_id=product_id, category=category)
