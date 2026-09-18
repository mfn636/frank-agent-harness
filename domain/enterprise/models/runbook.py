"""
domain/enterprise/models/runbook.py

运维手册检索的输出视图。
"""

from pydantic import BaseModel, Field


class RunbookItem(BaseModel):
    source: str = Field(description="来源：runbook / policy")
    title: str = Field(description="文档标题")
    content: str = Field(description="检索到的片段正文")
    score: float = Field(description="与查询的相似度得分")
