"""
eval/benchmarks/bfcl.py

BFCL v3（Berkeley Function Calling Leaderboard）工具调用评测。
测的是 harness 的「工具调用通道」：把 BFCL 的函数 schema 传给模型 → 解析 tool_calls → 与标准答案比对。

数据：eval/benchmarks/bfcl_data/（从 HF gorilla-llm/Berkeley-Function-Calling-Leaderboard 下载）
运行：python -m eval.benchmarks.bfcl [simple|multiple|parallel|parallel_multiple|irrelevance] [limit]

说明：官方 BFCL 用完整 AST 检查器；此处为**简化检查器**（名称 + 参数值容忍匹配、集合配对），
用于快速自查，不等于官方榜单分数。
"""

import json
import sys
import copy
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from llm.client import LLMClient

DATA = Path(__file__).parent / "bfcl_data"
CATEGORIES = ["simple", "multiple", "parallel", "parallel_multiple", "irrelevance"]

# BFCL 的 python 类型 → OpenAI/JSON Schema 类型
_TYPE_MAP = {
    "dict": "object", "float": "number", "list": "array", "tuple": "array",
    "any": "string", "bool": "boolean",
}


def _read_jsonl(path: Path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_cases(category: str):
    return _read_jsonl(DATA / f"BFCL_v3_{category}.json")


def load_answers(category: str):
    rows = _read_jsonl(DATA / "possible_answer" / f"BFCL_v3_{category}.json")
    return {r["id"]: r.get("ground_truth", []) for r in rows}


def _normalize_schema(params):
    """BFCL 用 python 类型名，转成 OpenAI 兼容类型（dict->object 等）。"""
    node = copy.deepcopy(params) if params else {"type": "object", "properties": {}}

    def walk(n):
        if isinstance(n, dict):
            t = n.get("type")
            if isinstance(t, str) and t in _TYPE_MAP:
                n["type"] = _TYPE_MAP[t]
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)

    walk(node)
    return node


def _sanitize_name(name, seen):
    """BFCL 函数名可能含 '.' 等字符，API 要求 ^[a-zA-Z0-9_-]+$，做安全化并保序去重。"""
    safe = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
    if not safe or not re.match(r"^[a-zA-Z]", safe):
        safe = "fn_" + safe
    base, i = safe, 1
    while safe in seen:
        safe = f"{base}_{i}"
        i += 1
    seen.add(safe)
    return safe


def _tools_from_functions(funcs):
    """返回 (tools, name_map)：name_map[安全名] = 原始名。"""
    tools, name_map, seen = [], {}, set()
    for f in funcs:
        safe = _sanitize_name(f["name"], seen)
        name_map[safe] = f["name"]
        tools.append({
            "type": "function",
            "function": {
                "name": safe,
                "description": f.get("description", ""),
                "parameters": _normalize_schema(f.get("parameters")),
            },
        })
    return tools, name_map


def _to_messages(question):
    """BFCL question: 多轮，每轮是一个 message 列表。"""
    msgs = []
    for turn in question:
        for m in turn:
            content = m.get("content", "")
            if not isinstance(content, str):
                content = json.dumps(content, ensure_ascii=False)
            msgs.append({"role": m.get("role", "user"), "content": content})
    return msgs


def predict(llm, case):
    """跑一次工具调用通道，返回 [{"name":..., "args": {...}}]。"""
    tools, name_map = _tools_from_functions(case.get("function", []))
    resp = llm.chat(
        messages=_to_messages(case["question"]),
        tools=tools,
        temperature=0.0,
    )
    calls = []
    for tc in (getattr(resp, "tool_calls", None) or []):
        raw = tc.function.arguments
        try:
            args = json.loads(raw) if isinstance(raw, str) else (raw or {})
        except json.JSONDecodeError:
            args = {}
        calls.append({
            "name": name_map.get(tc.function.name, tc.function.name),
            "args": args if isinstance(args, dict) else {},
        })
    return calls


# ---------- 简化检查器 ----------

def _value_ok(pred, acceptable):
    for a in acceptable:
        if pred == a or str(pred) == str(a):
            return True
        try:
            if float(pred) == float(a):
                return True
        except (TypeError, ValueError):
            pass
    return False


def _call_matches(pred, gt_name, gt_args, allow_extra=True):
    if pred["name"] != gt_name:
        return False
    for k, acceptable in gt_args.items():
        if k not in pred["args"]:
            # 标准答案里含 "" = 该参数可选，省略合法
            if "" in acceptable:
                continue
            return False
        if not _value_ok(pred["args"][k], acceptable):
            return False
    if not allow_extra and (set(pred["args"]) - set(gt_args)):
        return False
    return True


