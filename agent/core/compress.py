"""
agent/core/compress.py

工具结果的"硬压缩"：回填给 LLM / 喂给自检前，先按「领域包提供的字段表」裁剪字段、限制条数。
省 token，同时保证 LLM 与 state/Reflection 自检看到同一份精简数据。

harness 不关心有哪些工具；字段表由领域包注入（DomainPack.tool_field_map）。
"""

import json

DEFAULT_MAX_ITEMS = 8


def compress_tool_result(tool_name, result, field_map=None, max_items=DEFAULT_MAX_ITEMS):
    """
    按领域包提供的字段表把 result 压缩为结构化 JSON 字符串。

    Args:
        tool_name: 工具名（用于查字段表）
        result: 工具返回的 pydantic 对象列表
        field_map: {工具名: [保留字段]}；未提供的工具走全量兜底，不丢数据
        max_items: 最多展示多少条；超出时 items 截断、total 标注真实命中数

    Returns:
        str: {"items": [...], "total": N}
    """
    items = [item.model_dump() for item in result]

    fields = (field_map or {}).get(tool_name)
    if fields:
        items = [
            {k: item.get(k) for k in fields if k in item}
            for item in items
        ]

    visible = items[:max_items]
    return json.dumps({
        "items": visible,
        "total": len(items),
    }, ensure_ascii=False)
