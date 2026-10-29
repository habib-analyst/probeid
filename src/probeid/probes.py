"""Schema-driven probe-bank generation (paper §3.2, M1).

Type-aware enumeration over boundary values, enums and required/optional
fields. Deterministic per gold: a seeded shuffle of the family's value pool,
cycled to bank size B. Bank support is what near_twin/twin target.
"""

import random

from .tools import INT_POOL, FLOAT_POOL, STR_POOL, LIST_POOL, DATE_POOL

_POOLS = {"int": INT_POOL, "float": FLOAT_POOL, "str": STR_POOL,
          "list": LIST_POOL, "date": DATE_POOL}


def build_bank(tool, seed, size=64):
    """Return a list of `size` probe param-dicts for `tool`."""
    rng = random.Random(seed)
    params = list(tool.schema.items())
    bank = []
    for i in range(size):
        probe = {}
        for name, typ in params:
            pool = _POOLS[typ]
            probe[name] = pool[(i + rng.randrange(len(pool))) % len(pool)]
        bank.append(probe)
    return bank


def record(tool, bank):
    """Record canonicalized trusted responses for a probe bank."""
    return [tool.call(p) for p in bank]
