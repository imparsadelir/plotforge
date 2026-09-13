"""Tests for peak detection and smoothing.

Each test builds a curve whose peaks are known in advance, so the result
can be checked against the truth rather than against a screenshot.
"""

import numpy as np

from core.analysis.peaks import detect_peaks, smooth, strongest


def gaussian_curve(x, centres, depth=20.0, width=30.0, baseline=100.0, sign=-1):
    """Build a curve with peaks at known positions.

    sign = -1 gives dips (like a transmittance spectrum);
    sign = +1 gives peaks that point upwards.
    """
    y = np.full_like(x, baseline, dtype=float)
    for centre in centres:
        y += sign * depth * np.exp(-((x - centre) ** 2) / (2 * width ** 2))
    return y


def test_finds_peaks_at_the_expected_positions():
    """Three known dips should be found within a few units of the truth."""
    x = np.linspace(0, 1000, 2000)
    y = gaussian_curve(x, [200, 500, 800])

    found = detect_peaks(x, y, sensitivity=5)

    assert found["x"].size == 3
    for expected, actual in zip([200, 500, 800], sorted(found["x"])):
        assert abs(actual - expected) < 10


def test_direction_is_detected_for_dips():
    """A transmittance-style curve sits high and dips down."""
    x = np.linspace(0, 1000, 2000)
    y = gaussian_curve(x, [500], sign=-1)

    assert detect_peaks(x, y)["direction"] == "down"


def test_direction_is_detected_for_upward_peaks():
    """An absorbance-style curve sits low and rises."""
    x = np.linspace(0, 1000, 2000)
    y = gaussian_curve(x, [500], baseline=0.0, sign=1)

    assert detect_peaks(x, y)["direction"] == "up"


def test_higher_sensitivity_finds_fewer_peaks():
    """The sensitivity setting must actually change the outcome."""
    x = np.linspace(0, 1000, 2000)
    y = gaussian_curve(x, [200, 500, 800])
    y += -2.0 * np.exp(-((x - 350) ** 2) / (2 * 10 ** 2))  # one small dip

    many = detect_peaks(x, y, sensitivity=1)["x"].size
    few = detect_peaks(x, y, sensitivity=20)["x"].size

    assert many > few


def test_flat_line_has_no_peaks():
    """A constant signal must not produce peaks from rounding noise."""
    x = np.arange(500)
    y = np.ones(500)

    assert detect_peaks(x, y)["x"].size == 0


def test_short_input_is_handled():
    """Too few points to analyse should return nothing, not crash."""
    assert detect_peaks([], [])["x"].size == 0
    assert detect_peaks([1, 2, 3], [1, 2, 1])["x"].size == 0


def test_missing_values_are_ignored():
    """Gaps in the data must not stop the search."""
    x = np.linspace(0, 1000, 2000)
    y = gaussian_curve(x, [500])
    y[::50] = np.nan

    found = detect_peaks(x, y, sensitivity=5)

    assert found["x"].size >= 1


def test_strongest_returns_the_most_prominent_first():
    """The helper used for reporting should rank by prominence."""
    x = np.linspace(0, 1000, 2000)
    y = np.full_like(x, 100.0)
    y -= 30 * np.exp(-((x - 300) ** 2) / (2 * 30 ** 2))   # deep
    y -= 8 * np.exp(-((x - 700) ** 2) / (2 * 30 ** 2))    # shallow

    found = detect_peaks(x, y, sensitivity=2)
    ranked = strongest(found, count=2)

    assert len(ranked) == 2
    assert abs(ranked[0][0] - 300) < 15


def test_smoothing_reduces_noise():
    """Smoothing should bring a noisy curve closer to the clean one."""
    x = np.linspace(0, 100, 1000)
    clean = np.sin(x / 5)
    noisy = clean + np.random.default_rng(0).normal(0, 0.3, x.size)

    smoothed = smooth(noisy, window=31, order=3)

    error_before = np.abs(noisy - clean).mean()
    error_after = np.abs(smoothed - clean).mean()

    assert error_after < error_before


def test_smoothing_keeps_peak_height():
    """A moving average would flatten the peak; this filter should not."""
    x = np.linspace(0, 100, 1000)
    y = np.exp(-((x - 50) ** 2) / (2 * 3 ** 2))

    smoothed = smooth(y, window=11, order=3)

    assert abs(smoothed.max() - y.max()) < 0.05


def test_smoothing_short_input_is_safe():
    """Fewer points than the window must not raise."""
    values = np.array([1.0, 2.0, 3.0])

    assert smooth(values, window=51).size == 3
