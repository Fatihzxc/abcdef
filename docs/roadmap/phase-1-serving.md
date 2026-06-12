# Phase 1 — Serving + Top Roles

Goal: the bake-off winners answering through all three daily interfaces —
browser chat (R1, R2, R6), VS Code (R3, R4), CLI/pre-commit (R3, R4) — with
every role defined exactly once in `configs/roles/`.

Prerequisite: `docs/bakeoff/results.md` exists (phase 0 done).

Acceptance criteria:

- [ ] `llama-swap` serves all winner models behind one OpenAI-compatible
      endpoint; requesting a role-named model hot-swaps to the right GGUF.
- [ ] `configs/roles/*.yaml` is the single source of truth; render script
      generates the Continue config and Open WebUI presets from it.
- [ ] Open WebUI: one preset per R1/R2/R6, working chats in Turkish.
- [ ] Continue in VS Code: inline + chat against r3-coder; `/review` prompt
      runs R4 on the current diff.
- [ ] `llmctl` CLI works; pre-commit hook runs R4 on staged diffs.

Estimated effort: 3–4 working sessions.

---

## Architectural invariant (restated on purpose)

Everything — chat UI, IDE, CLI, eval harness — talks to **one
OpenAI-compatible endpoint** (`http://localhost:8080/v1` today). In phase 3
the backend behind that URL becomes vLLM on a GPU server and the URL gains
a hostname; nothing else changes. Do not let any interface grow a
backend-specific dependency.

## Step 1 — llama-swap + llama.cpp

