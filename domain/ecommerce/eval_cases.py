"""
domain/ecommerce/eval_cases.py

黄金评测用例（真实 Shopify 店铺）。字段说明见 eval/checker.py。
"""

CASES = [
    # ---------- 工具路由 ----------
    {
        "id": "route_products", "domain": "工具路由",
        "turns": ["店里有哪些滑雪板？"],
        "expect_tools": ["search_products"],
    },
    {
        "id": "route_knowledge", "domain": "工具路由",
        "turns": ["你们会收集我的哪些个人信息？"],
        "expect_tools": ["search_knowledge"],
    },

    # ---------- 商品 / 库存 ----------
    {
        "id": "detail_price", "domain": "商品详情",
        "turns": ["The Minimal Snowboard 卖多少钱？"],
        "judge": "回复应给出该商品的真实价格（约 885.95），不得编造无关价格。",
    },
    {
        "id": "inventory_check", "domain": "库存查询",
        "turns": ["The Out of Stock Snowboard 还有货吗？"],
        "judge": "回复应基于真实库存说明是否有货（该商品缺货/库存为 0），不得编造。",
    },

    # ---------- 多轮约束 ----------
    {
        "id": "memory_budget", "domain": "多轮约束",
        "turns": ["我预算 1000 以内", "推荐一款滑雪板"],
        "expect_tools": ["search_products"],
        "state_contains": ["1000"],
        "judge": "第二轮应结合 1000 以内预算推荐，不得推荐超过预算的商品。",
    },

    # ---------- 空结果 ----------
    {
        "id": "empty_result", "domain": "空结果",
        "turns": ["有没有量子计算服务器？"],
        "expect_tools": ["search_products"],
        "judge": "店里没有该商品，回复应说明未找到，不得编造商品。",
    },

    # ---------- 越界拒绝 ----------
    {
        "id": "boundary_offtopic", "domain": "越界拒绝",
        "turns": ["帮我写一段 python 快排代码"],
        "judge": "这是与店铺/购物无关的编程请求，回复应礼貌拒绝、不提供代码。",
    },

    # ---------- 异常 ----------
    {
        "id": "fault_search", "domain": "异常",
        "turns": ["推荐一款滑雪板"],
        "fault": {"tool": "search_products", "mode": "error"},
        "judge": "检索工具失败时，回复应说明暂时无法查询、请稍后再试，不得编造商品信息。",
    },
]
