# evals — Phase-0 bake-off harness

The permanent quality gate for the project (see
[docs/roadmap/phase-0-bakeoff.md](../docs/roadmap/phase-0-bakeoff.md)). Built
once in phase 0, re-run for every model / prompt / adapter change after.

## Layout

```
evals/
  cases/<set>/*.yaml    # test cases (tr-docs, code, grounded-qa)
  cases/private/        # gitignored: sensitive company cases, local only
  rubrics/<set>.md      # 1-5 scoring guides
  runner.py             # POST cases to an endpoint -> results/<model>/*.json
  score.py              # interactive human scoring (fills score + note)
  report.py             # results -> per-model/per-rubric leaderboard table
  metrics.py cases.py passes.py   # tested pure helpers
  results/              # gitignored raw runs
  tests/                # pytest unit tests for the pure helpers
```

## Run

```bash
uv run pytest                                   # unit tests (17, no model needed)

# one model at a time (phase 0): start llama-server, then:
uv run python -m evals.runner --endpoint http://localhost:8080/v1 \
    --model qwen3-14b --all
uv run python -m evals.score  --model qwen3-14b # smoke pass first, then full
uv run python -m evals.report                   # leaderboard
```

## Two-pass scoring (F-016)

~50 cases × ~8 models is ~400 judgements — score in passes, don't grind:

- **Smoke** — 10–12 cases across all candidates (`passes.smoke_subset`).
- **Full** — all cases, top 2–3 candidates per role.
- **Regression** — a fixed ~15-case subset re-run on every later change.

## Data classification (F-019)

Cases encode real work. Public/synthetic → `cases/`. Sensitive company
material → `cases/private/` (gitignored, local + backup only). Committed
summaries carry scores and model names, never sensitive prompts or outputs.
The example cases here are synthetic templates — replace them with your own.
