# Phase 5 experiment record and decisions

1 November 2026 (Asia/Bangkok). All tick replays use the original September
9–30 development sample, not new validation data.

| Experiment | Evidence | Decision |
| --- | --- | --- |
| V1 historical positive-edge veto | No supplied stock has a positive net five-session proxy mean under the declared pre-start calibration; C1 equal/quality smoke tests make zero trades | Reject as infeasible for participation/exposure; preserve declaration, source, config and smoke hashes |
| V2 daily full-universe selection | All 48 names assessed daily; 20 equal/quality simulations, two per existing model | Completed comparison; no candidate promoted |
| Quality versus equal allocation | Quality improves total return in 6/10 pairs and payoff in 4/10; all 20 retain negative payoff and insufficient exposure | No evidence supporting promotion of the added sizing complexity |
| C1/C3 doubled commission | Four actual engine replays, with endogenous fills/cash and independently reconciled fees | Does not establish a robust, eligible candidate |
| C1/C3 0.6%-NAV band | Four actual engine replays | Does not establish a robust, eligible candidate |
| C1-quality repeat | Full 16-session repeat; all nine deterministic artifacts match | Reproducibility passes |
| Independent preparation | All 30 calibration/config/manifest JSON files match byte for byte | Reproducibility passes; use the safe preparation entrypoint |
| Relative-output path recovery | Alternate preparation wrote generated files beneath the package; four queued T4/T5 attempts failed checksum preflight before trading | Generated files moved out; original tree reverified; all four replayed successfully in a separate recovery folder; original failed logs/statuses preserved |

## Measured outcome

Across the twenty base runs:

- **20/20** completed more than five FIFO lots: **317–535** per run.
- **20/20** satisfy the strict maximum drawdown boundary of **6.149244%**.
  Official maximum drawdown ranges from **2.444854% to 4.872953%**.
- **0/20** reach 50% average exposure: realized averages are **22.975–47.292%**.
- **0/20** have positive completed-lot expected payoff.
- **0/20** pass common criteria or Best Alpha. Net returns range from
  **-4.495467% to -2.504061%**.

The larger FIFO counts do not establish better decision quality. C4's and T5's
median closed-position holding period is one session in both weighting modes,
well below the five-session calibration proxy. Daily loss of entry eligibility
can force exits and later re-entry, raising turnover despite the buy budget.
The sample results reject a high-probability-profit claim for these policies.

Risk controls are also measured rather than assumed: across 320 base
strategy-days there are 26 closing position-cap breaches and one sector-cap
breach after pre-buy checks. The largest closing stock weight is **8.5833%**
against the 8% cap; the largest closing sector is **20.0157%** against 20%.
No base closing exposure exceeds 80%. Sampled controls do not prevent all drift,
gaps or incomplete exits. The 35% hard portfolio target protects exposure to
further market loss but contributes to failure of the minimum-average-exposure rule.

All 448 comparison strategy-days reconcile. **108 tests pass**, including
same-slot suppression, actual partial/rejected fills, risk exits, fee stresses,
prior-only calibration, allocation constraints, path safety and explicit
preflight recovery. The source and original package remain checksum-verifiable.

## Phase decision

Implementation, declared experiments and reporting are complete. **The Phase 5
improvement checkpoint is not met.** Reject promotion of this version; retain
the original engineering fallback and P-C3 as a historical research comparator.
Neither is a validated profitable submission. Independent Phase 4 validation is
still open because additional permitted tick dates and effective-dated membership
are absent.

The [visual report](result-data-visualisation/phase-5/phase-5-results.md) contains
all outcomes; [strategy explanations](phase-5-strategies.md) define the rules.
Next experiments and Phase 6 recovery/submission guidance are confined to
[docs/to-do](to-do/phase-6.md).
