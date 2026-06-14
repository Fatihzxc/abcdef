from evals.metrics import tokens_per_second


def test_tokens_per_second_basic():
    assert tokens_per_second(100, 5.0) == 20.0


def test_tokens_per_second_zero_elapsed_returns_zero():
    # A zero/negative interval must yield 0.0, never a ZeroDivisionError.
    assert tokens_per_second(100, 0.0) == 0.0


def test_tokens_per_second_negative_elapsed_returns_zero():
    assert tokens_per_second(100, -1.0) == 0.0


def test_tokens_per_second_zero_tokens():
    assert tokens_per_second(0, 5.0) == 0.0
