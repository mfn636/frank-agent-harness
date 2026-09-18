"""
domain/enterprise/models/service.py

内部服务存储模型。
"""

from pydantic import BaseModel, Field


class Service(BaseModel):
    id: str = Field(description="服务唯一编码，如 svc-gateway")
    name: str = Field(description="服务名称")
    owner: str = Field(description="负责团队")
    tier: str = Field(description="重要级别：核心 / 重要 / 一般")
    runtime: str = Field(description="运行形态：K8s / 物理机 / 云服务")
    status: str = Field(description="当前状态：healthy / degraded / down")
    uptime_pct: float = Field(description="可用性百分比")
    depends_on: list[str] = Field(default_factory=list, description="依赖的服务 ID")
    description: str = Field(description="服务说明")
