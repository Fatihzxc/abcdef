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

## Step 0 — Purchase-time benchmark gate (before buying hardware)

The 5-concurrent × 32k design point and the 160–190 GB VRAM estimate in
[hardware-team-server.md](hardware-team-server.md) are **estimates, not
measurements**. Before committing money, run this acceptance benchmark on a
**loaner / rented / integrator-demo box of the candidate GPU config** and
require every target to pass. If a target fails, change the lineup,
quantization, or the box — not the target.

**Fix the configuration under test first:**

- [ ] Exact model lineup + quantization recorded (chat 70B-class, coder,
      vision, embeddings/reranker — the FP8 weights from the sizing table).
- [ ] Max resident models loaded simultaneously (no swapping) = the full
      R1–R8 stack the table assumes.
- [ ] Max context per role set to the served value (32k for the chat/docs
      roles; record coder/vision limits too).

**Acceptance targets (5-user mixed workload):**

| Metric | Target | Pass? |
|---|---|---|
| Workload | 5 concurrent users, mixed chat + code + 1 vision, 32k context on chat roles | — |
| p95 time-to-first-token | **≤ target you set before the run** (e.g. ≤ 2 s) | [ ] |
| Aggregate generation throughput | **≥ target tok/s** across the 5 streams | [ ] |
| Peak VRAM | **fits the card with headroom** (no OOM, no eviction of a resident role) | [ ] |
| Peak CPU RAM | within the 512 GB (256 GB floor) sizing | [ ] |

**Graceful-degradation policy (define + verify, don't discover in prod):**

- [ ] What happens when a 6th+ concurrent request or a >32k context arrives:
      queue, reject with a clear error, or shrink batch — decide, configure
      in vLLM/LiteLLM, and confirm it degrades that way under overload (no
      OOM-kill, no silent truncation).

Record the run (config + numbers) next to the GPU bake-off in
`docs/bakeoff/`. **No purchase order until this gate is green on the actual
candidate hardware.**

## Step 1 — Backend swap (the payoff of the API invariant)

Install Ubuntu LTS + drivers + Docker per the hardware doc. Bring up:

- **vLLM** — one instance per resident model (chat 70B-class, coder,
  vision), each on its own port, continuous batching, FP8 KV cache,
  `--enable-lora` on the bases that take adapters.
- **LiteLLM proxy** on `:4000` in front of the vLLM instances — this is
  the new "one endpoint": it maps the **same role aliases**
  (`r1-docs-tr`, `r3-coder`, …) to backend model+adapter combinations,
  issues per-user API keys, and logs usage per user. Per-user keys are the
  **minimum** auth (5–10 trusted LAN users — no SSO project), but not the
  whole story: a trusted-LAN deployment still needs the operational
  controls in the [Operations & security](#operations--security) section
  below (key DB + backup, revocation, interface binding, firewall, logs,
  restore drill).

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

## Operations & security

Per-user LiteLLM keys are the floor. Even on a trusted LAN, these are the
operational controls the deployment still needs — set up in this phase:

- [ ] **LiteLLM key store has a backing database** (Postgres, not the
      in-memory/SQLite default) — virtual keys need it to survive a
      restart. Include it in the nightly backup; verify it's actually
      captured.
- [ ] **Key lifecycle owned:** documented procedure to create a key on
      onboarding and **revoke** it on offboarding (engineer leaves → key
      dies same day). One named owner runs it.
- [ ] **Open WebUI admin ownership:** named admin account; sign-up disabled
      or admin-approved (no open self-registration on the LAN); admin
      account itself protected.
- [ ] **Bind endpoints to intended interfaces only:** LiteLLM `:4000`, vLLM
      ports, Open WebUI, and the MCP/knowledge index bind to the LAN/loopback
      address — never `0.0.0.0` exposed to a routable/WAN interface.
- [ ] **Host firewall allowlist:** only the serving ports, only from the
      office subnet; default-deny everything else.
- [ ] **Log retention:** decide how long per-user usage logs (LiteLLM) and
      access logs are kept and where; enough to answer "who ran what" without
      growing unbounded.
- [ ] **Restore drill:** restore the LiteLLM key DB + index + configs from
      backup onto a clean target once, and confirm keys/accounts still work
      — same discipline as the index restore drill in Step 5.

## Out of scope (unchanged from spec)

Department/company-wide rollout beyond the 5–10 team; in-tool plugins for
Word/Vivado/Altium/Eclipse; training from scratch; any cloud inference.
