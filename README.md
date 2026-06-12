# local_llm

Goal: build and run custom LLMs fully offline on my local computer, tailored to
various company needs:

- Turkish document creator (write company documents in Turkish)
- Turkish document reviewer
- Coder (coding assistant)
- Code reviewer
- Code-standard reviewer (check code against company coding standards)
- General document creator
- ...and similar company-internal assistant roles

Status: greenfield — planning phase. No code yet.

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
