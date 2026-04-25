"""Statistical helpers required by §7 of the validation plan.

Functions:
  wilson_ci(successes, total, confidence=0.95) -> (lo, hi)
  cohen_kappa(rater_a, rater_b) -> float
  percentile(values, p) -> float
  bootstrap_ci(values, statistic, n=10000, confidence=0.95) -> (lo, hi)
  cohen_h(p1, p2) -> float            # effect size for proportions
  cohen_d(a, b) -> float              # effect size for continuous
  mcnemar_pvalue(b, c) -> float       # exact McNemar's test for paired binary

All public functions take plain Python sequences. No SciPy dependency.
"""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Sequence
from typing import Any


def wilson_ci(successes: int, total: int, confidence: float = 0.95) -> tuple[float, float]:
    """Wilson-score 95% CI for a binomial proportion.

    Used per §7.2: prefer Wilson over normal approximation because samples
    are small and rates near boundaries.
    """
    if total <= 0:
        return (0.0, 0.0)
    z = _z_for_confidence(confidence)
    p = successes / total
    denom = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denom
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def _z_for_confidence(confidence: float) -> float:
    table = {0.90: 1.6449, 0.95: 1.96, 0.99: 2.5758}
    if confidence in table:
        return table[confidence]
    # Acklam's inverse-normal approximation for arbitrary confidence
    p = 1 - (1 - confidence) / 2
    return _norm_inv(p)


def _norm_inv(p: float) -> float:
    # Beasley-Springer-Moro inverse normal CDF
    a = [-39.6968302866538, 220.946098424521, -275.928510446969, 138.357751867269, -30.6647980661472, 2.50662827745924]
    b = [-54.4760987982241, 161.585836858041, -155.698979859887, 66.8013118877197, -13.2806815528857]
    c = [-0.00778489400243029, -0.322396458041136, -2.40075827716184, -2.54973253934373, 4.37466414146497, 2.93816398269878]
    d = [0.00778469570904146, 0.32246712907004, 2.445134137143, 3.75440866190742]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p <= phigh:
        q = p - 0.5
        r = q * q
        return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
    q = math.sqrt(-2 * math.log(1 - p))
    return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)


def cohen_kappa(rater_a: Sequence[Any], rater_b: Sequence[Any]) -> float:
    """Cohen's κ for inter-rater agreement on categorical labels."""
    if len(rater_a) != len(rater_b) or not rater_a:
        return float("nan")
    cats = sorted(set(rater_a) | set(rater_b))
    n = len(rater_a)
    cm = {(c1, c2): 0 for c1 in cats for c2 in cats}
    for a, b in zip(rater_a, rater_b):
        cm[(a, b)] += 1
    po = sum(cm[(c, c)] for c in cats) / n
    pa_marginals = {c: sum(cm[(c, c2)] for c2 in cats) / n for c in cats}
    pb_marginals = {c: sum(cm[(c1, c)] for c1 in cats) / n for c in cats}
    pe = sum(pa_marginals[c] * pb_marginals[c] for c in cats)
    if pe == 1:
        return 1.0
    return (po - pe) / (1 - pe)


def percentile(values: Sequence[float], p: float) -> float:
    """Linear-interpolation percentile (numpy-compatible)."""
    if not values:
        return float("nan")
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return s[int(k)]
    return s[f] + (s[c] - s[f]) * (k - f)


def bootstrap_ci(
    values: Sequence[float],
    statistic: Callable[[Sequence[float]], float] = lambda xs: sum(xs) / len(xs),
    n: int = 10000,
    confidence: float = 0.95,
    seed: int | None = 42,
) -> tuple[float, float]:
    """Non-parametric bootstrap CI for arbitrary statistic."""
    if not values:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    sample_size = len(values)
    samples = []
    for _ in range(n):
        resample = [values[rng.randrange(sample_size)] for _ in range(sample_size)]
        samples.append(statistic(resample))
    samples.sort()
    lo_idx = int(((1 - confidence) / 2) * n)
    hi_idx = int((1 - (1 - confidence) / 2) * n)
    return (samples[lo_idx], samples[min(hi_idx, n - 1)])


def cohen_h(p1: float, p2: float) -> float:
    """Effect size for proportion difference."""
    phi1 = 2 * math.asin(math.sqrt(max(0.0, min(1.0, p1))))
    phi2 = 2 * math.asin(math.sqrt(max(0.0, min(1.0, p2))))
    return phi1 - phi2


def cohen_d(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    mean_a = sum(a) / len(a)
    mean_b = sum(b) / len(b)
    var_a = sum((x - mean_a) ** 2 for x in a) / (len(a) - 1)
    var_b = sum((x - mean_b) ** 2 for x in b) / (len(b) - 1)
    pooled = math.sqrt((var_a + var_b) / 2)
    return (mean_a - mean_b) / pooled if pooled > 0 else float("nan")


def mcnemar_pvalue(b: int, c: int) -> float:
    """Exact two-sided McNemar p-value via binomial. b=A→¬B, c=¬A→B counts."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(_binom(n, i) for i in range(k + 1)) * (0.5 ** n)
    return min(1.0, 2 * p)


def _binom(n: int, k: int) -> int:
    if k < 0 or k > n:
        return 0
    return math.comb(n, k)
