# Phase 0 — Model Bake-off

Goal: pick the best model per role (R1–R8) for **this** machine (32 GB RAM,
i9-14900HX 24-core, RTX 4070 Laptop 8 GB VRAM, Windows 11), based on the
user's own test cases, and
commit the decision as a model-per-role table. The eval harness built here
stays for the life of the project as the regression gate for every model,
prompt, or hardware change.

Spec: [use-case design](../superpowers/specs/2026-06-12-use-cases-design.md)
(roles, risks, candidate families).

Acceptance criteria (phase done when all true):

- [ ] WSL2 environment with llama.cpp serving GGUF models over the
      OpenAI-compatible API.
- [ ] Eval harness in `evals/` runs all three test sets against any endpoint
      and emits JSON results + a markdown report.
- [ ] All candidate models scored on quality (human rubric) **and**
      tokens/sec.
- [ ] `docs/bakeoff/results.md` committed: model-per-role table + decision
      notes.
- [ ] Turkish risk gate decided: go / heavier-RAG-and-templating / defer
      Turkish generation to GPU phase.

Estimated effort: 4–6 working sessions (most of it authoring test cases and
human scoring, not tooling).

---

## Step 1 — Environment setup (Windows 11 host)

Use **WSL2 + Ubuntu** as the working environment. Rationale: Docker (needed
for Open WebUI in phase 1), pandoc, Python tooling, and llama.cpp all work
first-class on Linux; llama.cpp CPU throughput in WSL2 is on par with native
Windows; and everything written here ports unchanged to the Linux GPU server
in phase 3. Native-Windows fallback notes are at the end of this step.

```powershell
# Windows (admin PowerShell), one time:
wsl --install -d Ubuntu-24.04
wsl --set-default Ubuntu-24.04
```

Inside Ubuntu:

```bash
sudo apt update && sudo apt install -y build-essential cmake git curl pandoc
# Python via uv (fast, no system-python fights)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv python install 3.12
```

WSL2 memory: by default WSL2 caps at 50% of host RAM (~16 GB here), which is
not enough for a ~18 GB MoE model plus context. Raise it, but leave headroom
for Windows + Docker Desktop. Create `C:\Users\<you>\.wslconfig`:

```ini
[wsl2]
memory=24GB        # of 32 GB total — leaves ~8 GB for Windows/Docker
processors=24      # i9-14900HX: 24 physical cores (32 logical)
```

then `wsl --shutdown` and reopen. A ~18 GB 30B-A3B model is marginal at this
RAM with large context — watch peak RSS (`free -h` during a run) and drop
context length or model size if it starts to swap.

### llama.cpp

Build from source so the binary uses every CPU feature available (AVX2 is
detected automatically). The RTX 4070 Laptop (8 GB) can partly offload small
models, so also build the CUDA variant (needs the CUDA toolkit in WSL):

```bash
git clone https://github.com/ggml-org/llama.cpp ~/llama.cpp
cd ~/llama.cpp
git checkout <commit>     # pin it; record the hash in artifacts.lock
# CPU build:
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j"$(nproc)"
# CUDA build (optional — partial GPU offload on the 4070):
cmake -B build-cuda -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON
cmake --build build-cuda --config Release -j"$(nproc)"
# binaries: build/bin/llama-server, build/bin/llama-bench, build/bin/llama-cli
```

With the CUDA build, offload as many layers as fit in 8 GB via `-ngl N`
(small models only — a 30B-A3B will not fully fit). Pin the llama.cpp commit
hash in `artifacts.lock` (and the environment record in
`docs/bakeoff/results.md`) — throughput changes between releases.

### Model storage convention

All models live in one place, with a manifest, so "fully offline" is real
and restorable. The manifest is the canonical artifact record for the whole
project — phase 3 (vLLM safetensors) and the training plan (LoRA adapters)
extend the same schema, so every row is unambiguous about what it is and how
it is served:

```
models/
  manifest.tsv          # TAB-separated, one row per artifact:
  #   filename  sha256  source_url  date  artifact_type  serving_backend
  #   base_model  quantization  compatible_roles
  #   artifact_type   = gguf | hf-safetensors | lora-adapter
  #   serving_backend = llama.cpp | vllm
  qwen3-30b-a3b-instruct-q4_k_m.gguf
  ...
```

Put `models/` on the largest disk (budget ~150–200 GB for the full candidate
set). Download once with `huggingface-cli download` (or browser), record
sha256 (`sha256sum`), and back the directory up to external storage. After
this step, no network access is required to run anything.

Native-Windows fallback (only if WSL2 is blocked by IT policy): llama.cpp
ships Windows release binaries (AVX2 build); the eval harness is plain
Python and runs unchanged; Open WebUI in phase 1 would need Docker Desktop
or `pip install open-webui`. Everything else in this roadmap still applies.

### Reproducible / offline setup lock

