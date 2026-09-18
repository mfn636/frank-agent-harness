"""
domain/enterprise/tools/incidents.py

工单 / 故障记录查询：结构化过滤。
"""

from typing import List, Optional

from domain.enterprise.loader import load_incidents
from domain.enterprise.models.incident import Incident

INCIDENTS: List[Incident] = load_incidents()


def list_incidents(
    service_id: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
) -> List[Incident]:
    """按服务 / 级别 / 状态查询工单。"""
    results = []
    for inc in INCIDENTS:
        if service_id and inc.service_id != service_id:
            continue
        if severity and inc.severity != severity:
            continue
        if status and inc.status != status:
            continue
        results.append(inc)
    return results
