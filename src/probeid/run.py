"""Experiment driver: pilot | headtohead | gate-study | summarize.

All randomness flows from one seed per mode; rerunning headtohead with the
same seed must reproduce byte-identical rows (determinism digest).
Usage: python3 -m probeid.run <mode> --seed N --out results/<file>.jsonl
"""

import argparse
import json
import random
import sys

from .canonical import bounded_distance, exact_distance
from .probes import build_bank, record
from .stats import paired_bootstrap_ci, rate_ci
from .tools import (build_golds, make_noisy_gold, make_squatter,
                    numeric_golds)
from .verify import (bm25_router, gated_choice, strict_choice, tfidf_router)

# Headline pool = separable squatter families only. near_twin (differs on
# exactly 1 of 64 bank probes) is a small-margin phenomenon: with m=12
# probes it is invisible ~81% of the time, which would cap headline hit@1
# far below the paper's 0.956 and conflate the two studies. The paper makes
# the same separation: headline golds enter only if some squatter is
# separable (App. T), while small margins are studied in the bank/gate
# rows of Table 1. near_twin therefore lives in the gate study only.
HEADLINE_KINDS = ["drift_full", "drift_half", "drift_small",
                  "field_drop", "input_partial"]


def _case_deterministic(gold, rng, k=8, m=12):
    """One headline case: gold + k squatters, fixed first-m bank probes."""
    bank = build_bank(gold, seed=rng.randrange(10 ** 9))
    probes = bank[:m]
    ref = record(gold, probes)
    squatters = []
    for _ in range(k):
        kind = rng.choice(HEADLINE_KINDS)
        squatters.append(make_squatter(kind, gold, rng, bank=bank))
    cands = [gold] + squatters
    cand_resps = [record(c, probes) for c in cands]
    out = {}
    pick = strict_choice(ref, cand_resps, bounded_distance, tol=0.05)
    out["probeid"] = 1 if pick == 0 else 0
    pick = strict_choice(ref, cand_resps, exact_distance)
    out["exact"] = 1 if pick == 0 else 0
    q = gold.description
    out["bm25"] = 1 if bm25_router(q, cands, rng) is gold else 0
    out["tfidf"] = 1 if tfidf_router(q, cands, rng) is gold else 0
    return out


def _case_noise(gold, rng, k=8, m=32):
    """Noise-regime case: jittered gold + noisy-drift squatters, m=32 draws."""
    noisy_gold = make_noisy_gold(gold, rng)
    bank = build_bank(gold, seed=rng.randrange(10 ** 9))
    probes = rng.sample(bank, m)
    ref = record(noisy_gold, probes)
    squatters = [make_squatter("noisy_drift", gold, rng, bank=bank)
                 for _ in range(k)]
    cands = [noisy_gold] + squatters
    cand_resps = [record(c, probes) for c in cands]
    out = {}
    pick = strict_choice(ref, cand_resps, bounded_distance, tol=0.05)
    out["probeid"] = 1 if pick == 0 else 0
    pick = strict_choice(ref, cand_resps, exact_distance)
    out["exact"] = 1 if pick == 0 else 0
    return out


def cmd_headtohead(seed, out_path, n_det=120, n_noise=50):
    rng = random.Random(seed)
    golds = build_golds()
    rows = []
    for gold in golds[:n_det]:
        res = _case_deterministic(gold, rng)
        for method, val in res.items():
            rows.append({"regime": "deterministic", "gold": gold.name,
                         "k": 8, "m": 12, "method": method, "correct": val})
    for gold in numeric_golds(golds)[:n_noise]:
        res = _case_noise(gold, rng)
        for method, val in res.items():
            rows.append({"regime": "noise", "gold": gold.name,
                         "k": 8, "m": 32, "method": method, "correct": val})
    with open(out_path, "w") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")
    return rows


