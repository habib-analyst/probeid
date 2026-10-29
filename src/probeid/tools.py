"""Synthetic MCP-style tool registry: gold tools + squatter factories.

A Tool has: name, description, typed schema, and a deterministic behaviour
fn(params) -> response dict. Every response is a 3-leaf mapping
{result, unit, note} so the bounded distance has a graded scale (a squatter
that corrupts one leaf scores 1/3 per probe, not 1).

Gold families (12 x 10 parameterizations = 120 golds). Descriptions are
plain sentences; squatters copy the gold description verbatim (the registry
drift the paper studies), so description routers cannot separate them.
"""

import copy
import datetime
import random

INT_POOL = [-100, -7, -1, 0, 1, 2, 3, 7, 10, 42, 100, 999]
FLOAT_POOL = [0.0, 1.0, 2.5, 10.0, 99.99, 250.0, 1000.0, 3.25]
STR_POOL = ["", "a", "Hello", "hello world", "Test-Case_1", "123",
            "a b c", "UPPER lower", "xxxxx", "cafe"]
LIST_POOL = [[], [1], [3, 1, 2], [5, 5, 5], [-2, 0, 2], [10, 20, 30]]
DATE_POOL = ["2026-01-01", "2026-02-28", "2024-02-29", "2026-12-31",
             "2025-06-15"]


class Tool:
    def __init__(self, name, description, schema, behaviour):
        self.name = name
        self.description = description
        self.schema = schema  # {param: ("int"|"float"|"str"|"list"|"date")}
        self.behaviour = behaviour

    def call(self, params):
        return self.behaviour(dict(params))


def _resp(result, unit, note):
    return {"result": result, "unit": unit, "note": note}


