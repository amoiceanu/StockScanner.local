from app.scoring.scoring_engine import CandidateFilter, deterministic_confidence, recommendation_level, weighted_score


def test_recommendation_boundaries():
    assert recommendation_level(9) == "STRONG BUY"
    assert recommendation_level(7.5) == "BUY"
    assert recommendation_level(5) == "HOLD"
    assert recommendation_level(0.5) == "STRONG SELL"


def test_missing_fundamental_redistributes_weight():
    score = weighted_score({"technical": 8, "news": 7, "sentiment": 7, "fundamental": None, "debate": 8, "risk": 3})
    assert 7 <= score <= 8.5


def test_candidate_filter():
    filter_ = CandidateFilter(6)
    assert filter_.is_interesting(6.1, [])
    assert filter_.is_interesting(5, ["20-day breakout"])
    assert not filter_.is_interesting(5, [])


def test_confidence_is_bounded_and_calibrated():
    confidence = deterministic_confidence([8, 8.2, 7.9], .9, 1, historical_win_rate=.6)
    assert .5 < confidence <= .72
