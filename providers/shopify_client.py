"""
providers/shopify_client.py

Shopify Admin API 客户端（里程碑 1：只读）。
- client-credentials 换取 access token（缓存 + 到期前 60s 刷新，24h 有效）
- graphql() 执行 GraphQL 查询
"""

import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

_TOKEN_URL = "https://{shop}.myshopify.com/admin/oauth/access_token"
_GRAPHQL_URL = "https://{shop}.myshopify.com/admin/api/{version}/graphql.json"


class ShopifyClient:

    def __init__(self, shop=None, client_id=None, client_secret=None,
                 api_version=None, timeout=30):
        self.shop = shop or os.getenv("SHOPIFY_SHOP")
        self.client_id = client_id or os.getenv("SHOPIFY_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("SHOPIFY_CLIENT_SECRET")
        self.api_version = api_version or os.getenv("SHOPIFY_API_VERSION", "2026-07")
        self.timeout = timeout
        self._token = None
        self._expires_at = 0.0
        if not (self.shop and self.client_id and self.client_secret):
            raise ValueError(
                "Shopify 凭据缺失：需要 SHOPIFY_SHOP / SHOPIFY_CLIENT_ID / SHOPIFY_CLIENT_SECRET"
            )

    def _get_token(self) -> str:
        """换取并缓存 access token；到期前 60s 自动刷新。"""
        if self._token and time.time() < self._expires_at - 60:
            return self._token
        resp = requests.post(
            _TOKEN_URL.format(shop=self.shop),
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._expires_at = time.time() + int(data.get("expires_in", 86399))
        return self._token

    def graphql(self, query: str, variables: dict = None) -> dict:
        """执行 GraphQL；有 errors 抛异常（由工具层降级兜底）。"""
        resp = requests.post(
            _GRAPHQL_URL.format(shop=self.shop, version=self.api_version),
            headers={
                "X-Shopify-Access-Token": self._get_token(),
                "Content-Type": "application/json",
            },
            json={"query": query, "variables": variables or {}},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("errors"):
            raise RuntimeError(f"Shopify GraphQL errors: {data['errors']}")
        return data.get("data", {})


_client = None


def get_shopify_client() -> ShopifyClient:
    """进程内单例。"""
    global _client
    if _client is None:
        _client = ShopifyClient()
    return _client
