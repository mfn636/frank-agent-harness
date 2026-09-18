"""
domain/registry.py

领域包注册表：按名取领域包。新增领域只需在此注册，核心与引擎零改动。
"""

import os

from domain.base import DomainPack
from domain.ecommerce import PACK as ECOMMERCE_PACK
from domain.enterprise import PACK as ENTERPRISE_PACK

DOMAINS = {
    ECOMMERCE_PACK.name: ECOMMERCE_PACK,
    ENTERPRISE_PACK.name: ENTERPRISE_PACK,
}
DEFAULT_DOMAIN = ECOMMERCE_PACK.name


def get_domain(name: str | None = None) -> DomainPack:
    """按名取领域包；name 为空时读环境变量 AGENT_DOMAIN，再回退默认（ecommerce）。"""
    name = name or os.getenv("AGENT_DOMAIN") or DEFAULT_DOMAIN
    if name not in DOMAINS:
        raise KeyError(f"未知领域：{name}（可选：{list(DOMAINS)}）")
    return DOMAINS[name]
