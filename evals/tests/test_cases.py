import pytest

from evals.cases import Case, CaseError, load_case


def _valid():
    return {
        "id": "tr-docs/formal-letter-01",
        "role": "r1",
        "prompt": "Bir resmi sirket mektubu yaz.",
        "rubric": "tr-docs",
        "max_tokens": 1024,
    }


def test_load_case_returns_case_with_fields():
    c = load_case(_valid())
    assert isinstance(c, Case)
    assert c.id == "tr-docs/formal-letter-01"
    assert c.role == "r1"
    assert c.rubric == "tr-docs"
    assert c.max_tokens == 1024


def test_load_case_normalizes_role_to_lower():
    d = _valid()
    d["role"] = "R1"
    assert load_case(d).role == "r1"


def test_load_case_missing_required_field_raises():
    d = _valid()
    del d["prompt"]
    with pytest.raises(CaseError):
        load_case(d)


def test_load_case_defaults_max_tokens():
    d = _valid()
    del d["max_tokens"]
    assert load_case(d).max_tokens == 1024


def test_load_case_grounded_keeps_context_and_expected():
    d = _valid()
    d.update(
        id="grounded-qa/reset-01",
        rubric="grounded-qa",
        context="UART_CR reset value = 0x00",
        expected="0x00",
    )
    c = load_case(d)
    assert c.context == "UART_CR reset value = 0x00"
    assert c.expected == "0x00"
