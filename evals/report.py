"""Aggregate scored result records into a per-model/per-rubric leaderboard.

    uv run python -m evals.report               # print the leaderboard table
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

RESULTS_DIR = Path(__file__).parent / "results"


def aggregate(records: list[dict]) -> dict[tuple[str, str], dict]:
    """Group records by (model, rubric). ``mean_score`` ignores unscored rows
    (score is None); ``mean_tok_s`` counts every row, since throughput is
    measured regardless of human scoring."""
    buckets: dict[tuple[str, str], dict[str, list]] = defaultdict(
        lambda: {"scores": [], "tok_s": []}
    )
    for r in records:
        key = (r["model"], r["rubric"])
        if r.get("score") is not None:
            buckets[key]["scores"].append(r["score"])
        if r.get("tokens_per_second") is not None:
            buckets[key]["tok_s"].append(r["tokens_per_second"])

    out: dict[tuple[str, str], dict] = {}
    for key, v in buckets.items():
        out[key] = {
            "n": len(v["scores"]),
            "mean_score": round(mean(v["scores"]), 2) if v["scores"] else None,
            "mean_tok_s": round(mean(v["tok_s"]), 2) if v["tok_s"] else None,
        }
    return out


def render_markdown(agg: dict[tuple[str, str], dict]) -> str:
    """Render the aggregate as a Markdown table sorted by (model, rubric)."""
    lines = [
        "| Model | Rubric | Mean score | n | Mean tok/s |",
        "|---|---|---|---|---|",
    ]
    for model, rubric in sorted(agg):
        a = agg[(model, rubric)]
        lines.append(
            f"| {model} | {rubric} | {a['mean_score']} | {a['n']} | {a['mean_tok_s']} |"
        )
    return "\n".join(lines)


def load_results(results_dir: Path) -> list[dict]:
    """Read every result JSON written by runner.py under results_dir."""
    return [
        json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(Path(results_dir).rglob("*.json"))
    ]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Print the bake-off leaderboard.")
    ap.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    args = ap.parse_args(argv)
    print(render_markdown(aggregate(load_results(args.results_dir))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
