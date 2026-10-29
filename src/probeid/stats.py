"""Paired bootstrap CIs (paper §5.1: 95% paired bootstrap, 10^4 resamples).

Pairs are per-gold (gold-clustered, as in the paper's headline interval):
resampling resamples golds, keeping each gold's paired outcomes together.
"""

import random


def paired_bootstrap_ci(a, b, reps=10000, seed=12345):
    """95% CI for mean(a) - mean(b) with a, b paired per gold."""
    assert len(a) == len(b) and len(a) > 0
    rng = random.Random(seed)
    n = len(a)
    diffs = [x - y for x, y in zip(a, b)]
    point = sum(diffs) / n
    boots = []
    for _ in range(reps):
        s = 0.0
        for _ in range(n):
            s += diffs[rng.randrange(n)]
        boots.append(s / n)
    boots.sort()
    lo = boots[int(0.025 * reps)]
    hi = boots[int(0.975 * reps) - 1]
    return point, lo, hi


def rate_ci(values, reps=10000, seed=12345):
    """95% bootstrap CI for a mean rate (gold-clustered resampling)."""
    rng = random.Random(seed)
    n = len(values)
    point = sum(values) / n
    boots = []
    for _ in range(reps):
        boots.append(sum(values[rng.randrange(n)] for _ in range(n)) / n)
    boots.sort()
    return point, boots[int(0.025 * reps)], boots[int(0.975 * reps) - 1]
