# Team Server — Hardware Recommendation (5–10 engineers)

Sizing for phase 3: one on-prem GPU server on the company LAN serving 5–10
engineers with multi-user inference (vLLM), the shared knowledge index, and
occasional LoRA training. The *sizing math* below is the durable part of
this document. Volatile SKU/price/power/availability claims live in
[hardware-sku-checklist.md](hardware-sku-checklist.md) and **must be
re-verified from the vendor / a system integrator at purchase time** — that
market moves fast.

## Sizing model (do the arithmetic, then pick the box)

**Concurrency.** 5–10 engineers ≈ **3–5 concurrent generations** at peak
(people read more than they generate; vLLM continuous batching absorbs
bursts). Design point: 5 concurrent × 32k-token context.

**What must be resident in VRAM simultaneously:**

| Component | Model class | Weights (quantized) |
|---|---|---|
| Chat/docs/Q&A model (R1/R2/R6/R8) | ~70B dense or large MoE, FP8 | ~70 GB |
| Coder model (R3/R4/R5) | ~30B class, FP8 | ~30 GB |
| Vision model (R7, schematic review) | ~10–30B VLM | ~15 GB |
| Embeddings + reranker (knowledge layer) | bge-m3 class | ~3 GB |
| LoRA adapters (training plan) | per-role, on shared base | ~0.5 GB total |

**KV cache.** For a 70B-class dense model (80 layers, GQA with 8 KV heads,
head dim 128): 2 × 80 × 8 × 128 = 160 K values/token ≈ **320 KB/token at
FP16, 160 KB at FP8**. A 32k-context session ≈ 10 GB (FP16) / 5 GB (FP8);
5 concurrent sessions ≈ **25–50 GB**. The coder adds its own, smaller, KV
pool.

**Total:** ~120 GB weights + ~40 GB KV + headroom ≈ **160–190 GB VRAM** to
run the full role stack resident with no model swapping. That number is
what drives the recommendation; if the model lineup changes, redo this
table, not the conclusion.

## Recommended configuration (primary)

| Component | Spec | Rationale |
|---|---|---|
| GPU | **2× 96 GB-class workstation card (192 GB total)** — see [SKU checklist](hardware-sku-checklist.md) | 192 GB clears the 160–190 GB sizing above with headroom; ECC + high bandwidth + FP8/FP4 = whole stack resident + tensor-parallel 70B. Exact SKU/price/power: re-verify in the checklist |
| CPU | AMD EPYC 9004/9005 (32-core) or Threadripper PRO 7975WX | PCIe 5.0 lanes for 2 GPUs at x16 + NVMe; ingestion/parsing work is CPU-side |
| RAM | **512 GB DDR5 ECC** (256 GB floor) | Model load staging, page cache for the index, headroom for ingestion jobs |
| Storage | 2× 4 TB NVMe Gen4/5 (models + vector index) **+** 2× 8 TB SATA/NVMe in RAID1 (corpus + backups) | Models alone run 200–500 GB; corpus and index grow; RAID1 where loss hurts |
| Network | **10 GbE** to the team switch | Token streams are tiny but document uploads/index syncs aren't |
| PSU / chassis | ≥ 2000 W (each GPU ~600 W), 4U or full tower, server airflow | See power/placement notes |
| OS / stack | Ubuntu LTS, NVIDIA driver + CUDA, Docker, **vLLM**, LiteLLM, Open WebUI | Phase-3 software plan |

Ballpark system cost depends on GPU street price and platform choice;
re-quote from the [SKU checklist](hardware-sku-checklist.md) at purchase
time rather than budgeting from a stale figure.

This box also covers the training plan: QLoRA fine-tuning of a 70B-class
base fits easily in 96 GB, so company data never leaves the building.

## Alternative tiers

**Budget — 4× consumer 32 GB card = 128 GB** (SKU/price in the
[checklist](hardware-sku-checklist.md)).
Works, but: 70B FP8 + KV across 4 consumer cards means 4-way tensor
parallel over PCIe without P2P guarantees (consumer driver), no ECC,
2 fewer years of warranty/MTBF comfort, and ~128 GB caps headroom — the
vision model or the second big model gets evicted. Acceptable if budget
forces it; expect more operational fiddling and plan model lineup around
~110 GB usable.

**Premium — H200/B200-class server (141 GB+/GPU).** Explicitly **overkill**
for 10 LAN users: you pay datacenter premiums for bandwidth and NVLink that
batch-of-5 inference doesn't need. Only justified if the team grows past
~25 users or training becomes continuous rather than quarterly.

**Two smaller boxes instead of one big one?** No — one box keeps the
knowledge index, the auth proxy, and the models on one PCIe fabric;
splitting buys availability the spec doesn't ask for and doubles admin.

## Power, cooling, placement

- 2× ~600 W GPUs + platform ≈ **1.6–1.9 kW sustained** under load: that is
  a dedicated 16 A circuit in most office wiring — check before ordering.
- Workstation-edition blower cards can live in a tower in a ventilated
  room; a **Max-Q-class variant (~half the board power)** trades ~15%
  throughput for half the heat/noise if the box must sit near desks.
  Server/rack-edition cards need rack airflow — only with a real server
  room. Confirm the exact board editions and their power in the
  [SKU checklist](hardware-sku-checklist.md).
- UPS sized for graceful shutdown (not runtime): ~3 kVA line-interactive.
- Noise: a loaded 4U is not office-compatible; a tower with Max-Q cards is
  borderline. Decide placement before the chassis, not after.

## Purchase-time checklist

- [ ] Re-verify GPU SKU / price / power from the
      [SKU checklist](hardware-sku-checklist.md) (successor cards may exist;
      re-run the sizing table against the actual card you'll buy).
- [ ] Confirm chosen models' FP8 weights actually fit the table above
      (model lineup will have changed since this was written).
- [ ] Verify motherboard PCIe slot spacing fits two triple-slot cards at
      x16/x16.
- [ ] Confirm the electrical circuit and placement room.
- [ ] Order 10 GbE NIC + switch port at the same time, not after.
- [ ] **Pass the purchase-time benchmark gate** (Step 0 in
      [phase-3-gpu-team.md](phase-3-gpu-team.md)) on loaner/rented candidate
      hardware before raising the PO — the 160–190 GB sizing above is an
      estimate until measured.
