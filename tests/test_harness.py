"""G0 harness tests — all must pass before any measurement."""

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from probeid.canonical import (bounded_distance, canonicalize,
                               exact_distance)
from probeid.probes import build_bank, record
from probeid.tools import (build_golds, make_noisy_gold, make_squatter)
from probeid.verify import (bm25_router, gated_choice, strict_choice)


def test_canonicalizer_drops_volatile_and_sorts():
    a = {"b": 1, "timestamp": "x", "a": {"z": 2, "y": 3}}
    b = {"a": {"y": 3, "z": 2}, "b": 1, "request_id": "q"}
    assert canonicalize(a) == canonicalize(b)


def test_bounded_distance_grades_partial_corruption():
    gold = {"result": 5, "unit": "count", "note": "sum"}
    dropped = {"result": 5, "unit": "count"}
    assert bounded_distance(gold, dropped) == 1 / 3
    assert exact_distance(gold, dropped) == 1.0
    assert bounded_distance(gold, gold) == 0.0


def test_numeric_tolerance():
    a = {"result": 10.02, "unit": "m", "note": "x"}
    b = {"result": 10.0, "unit": "m", "note": "x"}
    assert bounded_distance(a, b, tol=0.05) == 0.0
    assert exact_distance(a, b) == 1.0


def test_gold_count_and_families():
    golds = build_golds()
    assert len(golds) == 120
    assert len({g.name for g in golds}) == 120


def test_twin_uncatchable_on_bank():
    rng = random.Random(7)
    gold = build_golds()[0]
    bank = build_bank(gold, seed=99)
    twin = make_squatter("twin", gold, rng, bank=bank)
    ref = record(gold, bank)
    got = record(twin, bank)
    assert all(exact_distance(r, c) == 0.0 for r, c in zip(ref, got))
    # ...but it DOES differ outside bank support
    outside = [{"x": 20000}]
    assert exact_distance(gold.call(outside[0]), twin.call(outside[0])) == 1.0


def test_router_ties_under_copied_descriptions():
    rng = random.Random(3)
    gold = build_golds()[0]
    bank = build_bank(gold, seed=5)
    sq = make_squatter("drift_full", gold, rng, bank=bank)
    assert sq.description == gold.description
    picks = {bm25_router(gold.description, [gold, sq], rng) for _ in range(20)}
    assert len(picks) == 2  # tie broken randomly, not always the gold


def test_strict_choice_tie_is_miss():
    ref = [{"result": 1, "unit": "c", "note": "n"}]
    cands = [[{"result": 1, "unit": "c", "note": "n"}],
             [{"result": 1, "unit": "c", "note": "n"}]]
    assert strict_choice(ref, cands, exact_distance) is None


def test_single_gate_accepts_gold_refuses_full_drift():
    rng = random.Random(11)
    gold = build_golds()[1]
    bank = build_bank(gold, seed=13)
    probes = bank[:32]
    ref = record(gold, probes)
    sq = make_squatter("drift_full", gold, rng, bank=bank)
    assert gated_choice(ref, [record(gold, probes)], exact_distance, 32) == 0
    assert gated_choice(ref, [record(sq, probes)], exact_distance, 32) is None


def test_noisy_gold_self_distance_bounded_zero_exact_positive():
    rng = random.Random(21)
    gold = [g for g in build_golds() if g.name.startswith("add_")][0]
    noisy = make_noisy_gold(gold, rng)
    bank = build_bank(gold, seed=23)
    probes = bank[:32]
    ref = record(noisy, probes)
    fresh = record(noisy, probes)
    bd = sum(bounded_distance(r, c, tol=0.05) for r, c in zip(ref, fresh)) / 32
    ed = sum(exact_distance(r, c) for r, c in zip(ref, fresh)) / 32
    assert bd == 0.0
    assert ed > 0.3
