# LinkedIn draft — DRAFT ONLY, never queued for posting

**Your agent picks tools by their descriptions. A squatter just has to
copy the description.**

I replicated ProbeID (arXiv 2610.33633) on 120 scripted tools to test
whether checking a tool's *behaviour* — probing it and comparing
responses to a trusted reference — actually fixes that.

What I measured:

- Description routers collapse to chance (8% hit@1) when squatters copy
  the description. Behavioural probing identifies the right tool 98% of
  the time.
- Honest concession, reproduced exactly: on deterministic tools, simple
  exact-match comparison ties ProbeID on all 120 cases. The paper admits
  this itself.
- The real advantage shows up under noise: when a tool's own responses
  jitter, exact matching falls to 36% while tolerance-aware probing
  stays at 100%.
- And the hard limit, also reproduced: if no probe reaches the drift,
  the squatter always passes. Verification is only as good as its probe
  bank.

Full writeup, code, preregistration and per-gate verdicts in the repo
(link on publish). No author code was used — the paper's code isn't
released yet — so this is a clean-room replication on synthetic tools,
not a reproduction of the paper's benchmark numbers.

---
DRAFT ONLY — LinkedIn lanes are stopped; do not queue or post.
