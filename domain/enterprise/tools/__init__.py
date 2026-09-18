"""
domain/enterprise/tools/__init__.py

企业运维领域工具：由工厂绑定检索服务，生成工具契约清单。
"""

from functools import partial

from contract.retrieval import SearchService
from domain.enterprise.tool_args import (
    GetServiceDetailArgs,
    ListIncidentsArgs,
    QueryServiceStatusArgs,
    SearchRunbookArgs,
)
from domain.enterprise.tools.incidents import list_incidents
from domain.enterprise.tools.runbook_search import search_runbook
from domain.enterprise.tools.service_status import get_service_detail, query_service_status


def build_tool_specs(search_service: SearchService) -> list[dict]:
    """每次装配独立绑定依赖；服务不会成为暴露给模型的工具参数。"""
    return [
        {
            "name": "query_service_status",
            "description": "查询内部服务的运行状态。可按服务名称关键词、状态（healthy/degraded/down）、重要级别（核心/重要/一般）过滤。",
            "args_model": QueryServiceStatusArgs,
            "fn": query_service_status,
        },
        {
            "name": "get_service_detail",
            "description": "按服务 ID 查询单个服务的完整信息（负责人、级别、运行形态、当前状态、可用性、依赖服务）。",
            "args_model": GetServiceDetailArgs,
            "fn": get_service_detail,
        },
        {
            "name": "search_runbook",
            "description": "检索运维手册 / 排障步骤 / 流程规范（如网关 5xx、数据库连接池、消息积压、发布回滚、变更审批等）。",
            "args_model": SearchRunbookArgs,
            "fn": partial(search_runbook, search_service=search_service),
        },
        {
            "name": "list_incidents",
            "description": "查询工单 / 故障记录。可按服务 ID、严重级别（P0/P1/P2）、状态（open/mitigated/closed）过滤。",
            "args_model": ListIncidentsArgs,
            "fn": list_incidents,
        },
    ]


# 各工具回填给 LLM 前保留的字段（未列出的字段丢弃，省 token）
TOOL_FIELD_MAP = {
    "query_service_status": ["id", "name", "owner", "tier", "status", "uptime_pct"],
    "get_service_detail": ["id", "name", "owner", "tier", "runtime", "status",
                           "uptime_pct", "depends_on", "description"],
    "search_runbook": ["source", "title", "content", "score"],
    "list_incidents": ["id", "service_id", "severity", "status", "opened_at", "title", "summary"],
}