def cmd_gate_study(seed, out_path):
    """Gold-absent single-gate refusal curves + twin limitation + tainted tasks."""
    rng = random.Random(seed)
    golds = build_golds()
    rows = []
    for m in (8, 32, 64):
        for kind, label in (("drift_full", "reachable"),
                            ("near_twin", "small_margin"),
                            ("twin", "twin")):
            for gold in golds[:40]:
                bank = build_bank(gold, seed=rng.randrange(10 ** 9))
                probes = rng.sample(bank, m) if m <= len(bank) else bank
                ref = record(gold, probes)
                sq = make_squatter(kind, gold, rng, bank=bank)
                sq_resps = record(sq, probes)
                for method, fn, kw in (("equality", exact_distance, {}),
                                       ("bounded", bounded_distance,
                                        {"tol": 0.05})):
                    pick = gated_choice(ref, [sq_resps], fn, m, **kw)
                    rows.append({"study": "gold_absent", "m": m,
                                 "kind": label, "gold": gold.name,
                                 "method": method,
                                 "refused": 0 if pick == 0 else 1})
        # gold-alone controls: gate must accept the gold itself
        for gold in golds[:40]:
            bank = build_bank(gold, seed=rng.randrange(10 ** 9))
            probes = rng.sample(bank, 32)
            ref = record(gold, probes)
            fresh = record(gold, probes)
            for method, fn, kw in (("equality", exact_distance, {}),
                                   ("bounded", bounded_distance,
                                    {"tol": 0.05})):
                pick = gated_choice(ref, [fresh], fn, 32, **kw)
                rows.append({"study": "gold_alone", "m": 32, "kind": "gold",
                             "gold": gold.name, "method": method,
                             "refused": 0 if pick == 0 else 1})
    # Tainted-task analog: 16 scripted agent tasks, single-candidate gate
    # (equality, m=32). Tainted = gate accepts a squatter as the task tool.
    comp = ([("reachable", "drift_full")] * 8
            + [("small_margin", "near_twin")] * 4
            + [("twin", "twin")] * 2
            + [("gold", None)] * 2)
    for i, (label, kind) in enumerate(comp):
        gold = golds[(seed + i * 7) % len(golds)]
        bank = build_bank(gold, seed=rng.randrange(10 ** 9))
        probes = rng.sample(bank, 32)
        ref = record(gold, probes)
        cand = gold if kind is None else make_squatter(kind, gold, rng,
                                                       bank=bank)
        pick = gated_choice(ref, [record(cand, probes)], exact_distance, 32)
        rows.append({"study": "tainted_task", "task": i, "kind": label,
                     "gold": gold.name, "method": "equality",
                     "accepted": 1 if pick == 0 else 0})
    with open(out_path, "w") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")
    return rows


def _rate(rows, **filt):
    vals = [r["correct"] for r in rows
            if all(r.get(k) == v for k, v in filt.items())]
    return sum(vals) / len(vals), len(vals), vals


def cmd_summarize(path):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    det = [r for r in rows if r["regime"] == "deterministic"]
    noi = [r for r in rows if r["regime"] == "noise"]
    out = {}
    for name, subset in (("deterministic", det), ("noise", noi)):
        methods = {}
        for method in sorted({r["method"] for r in subset}):
            rate, n, _ = _rate(subset, method=method)
            methods[method] = {"rate": rate, "n": n}
        out[name] = methods
    # Paired gaps (per-gold pairing).
    def paired(subset, a, b):
        golds = sorted({r["gold"] for r in subset})
        av, bv = [], []
        for g in golds:
            av.append(next(r["correct"] for r in subset
                          if r["gold"] == g and r["method"] == a))
            bv.append(next(r["correct"] for r in subset
                          if r["gold"] == g and r["method"] == b))
        return paired_bootstrap_ci(av, bv)
    out["deterministic"]["gap_probeid_minus_bm25"] = paired(det, "probeid", "bm25")
    out["deterministic"]["gap_probeid_minus_exact"] = paired(det, "probeid", "exact")
    out["noise"]["gap_probeid_minus_exact"] = paired(noi, "probeid", "exact")
    print(json.dumps(out, indent=2, default=str))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["headtohead", "gate-study", "summarize"])
    ap.add_argument("--seed", type=int, default=101)
    ap.add_argument("--out", default=None)
    ap.add_argument("--in", dest="inp", default=None)
    ap.add_argument("--n-det", type=int, default=120)
    ap.add_argument("--n-noise", type=int, default=50)
    args = ap.parse_args(argv)
    if args.mode == "headtohead":
        rows = cmd_headtohead(args.seed, args.out, args.n_det, args.n_noise)
        print(f"wrote {len(rows)} rows to {args.out}")
    elif args.mode == "gate-study":
        rows = cmd_gate_study(args.seed, args.out)
        print(f"wrote {len(rows)} rows to {args.out}")
    else:
        cmd_summarize(args.inp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
