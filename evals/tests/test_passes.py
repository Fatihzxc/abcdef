from evals.cases import Case
from evals.passes import smoke_subset


def _cases():
    tr = [Case(id=f"tr-docs/{i}", role="r1", prompt="p", rubric="tr-docs") for i in range(10)]
    code = [Case(id=f"code/{i}", role="r3", prompt="p", rubric="code") for i in range(10)]
    return tr + code


def test_smoke_subset_limits_n_per_rubric():
    sub = smoke_subset(_cases(), n_per_rubric=3)
    assert sum(1 for c in sub if c.rubric == "tr-docs") == 3
    assert sum(1 for c in sub if c.rubric == "code") == 3
    assert len(sub) == 6


def test_smoke_subset_keeps_stable_order():
    cases = [Case(id=f"tr-docs/{i}", role="r1", prompt="p", rubric="tr-docs") for i in range(5)]
    assert [c.id for c in smoke_subset(cases, 2)] == ["tr-docs/0", "tr-docs/1"]
