"""
domain/enterprise/tools/service_status.py

服务状态查询：结构化过滤（名称 / 状态 / 级别），不走向量检索。
"""

from typing import List, Optional

from domain.enterprise.loader import load_services
from domain.enterprise.models.service import Service

SERVICES: List[Service] = load_services()
SERVICE_MAP = {s.id: s for s in SERVICES}


def query_service_status(
    service_name: Optional[str] = None,
    status: Optional[str] = None,
    tier: Optional[str] = None,
) -> List[Service]:
    """按名称关键词 / 状态 / 级别查询服务列表。"""
    results = []
    for s in SERVICES:
        if service_name and service_name.lower() not in (s.name + s.id).lower():
            continue
        if status and s.status != status:
            continue
        if tier and s.tier != tier:
            continue
        results.append(s)
    return results


def get_service_detail(service_id: Optional[str] = None) -> List[Service]:
    """按服务 ID 查询单个服务的完整信息（含依赖）。"""
    service = SERVICE_MAP.get(service_id) if service_id else None
    return [service] if service else []
