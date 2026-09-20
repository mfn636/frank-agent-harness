"""
domain/ecommerce/shopify_source.py

从真实 Shopify 店铺读取商品/库存，并映射成领域模型（里程碑 2）。
— 只读；单页拉取（first:100），本地做关键词/品牌/类别/预算过滤。
"""

from typing import List, Optional

import html
import re

from domain.ecommerce.models.shopify import (
    ShopifyInventory,
    ShopifyProduct,
    ShopifyVariant,
)
from providers.shopify_client import get_shopify_client

_PRODUCTS_QUERY = """
{
  products(first: 100) {
    edges {
      node {
        id
        title
        productType
        vendor
        status
        description
        tags
        variants(first: 20) {
          edges {
            node {
              id
              title
              sku
              price
              inventoryQuantity
              selectedOptions { name value }
            }
          }
        }
      }
    }
  }
}
"""

_PRODUCT_QUERY = """
query($id: ID!) {
  product(id: $id) {
    id
    title
    productType
    vendor
    status
    description
    tags
    variants(first: 20) {
      edges {
        node {
          id
          title
          sku
          price
          inventoryQuantity
          selectedOptions { name value }
        }
      }
    }
  }
}
"""


def _normalize_id(product_id: str) -> str:
    """接受 gid 或纯数字，统一成 gid。"""
    if product_id.startswith("gid://"):
        return product_id
    return f"gid://shopify/Product/{product_id}"


def _map_product(node: dict) -> ShopifyProduct:
    variants = []
    for edge in (node.get("variants") or {}).get("edges", []):
        v = edge["node"]
        variants.append(ShopifyVariant(
            id=v["id"],
            title=v.get("title", "") or "",
            sku=v.get("sku"),
            price=v.get("price"),
            available=v.get("inventoryQuantity"),
            options=[f'{o["name"]}:{o["value"]}' for o in (v.get("selectedOptions") or [])],
        ))
    return ShopifyProduct(
        id=node["id"],
        title=node.get("title", "") or "",
        product_type=node.get("productType") or "",
        vendor=node.get("vendor") or "",
        status=node.get("status") or "",
        price=variants[0].price if variants else None,
        description=(node.get("description") or "")[:300],
        tags=node.get("tags") or [],
        variants=variants,
    )


def fetch_all_products() -> List[ShopifyProduct]:
    data = get_shopify_client().graphql(_PRODUCTS_QUERY)
    return [_map_product(e["node"]) for e in data.get("products", {}).get("edges", [])]


def fetch_product(product_id: Optional[str]) -> List[ShopifyProduct]:
    if not product_id:
        return []
    data = get_shopify_client().graphql(_PRODUCT_QUERY, {"id": _normalize_id(product_id)})
    node = data.get("product")
    return [_map_product(node)] if node else []


def _price(product: ShopifyProduct) -> Optional[float]:
    try:
        return float(product.price)
    except (TypeError, ValueError):
        return None


def search_products(category=None, budget=None, brand=None,
                    keyword=None) -> List[ShopifyProduct]:
    """本地过滤：类别 / 品牌 / 预算（价格上限）/ 关键词。"""
    results = []
    for p in fetch_all_products():
        if category and category.lower() not in (p.product_type or "").lower():
            continue
        if brand and brand.lower() not in (p.vendor or "").lower():
            continue
        if budget is not None:
            price = _price(p)
            if price is None or price > budget:
                continue
        if keyword:
            haystack = (p.title + p.product_type + p.description).lower()
            if keyword.lower() not in haystack:
                continue
        results.append(p)
    return results


def inventory(product_id=None, category=None) -> List[ShopifyInventory]:
    products = fetch_product(product_id) if product_id else fetch_all_products()
    results = []
    for p in products:
        if category and category.lower() not in (p.product_type or "").lower():
            continue
        for v in p.variants:
            results.append(ShopifyInventory(
                product_id=p.id,
                product_title=p.title,
                variant_title=v.title,
                sku=v.sku,
                available=int(v.available or 0),
            ))
    return results


# ---------- 知识源：店铺 pages / 政策（真实） ----------

_PAGES_QUERY = """
{
  pages(first: 50) {
    edges { node { id title handle body } }
  }
}
"""

_POLICIES_QUERY = """
{
  shop {
    shopPolicies { type title body }
  }
}
"""


def _html_to_text(raw: str) -> str:
    """HTML → 文本：块级标签转换行、去标签、反转义（保留段落换行，供分块）。"""
    if not raw:
        return ""
    text = re.sub(r"(?i)<\s*br\s*/?>", "\n", raw)
    text = re.sub(r"(?i)</\s*(p|div|li|h[1-6]|tr|section|article)\s*>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def fetch_pages() -> List[dict]:
    """店铺页面 → 知识条目（含 id/title/source/content）。"""
    data = get_shopify_client().graphql(_PAGES_QUERY)
    items = []
    for e in data.get("pages", {}).get("edges", []):
        n = e["node"]
        content = _html_to_text(n.get("body") or "")
        if content:
            items.append({
                "id": f"page-{n['handle']}",
                "title": n.get("title", "") or "",
                "source": "page",
                "content": content,
            })
    return items


def fetch_policies() -> List[dict]:
    """店铺政策（退款/配送/隐私/条款等）→ 知识条目。"""
    data = get_shopify_client().graphql(_POLICIES_QUERY)
    items = []
    for p in data.get("shop", {}).get("shopPolicies", []):
        content = _html_to_text(p.get("body") or "")
        if content:
            items.append({
                "id": f"policy-{p['type'].lower()}",
                "title": p.get("title", "") or "",
                "source": "policy",
                "content": content,
            })
    return items