def check(category, pred, gt):
    if category == "irrelevance":
        return len(pred) == 0
    if category == "simple":
        if len(pred) != 1 or len(gt) != 1:
            return False
        name = next(iter(gt[0]))
        return _call_matches(pred[0], name, gt[0][name])
    # multiple / parallel / parallel_multiple：集合配对（顺序无关）
    if len(pred) != len(gt):
        return False
    used = [False] * len(pred)
    for g in gt:
        name = next(iter(g))
        hit = False
        for i, p in enumerate(pred):
            if not used[i] and _call_matches(p, name, g[name]):
                used[i] = True
                hit = True
                break
        if not hit:
            return False
    return True


def _run_one(llm, category, case, answers):
    pred = predict(llm, case)
    return case, pred, check(category, pred, answers.get(case["id"], []))


def run(category="simple", limit=None, llm=None, verbose=True, workers=8):
    if category not in CATEGORIES:
        raise SystemExit(f"未知类别：{category}（可选 {CATEGORIES}）")
    cases = load_cases(category)
    answers = load_answers(category) if category != "irrelevance" else {}
    if limit:
        cases = cases[:limit]

    llm = llm or LLMClient()
    mark = len(llm.usage_log)

    if workers and workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            outcomes = list(ex.map(lambda c: _run_one(llm, category, c, answers), cases))
    else:
        outcomes = [_run_one(llm, category, c, answers) for c in cases]

    passed = sum(int(ok) for _, _, ok in outcomes)
    fails = [(c["id"], pred, answers.get(c["id"])) for c, pred, ok in outcomes if not ok]

    entries = llm.usage_log[mark:]
    total = len(cases)
    acc = passed / total * 100 if total else 0.0
    result = {
        "category": category, "total": total, "passed": passed, "accuracy": acc,
        "llm_calls": len(entries),
        "tokens": sum(e["total_tokens"] for e in entries),
        "latency_s": round(sum(e["latency_ms"] for e in entries) / 1000, 1),
        "fails": fails,
    }
    if verbose:
        print(f"BFCL v3 · {category}（简化检查器）")
        print(f"  通过 {passed}/{total} = {acc:.1f}%")
        print(f"  LLM 调用 {len(entries)} 次 · 总 token {result['tokens']} · 耗时 {result['latency_s']}s")
        for cid, pred, gt in fails[:5]:
            print(f"  [FAIL] {cid}\n    pred={json.dumps(pred, ensure_ascii=False)}\n    gt  ={json.dumps(gt, ensure_ascii=False)}")
    return result


RESULT_JSON = Path(__file__).parent / "bfcl_results.json"
REPORT = Path(__file__).parent / "bfcl_report.md"


def _save_partial(results):
    RESULT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")


def run_all(limit=None, workers=8):
    from datetime import datetime
    llm = LLMClient()
    results = []
    for cat in CATEGORIES:
        results.append(run(cat, limit=limit, llm=llm, workers=workers))
        _save_partial(results)          # 逐类落盘，中断也不丢
        _render_report(results, limit, llm.model)
    return results


def _render_report(results, limit, model):
    total = sum(r["total"] for r in results)
    passed = sum(r["passed"] for r in results)
    lines = [
        "# BFCL v3 工具调用评测报告（简化检查器）",
        "",
        f"> 时间：{__import__('datetime').datetime.now():%Y-%m-%d %H:%M} · 模型：{model} · "
        f"{'全量' if not limit else f'每类前 {limit} 条'}",
        "",
        "| 类别 | 通过 / 总数 | 准确率 |",
        "|---|---|---|",
    ]
    for r in results:
        lines.append(f"| {r['category']} | {r['passed']} / {r['total']} | {r['accuracy']:.1f}% |")
    lines.append(f"| **合计** | **{passed} / {total}** | **{passed / total * 100:.1f}%** |")
    lines += [
        "",
        f"> LLM 调用 {sum(r['llm_calls'] for r in results)} 次 · "
        f"总 token {sum(r['tokens'] for r in results)} · "
        f"耗时 {sum(r['latency_s'] for r in results):.1f}s",
        "",
        "> 注：使用**简化 AST 检查器**（名称 + 参数值容忍匹配、集合配对、可选项 `\"\"` 省略合法），"
        "不等同官方 BFCL 榜单分数；用于自查 harness 工具调用通道。",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "simple"
    lim = int(sys.argv[2]) if len(sys.argv) > 2 else None
    wk = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    if arg == "all":
        run_all(lim, workers=wk)
        print(f"\n报告已写入：{REPORT}")
    else:
        run(arg, lim, workers=wk)
