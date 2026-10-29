# probeid — open replication of ProbeID (arXiv 2610.33633)

Agents pick tools by copyable descriptions — but a description can't prove
which implementation actually runs. ProbeID (Chen et al., 2026) verifies a
tool by its **behaviour**: it probes each candidate on schema-valid inputs
and compares canonicalized responses against a trusted reference recorded
at admission, abstaining when no candidate matches or the decision is
ambiguous.

This repo is a clean-room, scripted replication of that mechanism — no
author code (the paper states its code "will be released upon acceptance"
and none exists as of 2026-10-29), zero LLM, zero API spend, CPU only.

## What we measured

| Regime | ProbeID | Best trivial baseline | Gap (95% CI) |
|---|---|---|---|
| Deterministic, k=8, m=12, n=120 | hit@1 **0.983** | description router 0.083 | 0.900 [0.833, 0.950] |
| Deterministic, same | 0.983 | exact-match 0.983 | 0.000 [0.000, 0.000] — the paper's concession, reproduced |
| Value-noise, k=8, m=32, n=50 | hit@1 **1.000** | exact-match 0.360 | 0.640 [0.500, 0.780] |

Gate study (gold absent, theory-set thresholds): equality refuses
reachable replacements from m=8 probes, bounded distance from m=32;
small-margin drift (1 differing bank probe) passes under both; twins
whose drift no bank probe reaches **always pass** — the paper's stated
limitation, reproduced honestly.

## Run it

```bash
python3 -m pytest tests/ -q            # G0: 9/9 tests green
PYTHONPATH=src python3 -m probeid.run headtohead --seed 101 \
    --out results/headtohead.jsonl     # 580 rows, deterministic
PYTHONPATH=src python3 -m probeid.run gate-study --seed 101 \
    --out results/gate_study.jsonl
PYTHONPATH=src python3 -m probeid.run summarize --in results/headtohead.jsonl
```

Re-running seed 101 reproduces byte-identical results:
SHA-256 `0b2cfc5c00bd659a402441a408136a0fdb68d42d10754115cb0f722dd3f47358`.

## Layout

- `src/probeid/` — `tools.py` (120 golds + squatter factories),
  `probes.py` (bank generation), `canonical.py` (canonicalizer + distances),
  `verify.py` (ProbeID strict/gated choice + router baselines),
  `stats.py` (paired bootstrap), `run.py` (driver).
- `tests/` — G0 harness tests.
- `results/` — `headtohead.jsonl`, `headtohead_rerun.jsonl`,
  `gate_study.jsonl`, `pilot.jsonl` (calibration only).
- `PREREG.md` — bars locked before the head-to-head. `KILLGATE.md` —
  per-gate verdicts. `PAPER.md` — full writeup. `LINKEDIN_DRAFT.md` —
  draft only, never queued for posting.

## Scope limits (read before citing)

All tools, descriptions, squatters and probes are synthetic. The paper's
benchmark figures (hit@1 0.956 on cached MCP-IdentityDrift cases, tainted
tasks 15 → 9 of 16) are context only and are NOT claimed as reproduced.
The noise regime assumes benign jitter inside a fixed 0.05 tolerance;
real tool noise may exceed it. Probe coverage is the binding constraint:
anything no sampled probe reaches is uncatchable, by construction.

## License

MIT. The target paper is by Chen, Zhang, He, Lv, Huang & Huang (2026);
this is an independent reimplementation of the mechanism described in
its abstract and §§3–5, not a derivative of author code.