"Offline after setup" means *restorable*, not just downloaded. During the
online setup window, record every moving piece once in a tracked
`artifacts.lock` at the repo root, and archive the binaries/images it names
alongside `models/`:

- Ubuntu image version (`Ubuntu-24.04`) and the `apt` package list + date
- `uv` installer version/checksum and the pinned Python version
- llama.cpp commit hash (the `git checkout` above)
- container image digests (Open WebUI etc.) — pin by `@sha256:…`, never `:main`
- model file sha256s (mirrors `models/manifest.tsv`)
- eval-harness commit

Floating installer scripts (`astral.sh/uv/install.sh`) and `:latest`/`:main`
tags change behaviour between runs and silently break bake-off
repeatability — pin them here and re-verify checksums on restore.

## Step 2 — Candidate models

Candidates per spec plus releases since (verified June 2026). All GGUF
**Q4_K_M** unless noted. On 32 GB RAM the smaller models (8–14B, ~5–9 GB) run
comfortably; the ~16–18 GB 30B-class MoE models are marginal once WSL +
Windows overhead and large context are added, so run one large model at a
time and stage the bake-off — small models first, 30B-class with reduced
context.

| Model | Type | ~GGUF size | Roles targeted | Why |
|---|---|---|---|---|
| Qwen3-30B-A3B-Instruct | MoE, 3B active | ~18 GB | R1, R2, R6, R8 | The speed hope: 30B quality at ~3B-active cost; strong multilingual |
| Qwen3-Coder-30B-A3B-Instruct | MoE, 3B active | ~18 GB | R3, R4, R5 | Coder variant of the above; ~10 tok/s reported on CPU-only boxes |
| Gemma 4 26B-A4B | MoE, ~3.8B active | ~16 GB | R1, R2, R6, R8 | Newest small-active MoE; strong general quality, Apache-2.0 |
| Gemma 3 27B | dense | ~16 GB | R1, R2, R6 | Quality ceiling check; expect slow (~2–4 tok/s) |
| Gemma 3 12B | dense | ~7 GB | R6, fallback | Fast dense baseline |
| Qwen3-14B | dense | ~9 GB | R6, R8 | Dense mid-size baseline |
| Aya-Expanse-8B | dense | ~5 GB | R1, R2 | Turkish-specialist check; 32B variant only if 8B shows promise |
| Qwen2.5-Coder-14B | dense | ~9 GB | R3, R4 | Dense coder baseline vs the MoE coder |

Before downloading, spend 30 minutes checking for newer releases in the
same families (Qwen, Gemma, Aya, coder-MoE) — this table is a snapshot, the
families are the decision. Drop a candidate rather than growing the list
past ~8; each added model costs a full human-scoring pass.

The table is a snapshot; the *living* candidate list is
`docs/bakeoff/candidates.md` — one row per model with upstream model id,
quant source, license, sha256, download date, context limit, expected
RAM/VRAM, intended roles, and (if dropped) the exclusion reason. The roadmap
keeps the selection *process*; the manifest carries the volatile model facts.

Expected throughput on the i9-14900HX (24 cores; set expectations, then
measure with `llama-bench`): MoE ~3B active ≈ 15–30 tok/s; dense 12–14B ≈
6–12 tok/s; dense 27B+ ≈ 3–6 tok/s. Partial GPU offload (`-ngl`) on the 4070
lifts the small-model numbers further. The spec's long-document risk is real
for dense models — this is why the MoE candidates matter.

## Step 3 — Eval harness (`evals/`)

Small bespoke Python package (custom citation scoring makes promptfoo a
poor fit; revisit only if the bespoke runner exceeds ~300 lines).

```
evals/
  cases/
    tr-docs/*.yaml        # test set 1
    code/*.yaml           # test set 2
    grounded-qa/*.yaml    # test set 3
    private/              # gitignored: sensitive company cases (see Step 4)
  rubrics/*.md            # scoring rubrics, one per test set
  runner.py               # run cases against an endpoint
  score.py                # interactive human scoring -> fills scores into results
  report.py               # results JSON -> markdown table
  results/                # gitignored raw runs; committed summaries go to docs/bakeoff/
```

Case format (one YAML per case):

```yaml
id: tr-docs/formal-letter-01
role: r1
prompt: |
  ... (the actual task, in Turkish for TR cases)
context: |          # only for grounded-qa cases: the source excerpt
expected: |         # reference answer / key points (grounded-qa) or n/a
rubric: tr-docs     # which rubric scores this
max_tokens: 1024
```

`runner.py` behavior: for each case × model, POST to the OpenAI-compatible
`/v1/chat/completions` endpoint, record the completion, wall time,
prompt/completion token counts, and computed tokens/sec, into
`results/<model>/<case>.json`. Model is selected by name (llama-swap in
phase 1; for phase 0, start `llama-server -m <gguf> --port 8080` per model
manually — one model at a time is fine).

`score.py`: iterates unscored results, shows prompt + output + rubric,
records a 1–5 score and a note. ~50 cases × 8 models is ~400 human
judgements — too much to do well in one sitting, and corner-cutting here
corrupts the gate every later phase leans on. Score in passes instead:

