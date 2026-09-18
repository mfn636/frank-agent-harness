"""
providers/local.py

本地工具适配器：把工具注册表包装成核心依赖的 ToolProvider 端口。
核心只认 list_tools / call，不关心注册表从哪个领域包来。
"""

from contract.tool import ToolRegistry


class LocalToolProvider:
    """本地工具适配器：包装一个 ToolRegistry。"""

    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def list_tools(self) -> list:
        return self.registry.list_tools()

    def call(self, name: str, args: dict):
        return self.registry.call(name, args)
