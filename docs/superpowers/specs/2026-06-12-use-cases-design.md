# Offline Local LLM Stack — Use-Case Design

Date: 2026-06-12
Status: approved (brainstorm with user, 2026-06-12)
Feeds: remote ultraplan session (implementation planning happens there)

## Goal

Run custom LLM assistants fully offline on a local machine, specialized for
one engineer's company work: Turkish document writing/review, coding across
the embedded spectrum, code review, and code-standard enforcement.

## User & deployment

- Today: single user (the owner), on his own machine. No multi-user
  serving, no auth, no access control on current hardware.
- Future (with the powerful machines): a 5-10 person team uses the stack
  over the company LAN. Multi-user serving, concurrent sessions, and a
  shared knowledge index become requirements then; the implementation plan
  must include a recommended hardware configuration sized for 5-10
  concurrent users (GPU server class, VRAM sizing, RAM, storage).
- Fully offline after initial setup (model downloads happen once).

## Hardware

- Today (live dev machine): 32 GB RAM, Intel Core i9-14900HX (24 cores /
  32 threads), NVIDIA RTX 4070 Laptop GPU (8 GB VRAM), Windows 11 →
  llama.cpp/GGUF inference, optionally offloading small models partly to the
  8 GB GPU. RAM is the binding constraint: favor small dense models (7–14B)
  or MoE models with few active parameters (e.g. ~30B total / ~3B active),
  quantized ~Q4, with one large model resident at a time.
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
- For the phase-0 Turkish risk gate, treat R6 as subcapabilities: R6-EN
  (English docs), R6-TR (Turkish generation), and summaries. R6-TR
  generation shares R1's Turkish-quality risk and fallback; R6-EN and
  summarisation do not.

### R7 — Hardware/EDA assistant (later phase)
- Works on files exported from EDA tools, not inside them: netlists, BOMs,
  Altium exports, Vivado Tcl/constraint files, HDL.
- Schematic-image review requires vision-capable models → explicitly
  deferred to the GPU phase.
- No in-tool plugins for Vivado/Altium/Eclipse are assumed to exist;
  integration is file-level only.

### R8 — Domain expert Q&A
- Answers questions about the user's hardware, registers, board
  connectivity (schematics/netlists), and subsea dynamics, grounded in the
  Domain Knowledge Layer (below).
- Every factual answer cites its source (document, page/section), matching
  the citation discipline of the existing datasheet-kb. "Not found in the
  corpus" is a valid answer; uncited facts are not.

## Domain Knowledge Layer

Extension of the user's existing datasheet-kb MCP server (which already
indexes vendor datasheets and serves register lookups) — not a new system.

- Corpora:
  - Vendor PDFs: chip datasheets, reference manuals, IP core docs
    (already indexed today).
  - Company design documents: design docs, test reports, architecture
    documents for the user's boards and systems.
  - Schematics/CAD as extracted text: netlists, BOMs, pin/connector maps
    exported from Altium. Schematic-image understanding (vision) is
    deferred to the GPU phase.
  - Subsea engineering literature: textbooks, papers, DNV/API-class
    standards, company analyses. Math-heavy PDFs need equation-aware
    chunking.
- Exposed via MCP to all interfaces, serving two purposes:
  1. Standalone R8 expert Q&A.
  2. Automatic grounding for all other roles (e.g. code reviewer checks a
     driver against the actual register map; document creator knows the
     board it is describing).
- Architectural rule: facts live in retrieval, never in weights. RAG
  provides citations, instant updates when a document revs, and no
  hallucinated register values. Phase-3 LoRA fine-tuning may add domain
  fluency (terminology, style) but factual questions always go through
  retrieval.

## Interfaces

| Interface | Roles | Phase notes |
|---|---|---|
| Browser chat UI (Open WebUI class) | R1, R2, R6 | Phase 1 |
| IDE integration (Continue class, VS Code) | R3, R4 (R5 from phase 2) | Phase 1 |
| CLI / scriptable (batch review, pre-commit, doc pipelines) | R3, R4 (R5 from phase 2) | Phase 1 |
| Office: template-based .docx generation | R1, R6 | Phase 2 |
| EDA tools: file-level exchange only | R7 | GPU phase |
| Domain Knowledge Layer via MCP (all interfaces) | R8 + grounding for all | Phase 2 |

## Phasing

- Phase 0 — model bake-off (first deliverable, user priority):
  - Build a small eval harness with the user's own test cases: Turkish
    document samples per doc family, representative code snippets per
    language.
  - Third test set: retrieval-grounded Q&A — hardware/register/subsea
    questions with known answers plus the relevant source excerpt, scoring
    how faithfully each model uses provided context and cites it (context
    faithfulness matters more than eloquence for R8 and grounded roles).
  - Candidates: Qwen3 family incl. MoE (30B-A3B class), Gemma 3,
    Aya-Expanse (Turkish), Qwen2.5-Coder class (code).
  - Score per role on quality AND tokens/sec on this CPU. Output: a
    model-per-role table committed to the repo.
- Phase 1 — serving + top roles: llama.cpp/Ollama behind an
  OpenAI-compatible endpoint; chat UI + IDE + CLI wired to bake-off
  winners; per-role system-prompt configs.
- Phase 2 — knowledge grounding: extend datasheet-kb into the Domain
  Knowledge Layer (company docs, netlist/BOM extraction from Altium
  exports, subsea literature) and wire it into all roles + R8; standards
  codification (per-language docs) + R5 standard reviewer; .docx template
  pipeline.
- Phase 3 — GPU arrival: LoRA fine-tuning on company corpus (Turkish
  style, code conventions), larger/dense models, vision models for R7
  schematic review; team rollout — multi-user serving (vLLM class),
  shared knowledge index, basic auth for 5-10 engineers on the LAN.

## Out of scope

- Multi-user serving, auth, user management on TODAY's hardware (phases
  0-2 are single-user; team serving arrives with the GPU machines in
  phase 3).
- Department/company-wide rollout beyond the 5-10 person team.
- In-tool plugins for Word, Vivado, Altium, Eclipse.
- Training models from scratch; any cloud inference.

## Risks

- Turkish output quality on small CPU-friendly models is the top risk;
  this is why the bake-off is phase 0 and includes a Turkish-specific
  test set. Mitigation if all candidates fail: heavier RAG/templating, or
  defer Turkish generation roles to the GPU phase.
- RAM (32 GB) is the binding constraint, not CPU: a 30B-A3B GGUF (~18 GB)
  plus WSL/Windows overhead and large context is marginal, so long-document
  generation may need reduced context or a smaller model. The 24-core
  i9-14900HX (plus optional 8 GB GPU offload) keeps throughput workable; the
  bake-off measures tokens/sec and peak RAM explicitly so expectations are
  set by data.
- Informal standards (R5) depend on the user writing/approving the
  codified docs; schedule slack for that human step.
- Schematic grounding quality depends on source availability: Altium
  sources allow clean netlist/BOM export; PDF-only schematics degrade to
  the GPU/vision phase.
- Subsea literature is math-heavy; naive PDF chunking mangles equations.
  Equation-aware extraction is required, and the bake-off Q&A set should
  include subsea questions to verify it works end to end.
