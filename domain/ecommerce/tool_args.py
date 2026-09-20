"""
domain/ecommerce/tool_args.py

工具入参的 Pydantic 模型（工具契约的数据侧）。
- 商品/库存：自由文本参数（对接真实店铺，不绑枚举）
- 知识：自然语言 query
"""

from typing import Optional

from pydantic import BaseModel, Field


class SearchProductsArgs(BaseModel):
    category: Optional[str] = Field(
        None, description="商品类别/类型（自由文本，如 snowboard）"
    )
    budget: Optional[float] = Field(None, gt=0, description="最高预算（价格上限）")
    brand: Optional[str] = Field(None, description="品牌/供应商（自由文本）")
    keyword: Optional[str] = Field(
        None, min_length=1, description="关键词，在商品名称/类型/简介中模糊匹配"
    )
    query: Optional[str] = Field(
        None, min_length=1, description="用户原始需求描述，当 keyword 未传时生效"
    )


class CheckInventoryArgs(BaseModel):
    product_id: Optional[str] = Field(
        None, min_length=1, description="商品 ID（gid 或数字），例如：gid://shopify/Product/123"
    )
    category: Optional[str] = Field(
        None, description="商品类别/类型（自由文本）"
    )


class GetProductDetailArgs(BaseModel):
    product_id: str = Field(
        ..., min_length=1, description="商品 ID（gid 或数字），例如：gid://shopify/Product/123"
    )


class SearchKnowledgeArgs(BaseModel):
    query: str = Field(..., min_length=1, description="用户问题（自然语言），用于知识库语义检索")
    top_k: Optional[int] = Field(None, ge=1, le=10, description="返回条数上限，默认 5")
