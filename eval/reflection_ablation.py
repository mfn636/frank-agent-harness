"""
eval/reflection_ablation.py

自检（Reflection）开 / 关消融：同一用例集各跑一遍，对比通过率与成本，
用来决定 Reflection 是否值得保留。

运行：python -m eval.reflection_ablation
"""

from datetime import datetime
from pathlib import Path

from domain.registry import get_domain
from eval.checker import rule_check
from eval.judge import llm_judge
from eval.runner import build_eval_agent
from llm.client import LLMClient

JUDGE_PASS = 0.6
REPORT = Path("eval/reflection_ablation.md")
SESSIONS = Path("sessions")


def _cleanup():
    if SESSIONS.is_dir():
        for f in SESSIONS.glob("abl_*.json"):
            f.unlink()


def _run_once(pack, reflect, llm):
    rows = []
    for case in pack.eval_cases:
        mark = len(llm.usage_log)
        agent = build_eval_agent(pack, case, llm, reflect=reflect,
                                 session_id=f"abl_{'on' if reflect else 'off'}_{case['id']}")
        replies, tool_calls = [], []
        for turn in case["turns"]:
            r = agent.run(turn)
            replies.extend(r.replies)
            tool_calls.extend(r.tool_calls)

        issues = rule_check(case, replies, tool_calls, agent.state.text)
        if case.get("judge"):
            judge = llm_judge(llm, case["judge"], " / ".join(case["turns"]), "\n".join(replies))
            if judge["score"] < JUDGE_PASS:
                issues.append(f"judge 不达标（{judge['score']:.2f}）")

        entries = llm.usage_log[mark:]
        rows.append({
            "id": case["id"], "passed": not issues, "issues": issues,
            "calls": len(entries),
            "tokens": sum(e["total_tokens"] for e in entries),
            "latency_s": round(sum(e["latency_ms"] for e in entries) / 1000, 1),
        })
    return rows


def _summary(rows):
    total = len(rows)
    passed = sum(1 for r in rows if r["passed"])
    return {
        "total": total, "passed": passed,
        "rate": passed / total * 100 if total else 0.0,
        "calls": sum(r["calls"] for r in rows),
        "tokens": sum(r["tokens"] for r in rows),
        "latency_s": round(sum(r["latency_s"] for r in rows), 1),
    }


def ablate(pack):
    llm = LLMClient()
    on = _run_once(pack, True, llm)
    off = _run_once(pack, False, llm)
    return {"on": on, "off": off}


def _render(per_pack):
    lines = [
        "# Reflection 开 / 关消融报告",
        "",
        f"> 时间：{datetime.now():%Y-%m-%d %H:%M}",
        "",
    ]
    for name, res in per_pack.items():
        s_on, s_off = _summary(res["on"]), _summary(res["off"])
        lines += [
            f"## 领域：{name}（用例 {s_on['total']}）",
            "",
            "| 配置 | 通过 / 总数 | 通过率 | LLM 调用 | tokens | 耗时 |",
            "|---|---|---|---|---|---|",
            f"| Reflection 开 | {s_on['passed']} / {s_on['total']} | {s_on['rate']:.1f}% | {s_on['calls']} | {s_on['tokens']} | {s_on['latency_s']}s |",
            f"| Reflection 关 | {s_off['passed']} / {s_off['total']} | {s_off['rate']:.1f}% | {s_off['calls']} | {s_off['tokens']} | {s_off['latency_s']}s |",
            "",
            "| 用例 | 开 | 关 |",
            "|---|---|---|",
        ]
        on_map = {r["id"]: r for r in res["on"]}
        for r in res["off"]:
            o = on_map.get(r["id"], {})
            lines.append(f"| {r['id']} | {'PASS' if o.get('passed') else 'FAIL'} | {'PASS' if r['passed'] else 'FAIL'} |")
        lines.append("")

    # 汇总
    all_on = [r for res in per_pack.values() for r in res["on"]]
    all_off = [r for res in per_pack.values() for r in res["off"]]
    a_on, a_off = _summary(all_on), _summary(all_off)
    lines += [
        "## 合计",
        "",
        "| 配置 | 通过 / 总数 | 通过率 | LLM 调用 | tokens | 耗时 |",
        "|---|---|---|---|---|---|",
        f"| Reflection 开 | {a_on['passed']} / {a_on['total']} | {a_on['rate']:.1f}% | {a_on['calls']} | {a_on['tokens']} | {a_on['latency_s']}s |",
        f"| Reflection 关 | {a_off['passed']} / {a_off['total']} | {a_off['rate']:.1f}% | {a_off['calls']} | {a_off['tokens']} | {a_off['latency_s']}s |",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    _cleanup()
    pack = get_domain()
    report = _render({pack.name: ablate(pack)})
    REPORT.write_text(report, encoding="utf-8")
    _cleanup()
    print(report)
    print(f"\n报告已写入：{REPORT}")
