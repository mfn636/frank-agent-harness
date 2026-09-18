"""
domain/enterprise/models/incident.py

工单 / 故障记录模型。
"""

from pydantic import BaseModel, Field


class Incident(BaseModel):
    id: str = Field(description="工单编号，如 INC-2041")
    service_id: str = Field(description="关联服务 ID")
    severity: str = Field(description="严重级别：P0 / P1 / P2")
    status: str = Field(description="状态：open / mitigated / closed")
    opened_at: str = Field(description="发生时间")
    title: str = Field(description="标题")
    summary: str = Field(description="摘要")