- **Smoke pass:** 10–12 cases spanning all three sets, across *all*
  candidates — cheap, kills the obviously-weak models fast.
- **Full pass:** the full ~50 cases, but only the top 2–3 candidates *per
  role* that survived the smoke pass.
- **Regression pass:** a fixed ~15-case subset, re-run on every later prompt
  or model change — this is the permanent gate, not a one-off.

Run with deterministic settings (temperature 0, fixed seed) so reruns are
comparable.

## Step 4 — The three test sets

The user authors the cases (they encode his actual work); the harness ships
with one template per set. Target ~50 cases total.

**Eval data classification (decide before authoring).** Cases encode real
work — datasheet excerpts, board netlists/pin-maps, subsea figures — so
classify before committing anything:

- Public or synthetic cases → may be committed under `evals/cases/`.
- Sensitive company cases → live in `evals/cases/private/` (gitignored), on
  local disk + backup only, never pushed.
- Committed bake-off summaries (`docs/bakeoff/`) carry scores and model
  names — never the sensitive prompt text or raw model output.
- If a sensitive case must be tracked for regression, commit a *redacted*
  fixture, not the original.

`.gitignore` enforces this (`evals/cases/private/`, `evals/results/`).

**Set 1 — Turkish documents (~16 cases).** 3–5 prompts per doc family from
the spec: design-doc section, test report section, formal company letter,
proposal/offer paragraph, procedure/work instruction, executive summary.
Rubric scores (1–5 each): formal register correctness, grammar, structural
fit to the requested doc type, terminology. *This set carries the project's
top risk — if every candidate fails here, the risk gate in Step 7 fires.*

**Set 2 — Code (~20 cases).** One generation task and (where cheap) one
explain/fix task per language in the spec: embedded C register-level driver
(bare-metal, e.g. UART init from a register map given in the prompt), C++
RTOS task, Python test-automation script, VHDL entity + architecture,
Verilog module, C# or TypeScript application snippet, Linux device-tree
fragment, Yocto recipe, Vivado Tcl constraint/build script. Rubric:
correctness, idiomatic style, would-compile plausibility (actually compile
the C/Python where trivial).

**Set 3 — Grounded Q&A (~14 cases).** Each case = question + source excerpt
in `context` + known answer. Sources: a vendor datasheet register
description (reuse datasheet-kb content), a board netlist/pin-map excerpt,
and **at least 3 subsea-engineering cases with equations** (spec risk:
verifies math survives extraction and the model can use it). Include 2–3
trap cases where the answer is *not* in the excerpt — the correct response
is "not found in the provided context". Rubric: faithfulness to context
(answer uses only provided facts), citation present, traps refused.
**Faithfulness outranks eloquence for R8 and all grounded roles.**

## Step 5 — Run and score

1. For each candidate: start `llama-server`, run
   `uv run evals/runner.py --endpoint http://localhost:8080/v1 --model <name> --all`,
   stop the server.
2. Also run `llama-bench` per model and record pp/tg numbers alongside (a
   second, prompt-independent throughput datapoint).
3. Human-score everything with `score.py`. No LLM-as-judge in phase 0:
   there is no trusted local judge yet, and the judge would be one of the
   contestants. (Revisit in phase 3 when a large GPU model can judge the
   small ones.)
4. `report.py` → per-role leaderboard: mean rubric score per test set per
   model, plus tokens/sec.

## Step 6 — Deliverable: `docs/bakeoff/results.md`

Committed to the repo:

- The model-per-role table (this becomes phase 1's serving config):

  | Role | Model | Quant | Quality (per-set mean) | tok/s | Notes |
  |---|---|---|---|---|---|

- Decision notes per role (why the winner won, runner-up, anything
  surprising).
- Environment record: llama.cpp commit, CPU, RAM, WSL2 config, sampling
  settings.

One model may win several roles — fewer resident models is a feature on
this hardware, not a compromise to apologize for.

## Step 7 — Turkish risk gate (explicit decision point)

If **no** candidate reaches an acceptable bar on Set 1 (suggested bar:
mean ≥ 3.5/5 with no register-correctness score below 3):

1. First fallback: keep the best model but move quality into scaffolding —
   heavier RAG over company documents for style/terminology plus stricter
   templates (phase 2 machinery, pulled earlier for R1/R2).
2. Second fallback: defer Turkish *generation* (R1) to the GPU phase;
   Turkish *review* (R2) may still clear the bar since critique is easier
   than generation — test that explicitly before deferring both.

Record the decision and its rationale in `docs/bakeoff/results.md`. R3–R5
proceed to phase 1 regardless of this gate. R6 is split for this decision:
R6-EN (English docs) and summary tasks proceed; R6-TR *generation* is gated
with the same Turkish fallback as R1 above — it does not get a pass just
because R6 is labelled "general purpose".
