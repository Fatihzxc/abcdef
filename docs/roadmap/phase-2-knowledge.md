# Phase 2 — Knowledge Grounding

Goal: extend the existing **datasheet-kb** MCP server into the Domain
Knowledge Layer (company docs, netlists/BOMs, subsea literature), wire it
into every interface, bring up R8 (domain Q&A) and R5 (standards reviewer),
and ship the `.docx` template pipeline for R1/R6.

Prerequisite: phase 1 serving stack in daily use.

**Milestones, not one gate.** Phase 2 is too large to land behind a single
acceptance test, so it ships as five independent milestones — each with its
own acceptance criteria, each shippable on its own. Do them roughly in
order, but any one can complete and deliver value without the rest:

- **2A** — text corpus ingestion + R8 over datasheet/company docs.
- **2B** — standards docs + R5.
- **2C** — `.docx` template pipeline.
- **2D** — Altium netlist/BOM/pin-map structured ingestion.
- **2E** — subsea equation-aware PDF pipeline.

Estimated effort: 6–10 working sessions across the five milestones —
ingestion quality dominates. Standards codification (2B) has a
human-approval step: schedule slack for it (spec risk).

---

## Architectural rule (from the spec, non-negotiable)

**Facts live in retrieval, never in weights.** Retrieval provides
citations, instant updates when a document revs, and no hallucinated
register values. Phase-3 fine-tuning may add fluency; factual questions
always go through this layer.

**datasheet-kb is the ONLY authoritative knowledge path.** Every grounded
answer in every interface resolves through it so revision handling, "not
found" discipline, and citation metadata stay consistent. Do not stand up
a second index that bypasses these (see the Open WebUI note in Step 2).

---

## Milestone acceptance criteria

Each milestone is its own gate. A milestone is done only when its criteria
pass; later milestones do not block earlier ones from shipping.

### Phase 2A — text corpus + R8

Datasheet and company-doc text indexed; R8 answers from it with citations.
Implemented by Step 1 (text corpora), Step 2 (MCP wiring + R8 role).

**Retrieval gates first — they run BEFORE any model-answer scoring.** A
wrong citation is worse than none, so retrieval quality is gated on its own
before R8's prose is judged:

- [ ] Top-k recall on a fixed set of known register/document questions:
      the correct page/section is in the top-k for each.
- [ ] Register-name lookups exact-match (or rerank to) the named register;
      a query for a specific control register must not surface unrelated
      (e.g. GPIO) registers as top hits.
- [ ] Minimum relevance threshold enforced: when the top reranked score is
      below threshold, the system returns "not found in the corpus" rather
      than citing a weak chunk.
- [ ] Negative tests reject irrelevant cited chunks. A low-relevance cited
      answer is a FAILURE even if the prose reads plausibly.

Then the answer gates:

- [ ] R8 answers hardware/register questions with citations in chat, IDE,
      and CLI; "not found in the corpus" is returned when true.
- [ ] Grounding available to other roles (R4 can pull the register map the
      driver under review writes to).
- [ ] Open WebUI invokes a datasheet-kb tool and returns a citation from
      the canonical corpus (transport test, see Step 2).
- [ ] Continue (or `llmctl review --ground`) makes a real MCP call on a
      diff and the finding cites the datasheet page (mode test, see Step 2).

### Phase 2B — standards docs + R5

At least 2 per-language standards docs written and approved; R5 enforces
them. Implemented by Step 3. The 2A retrieval gates apply to the
`standards/` index too: a finding must cite a rule that the reranker
actually surfaced, not a low-relevance match.

- [ ] At least 2 per-language standards docs written and approved.
- [ ] `llmctl review --role r5` on code with a known violation cites the
      rule ID; the prompt invents no rule absent from the retrieved standard.
- [ ] Standards retrieval passes the 2A relevance-threshold and
      reject-irrelevant-chunk gates, scoped to `standards/`.

### Phase 2C — `.docx` template pipeline

Implemented by Step 4.

- [ ] `llmctl docgen` renders an R1 output into a company `.docx` template;
      the file opens clean in Word with company styles intact.
- [ ] R2 reviews a generated `.docx` against the same template structure.

### Phase 2D — Altium structured ingestion

Netlists, BOMs, and pin/connector maps parsed and queryable. Implemented by
the Altium-parser part of Step 1.

- [ ] Structured lookup answers "what connects to U12 pin 4" from a parsed
      netlist with a citation to the source export.
- [ ] BOM/pin-map queries return refdes/part-number/value fields.

### Phase 2E — subsea equation-aware PDF pipeline