Only one ~18 GB model fits comfortably in RAM at a time, but different roles
want different models. [llama-swap](https://github.com/mostlygeek/llama-swap)
is a small proxy that starts/stops `llama-server` processes on demand based
on the `model` field of each request — exactly the single-user
model-multiplexing this phase needs.

Why not Ollama: llama-swap keeps raw `llama-server` flags (full control over
context size, threads, sampling — the knobs the bake-off tuned), uses the
same GGUF files directly from `models/` without an import step, and the
client-facing contract (OpenAI API, role-named models) is identical to the
phase-3 vLLM setup. Ollama remains a fine fallback if llama-swap proves
flaky.

`configs/llama-swap.yaml` (generated — see Step 2; hand-written example):

```yaml
models:
  "r1-docs-tr":
    cmd: >
      ~/llama.cpp/build/bin/llama-server
      -m ~/models/qwen3-30b-a3b-instruct-q4_k_m.gguf
      --port ${PORT} -c 16384 -t 8 --temp 0.4
  "r3-coder":
    cmd: >
      ~/llama.cpp/build/bin/llama-server
      -m ~/models/qwen3-coder-30b-a3b-instruct-q4_k_m.gguf
      --port ${PORT} -c 32768 -t 8 --temp 0.2
  # r2-review-tr, r4-code-review, r6-docs-general, ... same pattern
healthCheckTimeout: 300   # big GGUFs take a while to load from disk
```

Run as a user service so it survives reboots
(`systemd --user` unit in WSL2, or a scheduled task running `wsl -e`).
Verify:

```bash
curl http://localhost:8080/v1/models
curl http://localhost:8080/v1/chat/completions -d '{"model":"r3-coder","messages":[{"role":"user","content":"hi"}]}'
```

Model aliases are fixed project-wide: `r1-docs-tr`, `r2-review-tr`,
`r3-coder`, `r4-code-review`, `r5-standards` (phase 2), `r6-docs-general`,
`r7-eda` (phase 2/3), `r8-domain-qa` (phase 2). Swap latency note: changing
roles costs a model load (~15–60 s from NVMe). Group work by role; the
winner table mapping several roles to one model means most switches are
free.

## Step 2 — Per-role configs: `configs/roles/*.yaml`

One YAML per role; everything downstream is generated from these.

```yaml
# configs/roles/r4-code-review.yaml
role: r4
name: Code Reviewer
model: r3-coder            # llama-swap alias (may be shared across roles)
system_prompt: |
  You are a senior embedded-software reviewer. Review the provided diff for
  correctness bugs only: memory errors, race conditions, register misuse,
  off-by-one... Output findings as: severity, file:line, problem, fix.
  Do not comment on style.
params: { temperature: 0.2, max_tokens: 2048 }
context_length: 32768
rag: false                 # flips on in phase 2 for grounded roles
```

`configs/render.py` (small script, part of this phase) reads all role files
and emits:

- `configs/llama-swap.yaml` (Step 1) — model aliases + llama-server flags,
- the `models:` block for Continue's `~/.continue/config.yaml`,
- Open WebUI preset JSON for import (or applied via its API),
- nothing for the CLI — `llmctl` reads `configs/roles/` directly.

Editing a system prompt = edit one YAML, rerun `render.py`, restart
llama-swap. Prompts are versioned in git; the eval harness re-runs against
a role alias to regression-check a prompt change.

## Step 3 — Open WebUI (R1, R2, R6)

```bash
docker run -d --name open-webui -p 3000:8080 \
  -e OPENAI_API_BASE_URL=http://host.docker.internal:8080/v1 \
  -e OPENAI_API_KEY=local \
  -v open-webui:/app/backend/data \
  ghcr.io/open-webui/open-webui:main
```

(WSL2: enable Docker Desktop WSL integration or install docker-ce inside
Ubuntu; `host.docker.internal` needs `--add-host host.docker.internal:host-gateway`
on plain docker-ce.)

In Workspace → Models, create one preset per role (r1-docs-tr,
r2-review-tr, r6-docs-general) carrying the rendered system prompt and
pointing at the matching llama-swap alias. R2 usage pattern: paste/upload
the Turkish document, get the findings list (severity, location, suggested
fix) per the spec — the system prompt enforces findings-list-not-rewrite.

Single-user note: auth stays off / single-admin in phases 0–2 per spec;
multi-user arrives in phase 3.

## Step 4 — VS Code + Continue (R3, R4)

Install the Continue extension; point it at the endpoint. The relevant
`~/.continue/config.yaml` blocks are generated by `render.py`:

```yaml
models:
  - name: r3-coder
    provider: openai
    apiBase: http://localhost:8080/v1
    apiKey: local
    model: r3-coder
    roles: [chat, edit, apply]
  - name: r4-code-review
    provider: openai
    apiBase: http://localhost:8080/v1
    apiKey: local
    model: r4-code-review
    roles: [chat]
prompts:
  - name: review
    description: R4 diff review
    prompt: |
      @diff Review this diff per your instructions.
```

Notes for this hardware: use a *small fast* model (Gemma 3 12B class, alias
`r3-autocomplete`) for tab-autocomplete if used at all — a 30B MoE is fine
for chat/edit but autocomplete latency budgets are ~500 ms and may simply
not be viable on CPU; chat-first usage is the expectation. Embedded C/C++,
VHDL/Verilog, device-tree, Yocto, Tcl all arrive as plain text in context —
no extra IDE work needed beyond the role prompts.

## Step 5 — CLI: `llmctl` (R3, R4; later R1/R6 docgen and R5/R8)

Small Python package in `cli/`, installed with `uv tool install -e ./cli`.
Reads `configs/roles/` directly; talks to the same endpoint.

```
llmctl ask  --role r3 "write a Yocto recipe for ..."
llmctl ask  --role r1 --file brief.md          # long-form from a brief
llmctl review --diff HEAD~1                    # R4 on a git range
llmctl review --staged                         # R4 on staged changes
llmctl sweep --role r4 src/**/*.c              # batch whole-repo review
```

`review` chunks large diffs file-by-file (32k context ceiling), emits the
findings list to stdout (human) or `--json` (tooling). Exit code 1 if any
finding ≥ the `--fail-on` severity → that *is* the pre-commit gate:

```bash
# .git/hooks/pre-commit (template shipped in cli/hooks/)
llmctl review --staged --fail-on high || {
  echo "LLM review found high-severity issues (bypass: git commit --no-verify)"; exit 1; }
```

Keep the hook advisory-fast: high-severity-only, and skip when the diff
exceeds ~400 lines (full sweeps are `llmctl sweep`, run deliberately).

## Step 6 — End-to-end acceptance

1. `curl /v1/models` lists all role aliases.
2. Open WebUI: generate a short Turkish formal letter via r1-docs-tr;
   review a pasted Turkish doc via r2-review-tr → findings list.
3. VS Code: ask r3-coder for a register-init function; run `/review` on a
   real diff.
4. `llmctl review --staged` on a deliberately buggy change → finding found,
   nonzero exit; pre-commit hook blocks the commit.
5. Re-run the phase-0 harness against the role aliases (not raw models) —
   scores must match the bake-off; this proves prompts/params didn't
   regress anything and wires the harness to the permanent serving path.
