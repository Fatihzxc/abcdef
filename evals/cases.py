"""Eval case model + validation (see docs/roadmap/phase-0-bakeoff.md, Step 3)."""
from __future__ import annotations

from dataclasses import dataclass

REQUIRED = ("id", "role", "prompt", "rubric")
DEFAULT_MAX_TOKENS = 1024


class CaseError(ValueError):
    """A case dict is missing a required field or is malformed."""


@dataclass(frozen=True)
class Case:
    id: str
    role: str
    prompt: str
    rubric: str
    max_tokens: int = DEFAULT_MAX_TOKENS
    context: str | None = None   # grounded-qa only: the source excerpt
    expected: str | None = None  # grounded-qa only: reference answer / key points


def load_case(d: dict) -> Case:
    """Validate one case dict and return a Case. Raises CaseError on a missing
    required field."""
    missing = [k for k in REQUIRED if not d.get(k)]
    if missing:
        raise CaseError(f"case {d.get('id', '<no id>')!r} missing required: {missing}")
    return Case(
        id=d["id"],
        role=str(d["role"]).lower(),
        prompt=d["prompt"],
        rubric=d["rubric"],
        max_tokens=int(d.get("max_tokens", DEFAULT_MAX_TOKENS)),
        context=d.get("context"),
        expected=d.get("expected"),
    )
