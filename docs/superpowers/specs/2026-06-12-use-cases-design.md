# Offline Local LLM Stack — Use-Case Design

Date: 2026-06-12
Status: approved (brainstorm with user, 2026-06-12)
Feeds: remote ultraplan session (implementation planning happens there)

## Goal

Run custom LLM assistants fully offline on a local machine, specialized for
one engineer's company work: Turkish document writing/review, coding across
the embedded spectrum, code review, and code-standard enforcement.

## User & deployment

- Single user (the owner), on his own machine. No multi-user serving, no
  auth, no access control in any phase.
- Fully offline after initial setup (model downloads happen once).

## Hardware

- Today: 64 GB RAM, 8-core CPU, no usable GPU → CPU-only inference via
  llama.cpp/GGUF. Favor small dense models (7–14B) or MoE models with few
  active parameters (e.g. ~30B total / ~3B active), quantized ~Q4.
- Future: powerful GPU machines will arrive. Architecture must port
  cleanly: model-agnostic OpenAI-compatible serving API, RAG pipeline,
  eval suite, and per-role configs survive the hardware upgrade; only the
  model/backend swaps.

## Roles

### R1 — Turkish document creator
- Creates: technical/engineering docs (design docs, test reports,
  requirement specs, manuals), official company correspondence (formal
  letters, proposals, offers), process/quality documents (procedures, work
  instructions, ISO-style), presentation content and executive summaries.
- Template-driven: generates into company document structures, not free
  prose. RAG over existing company documents supplies house style,
  terminology, and formal Turkish register.
- Output path includes `.docx` generation from templates (pandoc/python-docx
  class tooling) — no in-Word plugin required.

### R2 — Turkish document reviewer
- Reviews Turkish documents for: grammar and formal register, clarity,
  structural conformance to the relevant template, and terminology
  consistency with the company corpus.
- Output: a findings list (severity, location, suggested fix), not a
  rewritten document, unless a rewrite is requested.

### R3 — Coder
- Languages/stacks: embedded C/C++ (bare-metal/RTOS, drivers, registers),
  Python (tooling/test automation), VHDL/Verilog, application stack
  (C#/Java/JS/TS class), Linux work (kernel config, device trees), Yocto
  (recipes, layers), Vivado Tcl.
- Used via IDE integration (inline + chat) and CLI.

### R4 — Code reviewer
- Diff-based correctness/bug review in the IDE; batch mode via CLI
  (whole-repo sweep, git pre-commit hook).
- Same language coverage as R3.

### R5 — Code-standard reviewer
- Enforces the company coding standard per language.
- Prerequisite deliverable: the standard is today partial/informal. Phase 2
  includes codifying conventions into written per-language standards docs;
  the reviewer RAGs over those docs. The reviewer can only enforce what is
  written down.

### R6 — General document creator
- English and Turkish general-purpose documents and summaries; lighter
  sibling of R1 without company-template constraints.

### R7 — Hardware/EDA assistant (later phase)
- Works on files exported from EDA tools, not inside them: netlists, BOMs,
  Altium exports, Vivado Tcl/constraint files, HDL.
- Schematic-image review requires vision-capable models → explicitly
  deferred to the GPU phase.
- No in-tool plugins for Vivado/Altium/Eclipse are assumed to exist;
  integration is file-level only.

## Interfaces

| Interface | Roles | Phase notes |
|---|---|---|
| Browser chat UI (Open WebUI class) | R1, R2, R6 | Phase 1 |
| IDE integration (Continue class, VS Code) | R3, R4 (R5 from phase 2) | Phase 1 |
| CLI / scriptable (batch review, pre-commit, doc pipelines) | R3, R4 (R5 from phase 2) | Phase 1 |
| Office: template-based .docx generation | R1, R6 | Phase 2 |
| EDA tools: file-level exchange only | R7 | GPU phase |

## Phasing

- Phase 0 — model bake-off (first deliverable, user priority):
  - Build a small eval harness with the user's own test cases: Turkish
    document samples per doc family, representative code snippets per
    language.
  - Candidates: Qwen3 family incl. MoE (30B-A3B class), Gemma 3,
    Aya-Expanse (Turkish), Qwen2.5-Coder class (code).
  - Score per role on quality AND tokens/sec on this CPU. Output: a
    model-per-role table committed to the repo.
- Phase 1 — serving + top roles: llama.cpp/Ollama behind an
  OpenAI-compatible endpoint; chat UI + IDE + CLI wired to bake-off
  winners; per-role system-prompt configs.
- Phase 2 — knowledge grounding: RAG over company documents; standards
  codification (per-language docs) + R5 standard reviewer; .docx template
  pipeline.
- Phase 3 — GPU arrival: LoRA fine-tuning on company corpus (Turkish
  style, code conventions), larger/dense models, vision models for R7
  schematic review.

## Out of scope

- Multi-user serving, auth, user management (single user only).
- In-tool plugins for Word, Vivado, Altium, Eclipse.
- Training models from scratch; any cloud inference.

## Risks

- Turkish output quality on small CPU-friendly models is the top risk;
  this is why the bake-off is phase 0 and includes a Turkish-specific
  test set. Mitigation if all candidates fail: heavier RAG/templating, or
  defer Turkish generation roles to the GPU phase.
- 8-core CPU throughput may make long-document generation slow even with
  MoE models; the bake-off measures tokens/sec explicitly so expectations
  are set by data.
- Informal standards (R5) depend on the user writing/approving the
  codified docs; schedule slack for that human step.
