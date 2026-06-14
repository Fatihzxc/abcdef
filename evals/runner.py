"""Run cases against an OpenAI-compatible endpoint and record raw results.

Pure helpers (build_payload / make_record) are unit-tested; call_model and the
CLI are the thin I/O shell. See docs/roadmap/phase-0-bakeoff.md, Step 3 & 5.

    uv run python -m evals.runner --endpoint http://localhost:8080/v1 \
        --model qwen3-coder --all
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.request
from pathlib import Path

import yaml

from .cases import Case, load_case
from .metrics import tokens_per_second

CASES_DIR = Path(__file__).parent / "cases"
RESULTS_DIR = Path(__file__).parent / "results"

# Grounded cases must answer ONLY from context, with an exact refusal string —
# this is what the faithfulness rubric and the F-021 "not found" trap rely on.
GROUNDING_SYSTEM = (
    "Answer using only the provided context. If the answer is not in the "
    "context, reply exactly: not found in the provided context.\n\nContext:\n"
)


def build_payload(case: Case, model: str) -> dict:
    """Deterministic request body (temperature 0, fixed seed) so reruns match."""
    messages = []
    if case.context:
        messages.append({"role": "system", "content": GROUNDING_SYSTEM + case.context})
    messages.append({"role": "user", "content": case.prompt})
    return {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "seed": 0,
        "max_tokens": case.max_tokens,
    }


def make_record(case: Case, model: str, response_json: dict, elapsed_s: float) -> dict:
    """Turn a raw API response into a result record. score/note stay empty
    until score.py fills them in."""
    usage = response_json.get("usage", {})
    completion_tokens = int(usage.get("completion_tokens", 0))
    completion = response_json["choices"][0]["message"]["content"]
    return {
        "case_id": case.id,
        "role": case.role,
        "rubric": case.rubric,
        "model": model,
        "completion": completion,
        "prompt_tokens": int(usage.get("prompt_tokens", 0)),
        "completion_tokens": completion_tokens,
        "elapsed_s": round(elapsed_s, 3),
        "tokens_per_second": round(tokens_per_second(completion_tokens, elapsed_s), 2),
        "score": None,
        "note": "",
    }


def call_model(endpoint: str, payload: dict, api_key: str = "local", timeout: int = 600):
    """POST to <endpoint>/chat/completions; return (response_json, elapsed_s)."""
    req = urllib.request.Request(
        endpoint.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode())
    return body, time.perf_counter() - t0


def iter_cases(cases_dir: Path = CASES_DIR):
    """Yield Case objects from every *.yaml under cases/ except cases/private
    (which is gitignored and may hold sensitive material; include it explicitly
    if you mean to)."""
    for path in sorted(cases_dir.rglob("*.yaml")):
        if "private" in path.relative_to(cases_dir).parts:
            continue
        yield load_case(yaml.safe_load(path.read_text(encoding="utf-8")))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run bake-off cases against an endpoint.")
    ap.add_argument("--endpoint", required=True, help="OpenAI-compatible base URL, e.g. http://localhost:8080/v1")
    ap.add_argument("--model", required=True, help="model name/alias to request")
    ap.add_argument("--api-key", default="local")
    ap.add_argument("--all", action="store_true", help="run every case under cases/")
    ap.add_argument("--cases-dir", type=Path, default=CASES_DIR)
    args = ap.parse_args(argv)

    out_dir = RESULTS_DIR / args.model
    out_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for case in iter_cases(args.cases_dir):
        body, elapsed = call_model(args.endpoint, build_payload(case, args.model), args.api_key)
        record = make_record(case, args.model, body, elapsed)
        dest = out_dir / (case.id.replace("/", "__") + ".json")
        dest.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{case.id:40s} {record['tokens_per_second']:>6.1f} tok/s")
        n += 1
    print(f"\n{n} cases -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