Math-heavy literature ingested without mangling equations. Implemented by
the equation-aware part of Step 1.

- [ ] Phase-0 subsea/equation Q&A cases pass through the live MCP path;
      retrieved equation blocks stay intact with their defining prose.

---

## Step 1 — Corpora ingestion into datasheet-kb

datasheet-kb already indexes vendor PDFs and serves register lookups with
citations. This step adds three corpora and upgrades two shared components.
(datasheet-kb lives in its own repo; this section is its requirements list,
tracked there.)

| Corpus | Source format | Extraction approach |
|---|---|---|
| Vendor datasheets / ref manuals / IP docs | PDF | already done today |
| Company design docs, test reports, architecture docs | docx/PDF | pandoc (docx→md) or PDF pipeline below; keep doc-type + revision metadata |
| Schematics/CAD as text | Altium exports: netlists, BOMs, pin/connector maps | dedicated parsers, see below |
| Subsea engineering literature | math-heavy PDFs (textbooks, papers, DNV/API-class standards, company analyses) | **equation-aware** PDF pipeline, see below |

**Equation-aware PDF extraction.** Naive text extraction (plain
pymupdf-class) mangles equations — spec calls this out as a risk. Use an
OCR/layout pipeline that emits LaTeX for math: `marker` (marker-pdf) as
the default, `nougat` as the alternative for the worst documents. Both run
on CPU (slow — batch overnight; ingestion is offline work, not
interactive). Chunking must not split an equation from the prose that
defines its symbols: chunk on section boundaries, keep equation blocks
atomic. **Verify end-to-end with the phase-0 subsea Q&A cases** before
declaring the corpus ingested — that's exactly what they exist for.

**Altium export parsers.** Altium sources export clean structured text; no
EDA-tool integration (per spec, file-level only):

- Netlists (Protel/EDIF/keep whatever format the team already exports):
  parse to `net → [(refdes, pin), ...]` records; index as both searchable
  text and structured lookup ("what connects to U12 pin 4").
- BOMs (CSV/xlsx): straight tabular ingestion with refdes/part-number/value
  fields preserved.
- Pin/connector maps: tabular, same treatment.

PDF-only schematics (no Altium source) are **not** ingested — schematic
*images* are the GPU/vision phase (R7); degrade gracefully per spec.

**Embeddings + reranking.** Multilingual is mandatory (Turkish docs +
English datasheets in one index): `bge-m3` embeddings + `bge-reranker-v2-m3`
reranker. Both run acceptably on CPU at index/query scale (cheap next to
generation, and the 24-core CPU has ample headroom). They serve the whole
stack — but datasheet-kb stays the
**only** authoritative index. Do **not** enable Open WebUI document-chat
indexing for company/domain corpora: a separate index bypasses revision
handling, "not found" discipline, and citation metadata, producing
inconsistent citations. Only allow it if it is backed by the same canonical
index and citation metadata as datasheet-kb.

**Citations.** Preserve datasheet-kb's existing citation discipline:
every chunk carries (document, revision, page/section); every answer built
on retrieval must cite, and "not found in the corpus" is a first-class
answer. Uncited facts are bugs.

## Step 2 — MCP wiring into every interface

datasheet-kb already speaks MCP. Connect it everywhere:

- **Continue (VS Code):** native MCP support — add datasheet-kb to the
  `mcpServers` block (generated by `configs/render.py`). MCP tools only fire
  in a tool-capable agent/chat mode; a plain slash-prompt template that
  receives only `@diff` may never auto-call a tool. So **pin the mode**:
  the R4/R8 path must run where tool use is enabled. Acceptance test:
  create a diff touching a known register, invoke the R4/R8 path, confirm a
  real MCP call is made, and confirm the finding cites the datasheet/source
  page. If automatic tool use proves unreliable in the IDE, make
  `llmctl review --ground` the **canonical** grounded-review path and treat
  IDE tool use as convenience only.
- **Open WebUI:** one supported transport, decided up front. **Preferred:**
  run datasheet-kb as an HTTP/streamable MCP server and connect it natively
  (Open WebUI v0.6.31+ supports native MCP for HTTP/streamable transports).
  **Fallback:** bridge a stdio/SSE datasheet-kb via `mcpo` (MCP-to-OpenAPI)
  and register it as a tool server. Acceptance test: Open WebUI invokes a
  datasheet-kb tool and returns a citation from the canonical corpus.
- **CLI:** `llmctl` gains a lightweight MCP client (Python `mcp` package)
  and a `--ground` flag: retrieve → stuff context → answer-with-citations.

