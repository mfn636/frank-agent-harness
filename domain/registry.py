"""
domain/registry.py

领域入口。当前项目聚焦单一领域（电商客服）；
保留「领域包」这道 seam 以维持解耦，但不做多领域切换。
"""

from domain.base import DomainPack
from domain.ecommerce import PACK


def get_domain() -> DomainPack:
    """返回当前领域包（电商客服）。"""
    return PACK
