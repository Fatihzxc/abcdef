from evals.cases import Case
from evals.runner import build_payload, make_record


def _case():
    return Case(
        id="code/uart-init-01",
        role="r3",
        prompt="Write a UART init in bare-metal C.",
        rubric="code",
        max_tokens=512,
    )


def test_build_payload_is_deterministic():
    p = build_payload(_case(), model="qwen3-coder")
    assert p["model"] == "qwen3-coder"
    assert p["temperature"] == 0
    assert p["seed"] == 0
    assert p["max_tokens"] == 512
    assert p["messages"][-1]["content"] == "Write a UART init in bare-metal C."


def test_build_payload_grounded_includes_context():
    c = Case(
        id="grounded-qa/reset-01",
        role="r8",
        prompt="What is the reset value of UART_CR?",
        rubric="grounded-qa",
        context="UART_CR reset value = 0x00",
    )
    p = build_payload(c, model="m")
    joined = " ".join(msg["content"] for msg in p["messages"])
    assert "UART_CR reset value = 0x00" in joined


def test_make_record_computes_tokens_per_second_and_is_unscored():
    resp = {
        "choices": [{"message": {"content": "void uart_init(void){}"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 40},
    }
    r = make_record(_case(), "m", resp, elapsed_s=2.0)
    assert r["case_id"] == "code/uart-init-01"
    assert r["model"] == "m"
    assert r["completion"] == "void uart_init(void){}"
    assert r["completion_tokens"] == 40
    assert r["tokens_per_second"] == 20.0
    assert r["score"] is None
