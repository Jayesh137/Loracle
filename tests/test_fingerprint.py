"""Targeted tests for position reconstruction and position-based metrics."""
from src.fingerprint import (
    positions_from_fills, compute_hold_duration, compute_position_sizing,
    compute_entry_exit_style,
)

MIN = 60_000  # ms per minute


def _fill(coin, side, sz, px, t_min, pnl=0.0, dir="", crossed=True):
    return {"coin": coin, "side": side, "sz": sz, "px": px,
            "time": t_min * MIN, "closedPnl": pnl, "dir": dir, "crossed": crossed}


def test_scale_in_out_is_one_position():
    # Scale into a long over 3 buys, scale out over 2 sells -> exactly ONE position.
    fills = [
        _fill("BTC", "B", 1, 100, 0),
        _fill("BTC", "B", 1, 100, 10),
        _fill("BTC", "B", 1, 100, 20),
        _fill("BTC", "A", 2, 110, 60),
        _fill("BTC", "A", 1, 110, 120, pnl=30.0),
    ]
    positions = positions_from_fills(fills)
    assert len(positions) == 1
    p = positions[0]
    assert p["is_open"] is False
    assert p["direction"] == "long"
    assert p["num_fills"] == 5
    # Peak notional at max size (3 units @ ~100), NOT a single fill's notional.
    assert p["peak_notional"] >= 300
    assert p["duration_minutes"] == 120.0


def test_hold_duration_counts_positions_not_fills():
    # 4 fills but only 2 completed round-trips -> 2 duration samples, not 4.
    fills = [
        _fill("ETH", "B", 1, 10, 0), _fill("ETH", "A", 1, 11, 30),   # 30 min
        _fill("ETH", "B", 1, 10, 100), _fill("ETH", "A", 1, 11, 340),  # 240 min
    ]
    positions = positions_from_fills(fills)
    closed = [p for p in positions if not p["is_open"]]
    assert len(closed) == 2
    hd = compute_hold_duration(positions)
    # Sample count reflects positions (2), not fills (4).
    total = sum(round(v * 2) for v in hd["distribution_buckets"].values())
    assert total == 2


def test_still_open_position_excluded_from_duration():
    fills = [_fill("SOL", "B", 1, 5, 0), _fill("SOL", "B", 1, 5, 10)]  # never closed
    positions = positions_from_fills(fills)
    assert len(positions) == 1 and positions[0]["is_open"] is True
    hd = compute_hold_duration(positions)
    assert hd["overall_minutes"] == {}  # no closed positions -> no durations


def test_position_sizing_uses_peak_notional():
    # Position peaks at 10 units @ $100 = $1000, far above any single fill notional.
    fills = [_fill("BTC", "B", 5, 100, 0), _fill("BTC", "B", 5, 100, 5),
             _fill("BTC", "A", 10, 100, 60)]
    positions = positions_from_fills(fills)
    ps = compute_position_sizing(positions, account_value=10_000)
    assert ps["notional_ranges"]["BTC"]["mean_usd"] >= 1000
    assert ps["size_to_account_ratio"]["mean"] > 0  # not the old 0.0 bug


def test_win_rate_is_per_position():
    # 2 round-trips: one win, one loss -> win_rate 0.5, 2 closed trades (not 4 fills).
    fills = [
        _fill("BTC", "B", 1, 100, 0), _fill("BTC", "A", 1, 110, 60, pnl=10.0),
        _fill("BTC", "B", 1, 100, 120), _fill("BTC", "A", 1, 90, 180, pnl=-10.0),
    ]
    positions = positions_from_fills(fills)
    ee = compute_entry_exit_style(fills, positions)
    assert ee["total_closed_trades"] == 2
    assert ee["win_rate"] == 0.5
