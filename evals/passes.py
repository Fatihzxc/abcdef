"""Two-pass scoring helpers (F-016): a cheap smoke pass across all candidates,
then a full pass on the survivors, then a fixed regression subset."""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from .cases import Case


def smoke_subset(cases: Iterable[Case], n_per_rubric: int) -> list[Case]:
    """First ``n_per_rubric`` cases of each rubric, preserving input order, for
    the smoke pass that eliminates obviously-weak models early."""
    out: list[Case] = []
    counts: dict[str, int] = defaultdict(int)
    for c in cases:
        if counts[c.rubric] < n_per_rubric:
            out.append(c)
            counts[c.rubric] += 1
    return out
