from evals.report import aggregate, render_markdown


def _records():
    return [
        {"model": "A", "rubric": "tr-docs", "score": 4, "tokens_per_second": 10.0},
        {"model": "A", "rubric": "tr-docs", "score": 2, "tokens_per_second": 12.0},
        {"model": "A", "rubric": "code", "score": 5, "tokens_per_second": 8.0},
        {"model": "B", "rubric": "tr-docs", "score": 3, "tokens_per_second": 20.0},
        # Unscored: excluded from the score mean, still counted for tok/s.
        {"model": "B", "rubric": "tr-docs", "score": None, "tokens_per_second": 21.0},
    ]


def test_aggregate_mean_score_per_model_and_rubric():
    agg = aggregate(_records())
    assert agg[("A", "tr-docs")]["mean_score"] == 3.0
    assert agg[("A", "code")]["mean_score"] == 5.0
    assert agg[("B", "tr-docs")]["mean_score"] == 3.0
    assert agg[("A", "tr-docs")]["n"] == 2


def test_aggregate_tok_s_includes_unscored_rows():
    agg = aggregate(_records())
    assert agg[("B", "tr-docs")]["mean_tok_s"] == 20.5


def test_render_markdown_has_header_and_rows():
    md = render_markdown(aggregate(_records()))
    assert "| Model | Rubric |" in md
    assert "tr-docs" in md
    assert "code" in md