R8 role config (`configs/roles/r8-domain-qa.yaml`): grounded-Q&A system
prompt — answer **only** from retrieved context, cite every fact
(document + page/section), say "not found in the corpus" otherwise.
`rag: true`. Model: the bake-off's Set-3 (faithfulness) winner, which may
differ from the eloquence winner — that's the point.

Grounding for other roles is opt-in per role config (`rag: true` +
retrieval scope), e.g. R4 retrieves the register map for the peripheral
named in the diff; R1 retrieves prior documents about the board being
described.

## Step 3 — Standards codification + R5

R5 can only enforce what is written down (spec). Today the standard is
partial/informal. Workflow per language (C/C++ first, then Python, then
HDL/the rest):

1. **Mine:** `llmctl sweep --role r3 --prompt standards-mining <repo>` —
   the LLM reads representative company code and drafts the conventions it
   observes (naming, layout, error handling, register-access idioms,
   forbidden constructs) as a structured draft.
2. **Human pass:** the user edits, corrects, and *approves* the draft. This
   step is the schedule risk; timebox each language to one session and
   accept "good enough, versioned" over complete.
3. **Commit:** `standards/<lang>.md` with stable rule IDs
   (`C-NAM-001` style) so findings can cite rules.
4. **Enforce:** r5-standards role — RAG scoped to `standards/` **only**;
   findings list format: rule ID, severity, file:line, violation, fix. The
   prompt forbids inventing rules not present in the retrieved standard.
   Runs through the same `llmctl review`/`sweep`/pre-commit plumbing as R4
   (`--role r5`), and in the IDE as a `/standards` prompt.

Division of labor with R4 stays sharp: R4 = correctness bugs, R5 = written
standard, so findings don't blur. Add a small R5 eval set (snippets with
known violations) to `evals/cases/` as the standards land.

## Step 4 — `.docx` template pipeline (R1, R6)

No in-Word plugin (spec). Output path: role emits structured content; a
renderer fills the company template.

```
templates/
  design-doc.docx        # company templates with Jinja tags ({{ ... }})
  formal-letter.docx
  test-report.docx
  map/design-doc.yaml    # template field map: which sections/fields exist
```

- Renderer: **docxtpl** (Jinja2 inside real company .docx — styles,
  headers, logos survive untouched). `python-docx` for programmatic edits
  docxtpl can't express; pandoc (md → docx via `--reference-doc`) as the
  low-fi fallback for R6 general documents.
- Flow: `llmctl docgen --template design-doc --brief brief.md out.docx`
  → r1-docs-tr generates per-section content as structured
  markdown/JSON keyed to the template's field map → docxtpl renders →
  user reviews in Word. The LLM never touches XML; it fills named fields.
- R2 closes the loop: `llmctl ask --role r2 --file out.docx` (docx→md via
  pandoc) reviews the generated document against the same template
  structure.

Start with the 2–3 most-used templates; each new template is just a tagged
.docx + a field-map YAML.

## Step 5 — Verification procedures

Concrete checks that satisfy the per-milestone acceptance criteria above.
Run each milestone's checks against that milestone's gate.

**2A — retrieval gates (run first, before any answer scoring):**

1. Top-k recall on the fixed register/document question set — correct
   page/section in top-k for each.
2. Register-name lookup returns the named register exactly (or reranked to
   the top); reject runs where unrelated registers (e.g. GPIO) outrank the
   target.
3. Below-threshold query returns "not found in the corpus" instead of
   citing a weak chunk. A plausible-looking answer over a low-relevance
   chunk is a FAILURE.

**2A — R8 answer + interface checks:**

4. Re-run the phase-0 grounded-QA set **through the MCP path** (retrieval
   live, not hand-fed excerpts) — faithfulness and citation scores must
   hold.
5. Ask R8 a register question whose answer changed between datasheet
   revisions — answer must cite the *current* revision (instant-update
   property).
6. Ask R8 a question the corpus cannot answer — must return "not found in
   the corpus".
7. Open WebUI invokes a datasheet-kb tool and returns a citation from the
   canonical corpus (transport test).
8. Continue (or `llmctl review --ground`) on a diff touching a known
   register makes a real MCP call and the finding cites the datasheet page
   (mode test).

**2B:** `llmctl review --role r5` on code with a known violation of an
approved standard → finding cites the rule ID; the cited rule passed the
relevance gate.

**2C:** `llmctl docgen` produces a .docx that opens clean in Word with
company styles intact; R2 reviews it against the template structure.

**2D:** structured netlist lookup ("what connects to U12 pin 4") answers
with a citation to the source export.

**2E:** phase-0 subsea/equation cases pass through the live MCP path with
equation blocks intact.
