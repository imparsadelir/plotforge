"""Tests for the unsupervised grouping.

Curves are generated in families that are known in advance, so the test
can check that the algorithm recovers the families it was never told
about. The refusals matter as much as the successes: the module is meant
to decline when the data cannot support a meaningful answer.
"""

import numpy as np
import pytest

from core.analysis.clustering import (
    ClusteringError,
    choose_k,
    cluster_curves,
    describe,
    normalise,
    quality,
    resample,
)

GRID = np.linspace(400, 4000, 600)

FAMILIES = {
    "alpha": [(3300, 40, 120), (1640, 15, 40), (1030, 35, 60)],
    "beta": [(2920, 30, 60), (1740, 40, 30), (1170, 25, 45)],
    "gamma": [(3400, 20, 150), (1600, 35, 50), (830, 30, 40)],
}


def make_curve(peaks, rng, noise=0.4):
    """One spectrum-like curve with the given dips."""
    y = np.full_like(GRID, 98.0)
    for centre, depth, width in peaks:
        y -= depth * np.exp(-((GRID - centre) ** 2) / (2 * width ** 2))
    return y + rng.normal(0, noise, GRID.size)


def make_dataset(per_family=4, seed=0):
    """Several curves from each family, with small random variation."""
    rng = np.random.default_rng(seed)
    curves = []

    for name, peaks in FAMILIES.items():
        for index in range(per_family):
            jittered = [
                (c + rng.normal(0, 12), d * rng.uniform(0.85, 1.15), w)
                for c, d, w in peaks
            ]
            curves.append(
                (f"{name}_{index + 1}", GRID, make_curve(jittered, rng))
            )

    return curves


def family_of(label):
    return label.split("_")[0]


def test_recovers_the_real_families():
    """The algorithm is never told the families, but should find them."""
    result = cluster_curves(make_dataset())

    assert result["k"] == 3

    for members in result["groups"].values():
        families = {family_of(name) for name in members}
        assert len(families) == 1, f"mixed group: {members}"


def test_chooses_the_number_of_groups_itself():
    """choose_k should prefer the true number over the alternatives."""
    names, grid, matrix = resample(make_dataset())
    data = normalise(matrix)

    best_k, best_score, scores = choose_k(data)

    assert best_k == 3
    assert scores[3] == max(scores.values())
    assert best_score == scores[3]


def test_a_fixed_k_is_respected():
    """When the user chooses the number of groups, it must be used."""
    result = cluster_curves(make_dataset(), k=2)

    assert result["k"] == 2
    assert len(result["groups"]) == 2


def test_too_few_curves_is_refused():
    """With two curves the result would be arithmetic, not a discovery."""
    curves = make_dataset()[:2]

    with pytest.raises(ClusteringError):
        cluster_curves(curves)


def test_curves_without_a_shared_range_are_refused():
    """Interpolating outside the measured range would invent data."""
    rng = np.random.default_rng(0)
    curves = [
        (f"c{i}", np.arange(i * 100, i * 100 + 50), rng.normal(0, 1, 50))
        for i in range(4)
    ]

    with pytest.raises(ClusteringError):
        resample(curves)


def test_identical_curves_score_as_meaningless():
    """k-means always answers; the score must expose an empty answer."""
    rng = np.random.default_rng(0)
    base = make_curve(FAMILIES["alpha"], rng, noise=0.0)
    curves = [
        (f"same_{i}", GRID, base + rng.normal(0, 0.001, GRID.size))
        for i in range(6)
    ]

    result = cluster_curves(curves)

    assert result["score"] < 0.25
    assert "meaningless" in quality(result["score"])


def test_normalisation_removes_the_effect_of_scale():
    """A curve in thousands must not dominate one in single digits."""
    rng = np.random.default_rng(1)
    small = make_curve(FAMILIES["alpha"], rng)
    large = small * 1000

    data = normalise(np.vstack([small, large]))

    assert np.allclose(data.mean(axis=0), 0, atol=1e-9)


def test_resampling_puts_curves_on_one_grid():
    """Curves of different lengths must become comparable vectors."""
    rng = np.random.default_rng(2)
    curves = [
        ("short", np.linspace(500, 3500, 120), rng.normal(0, 1, 120)),
        ("long", np.linspace(450, 3800, 900), rng.normal(0, 1, 900)),
        ("mid", np.linspace(480, 3600, 400), rng.normal(0, 1, 400)),
        ("other", np.linspace(460, 3700, 250), rng.normal(0, 1, 250)),
    ]

    names, grid, matrix = resample(curves, points=300)

    assert matrix.shape == (4, 300)
    assert grid.min() >= 500  # the narrowest start wins
    assert grid.max() <= 3500  # the narrowest end wins


def test_coordinates_are_two_dimensional():
    """The map drawn for the user always needs two axes."""
    result = cluster_curves(make_dataset())

    assert result["coords"].shape[1] == 2
    assert len(result["explained"]) >= 2


def test_summary_mentions_every_curve():
    """The text shown to the user should account for all the input."""
    result = cluster_curves(make_dataset())
    text = describe(result)

    for name in result["names"]:
        assert name in text


def test_quality_wording_matches_the_score():
    assert "strong" in quality(0.8)
    assert "reasonable" in quality(0.6)
    assert "caution" in quality(0.3)
    assert "meaningless" in quality(0.1)
