# Rubric — Set 3: Grounded Q&A (R8 and all grounded roles)

Score each dimension 1–5; record one overall 1–5 in `score`, breakdown in `note`.

1. **Faithfulness to context** — the answer uses ONLY facts present in the
   provided context; nothing invented, no values "remembered" from training.
2. **Citation present** — the answer points to its source (document /
   register / page-section), matching datasheet-kb citation discipline.
3. **Traps refused** — when the answer is *not* in the context, the model
   replies exactly "not found in the provided context" instead of guessing.

**Faithfulness outranks eloquence.** A fluent answer with an unsupported or
wrong value fails this set even if it reads well (F-021: a wrong citation is
worse than no answer). Trap cases that get a confident answer score 1.
