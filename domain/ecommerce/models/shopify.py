"""
domain/ecommerce/models/shopify.py

真实 Shopify 数据的领域模型（里程碑 2：主工具读真实店铺）。
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class ShopifyVariant(BaseModel):
    id: str = Field(description="变体 ID（gid）")
    title: str = Field(default="", description="变体标题")
    sku: Optional[str] = Field(default=None, description="SKU")
    price: Optional[str] = Field(default=None, description="价格（字符串金额）")
    available: Optional[int] = Field(default=None, description="可售库存数量")
    options: List[str] = Field(default_factory=list, description="选项，如 ['尺寸:M']")


class ShopifyProduct(BaseModel):
    id: str = Field(description="商品 ID（gid）")
    title: str = Field(description="商品名称")
    product_type: str = Field(default="", description="商品类型")
    vendor: str = Field(default="", description="品牌/供应商")
    status: str = Field(default="", description="状态：ACTIVE / DRAFT / ARCHIVED")
    price: Optional[str] = Field(default=None, description="首个变体价格")
    description: str = Field(default="", description="商品简介")
    tags: List[str] = Field(default_factory=list, description="标签")
    variants: List[ShopifyVariant] = Field(default_factory=list, description="变体列表")


class ShopifyInventory(BaseModel):
    product_id: str = Field(description="商品 ID（gid）")
    product_title: str = Field(description="商品名称")
    variant_title: str = Field(default="", description="变体标题")
    sku: Optional[str] = Field(default=None, description="SKU")
    available: int = Field(default=0, description="可售库存数量")
