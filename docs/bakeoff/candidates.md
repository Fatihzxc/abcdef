# Bake-off Candidates (living list)

The phase-0 roadmap table is a *snapshot*; this file is the source of truth
for what actually gets downloaded and scored. The roadmap owns the selection
**process** — this file owns the volatile **model facts**. Re-check upstream
pages for newer releases before downloading (the families are the decision,
not the exact checkpoints).

One row per candidate. Fill `sha256` and `download date` when the file lands
in `models/` (mirror them into `models/manifest.tsv` and `artifacts.lock`).
Drop a candidate by setting **status = dropped** and recording why — never
silently delete, so the decision history survives.

Required fields:

- **model id** — upstream id (e.g. `Qwen/Qwen3-30B-A3B-Instruct-2507`)
- **quant source** — where the GGUF came from (repo/uploader)
- **license** — and whether it permits the intended use
- **sha256** — of the downloaded file
- **download date** — `YYYY-MM-DD`
- **context limit** — max usable context for this quant
- **expected RAM/VRAM** — sizing for the current 32 GB / 8 GB-VRAM box
- **roles** — intended R1–R8 targets
- **status** — `candidate` | `dropped` (with reason)

| model id | quant source | license | sha256 | download date | context | exp. RAM/VRAM | roles | status / exclusion reason |
|---|---|---|---|---|---|---|---|---|
| Qwen/Qwen3-30B-A3B-Instruct-2507 | _tbd_ | Apache-2.0 | _tbd_ | _tbd_ | _tbd_ | ~18 GB RAM | R1,R2,R6,R8 | candidate |
| Qwen/Qwen3-Coder-30B-A3B-Instruct | _tbd_ | Apache-2.0 | _tbd_ | _tbd_ | _tbd_ | ~18 GB RAM | R3,R4,R5 | candidate |
| google/gemma-4-26b-a4b (verify id) | _tbd_ | Gemma terms | _tbd_ | _tbd_ | _tbd_ | ~16 GB RAM | R1,R2,R6,R8 | candidate |
| google/gemma-3-27b | _tbd_ | Gemma terms | _tbd_ | _tbd_ | _tbd_ | ~16 GB RAM | R1,R2,R6 | candidate (quality-ceiling check) |
| google/gemma-3-12b | _tbd_ | Gemma terms | _tbd_ | _tbd_ | _tbd_ | ~7 GB RAM | R6,fallback | candidate |
| Qwen/Qwen3-14B | _tbd_ | Apache-2.0 | _tbd_ | _tbd_ | _tbd_ | ~9 GB RAM | R6,R8 | candidate |
| CohereLabs/aya-expanse-8b | _tbd_ | CC-BY-NC (verify) | _tbd_ | _tbd_ | _tbd_ | ~5 GB RAM | R1,R2 | candidate (Turkish check) |
| Qwen/Qwen2.5-Coder-14B | _tbd_ | Apache-2.0 | _tbd_ | _tbd_ | _tbd_ | ~9 GB RAM | R3,R4 | candidate |

> Verify every license column before download — `aya-expanse` in particular
> may carry a non-commercial license that rules out company use.
