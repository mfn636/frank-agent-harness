"""
domain/enterprise/eval_cases.py

企业运维领域的黄金评测用例（字段说明见 eval/checker.py）。
"""

CASES = [
    # ---------- 工具路由 ----------
    {
        "id": "route_service_status", "domain": "工具路由",
        "turns": ["订单服务现在是什么状态"],
        "expect_tools": ["query_service_status"],
    },
    {
        "id": "route_runbook", "domain": "工具路由",
        "turns": ["网关 5xx 突然升高了，怎么排查"],
        "expect_tools": ["search_runbook"],
    },
    {
        "id": "route_incidents", "domain": "工具路由",
        "turns": ["现在还有哪些 P0 的工单"],
        "expect_tools": ["list_incidents"],
    },
    {
        "id": "route_service_detail", "domain": "工具路由",
        "turns": ["svc-gateway 的负责人是谁"],
        "expect_tools": ["get_service_detail"],
        "must_contain": ["平台组"],
    },

    # ---------- 多轮记忆 ----------
    {
        "id": "memory_service", "domain": "多轮记忆",
        "turns": ["我主要负责订单服务", "它最近有哪些工单"],
        "expect_tools": ["list_incidents"],
        "state_contains": ["svc-order"],
    },

    # ---------- 越界拒绝 ----------
    {
        "id": "boundary_offtopic", "domain": "越界拒绝",
        "turns": ["帮我写一段 python 快排代码"],
        "judge": "这是与运维/企业运营无关的编程请求，回复应礼貌拒绝、不提供代码。",
    },
]
