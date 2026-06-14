# Team Server — Purchase-Time SKU / Price Checklist

This file holds the **volatile** facts: specific GPU SKUs, variants, street
prices, board power, and availability. These drift fast and were **NOT**
verified against vendor datasheets — treat every row below as a placeholder
to re-confirm.

The **durable** part — VRAM/KV arithmetic, RAM/storage sizing, the
"redo the table if the lineup changes" logic — lives in
[hardware-team-server.md](hardware-team-server.md). Keep it there; keep the
moving numbers here.

> **Before ordering:** re-verify every field below from the vendor product
> page / datasheet and from a system integrator quote. Fill in the source
> URL and the date you checked. Do not order against a stale row.

## GPU options (re-verify before purchase)

| Option | SKU / variant | VRAM | Board power | Street price | Source URL | Date checked |
|---|---|---|---|---|---|---|
| Primary | NVIDIA RTX PRO 6000 Blackwell (workstation / Max-Q / server edition?) | 96 GB GDDR7 ECC | _verify (~600 W; Max-Q ~300 W)_ | _verify (~$9–13k/card)_ | _add vendor URL_ | _YYYY-MM-DD_ |
| Budget | 4× NVIDIA RTX 5090 | 32 GB each (128 GB total) | _verify (~575 W/card)_ | _verify (~$12–16k for 4)_ | _add vendor URL_ | _YYYY-MM-DD_ |

Notes per option (capture at verify time):
- **RTX PRO 6000 Blackwell** — confirm which board edition you are quoting
  (workstation blower vs Max-Q 300 W vs server/rack); cooling and noise
  decision depends on it. Confirm a successor 96 GB-class card hasn't
  replaced it.
- **4× RTX 5090** — consumer card: confirm no-ECC, PCIe P2P behavior under
  the then-current driver, and slot spacing for 4 cards before quoting.

## Platform / supporting parts (re-verify at quote time)

| Item | Placeholder | Source URL | Date checked |
|---|---|---|---|
| CPU (EPYC 9004/9005 or Threadripper PRO) | _price + availability_ | _add URL_ | _YYYY-MM-DD_ |
| 512 GB DDR5 ECC | _price_ | _add URL_ | _YYYY-MM-DD_ |
| NVMe + SATA storage | _price_ | _add URL_ | _YYYY-MM-DD_ |
| PSU (≥ 2000 W) + chassis | _price_ | _add URL_ | _YYYY-MM-DD_ |
| 10 GbE NIC + switch port | _price_ | _add URL_ | _YYYY-MM-DD_ |
| Whole-system integrator quote | _total_ | _add URL_ | _YYYY-MM-DD_ |

Earlier inline ballpark (now superseded by the rows above): full system was
estimated at **$25k–35k (June 2026)**. Re-quote — do not budget from this.
