# Phase 3 — GPU Arrival + Team Rollout

Goal: swap the serving backend onto the GPU server
([hardware spec](hardware-team-server.md)), re-run the bake-off with larger
models, add vision for R7, fine-tune per the
[training plan](training-plan.md), and roll the stack out to 5–10 engineers
on the LAN with basic auth.

Prerequisites: phases 1–2 in daily single-user use; GPU server installed.

Acceptance criteria:

- [ ] vLLM serves the new model lineup behind the same OpenAI-compatible
      contract; all role aliases preserved.
- [ ] LiteLLM proxy issues per-user API keys; usage is logged per user.
- [ ] 5–10 engineers using chat + IDE + CLI against the LAN endpoint;
      shared knowledge index serves everyone.
- [ ] R7 schematic-image review working with a vision model.
- [ ] GPU bake-off rerun committed; team model-per-role table locked.

Estimated effort: 2–3 sessions for the backend swap; rollout and the GPU
bake-off spread over a few weeks alongside team onboarding.

---

## Step 1 — Backend swap (the payoff of the API invariant)

Install Ubuntu LTS + drivers + Docker per the hardware doc. Bring up:

- **vLLM** — one instance per resident model (chat 70B-class, coder,
  vision), each on its own port, continuous batching, FP8 KV cache,
  `--enable-lora` on the bases that take adapters.
- **LiteLLM proxy** on `:4000` in front of the vLLM instances — this is
  the new "one endpoint": it maps the **same role aliases**
  (`r1-docs-tr`, `r3-coder`, …) to backend model+adapter combinations,
  issues per-user API keys, and logs usage per user. That key list is the
  entire auth story the spec asks for (5–10 trusted LAN users — no SSO
  project).

Client change = one URL + one key per user: Open WebUI's
`OPENAI_API_BASE_URL`, each engineer's Continue `apiBase`, `llmctl`'s
endpoint config. `configs/roles/*.yaml` and `render.py` carry over
unchanged — only the rendered endpoint/keys differ. **Nothing in phases
0–2 should need rework here; if it does, that's a phase-1 architecture bug
to fix, not work to accept.**

Key difference from phase 1: no llama-swap, no model swapping — everything
is resident and concurrent. Role switches become instant.

## Step 2 — GPU bake-off rerun (before locking the team lineup)

The CPU bake-off chose models under a constraint that no longer exists.
Re-run the phase-0 harness (same cases, same rubrics — that's why it was
kept) against the then-current larger candidates: 70B-class dense chat
models, big-MoE instruct models, 32B+ coders, with the CPU winners as
baselines. Two additions vs phase 0:

- **LLM-as-judge is now allowed** for first-pass scoring (the big chat
  model judging candidates), with human spot-checks — there is finally a
  judge that isn't a contestant.
- Throughput is measured **under concurrency** (vLLM batch of 5), not
  single-stream.

Commit results next to the originals in `docs/bakeoff/`; update the
model-per-role table. The Turkish risk gate gets re-evaluated here — if
R1 generation was deferred in phase 0, this is where it comes back.

## Step 3 — Vision for R7 (schematic review)

What phase 2 deliberately deferred: schematic *images* (PDF-only schematics
with no Altium source). Add a vision-capable model (Qwen-VL / Gemma-vision
class, per what the GPU bake-off says) as alias `r7-eda`:

- Inputs: schematic page images (PDF → PNG render), plus retrieved
  netlist/BOM context from the knowledge layer when the board is indexed —
  cross-checking the picture against the extracted netlist is the high-value
  trick.
- Usage: Open WebUI image upload, and `llmctl ask --role r7 --image page3.png`.
- Add a small vision eval set (schematic questions with known answers) to
  `evals/cases/` before trusting it — same discipline as everything else.

R7's file-level work (netlists, BOMs, Vivado Tcl, constraints) has been
live since phase 2 via the knowledge layer; this step only adds eyes.

## Step 4 — Fine-tuning

Execute [training-plan.md](training-plan.md) on this hardware (data never
leaves the building). Serve adapters via vLLM multi-LoRA on the shared
bases; map them into role aliases through LiteLLM. Gate every adapter on
the eval harness before it replaces a base-model role.

## Step 5 — Team rollout

1. **Shared knowledge index:** move datasheet-kb + corpus + vector index to
   the server (it was designed portable in phase 2); MCP served on the LAN;
   nightly index + config backup to the RAID pair, restore drill once.
2. **Accounts:** Open WebUI user accounts (it has them built in) + one
   LiteLLM API key per engineer for IDE/CLI.
3. **Onboarding doc** (`docs/team/onboarding.md`, written in this phase):
   endpoint + key setup, role catalog (what R1–R8 are for, with one example
   each), Continue + llmctl install steps.
4. **Usage guidelines** (one page): grounded answers must cite or say "not
   found"; LLM review assists, humans still approve; what data may be
   pasted (everything stays on-prem — that's the point of the stack).
5. **Operations:** model-update procedure = download → eval harness →
   update LiteLLM mapping → announce. One named owner (the user) for
   server, index, and model lineup. Watch usage logs for the first month to
   see which roles the team actually uses; prune or improve accordingly.

## Out of scope (unchanged from spec)

Department/company-wide rollout beyond the 5–10 team; in-tool plugins for
Word/Vivado/Altium/Eclipse; training from scratch; any cloud inference.
