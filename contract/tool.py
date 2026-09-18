"""
contract/tool.py

工具契约·数据侧的机制（领域无关）：
- build_tool_registry(specs)：由「工具 spec 列表」构建注册表
- 给模型的 function schema 由 args_model.model_json_schema() 自动生成并清洗
- 参数校验用同一份 pydantic 模型（单一真相来源）

具体领域有哪些工具，由各领域包提供（见 domain/<pack>/tools）。
"""

__all__ = ["ToolRegistry", "build_tool_registry", "clean_schema"]


def clean_schema(node):
    """清洗 model_json_schema 输出：折叠 anyOf[X, null]→X，去掉 title / default。"""
    if isinstance(node, list):
        return [clean_schema(item) for item in node]
    if not isinstance(node, dict):
        return node

    # anyOf: [X, null] -> X（保留原节点的 description）
    if "anyOf" in node:
        branches = node["anyOf"]
        non_null = [b for b in branches if b.get("type") != "null"]
        if len(non_null) == 1 and len(non_null) < len(branches):
            merged = dict(non_null[0])
            if "description" in node:
                merged["description"] = node["description"]
            node = merged

    node.pop("title", None)
    node.pop("default", None)
    for key, value in list(node.items()):
        if isinstance(value, (dict, list)):
            node[key] = clean_schema(value)
    return node


def _build_tools(specs):
    tools = []
    for item in specs:
        schema = clean_schema(item["args_model"].model_json_schema())
        schema.setdefault("required", [])
        tools.append({
            "type": "function",
            "function": {
                "name": item["name"],
                "description": item["description"],
                "parameters": schema,
            },
        })
    return tools


class ToolRegistry:
    """由工具 spec 构建的注册表：对外提供 schema 与校验后的调用。"""

    def __init__(self, specs):
        self.specs = list(specs)
        self._args_model = {s["name"]: s["args_model"] for s in self.specs}
        self._fn = {s["name"]: s["fn"] for s in self.specs}
        self._tools = _build_tools(self.specs)

    def list_tools(self) -> list:
        return self._tools

    def validate_args(self, name, args):
        """校验并补默认值；未知工具抛 KeyError，参数非法抛 ValidationError。"""
        return self._args_model[name].model_validate(args)

    def call(self, name, args):
        if name not in self._fn:
            raise KeyError(f"未知工具: {name}")
        validated = self.validate_args(name, args)
        return self._fn[name](**validated.model_dump(exclude_none=True))


def build_tool_registry(specs) -> ToolRegistry:
    """工具注册表工厂：领域包提供 specs，机制侧负责构建。"""
    return ToolRegistry(specs)
