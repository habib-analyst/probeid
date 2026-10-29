"""Canonicalization + bounded behavioural distance (paper §3.2, M2/M3).

Canonicalizer: drop named volatile fields, sort mapping keys recursively.
Bounded distance d_Y in [0, 1]: fraction of differing response-tree leaves,
with a numeric tolerance (default 0.05) so benign value jitter inside the
tolerance counts as agreement. Exact-match distance: 0 iff canonicalized
responses are fully equal, else 1 (per probe), averaged over probes.
"""

import json
import math

VOLATILE = {"timestamp", "request_id", "trace_id"}


def canonicalize(value):
    if isinstance(value, dict):
        return {k: canonicalize(v) for k, v in sorted(value.items())
                if k not in VOLATILE}
    if isinstance(value, list):
        return [canonicalize(v) for v in value]
    return value


def _leaves(value, prefix=""):
    """Yield (path, leaf) pairs for a canonicalized response tree."""
    if isinstance(value, dict):
        if not value:
            yield (prefix, "<empty>")
            return
        for k, v in value.items():
            yield from _leaves(v, f"{prefix}.{k}" if prefix else k)
    elif isinstance(value, list):
        if not value:
            yield (prefix, "<empty>")
            return
        for i, v in enumerate(value):
            yield from _leaves(v, f"{prefix}[{i}]")
    else:
        yield (prefix, value)


def _leaf_equal(a, b, tol):
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b or a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if isinstance(a, float) or isinstance(b, float):
            return abs(float(a) - float(b)) <= tol
        return a == b
    return a == b


def bounded_distance(resp_a, resp_b, tol=0.05):
    """Mean leaf disagreement in [0, 1]; missing leaf counts as differing."""
    ca, cb = canonicalize(resp_a), canonicalize(resp_b)
    la = dict(_leaves(ca))
    lb = dict(_leaves(cb))
    keys = set(la) | set(lb)
    if not keys:
        return 0.0
    diff = sum(0 if (k in la and k in lb and _leaf_equal(la[k], lb[k], tol))
               else 1 for k in keys)
    return diff / len(keys)


def exact_distance(resp_a, resp_b):
    """0 iff canonicalized responses are fully equal, else 1."""
    return 0.0 if canonicalize(resp_a) == canonicalize(resp_b) else 1.0


def mean_distance(fn, ref_resps, cand_resps, **kw):
    """Empirical behavioural distance over shared probes (paper Eq. 1)."""
    assert len(ref_resps) == len(cand_resps)
    return sum(fn(r, c, **kw) if kw else fn(r, c)
               for r, c in zip(ref_resps, cand_resps)) / len(ref_resps)


def theory_epsilon(n_candidates, m, delta=0.05):
    """epsilon = sqrt(log(2(n+k)/delta) / (2m)) (paper §4, Theorem 2)."""
    return math.sqrt(math.log(2 * n_candidates / delta) / (2 * m))
