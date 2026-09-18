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

    # ---------- 多轮约束 ----------
    {
        "id": "memory_change", "domain": "多轮约束",
        "turns": ["我先关注 svc-order", "其实我更关心支付服务", "它现在是什么状态"],
        "judge": "第三轮应针对用户最新关注的服务（支付服务 svc-payment）回答，不得仍答订单服务。",
    },
    {
        "id": "memory_context", "domain": "多轮约束",
        "turns": ["我在排查网关问题", "有哪些相关的 P1 工单"],
        "expect_tools": ["list_incidents"],
        "judge": "应结合上一轮提到的网关服务筛选相关工单，而不是泛泛列出所有工单。",
    },

    # ---------- 空结果 ----------
    {
        "id": "empty_service", "domain": "空结果",
        "turns": ["有没有量子计算集群这个服务"],
        "expect_tools": ["query_service_status"],
        "judge": "服务列表中不存在该服务时，回复应说明未找到，不得编造服务状态。",
    },
    {
        "id": "empty_runbook", "domain": "空结果",
        "turns": ["量子计算集群报错怎么处理"],
        "expect_tools": ["search_runbook"],
        "judge": "手册中没有相关内容时，回复应说明未找到对应手册，不得编造处置步骤。",
    },

    # ---------- 异常 ----------
    {
        "id": "fault_service_status", "domain": "异常",
        "turns": ["订单服务现在什么状态"],
        "fault": {"tool": "query_service_status", "mode": "error"},
        "judge": "查询工具失败时，回复应说明暂时无法查询、请稍后再试，不得编造服务状态。",
    },
]
