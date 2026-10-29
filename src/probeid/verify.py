"""Verifiers and routers (paper §3.2 Algorithm 1 + baselines).

- probeid_strict: nearest-fingerprint rule; a tie for first scores as a
  miss (paper's strict choice with adversarial tie-breaking).
- probeid_gated: Algorithm 1 with distance gate tau_hi and gap gate
  gamma_min = 2*epsilon; single candidate faces only the distance gate.
- exact_*: same rules with the exact-match distance.
- bm25_router / tfidf_router: description routers. Squatters copy the gold
  description verbatim, so all candidates tie on score; ties break by a
  seeded random draw (expected hit@1 = 1/(k+1), i.e. chance).
"""

import math
import random
import re

from .canonical import bounded_distance, exact_distance, theory_epsilon

_TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(text):
    return _TOKEN.findall(text.lower())


def _router_pick(query_text, candidates, rng):
    """Score = token overlap with the description; seeded random tie-break."""
    qtok = set(_tokens(query_text))
    scored = []
    for cand in candidates:
        dtok = set(_tokens(cand.description))
        scored.append((len(qtok & dtok), cand))
    best = max(s for s, _ in scored)
    tied = [c for s, c in scored if s == best]
    return rng.choice(tied)


def bm25_router(query_text, candidates, rng):
    # Lexical overlap router (BM25-style: shared-token count, no IDF needed
    # because copied descriptions make every candidate score identically).
    return _router_pick(query_text, candidates, rng)


def tfidf_router(query_text, candidates, rng):
    # TF-IDF cosine over description tokens; identical descriptions tie.
    qtok = _tokens(query_text)
    qset = set(qtok)
    scored = []
    for cand in candidates:
        dtok = _tokens(cand.description)
        inter = len(qset & set(dtok))
        denom = math.sqrt(len(qset) * len(dtok)) or 1.0
        scored.append((inter / denom, cand))
    best = max(s for s, _ in scored)
    tied = [c for s, c in scored if s == best]
    return rng.choice(tied)


def strict_choice(ref_resps, cand_resps_list, dist_fn, **kw):
    """Return index of the argmin distance, or None on a tie for first."""
    ds = [sum(dist_fn(r, c, **kw) if kw else dist_fn(r, c)
              for r, c in zip(ref_resps, cr)) / len(ref_resps)
          for cr in cand_resps_list]
    best = min(ds)
    winners = [i for i, d in enumerate(ds) if d == best]
    return winners[0] if len(winners) == 1 else None


def gated_choice(ref_resps, cand_resps_list, dist_fn, m, delta=0.05,
                 tau_hi=None, **dist_kw):
    """Algorithm 1. Returns index, or None for abstain.

    tau_hi defaults to epsilon above a zero self-distance (deterministic
    golds); callers with noisy golds pass tau_hi = self_dist + epsilon.
    """
    n = len(cand_resps_list)
    ds = [sum(dist_fn(r, c, **dist_kw) if dist_kw else dist_fn(r, c)
              for r, c in zip(ref_resps, cr)) / len(ref_resps)
          for cr in cand_resps_list]
    eps = theory_epsilon(max(n, 2), m, delta)
    tau = eps if tau_hi is None else tau_hi
    order = sorted(range(n), key=lambda i: ds[i])
    d1 = ds[order[0]]
    if n == 1:
        return order[0] if d1 <= tau else None
    d2 = ds[order[1]]
    gamma_min = 2 * eps
    if d1 > tau or (d2 - d1) < gamma_min:
        return None
    return order[0]
