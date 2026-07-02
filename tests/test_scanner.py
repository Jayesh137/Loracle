"""Targeted tests for scanner weighting and low-signal handling."""
from src.scanner import _get_weights, compute_similarity


def test_identical_fingerprints_score_high():
    fp = {
        "asset_preferences": {"coins_traded": ["BTC", "ETH"],
                              "coin_frequency": {"BTC": 0.6, "ETH": 0.4}},
        "timing_profile": {"hourly_distribution": [1] + [0] * 23},
        "leverage_profile": {"overall": {"mean": 5.0}},
        "entry_exit_style": {"order_type_ratio": {"market": 0.5, "limit": 0.5}},
        "hold_duration": {"distribution_buckets": {"under_1h": 1.0}},
    }
    score, dims = compute_similarity(fp, fp)
    assert score > 0.95


def test_missing_dimensions_are_dropped_not_zeroed():
    # Candidate has only asset+timing data; missing dims must not drag score to 0.
    full = {
        "asset_preferences": {"coins_traded": ["BTC"], "coin_frequency": {"BTC": 1.0}},
        "timing_profile": {"hourly_distribution": [1] + [0] * 23},
        "leverage_profile": {"overall": {"mean": 5.0}},
        "entry_exit_style": {"order_type_ratio": {"market": 1.0, "limit": 0.0}},
        "hold_duration": {"distribution_buckets": {"under_1h": 1.0}},
    }
    sparse = {
        "asset_preferences": {"coins_traded": ["BTC"], "coin_frequency": {"BTC": 1.0}},
        "timing_profile": {"hourly_distribution": [1] + [0] * 23},
        "leverage_profile": {},
        "entry_exit_style": {},
        "hold_duration": {},
    }
    score, _ = compute_similarity(full, sparse)
    # Only the two shared dimensions count, both perfect -> high score, not diluted.
    assert score > 0.95


def test_weights_come_from_config():
    w = _get_weights()
    assert set(w) >= {"asset_preferences", "timing_profile", "leverage_profile"}
    assert abs(sum(w.values()) - 1.0) < 1e-6
