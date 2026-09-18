"""
domain/registry.py

领域包注册表：按名取领域包。新增领域只需在此注册，核心与引擎零改动。
"""

from domain.base import DomainPack
from domain.ecommerce import PACK as ECOMMERCE_PACK

DOMAINS = {ECOMMERCE_PACK.name: ECOMMERCE_PACK}
DEFAULT_DOMAIN = ECOMMERCE_PACK.name


def get_domain(name: str = DEFAULT_DOMAIN) -> DomainPack:
    return DOMAINS[name]