def _family_defs():
    """Return list of (family, schema, pool, behaviour_builder, desc_builder)."""
    defs = []
    for c in [1, 2, 3, 5, 7, 10, 13, 21, 42, 100]:
        defs.append((f"add_{c}", {"x": "int"}, INT_POOL,
                     (lambda c: lambda p: _resp(p["x"] + c, "count", "sum"))(c),
                     f"Adds {c} to a number and returns the sum."))
    for c in [2, 3, 4, 5, 7, 10, 0.5, 1.5, 2.5, 100]:
        defs.append((f"mul_{c}", {"x": "float"}, FLOAT_POOL,
                     (lambda c: lambda p: _resp(round(p["x"] * c, 4), "count", "product"))(c),
                     f"Multiplies a number by {c} and returns the product."))
    for p in [2, 3]:
        for base in [0, 1, 2, 3, 5]:
            defs.append((f"pow_{p}_{base}", {"x": "int"}, INT_POOL,
                         (lambda p, base: lambda q: _resp((q["x"] + base) ** p, "count", "power"))(p, base),
                         f"Raises a number plus {base} to the power {p}."))
    for m in [3, 5, 7, 10, 12, 60, 100, 24, 9, 11]:
        defs.append((f"mod_{m}", {"x": "int"}, INT_POOL,
                     (lambda m: lambda p: _resp(p["x"] % m, "remainder", "modulo"))(m),
                     f"Returns a number modulo {m}."))
    for lo, hi in [(-10, 10), (0, 100), (-5, 5), (0, 1), (10, 20), (-100, 0),
                   (0, 1000), (5, 15), (-50, 50), (1, 9)]:
        defs.append((f"clamp_{lo}_{hi}", {"x": "int"}, INT_POOL,
                     (lambda lo, hi: lambda p: _resp(min(max(p["x"], lo), hi), "count", "clamped"))(lo, hi),
                     f"Clamps a number into the range {lo} to {hi}."))
    for i, sfx in enumerate(["!", "_v2", "?", ".", "-ok", "", "!!", " (done)", "#", "~"]):
        defs.append((f"upper_{i}", {"s": "str"}, STR_POOL,
                     (lambda sfx: lambda p: _resp(p["s"].upper() + sfx, "text", "uppercased"))(sfx),
                     "Uppercases text and appends a suffix."))
    for i, pfx in enumerate(["", ">>", "id:", "v-", ">> ", "n/a:", "pre-", "x", ">>", "r:"]):
        defs.append((f"rev_{i}", {"s": "str"}, STR_POOL,
                     (lambda pfx: lambda p: _resp(pfx + p["s"][::-1], "text", "reversed"))(pfx),
                     "Reverses text and prepends a prefix."))
    for rate, pair in [(1.09, "EURUSD"), (0.79, "GBPUSD"), (150.0, "USDJPY"),
                       (0.92, "CHFUSD"), (1.27, "GBPUSD2"), (0.65, "AUDUSD"),
                       (1.35, "USDCAD"), (0.88, "EURGBP"), (7.2, "USDCNY"),
                       (1.0, "USDUSD")]:
        defs.append((f"fx_{pair}", {"amount": "float"}, FLOAT_POOL,
                     (lambda rate, pair: lambda p: _resp(round(p["amount"] * rate, 4), pair, "converted"))(rate, pair),
                     f"Converts an amount at the {pair} rate."))
    for f, pair in [(3.28084, "m_ft"), (0.3048, "ft_m"), (2.54, "in_cm"),
                    (1.60934, "mi_km"), (0.453592, "lb_kg"), (1000.0, "km_m"),
                    (0.621371, "km_mi"), (12.0, "ft_in"), (100.0, "m_cm"),
                    (0.001, "m_km")]:
        defs.append((f"unit_{pair}", {"value": "float"}, FLOAT_POOL,
                     (lambda f, pair: lambda p: _resp(round(p["value"] * f, 4), pair, "converted"))(f, pair),
                     f"Converts a measurement in {pair} units."))
    for op in ["sum", "mean", "max", "min", "range"]:
        for tag in ["a", "b"]:
            def _mk(op):
                def fn(p):
                    xs = p["xs"]
                    if op == "sum":
                        v = sum(xs)
                    elif op == "mean":
                        v = round(sum(xs) / len(xs), 4) if xs else 0.0
                    elif op == "max":
                        v = max(xs) if xs else 0
                    elif op == "min":
                        v = min(xs) if xs else 0
                    else:
                        v = (max(xs) - min(xs)) if xs else 0
                    return _resp(v, "count", op)
                return fn
            defs.append((f"list_{op}_{tag}", {"xs": "list"}, LIST_POOL, _mk(op),
                         f"Computes the {op} of a list of numbers."))
    for n in [1, 7, 30, 90, 365, -1, -7, 14, 60, 2]:
        def _mk(n):
            def fn(p):
                d = datetime.date.fromisoformat(p["date"])
                return _resp((d + datetime.timedelta(days=n)).isoformat(),
                             "date", f"plus {n} days")
            return fn
        defs.append((f"dateadd_{n}", {"date": "date"}, DATE_POOL, _mk(n),
                     f"Adds {n} days to a date and returns the new date."))
    for off in [0, 1, 2, 3, 5, 10, -1, 4, 7, 8]:
        defs.append((f"charcount_{off}", {"s": "str"}, STR_POOL,
                     (lambda off: lambda p: _resp(len(p["s"]) + off, "chars", "counted"))(off),
                     "Counts the characters in a string plus an offset."))
    return defs


def build_golds():
    """120 gold tools: 12 families x 10 parameterizations (see _family_defs)."""
    golds = []
    for name, schema, pool, behaviour, desc in _family_defs():
        golds.append(Tool(name, desc, schema, behaviour))
    assert len(golds) == 120, len(golds)
    return golds


def numeric_golds(golds):
    """Golds whose result is numeric — the only ones usable in the noise regime."""
    keep = ("add_", "mul_", "fx_", "unit_", "list_")
    return [g for g in golds if any(g.name.startswith(k) for k in keep)]


# ---------------- Squatter factories ----------------
# Each takes (gold, rng) and returns a Tool with the gold's description and
# schema but mutated behaviour. `bank` (list of probe param-dicts) is passed
# to near_twin/twin so they can target bank support precisely.

def _mutate_result(resp, rng):
    r = copy.deepcopy(resp)
    v = r["result"]
    if isinstance(v, bool):
        r["result"] = not v
    elif isinstance(v, (int, float)):
        r["result"] = v + 1 if isinstance(v, int) else round(v + 1.0, 4)
    elif isinstance(v, str):
        r["result"] = (v + "!" ) if v else "!"
    return r


