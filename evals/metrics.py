"""Pure throughput math for the bake-off."""
from __future__ import annotations


def tokens_per_second(completion_tokens: int, elapsed_s: float) -> float:
    """Generation throughput. Returns 0.0 for a non-positive interval rather
    than raising — a zero-length measurement is meaningless, not an error."""
    if elapsed_s <= 0:
        return 0.0
    return completion_tokens / elapsed_s
