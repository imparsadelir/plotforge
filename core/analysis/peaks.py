"""Peak detection and smoothing.

Pure analysis code: no Qt, no plotting. Everything here takes plain
arrays and returns plain results, so it can be tested on its own.
"""

import numpy as np
from scipy.signal import find_peaks, savgol_filter


def smooth(values, window=11, order=3):
    """Smooth a curve with a Savitzky-Golay filter.

    Unlike a moving average, this fits a small polynomial to a sliding
    window, which keeps the height and position of narrow peaks instead
    of flattening them.
    """
    values = np.asarray(values, dtype=float)

    if values.size < 5:
        return values

    # The window must be odd, larger than the polynomial order, and
    # no longer than the data itself.
    window = int(window)
    if window % 2 == 0:
        window += 1
    window = min(window, values.size if values.size % 2 else values.size - 1)
    order = min(int(order), window - 1)

    if window <= order or window < 3:
        return values

    return savgol_filter(values, window, order)


def detect_peaks(
    x,
    y,
    sensitivity=5.0,
    direction="auto",
    smooth_window=11,
    min_distance=None,
):
    """Find peaks in a curve.

    Parameters
    ----------
    x, y : array-like
        The curve. ``x`` is only used to report where each peak sits.
    sensitivity : float
        Minimum prominence, as a percentage of the full signal range.
        Small values find more peaks; large values find only the
        strongest ones. Using a percentage rather than an absolute
        number means the same setting works for any unit.
    direction : {"auto", "up", "down"}
        Whether peaks point up (absorbance, intensity) or down
        (transmittance). ``"auto"`` decides from the shape of the data.
    smooth_window : int
        Width of the smoothing window applied before searching, so that
        noise is not mistaken for structure. Use 0 to disable.
    min_distance : float or None
        Minimum separation between two peaks, in x units.

    Returns
    -------
    dict with keys ``indices``, ``x``, ``y``, ``prominences``
    and ``direction``.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    empty = {
        "indices": np.array([], dtype=int),
        "x": np.array([]),
        "y": np.array([]),
        "prominences": np.array([]),
        "direction": "up",
    }

    if x.size != y.size or y.size < 5:
        return empty

    valid = np.isfinite(x) & np.isfinite(y)
    if valid.sum() < 5:
        return empty

    x = x[valid]
    y = y[valid]

    order = np.argsort(x)
    x = x[order]
    y = y[order]

    if direction == "auto":
        direction = "down" if _points_down(y) else "up"

    signal = y if direction == "up" else -y

    if smooth_window and smooth_window > 2:
        signal = smooth(signal, smooth_window)

    span = float(np.nanmax(signal) - np.nanmin(signal))
    scale = max(abs(float(np.nanmax(signal))), abs(float(np.nanmin(signal))), 1.0)
    if span <= scale * 1e-9:
        # A flat line has no peaks, only rounding noise.
        return empty

    prominence = span * (float(sensitivity) / 100.0)

    distance = None
    if min_distance:
        step = float(np.median(np.diff(x)))
        if step > 0:
            distance = max(1, int(round(float(min_distance) / step)))

    indices, properties = find_peaks(
        signal, prominence=prominence, distance=distance
    )

    return {
        "indices": indices,
        "x": x[indices],
        "y": y[indices],
        "prominences": properties.get("prominences", np.array([])),
        "direction": direction,
    }


def _points_down(y):
    """Guess whether the interesting features are dips rather than peaks.

    A transmittance spectrum sits near its maximum most of the time and
    dips down at each absorption band, so its median is much closer to
    the top of the range than to the bottom.
    """
    low = float(np.nanmin(y))
    high = float(np.nanmax(y))
    if high <= low:
        return False

    position = (float(np.nanmedian(y)) - low) / (high - low)
    return position > 0.6


def strongest(peaks, count=10):
    """Return the ``count`` most prominent peaks as (x, y) pairs."""
    prominences = peaks["prominences"]
    if prominences.size == 0:
        return []

    order = np.argsort(prominences)[::-1][:count]
    return [(float(peaks["x"][i]), float(peaks["y"][i])) for i in order]
