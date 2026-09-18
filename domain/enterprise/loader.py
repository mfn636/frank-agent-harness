"""
domain/enterprise/loader.py

加载企业运维领域的数据（服务 / 工单 / 运维手册）。
"""

import json
from pathlib import Path

from domain.enterprise.models.incident import Incident
from domain.enterprise.models.service import Service

SERVICES_FILE = Path(__file__).parent / "data" / "services.json"
INCIDENTS_FILE = Path(__file__).parent / "data" / "incidents.json"
RUNBOOKS_FILE = Path(__file__).parent / "data" / "runbooks.json"


def load_services():
    with open(SERVICES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Service(**item) for item in data["services"]]


def load_incidents():
    with open(INCIDENTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Incident(**item) for item in data]


def load_runbooks():
    """长文档（运维手册 / 流程）：返回原始 dict 列表（含 id/title/category/source/content）。"""
    with open(RUNBOOKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
