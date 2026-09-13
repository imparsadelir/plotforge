"""Grouping several curves by shape.

Each curve is resampled onto a shared grid so that all of them can be
compared as vectors of the same length. Principal component analysis then
compresses those vectors to two numbers for plotting, and k-means groups
them. The number of groups is chosen by the silhouette score rather than
being fixed in advance.

No Qt and no plotting here, so the whole module can be tested directly.
"""

import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

MIN_CURVES = 4
GRID_POINTS = 300


class ClusteringError(Exception):
    """Raised when the data cannot support a meaningful grouping."""


def resample(curves, points=GRID_POINTS):
    """Put every curve on one shared x grid.

    ``curves`` is a list of ``(name, x, y)``. The grid covers the range
    that all curves have in common, because extrapolating beyond the
    measured range would invent data.
    """
    cleaned = []

    for name, x, y in curves:
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)

        valid = np.isfinite(x) & np.isfinite(y)
        if valid.sum() < 5:
            continue

        x = x[valid]
        y = y[valid]

        order = np.argsort(x)
        cleaned.append((name, x[order], y[order]))

    if len(cleaned) < MIN_CURVES:
        raise ClusteringError(
            f"Grouping needs at least {MIN_CURVES} curves, "
            f"but only {len(cleaned)} could be used."
        )

    low = max(x.min() for _, x, _ in cleaned)
    high = min(x.max() for _, x, _ in cleaned)

    if not np.isfinite(low) or not np.isfinite(high) or high <= low:
        raise ClusteringError(
            "The selected curves do not share a common x range."
        )

    grid = np.linspace(low, high, points)

    names = []
    matrix = []
    for name, x, y in cleaned:
        names.append(name)
        matrix.append(np.interp(grid, x, y))

    return names, grid, np.asarray(matrix, dtype=float)


def normalise(matrix, method="standard"):
    """Put every curve on a comparable scale.

    Without this, a curve measured in thousands would dominate one
    measured in single digits, and the grouping would reflect units
    rather than shape.
    """
    if method == "none":
        return matrix

    if method == "minmax":
        low = matrix.min(axis=1, keepdims=True)
        high = matrix.max(axis=1, keepdims=True)
        span = np.where(high - low == 0, 1.0, high - low)
        return (matrix - low) / span

    if method == "curve":
        mean = matrix.mean(axis=1, keepdims=True)
        deviation = matrix.std(axis=1, keepdims=True)
        deviation = np.where(deviation == 0, 1.0, deviation)
        return (matrix - mean) / deviation

    return StandardScaler().fit_transform(matrix)


def choose_k(data, max_k=None):
    """Pick the number of groups with the best silhouette score.

    The silhouette score compares how close each curve is to its own
    group against how close it is to the nearest other group. It runs
    from -1 to 1; above roughly 0.5 the grouping is convincing, and
    near 0 the groups overlap so much that they carry little meaning.
    """
    count = data.shape[0]
    upper = min(max_k or count - 1, count - 1, 8)

    if upper < 2:
        raise ClusteringError("Too few curves to form groups.")

    best_k = 2
    best_score = -1.0
    scores = {}

    for k in range(2, upper + 1):
        labels = KMeans(n_clusters=k, n_init=10, random_state=0).fit_predict(data)

        if len(set(labels)) < 2:
            continue

        score = float(silhouette_score(data, labels))
        scores[k] = score

        if score > best_score:
            best_k = k
            best_score = score

    return best_k, best_score, scores


def cluster_curves(curves, k=None, normalisation="standard", points=GRID_POINTS):
    """Group curves by shape and return everything needed to plot it.

    Returns a dict with the curve ``names``, the ``labels`` assigning each
    curve to a group, the two-dimensional ``coords`` for the scatter plot,
    how much variance those two components explain, the chosen ``k``, its
    ``score``, and the score of every k that was tried.
    """
    names, grid, matrix = resample(curves, points)
    data = normalise(matrix, normalisation)

    if k is None:
        k, score, scores = choose_k(data)
    else:
        k = max(2, min(int(k), data.shape[0] - 1))
        labels = KMeans(n_clusters=k, n_init=10, random_state=0).fit_predict(data)
        score = (
            float(silhouette_score(data, labels))
            if len(set(labels)) > 1 else 0.0
        )
        scores = {k: score}

    labels = KMeans(n_clusters=k, n_init=10, random_state=0).fit_predict(data)

    components = min(2, data.shape[0], data.shape[1])
    pca = PCA(n_components=components)
    coords = pca.fit_transform(data)

    if coords.shape[1] == 1:
        coords = np.column_stack([coords[:, 0], np.zeros(coords.shape[0])])

    explained = list(pca.explained_variance_ratio_)
    while len(explained) < 2:
        explained.append(0.0)

    groups = {}
    for name, label in zip(names, labels):
        groups.setdefault(int(label), []).append(name)

    return {
        "names": names,
        "labels": labels,
        "coords": coords,
        "explained": explained,
        "k": k,
        "score": score,
        "scores": scores,
        "groups": groups,
        "grid": grid,
        "matrix": matrix,
    }


def describe(result):
    """A short plain-language summary of a clustering result."""
    lines = [
        f"{len(result['names'])} curves were sorted into {result['k']} groups.",
        f"Silhouette score: {result['score']:.2f} "
        f"({quality(result['score'])}).",
        "",
    ]

    for label in sorted(result["groups"]):
        members = ", ".join(result["groups"][label])
        lines.append(f"Group {label + 1}: {members}")

    explained = sum(result["explained"][:2]) * 100
    lines.append("")
    lines.append(
        f"The two axes of the map show {explained:.0f}% "
        "of the variation between curves."
    )

    return "\n".join(lines)


def quality(score):
    """Turn a silhouette score into a word of warning or confidence."""
    if score >= 0.7:
        return "strong separation"
    if score >= 0.5:
        return "reasonable separation"
    if score >= 0.25:
        return "weak separation, treat with caution"
    return "no real separation — the groups may be meaningless"
