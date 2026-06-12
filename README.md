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
- "Custom" likely means a mix of: selecting/quantizing open-weight base models,
  fine-tuning (LoRA/QLoRA) on personal data, and RAG over local documents —
  the plan should weigh these options per use case rather than assume
  training from scratch.
