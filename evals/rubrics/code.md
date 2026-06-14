# Rubric — Set 2: Code (R3/R4)

Score each dimension 1–5; record one overall 1–5 in `score`, breakdown in `note`.

1. **Correctness** — does it do what was asked? For register-level code, are
   the addresses/bit operations right against the map given in the prompt?
2. **Idiomatic style** — conventional for the language/stack (embedded C, C++
   RTOS, Python, VHDL/Verilog, Tcl, …); no obvious anti-patterns.
3. **Would-compile plausibility** — types, includes, syntax. For trivial C or
   Python, actually compile/run it and note the result.

Prefer correctness over cleverness. A confidently-wrong register write scores
lower than an incomplete-but-correct stub.
