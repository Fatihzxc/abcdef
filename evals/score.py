"""Interactive human scoring of bake-off results (Step 5).

Walks unscored result records, shows the completion + its rubric, and records a
1-5 score and a note in place. No LLM-as-judge in phase 0 (the judge would be
one of the contestants). Score the smoke pass first, then the full pass:

    uv run python -m evals.score                  # score everything unscored
    uv run python -m evals.score --model qwen3-14b
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"
RUBRICS_DIR = Path(__file__).parent / "rubrics"


def unscored_files(results_dir: Path, model: str | None = None):
    root = results_dir / model if model else results_dir
    if not root.exists():
        return
    for path in sorted(root.rglob("*.json")):
        rec = json.loads(path.read_text(encoding="utf-8"))
        if rec.get("score") is None:
            yield path, rec


def _read_score() -> int | None:
    while True:
        raw = input("score 1-5 (s=skip): ").strip().lower()
        if raw == "s":
            return None
        if raw in {"1", "2", "3", "4", "5"}:
            return int(raw)
        print("  enter 1-5 or s")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Score unscored bake-off results.")
    ap.add_argument("--model", default=None, help="only score this model's results")
    ap.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    args = ap.parse_args(argv)

    pending = list(unscored_files(args.results_dir, args.model))
    if not pending:
        print("nothing to score.")
        return 0
    for i, (path, rec) in enumerate(pending, 1):
        rubric_path = RUBRICS_DIR / f"{rec['rubric']}.md"
        rubric = rubric_path.read_text(encoding="utf-8") if rubric_path.exists() else "(rubric missing)"
        print("=" * 72)
        print(f"[{i}/{len(pending)}] {rec['case_id']}  model={rec['model']}  rubric={rec['rubric']}")
        print("-" * 72)
        print(rec["completion"])
        print("-" * 72)
        print(rubric)
        score = _read_score()
        if score is None:
            continue
        rec["score"] = score
        rec["note"] = input("note (optional): ").strip()
        path.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    print("done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
