"""
domain/enterprise/tool_args.py

企业运维领域工具入参的 Pydantic 模型。
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field

ServiceStatus = Literal["healthy", "degraded", "down"]
ServiceTier = Literal["核心", "重要", "一般"]
IncidentSeverity = Literal["P0", "P1", "P2"]
IncidentStatus = Literal["open", "mitigated", "closed"]


class QueryServiceStatusArgs(BaseModel):
    service_name: Optional[str] = Field(None, min_length=1, description="服务名称或 ID 的关键词，模糊匹配")
    status: Optional[ServiceStatus] = Field(None, description="按状态过滤（healthy / degraded / down）")
    tier: Optional[ServiceTier] = Field(None, description="按重要级别过滤（核心 / 重要 / 一般）")


class GetServiceDetailArgs(BaseModel):
    service_id: str = Field(..., pattern=r"^svc-[a-z0-9-]+$", description="服务 ID，例如：svc-gateway")


class SearchRunbookArgs(BaseModel):
    query: str = Field(..., min_length=1, description="用户问题（自然语言），用于运维手册语义检索")
    category: Optional[str] = Field(None, description="可选，按文档类别过滤（如 排障、流程）")
    top_k: Optional[int] = Field(None, ge=1, le=10, description="返回条数上限，默认 5")


class ListIncidentsArgs(BaseModel):
    service_id: Optional[str] = Field(None, pattern=r"^svc-[a-z0-9-]+$", description="按服务 ID 过滤")
    severity: Optional[IncidentSeverity] = Field(None, description="按严重级别过滤（P0 / P1 / P2）")
    status: Optional[IncidentStatus] = Field(None, description="按状态过滤（open / mitigated / closed）")
