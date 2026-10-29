# Preregistration — ProbeID mechanism replication (project #93)

Locked: 2026-10-29 (after pilot seed 0, n=30 deterministic + n=20 noise;
pilot seeds are calibration-only and never count toward the head-to-head).

## Target paper
arXiv 2610.33633, Chen, Zhang, He, Lv, Huang, Huang, "ProbeID: Verifying
MCP Tool Identity for LLM Agents under Registry Drift" (submitted 24 Oct
2026). Abstract read live 2026-10-29. The paper's figures (hit@1 0.956;
tainted tasks 15 -> 9 of 16; refusal from 64/512 probes) are CONTEXT ONLY
and are never presented as reproduced claims: this replication measures a
scripted, synthetic mechanism, not the paper's cached MCP-IdentityDrift
benchmark or agent study.

## Author-code recheck (Gate 1) — PASS, no author code
- arXiv abs page carries no code link (only generic arXivLabs toggles).
- The paper itself states (App. T / data availability): "Code, derived
  data and the full raw response corpus will be released upon acceptance"
  — i.e. NOT released as of 2026-10-29.
- GitHub API repo search "ProbeID": 1 hit, unrelated
  (karolpaczocha/ProbeID-merger, a dataframe-merge template).
  Repo search "MCP-IdentityDrift": 0 hits.
- Exact-title / author-name web searches returned no author repository
  (only unrelated MCP-security tools: sniffmcp, mcp-probe, mcp-guard,
  mcp-fingerprints — none is the authors' implementation).
- Verdict: NO author code found. Clean-room harness proceeds.

## Harness (Gate 0, tests green 9/9 before any measurement)
- 120 synthetic gold tools (12 families x 10 parameterizations) with typed
  schemas; every response is a 3-leaf mapping {result, unit, note} so the
  bounded distance has a graded scale.
- Probe bank: B=64 schema-valid probes per gold (type-aware enumeration
  over boundary values); headline uses the first m=12 (fixed cache-order,
  as in the paper's headline); noise/gate studies draw m at random.
- Squatters copy the gold description verbatim (registry drift) and mutate
  behaviour: drift_full / drift_half (phi=0.5) / drift_small (phi=0.3) /
  field_drop / input_partial (input-conditioned drift) / near_twin
  (differs on exactly 1 bank probe) / twin (identical on all bank probes,
  differs only outside bank support) / noisy_drift (noise regime only).
- Verifiers: ProbeID strict choice (nearest fingerprint, tie = miss) and
  Algorithm 1 gated choice (tau_hi, gamma_min = 2*epsilon, delta = 0.05);
  baselines: exact-match distance, BM25-style lexical router, TF-IDF
  cosine router (copied descriptions make all candidates tie; ties break
  by seeded random draw, expected hit@1 = 1/(k+1) = chance).
- Canonicalizer drops volatile fields and sorts keys. Bounded distance =
  fraction of differing response-tree leaves, numeric tolerance 0.05.
- All scripted, seeded RNG, stdlib only, zero LLM, zero API spend, CPU.

## Pilot results (calibration only)
- Pilot seed 0: deterministic (n=30, k=8, m=12) — ProbeID 1.000, BM25
  0.133, TF-IDF 0.100, gap ProbeID-BM25 0.867, 95% CI [0.733, 0.967];
  ProbeID minus exact = 0.000 exactly on every case.
- Pilot seed 0: noise regime (n=20, k=8, m=32) — ProbeID 1.000, exact
  0.350, gap 0.650, 95% CI [0.450, 0.850].
- Pilot gate study (seed 0): equality refuses reachable replacements
  40/40 from m=8; bounded from m=32 (0/40 at m=8, 40/40 at m=32 and m=64);
  small-margin (near_twin) refusal 0.05-0.10 (equality) / 0.000 (bounded);
  twin refusal 0.000 under both; gold-alone refusal 0/120. Tainted-task
  analog: 6/14 squatter tasks accepted (4 small-margin + 2 twin),
  8/8 reachable refused, 2/2 gold controls accepted.
- Two pilot-driven design fixes (both BEFORE locking, both documented):
  (1) near_twin removed from the headline squatter pool — with m=12 it is
  invisible ~81% of the time and would cap headline hit@1; the paper
  separates the same way (headline golds enter only if some squatter is
  separable; small margins live in the bank/gate rows). near_twin stays in
  the gate study. (2) drift decisions changed from per-distinct-value to
  per-probe-instance (deterministic hash of call counter + salt), because
  cached banks repeat values and value-keyed decisions made small-phi
  drift invisible far too often; input_partial stays value-conditioned
  (its coverage-dependence is the point) with predicates given positive
  mass in every pool (old x<0 predicate had zero mass in float pools).

## Locked head-to-head protocol
- Fresh seed, never the pilot seed: seed 101. Deterministic: n=120 golds,
  k=8, m=12, strict choice. Noise: n=50 numeric golds, k=8, m=32, strict
  choice. Gate study: seed 101, 40 golds per cell, m in {8, 32, 64}.
- Metrics: strict-choice hit@1; paired bootstrap 95% CIs (10,000 reps,
  gold-clustered, paired by gold) for all headline gaps.
- Determinism check: re-running seed 101 must reproduce an identical
  results-file SHA-256.

## Locked Gate 2 (disease) bars — ALL must hold
1. BM25 router hit@1 <= 0.30 (chance = 1/9 = 0.111; pilot 0.133).
2. ProbeID strict-choice hit@1 >= 0.85 in the deterministic regime
   (pilot 1.000; paper context 0.956).
3. Gap ProbeID minus BM25 >= 0.50 with paired bootstrap 95% CI lower
   bound > 0 (pilot 0.867 [0.733, 0.967]).
If any bar fails: KILL on scope, no bar-moving, no re-tuning.

## Locked Gate 3 (load-bearing) bars
1. Noise regime: ProbeID minus exact-match hit@1 >= 0.20 with paired
   bootstrap 95% CI lower bound > 0 (pilot 0.650 [0.450, 0.850]).
   Mechanism (pre-stated, not post-hoc): benign jitter inside the
   0.05 tolerance is invisible to bounded distance but a full mismatch
   for exact equality, so under a stochastic gold with positive
   self-distance, exact equality's ranking is noise-dominated while
   bounded distance still separates the gold from a 30%-drift squatter.
2. Required honest reporting (validity checks, not kill bars): twin pass
   rate in the gate study (expected ~1.00 — the paper's own uncatchable
   limitation, reproduced, not hidden); equality refusal of reachable
   replacements at m=64 (pilot 1.000; if this collapses the gate study
   itself is invalid and the run must be debugged, not shipped).
If bar 1 fails: KILL honestly (the paper's own concession — exact ties
ProbeID on deterministic tools — would then leave no demonstrated
advantage for probing over the trivial baseline in any regime tested).

## Structural note (stated before the head-to-head, not discovered after)
In the deterministic regime, ProbeID and exact-match strict choice coincide
BY CONSTRUCTION: bounded distance is 0 iff all leaves agree iff the
canonicalized responses are equal iff exact distance is 0, and the gold
sits at 0 under both rules — so identical outcomes there are a
mathematical identity of this harness, not an empirical discovery. The
empirical load-bearing claim therefore lives entirely in the noise regime
(Gate 3 bar 1), and the deterministic tie is reported as the paper's
concession reproduced, not as a win for either side.

## No-bar-moving rule
Bars above are frozen at lock time. Any post-lock change requires a new
dated amendment stating the change and the reason, and voids the
preregistered claim.
