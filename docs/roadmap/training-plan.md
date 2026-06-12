# Training Plan — LoRA Fine-tuning on Company Data

When and how to fine-tune. Executed in phase 3 (or earlier on a rented GPU
for non-sensitive data only); written now so dataset collection can start
early — data is the long pole, not GPU hours.

## What training is for — and not for

Fine-tuning here buys **style and fluency**: formal Turkish register and
company document tone (R1/R2/R6), and company code idioms (R3/R5). It does
**not** store facts. The spec's architectural rule stands: facts live in
retrieval with citations; a LoRA that "knows" register values is a bug
factory — values go stale silently and uncited. Every factual path keeps
going through the Domain Knowledge Layer.

**Decision gate (per adapter):** fine-tune only when prompting + RAG
measurably falls short on the eval suite for that role, and the shortfall
is stylistic (register, tone, idiom) rather than factual. If phase-2
RAG/templating already clears the quality bar, skip the adapter — zero
adapters is a valid outcome of this plan.

## Adapters

One LoRA per capability gap, on the bake-off-winning base for the role (so
adapters compose with the serving stack — vLLM multi-LoRA needs adapters to
share a resident base).

### Adapter 1: `tr-docs` (R1/R2/R6 — Turkish company style)

- **Data:** 1,000–3,000 instruction pairs mined from the company document
  corpus: (doc-family + brief) → approved document/section. Build with the
  stack itself: an extraction prompt reads each approved document and
  emits the *reverse* instruction ("write the brief this document answers"),
  then pair brief → real document. Include per-family coverage matching
  real usage (design docs, letters, procedures, summaries).
- **Also include** ~10–20% R2-style pairs: (flawed doc → findings list),
  with flaws synthesized by corrupting good documents (register slips,
  structure violations), so the reviewer role benefits too.

### Adapter 2: `code-conventions` (R3/R5 — company code idioms)

- **Data:** pairs from company repos + the phase-2 `standards/` docs:
  (task → conforming code) mined from real commits; (diff → standards
  findings citing rule IDs) synthesized by injecting known violations into
  conforming code. 1,000–2,000 pairs; per-language balance matching the
  spec's language list, weighted toward embedded C/C++.

### Dataset hygiene (both adapters)

- Format: ChatML, stored as JSONL in a private `datasets/` location
  (**not** this repo — it contains company documents).
- Dedup (exact + near-dup), strip anything an engineer marked
  draft/rejected, hold out 10% as a validation split **plus** keep the
  phase-0 eval cases out of training entirely (they are the test set;
  contaminating them voids the regression gate).
- Provenance file per dataset: which documents/repos, extraction date,
  counts per family/language.

## Method

- **QLoRA** (4-bit base, LoRA in bf16): rank r=16–32, alpha=2r, dropout
  0.05, target the attention + MLP projection matrices; 2–3 epochs,
  lr 1e-4–2e-4 cosine, effective batch 32–64 via gradient accumulation.
  Start at r=16 and 2 epochs; raise only if the validation split says
  underfit. Style transfer is an easy target — overfitting (memorized
  documents leaking verbatim) is the failure mode to watch, not underfit.
- **Tooling:** Axolotl (config-file driven, reproducible — commit the YAML
  config, without data, to this repo under `configs/training/`); Unsloth is
  the alternative if single-GPU throughput becomes the bottleneck.
- **Compute reality:** a 30B-class QLoRA over ~3k examples is hours, not
  days, on one 96 GB card; a 70B-class base also fits on one card with
  QLoRA. Today's CPU box is never an option.

## Where to train (in order of preference)

1. **On-prem GPU server (default, and the recommendation):** company
   documents and code never leave the building. Since data collection is
   the long pole anyway, waiting for the phase-3 hardware costs little.
2. **Rented GPU (RunPod/Lambda-class, A100/H100 hour-blocks):** only for
   datasets cleared as non-sensitive, and only if an adapter is urgently
   needed before the server arrives. Explicit caveat: uploading the company
   corpus to a rented box is a data-governance decision, not a technical
   one — get it approved or wait.
3. Never on the CPU box.

(Cloud *inference* remains forbidden regardless; renting applies to
training jobs only, per the project README.)

## Evaluation — the phase-0 harness is the gate

An adapter ships only if, versus its base model on the same serving stack:

1. It **improves** its target role's eval-set scores (e.g. `tr-docs` must
   raise Set-1 rubric means).
2. It does **not regress** any other set — especially Set 3
   (faithfulness/citations): a style adapter that makes the model chattier
   but less faithful is rejected.
3. Spot-check for verbatim training-document leakage in outputs
   (overfitting symptom).

Record results in `docs/bakeoff/` next to the model tables, with the
Axolotl config hash and dataset provenance reference.

## Serving

vLLM **multi-LoRA**: the resident base loads once; adapters attach
per-request. LiteLLM maps role aliases to base+adapter (e.g. `r1-docs-tr` →
chat-base + `tr-docs`), so interfaces notice nothing. Adapter files are
small (hundreds of MB); version them in the model store with the same
manifest discipline as GGUFs.

## Iteration loop

1. Engineers flag bad outputs in daily use (`llmctl flag` or a shared
   folder — keep capture friction near zero).
2. Flagged cases become new eval cases first (they harden the gate), then
   training examples once a corrected reference exists.
3. **Quarterly** retrain cadence at most; retrain sooner only if the eval
   gate shows drift after a base-model upgrade. Each retrain goes through
   the same gate — no adapter ships on vibes.
