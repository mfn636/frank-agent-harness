"""
bootstrap.py

组合根：按领域包装配出一个可用的 ReActAgent（工具 + 人设 + LLM）。
把「选哪个领域」和「怎么搭起来」集中到一处，main / web / eval 都复用它。
"""

from agent.core.loop import ReActAgent
from contract.tool import build_tool_registry
from domain.registry import get_domain
from providers.local import LocalToolProvider


def build_tools(pack):
    """由领域包的工具 spec 构建工具 Provider。"""
    return LocalToolProvider(build_tool_registry(pack.tool_specs))


def build_agent(pack=None, session_id="default", llm=None, tools=None):
    """装配 Agent：注入领域包的人设与工具，核心无需知道是哪个领域。"""
    pack = pack or get_domain()
    return ReActAgent(
        session_id=session_id,
        tools=tools or build_tools(pack),
        system_prompt=pack.system_prompt,
        tool_field_map=pack.tool_field_map,
        reflection_prompt=pack.reflection_prompt,
        state_update_prompt=pack.state_update_prompt,
        llm=llm,
    )
