# Phase 4 experiment log

Updated 30 October 2026 (Asia/Bangkok). Protocol:
[phase-4-research-spec.md](phase-4-research-spec.md). Baseline revision: `5554194`,
the merged Phase 3 PR #5. All September observations are development evidence.

| ID | Question | Status | Evidence / decision |
| --- | --- | --- | --- |
| D01 | Are completed-lot losses and fees sufficient to explain total losses? | Complete, aggregate evidence only | [Diagnostics](phase-4-diagnostics/README.md): most loss remains unrealized; all ten remain negative after fee add-back. Retain reference, revise hypothesis. |
| D02 | Which symbols, lots and holding horizons drive losses? | Complete for the available sample | Symbol/FIFO accounting, holding sessions, fill-price concessions and completed-lot quote MAE/MFE are measured. Portfolio intraday drawdown is not established. |
| R76 | Does the original reference at a 76% target change the comparison? | Full declared replay complete | −3.245602% net return at 75.690713% exposure; better net return than C2/C3, but no completed lots and undefined payoff. No promotion. |
| P-C2 | Do daily ranked C2 allocations beat equal weights in the same basket? | Complete | Equal weights improve net return by 0.097983 pp; one completed lot, so common criteria fail. Retain only as a development hypothesis. |
| P-C3 | Do daily ranked C3 allocations beat equal weights in the same basket? | Complete | Equal weights improve net return by 0.237349 pp; ten lots and THB 189.26 payoff pass common criteria. Negative return and underperformance of R76 prevent promotion. |
| H-C3 | Does active C3 beat a passive holding of the same initial quantities? | Complete | Passive net return improves by 0.210810 pp; no completed lots. Different guard behavior remains explicit. No promotion. |
| B-C3 | Does a 0.8%-NAV rebalance band improve on 0.4% after costs? | Complete after paired controls | Fees fall THB 2,367.52 but net return worsens 0.005825 pp; reject the change on current evidence. |
| V01 | Does an improvement persist chronologically beyond September? | Blocked | Additional permitted ticks/history and effective-dated membership absent; validation and final evaluation dates remain unassigned. |
| U15 | Does expansion to 15 fixed names improve diversification? | Blocked on declared membership requirement | No effective-dated universe supplied. Ten-stock diagnostic/control budget remains in force. |
| S01 | Do final-selection cost/lookback/liquidity sensitivities survive chronological checks? | Conditional, not started | No candidate meets the advancement gate. The declared band sensitivity and fixed-fill fee stresses are complete; no final-selection robustness claim is made. |

The [12-page visual report](result-data-visualisation/phase-4/phase-4-results.pdf),
[matching Markdown](result-data-visualisation/phase-4/phase-4-results.md), CSV/JSON
and ten figures retain every result. Phase 4 development work is complete;
Phase 4 as a whole remains open because V01/U15 inputs are absent. Phase 5
engineering can start from the retained baseline under the development guide,
with P-C3 as an additional research comparator and no candidate promotion.

## D01 findings

- All 160 committed strategy-days pass accounting/metric consistency checks.
- Adding commission/VAT back at unchanged fill prices leaves returns between
  −5.082650% and −3.390450%; fees alone do not explain the negative totals.
- Unrealized losses are 66.22–96.96% of net losses. C3 is 92.90%, with
  THB 333,471.95 unrealized against THB 358,950.19 total loss.
- C3's official excess is +0.509994 pp, but its first-close-aligned excess is
  −0.210980 pp. Benchmark anchoring changes the interpretation; neither measure
  substitutes for a matched portfolio control.
- September 30 is the largest daily NAV loss for all ten strategies. This is
  an observation about an already-inspected period, not a newly discovered holdout.
- Completed-lot P&L differs from realized P&L because partially sold open lots
  contribute realized gains/losses before lot completion. The report keeps them
  separate. No count of fills/lots is treated as independent statistical evidence.

## Restored inputs and R76 findings

The user reuploaded `tradeSim0.2.7.zip`; archive and extracted-tree checksums
exactly match the original provenance. The ZIP is saved at
`.local/archives/tradeSim0.2.7.zip`, and the package/ticks are installed at
`.local/tradesim-0.2.7/`, outside Git. No additional tick period or effective-dated
membership was included. The pre-run research spec and manifest are preserved.

R76 completed all 16 days with reconciled accounting. Net return is −3.245602%,
SET50 excess +0.853893 pp, official drawdown 3.148817%, and average exposure
75.690713%. It trades ten names but completes zero FIFO lots; payoff is undefined.
Common criteria and Best Alpha both fail. Its net return is 0.254039 pp worse
than the original 70%-target reference, with higher realized exposure.

C2 and C3 underperform R76 by 0.464395 pp and 0.343900 pp, respectively. Their
average exposures are 1.022596 pp and 1.536624 pp lower. These satisfy the
declared two-percentage-point comparison tolerance, but different baskets,
quantity anchors and risk policies still prevent causal attribution to signals.
The matched controls are now complete; their results above do not select R76
or any other portfolio as a competition strategy.

For C3, CPF/CCET/PTTEP are the largest symbol losses. The median completed-lot
holding period is three sessions (range 1–15). Actual fees plus observed price
concessions total THB 83,280.19; adding them back at fixed fills/marks leaves
−2.756700%. Portfolio losses cannot be explained solely by those recorded costs.

## Verification and limits

All **86 tests pass**, including the original 61 tests, 13 Phase 4 research tests,
two quote-concession checks, six allocation-control tests and four completed-lot
excursion tests. Python 3.13.5 and the pinned
dependency set are installed. The prior missing-package import errors are
resolved. R76 preflight now passes; its maximum local daily replay time was
67.410 seconds under concurrent historical replays.

All six recorded Phase 2 sources and three Phase 3 preparation sources retain
their hashes. The default strategy/configuration and ten frozen research
configurations are unchanged. New output records its input and analysis-code
hashes; repeated diagnostics produce identical Markdown, CSV and JSON bytes.

All 90 deterministic artifacts from the ten historical replays match. The
research strategy passes the two-day parity check for five behavioral artifacts
and performance before the full controls. All 112 strategy-days in the seven-
portfolio final comparison reconcile. Five new full simulations (R76 plus four
controls) and ten historical recoveries retain their full evidence under artifacts.

Completed-lot price paths are diagnostic only: known endpoint quotes plus strictly
interior timestamps avoid ambiguous same-time ticks, UTC fills are aligned to
Bangkok quotes, and all quotes may include auctions. Neither these paths nor the
new runs establish portfolio intraday protection, independent validation or
organizer acceptance. Continue from [next actions](to-do/README.md).
