"""Unit tests for dashboard service helpers."""

from backend.services.dashboard_service import calc_trend


def test_calc_trend_positive() -> None:
    pct, direction = calc_trend(12, 10)
    assert pct == 20.0
    assert direction == "up"


def test_calc_trend_negative() -> None:
    pct, direction = calc_trend(8, 10)
    assert pct == -20.0
    assert direction == "down"


def test_calc_trend_previous_zero_with_current() -> None:
    pct, direction = calc_trend(3, 0)
    assert pct == 100.0
    assert direction == "new"


def test_calc_trend_both_zero() -> None:
    pct, direction = calc_trend(0, 0)
    assert pct == 0.0
    assert direction == "neutral"
