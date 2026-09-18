"""
scripts/fetch_benchmarks.py

下载外部基准数据到 eval/benchmarks/ 下的数据目录（可重复跑，已存在则跳过）：
- BFCL v3 工具调用（gorilla-llm/Berkeley-Function-Calling-Leaderboard）→ eval/benchmarks/bfcl_data/
- BEIR scifact 检索（官方 zip）→ eval/benchmarks/scifact_data/

运行：python -m scripts.fetch_benchmarks
"""

import zipfile
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / "eval" / "benchmarks"
BFCL_DIR = BENCH / "bfcl_data"
SCIFACT_DIR = BENCH / "scifact_data"

BFCL_BASE = "https://huggingface.co/datasets/gorilla-llm/Berkeley-Function-Calling-Leaderboard/resolve/main"
BFCL_FILES = [
    "BFCL_v3_simple.json", "BFCL_v3_multiple.json", "BFCL_v3_parallel.json",
    "BFCL_v3_parallel_multiple.json", "BFCL_v3_irrelevance.json",
]
BFCL_ANSWER_FILES = [
    "BFCL_v3_simple.json", "BFCL_v3_multiple.json", "BFCL_v3_parallel.json",
    "BFCL_v3_parallel_multiple.json",
]
SCIFACT_URL = "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/scifact.zip"


def _download(url: str, dst: Path) -> None:
    if dst.exists() and dst.stat().st_size > 0:
        print(f"skip     {dst.relative_to(ROOT)}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    dst.write_bytes(resp.content)
    print(f"download {dst.relative_to(ROOT)}")


def fetch_bfcl() -> None:
    for name in BFCL_FILES:
        _download(f"{BFCL_BASE}/{name}", BFCL_DIR / name)
    for name in BFCL_ANSWER_FILES:
        _download(f"{BFCL_BASE}/possible_answer/{name}", BFCL_DIR / "possible_answer" / name)


def fetch_scifact() -> None:
    zip_path = SCIFACT_DIR / "scifact.zip"
    _download(SCIFACT_URL, zip_path)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(SCIFACT_DIR)
    print(f"extract  {(SCIFACT_DIR / 'scifact').relative_to(ROOT)}")


if __name__ == "__main__":
    fetch_bfcl()
    fetch_scifact()
    print("done")
