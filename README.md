# local_llm

Goal: build and run custom LLMs fully offline on my local computer, tailored to
various company needs. Single user (me). Full use-case spec:
[docs/superpowers/specs/2026-06-12-use-cases-design.md](docs/superpowers/specs/2026-06-12-use-cases-design.md)

Roles:

- R1 Turkish document creator — technical, official-correspondence,
  process/quality, presentation docs; template-driven + RAG for house style
- R2 Turkish document reviewer — register, structure-vs-template, terminology
- R3 Coder — embedded C/C++, Python, VHDL/Verilog, app stack, Linux/Yocto,
  Vivado Tcl
- R4 Code reviewer — diff-based in IDE, batch via CLI/pre-commit
- R5 Code-standard reviewer — needs standards codified first (today informal)
- R6 General document creator — EN/TR general docs and summaries
- R7 Hardware/EDA assistant — file-level only (netlists, BOMs, Tcl); vision
  for schematics deferred to GPU phase

Interfaces: browser chat, IDE (VS Code/Continue class), CLI/scriptable,
template-based .docx output. No in-tool plugins for Word/Vivado/Altium.

Phasing: 0) model bake-off (Turkish + code eval harness, model-per-role
table) → 1) serving + chat/IDE/CLI → 2) RAG + standards codification +
.docx pipeline → 3) GPU phase: LoRA fine-tuning, larger models, vision.

Status: greenfield — use-case spec approved; implementation planning next.

Constraints / context:

- Must work offline after initial setup (no cloud inference).
- Windows 11 host.
- Hardware: 64 GB RAM, 8-core CPU, no usable GPU — plan for CPU-only
  inference (llama.cpp/GGUF, quantized models). Large dense models will be
  too slow; favor small dense (7-14B) or MoE models with few active
  parameters. Local GPU fine-tuning is not feasible; if fine-tuning is
  needed, assume a one-off rented GPU or favor RAG + prompting instead.
- Powerful machines (proper GPUs) will be available in the future: design
  the architecture to scale up, not around today's hardware. Choices that
  port cleanly (model-agnostic serving API, RAG pipeline, eval suite,
  per-role configs) are preferred over CPU-only dead ends. Phase the plan:
  phase 1 runs on today's box; later phases (bigger models, LoRA
  fine-tuning on company data) activate when GPU hardware arrives.
- "Custom" likely means a mix of: selecting/quantizing open-weight base models,
  fine-tuning (LoRA/QLoRA) on personal data, and RAG over local documents —
  the plan should weigh these options per use case rather than assume
  training from scratch.
