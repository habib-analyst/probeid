# Kill-gate record — project #93 probeid

All gates evaluated in order. No gate was skipped, no bar moved after locking.

## G0 — harness (PASS)
Scripted MCP-style registry harness built first; 9/9 tests green
(`python3 -m pytest tests/ -q`) before any head-to-head measurement.
Deterministic, zero LLM, zero API spend, CPU only, stdlib only.
120 synthetic gold tools, 64-probe banks, squatter families, ProbeID
strict + gated choice, exact-match and description-router baselines.

## G1 — author-code recheck (PASS — no author code found)
- arXiv abs page for 2610.33633 (read live 2026-10-29) carries no code
  link (only generic arXivLabs toggles).
- The paper itself states code "will be released upon acceptance" — not
  released as of 2026-10-29 (App. T / data availability).
- GitHub API repo search "ProbeID": 1 hit, unrelated
  (karolpaczocha/ProbeID-merger, dataframe-merge template). Repo search
  "MCP-IdentityDrift": 0 hits.
- Exact-title / author-name web searches returned no author repository
  (only unrelated MCP-security tools).
- Proceeded with a clean-room harness; no author code reused.

## G2 — disease, pilot-calibrated and PREREG-locked (PASS)
Pilot (seed 0, n=30, calibration-only): ProbeID 1.000, BM25 0.133,
gap 0.867, 95% CI [0.733, 0.967]; exact ties ProbeID exactly.
Locked bars (PREREG.md): BM25 <= 0.30; ProbeID >= 0.85; gap >= 0.50
with CI lower bound > 0.
Head-to-head (seed 101, n=120 golds, k=8 squatters, m=12 probes,
strict choice, 480 rows):
- BM25 router hit@1: 0.083 (10/120) — bar 1 met (chance = 1/9 = 0.111).
- TF-IDF router hit@1: 0.125 (15/120) — second router also near chance.
- ProbeID strict-choice hit@1: 0.983 (118/120) — bar 2 met.
- Gap ProbeID minus BM25: 0.900, paired bootstrap 95% CI
  [0.833, 0.950] — bar 3 met.
- The 2 misses are the paper's own miss mechanism: small-phi drift with
  no drifted probe among the 12 sampled (0.7^12 = 1.4% per squatter).
G2 VERDICT: PASS.

## G3 — load-bearing (PASS)
Locked bar (PREREG.md): noise-regime ProbeID minus exact-match hit@1
>= 0.20 with paired bootstrap 95% CI lower bound > 0.
Head-to-head noise regime (seed 101, n=50 numeric golds, k=8, m=32):
- ProbeID bounded-distance hit@1: 1.000 (50/50).
- Exact-match hit@1: 0.360 (18/50).
- Gap: 0.640, paired bootstrap 95% CI [0.500, 0.780] — bar met.
Mechanism (pre-stated in PREREG): benign jitter inside the 0.05 tolerance
is invisible to bounded distance but a full mismatch for exact equality,
so under a stochastic gold exact equality's ranking is noise-dominated
while bounded distance still separates the gold from a 30%-drift squatter.
G3 VERDICT: PASS.

## Concession reproduced honestly (not a win for either side)
Deterministic regime: ProbeID 0.983 = exact-match 0.983, gap 0.000,
CI [0.000, 0.000] on all 120 cases. This is structural in this harness
(bounded distance 0 iff canonicalized responses equal iff exact 0, and
the gold sits at 0 under both), so it is reported as the paper's own
concession reproduced — simpler exact comparisons tie ProbeID on
deterministic tools — not as an empirical discovery. The demonstrated
advantage of probing over the trivial baseline lives entirely in the
noise regime (G3).

## Uncatchable cases (paper limitation, reproduced, not hidden)
Gate study (seed 101, 40 golds per cell, single-candidate Algorithm 1
gate, delta = 0.05, theory-set thresholds):
- Reachable replacements (full drift): equality refuses 40/40 from m=8;
  bounded refuses 0/40 at m=8, 40/40 at m=32 and m=64. Direction matches
  the paper's Table 1 (equality needs fewer probes than bounded);
  absolute budgets differ (paper: 64 vs 512) because margins differ —
  reported as a regime difference, not a reproduction of exact budgets.
- Small-margin replacements (near_twin, 1 differing bank probe):
  refusal 0.000-0.125 (equality), 0.000 (bounded) — small margins pass,
  as in the paper ("drift on one input in twenty passes").
- Twins (drift outside all bank probes): refusal 0.000 under BOTH
  comparisons at every budget — always pass. This is the paper's
  "two tools whose drift no bank probe reaches always pass", reproduced.
- Gold-alone controls: refusal 0/120 under both — no gold refused.
- Tainted-task analog (16 scripted tasks, single-candidate equality gate,
  m=32): 6/14 squatter tasks accepted (4 small-margin + 2 twin), 8/8
  reachable refused, 2/2 gold controls accepted. An ANALOG of the
  paper's 15 -> 9 of 16, not a reproduction of it (different gate setup).

## Determinism
Re-running seed 101 reproduced an identical results SHA-256:
0b2cfc5c00bd659a402441a408136a0fdb68d42d10754115cb0f722dd3f47358
(headtohead.jsonl == headtohead_rerun.jsonl).

## Honest caveats (carried into PAPER.md)
- All tools, descriptions, squatters and probes are synthetic; the
  measured effects are the mechanism's, not the paper's benchmark numbers
  (0.956, 15 -> 9, 64/512 probes), which remain context only.
- Strict-choice CIs in the deterministic regime are degenerate where
  outcomes coincide; the informative CIs are the gap intervals.
- The noise regime models a stochastic gold with jitter inside a fixed
  tolerance; real tool noise may exceed any fixed tolerance, in which
  case the bounded-distance advantage shrinks — stated as a limit.
- Probe coverage is the binding constraint throughout: twins and
  small-margin drift pass because no sampled probe reaches the
  difference, exactly as the paper warns ("verification depends on
  reference integrity, probe coverage, and response noise").