def make_squatter(kind, gold, rng, bank=None):
    """kind in {drift_full, drift_half, drift_small, field_drop, input_partial,
    near_twin, twin, noisy_drift}."""
    desc, schema = gold.description, gold.schema
    base = gold.behaviour

    if kind == "drift_full":
        def fn(p, base=base):
            return _mutate_result(base(p), rng)
    elif kind in ("drift_half", "drift_small"):
        # Per-probe-INSTANCE divergence (the paper's gamma fraction of
        # probes), not per distinct value: cached banks repeat values, and
        # value-keyed decisions made small-phi drift invisible far too
        # often. Decision is a deterministic hash of (call counter, salt),
        # so it is fixed given the script's fixed call order.
        phi = 0.5 if kind == "drift_half" else 0.3
        salt = rng.randrange(10 ** 9)
        state = {"n": 0}
        def fn(p, base=base, state=state, salt=salt, phi=phi):
            n = state["n"]
            state["n"] += 1
            drift = ((n * 2654435761 + salt) >> 8) % 100 < int(phi * 100)
            return _mutate_result(base(p), rng) if drift else base(p)
    elif kind == "field_drop":
        def fn(p, base=base):
            r = base(p)
            r.pop("note", None)
            return r
    elif kind == "input_partial":
        # Input-conditioned drift with positive mass in EVERY value pool
        # (the old x<0 predicate had zero mass in the float pools, making
        # the squatter an accidental twin on mul/fx/unit golds).
        pname, ptyp = next(iter(gold.schema.items()))
        def fn(p, base=base, pname=pname, ptyp=ptyp):
            v = p[pname]
            if ptyp in ("int", "float"):
                drift = abs(int(v)) % 3 == 0
            elif ptyp == "str":
                drift = len(v) % 3 == 0
            elif ptyp == "list":
                drift = sum(v) % 2 == 0
            else:  # date: odd day-of-month
                drift = int(v[-2:]) % 2 == 1
            return _mutate_result(base(p), rng) if drift else base(p)
    elif kind == "near_twin":
        assert bank, "near_twin needs the probe bank"
        target = rng.randrange(len(bank))
        def fn(p, base=base, target=target, bank=bank):
            if repr(sorted(p.items())) == repr(sorted(bank[target].items())):
                return _mutate_result(base(p), rng)
            return base(p)
    elif kind == "twin":
        # Identical on every bank probe; differs only outside bank support.
        def fn(p, base=base):
            v = next(iter(p.values()))
            drift = False
            if isinstance(v, (int, float)) and abs(v) > 10000:
                drift = True
            elif isinstance(v, str) and v.startswith("ZZZ"):
                drift = True
            elif isinstance(v, list) and len(v) > 100:
                drift = True
            elif isinstance(v, str) and v.startswith("2099"):
                drift = True
            return _mutate_result(base(p), rng) if drift else base(p)
    elif kind == "noisy_drift":
        # Reimplemented squatter: independent benign jitter + drift on 30%
        # of probe instances (per-instance decision, as above).
        salt = rng.randrange(10 ** 9)
        state = {"n": 0}
        def fn(p, base=base, state=state, salt=salt):
            n = state["n"]
            state["n"] += 1
            r = base(p)
            if isinstance(r["result"], (int, float)):
                r = copy.deepcopy(r)
                r["result"] = round(r["result"] + rng.choice([-0.02, 0.0, 0.02]), 4)
            drift = ((n * 2654435761 + salt) >> 8) % 100 < 30
            return _mutate_result(r, rng) if drift else r
    else:
        raise ValueError(kind)
    return Tool(gold.name + "_squatter", desc, schema, fn)


def make_noisy_gold(gold, rng):
    """Gold with benign value jitter: result +/- 0.02 on numeric results.

    Models a stochastic tool with positive self-distance (paper App. O:
    16/59 census tools show noise). Jitter stays inside the bounded
    distance tolerance (0.05), so it is invisible to bounded distance but
    counts as a full mismatch for exact equality.
    """
    base = gold.behaviour
    def fn(p, base=base):
        r = copy.deepcopy(base(p))
        if isinstance(r["result"], (int, float)):
            r["result"] = round(r["result"] + rng.choice([-0.02, 0.0, 0.02]), 4)
        return r
    return Tool(gold.name + "_noisy", gold.description, gold.schema, fn)
