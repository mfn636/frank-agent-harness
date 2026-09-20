"""
tests/test_shopify_tools.py

Shopify 只读工具的映射 / 过滤测试（mock 客户端，不真调网络）。
"""

import unittest
from unittest.mock import patch

from domain.ecommerce import shopify_source

_NODE_SNOWBOARD = {
    "id": "gid://shopify/Product/1", "title": "The Snowboard", "productType": "snowboard",
    "vendor": "losanlu", "status": "ACTIVE", "description": "a board", "tags": ["board"],
    "variants": {"edges": [{"node": {
        "id": "gid://shopify/ProductVariant/1", "title": "Default", "sku": "SKU1",
        "price": "100.00", "inventoryQuantity": 5,
        "selectedOptions": [{"name": "Size", "value": "M"}],
    }}]},
}
_NODE_GIFT = {
    "id": "gid://shopify/Product/2", "title": "Gift Card", "productType": "giftcard",
    "vendor": "shop", "status": "ACTIVE", "description": "gift", "tags": [],
    "variants": {"edges": [{"node": {
        "id": "gid://shopify/ProductVariant/2", "title": "Default", "sku": None,
        "price": "10.00", "inventoryQuantity": 0, "selectedOptions": [],
    }}]},
}
_PRODUCTS_DATA = {"products": {"edges": [{"node": _NODE_SNOWBOARD}, {"node": _NODE_GIFT}]}}


class FakeClient:
    def __init__(self, products_data=None, product_data=None):
        self._products = products_data
        self._product = product_data

    def graphql(self, query, variables=None):
        if "product(id:" in query:
            return {"product": self._product}
        return self._products


class ShopifyToolTests(unittest.TestCase):

    def test_search_maps_and_filters(self):
        client = FakeClient(products_data=_PRODUCTS_DATA)
        with patch("domain.ecommerce.shopify_source.get_shopify_client", return_value=client):
            res = shopify_source.search_products(keyword="snowboard")
        self.assertEqual([p.title for p in res], ["The Snowboard"])
        self.assertEqual(res[0].vendor, "losanlu")
        self.assertEqual(res[0].price, "100.00")
        self.assertEqual(res[0].variants[0].available, 5)
        self.assertEqual(res[0].variants[0].options, ["Size:M"])

    def test_search_budget_filter_excludes_expensive(self):
        client = FakeClient(products_data=_PRODUCTS_DATA)
        with patch("domain.ecommerce.shopify_source.get_shopify_client", return_value=client):
            titles = [p.title for p in shopify_source.search_products(budget=50)]
        self.assertEqual(titles, ["Gift Card"])

    def test_fetch_product_detail(self):
        client = FakeClient(product_data=_NODE_SNOWBOARD)
        with patch("domain.ecommerce.shopify_source.get_shopify_client", return_value=client):
            res = shopify_source.fetch_product("1")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].id, "gid://shopify/Product/1")
        self.assertEqual(res[0].status, "ACTIVE")

    def test_inventory_by_category(self):
        client = FakeClient(products_data=_PRODUCTS_DATA)
        with patch("domain.ecommerce.shopify_source.get_shopify_client", return_value=client):
            inv = shopify_source.inventory(category="snowboard")
        self.assertEqual(len(inv), 1)
        self.assertEqual(inv[0].available, 5)
        self.assertEqual(inv[0].product_title, "The Snowboard")

    def test_tools_delegate_to_shopify_source(self):
        client = FakeClient(products_data=_PRODUCTS_DATA)
        with patch("domain.ecommerce.shopify_source.get_shopify_client", return_value=client):
            from domain.ecommerce.tools.product_search import search_products
            titles = [p.title for p in search_products(keyword="gift")]
        self.assertEqual(titles, ["Gift Card"])


if __name__ == "__main__":
    unittest.main()
