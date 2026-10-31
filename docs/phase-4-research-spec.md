# Phase 4 research protocol

Declared 30 October 2026 (Asia/Bangkok), before any new Phase 4 engine run.
Phase 3 was merged through PR #5 at `5554194147d723bd7e833c8d831a14cfe99d3498`.
Read [current progress](current-progress/README.md) and [next actions](to-do/README.md).

## First question and scope

Can a defensible change improve net performance and completed-lot expectancy
against simple controls, at comparable exposure, without worsening eligibility?
First diagnose the ten existing runs. Preserve every outcome, including failures.
Do not select a candidate merely because it ranks first among losing strategies.

This first Phase 4 increment delivers reproducible diagnostics, one executable
control configuration, and a declared comparison protocol. It does not complete
Phase 4 validation. The original strategy, Phase 3 configurations and Phase 2
sources stay frozen so their recorded hashes and reference behavior remain usable.

## Data and chronological boundaries

| Role | Period | Status |
| --- | --- | --- |
| Development | 9–30 September 2026, all 16 supplied sessions | Already inspected and reused; includes all Phase 3 comparisons and these diagnostics |
| Validation | Unassigned | Requires additional permitted ticks, daily signal/benchmark history and effective-dated membership |
| Final evaluation | Unassigned | Reserve after the validation period, before viewing outcomes; freeze candidate before evaluation |

Do not carve a supposedly untouched validation set out of September. Any
early/late September diagnostic is still development evidence. When additional
data arrive, record source permission, file hashes, available dates, price
adjustments, effective-dated membership and when that membership was known.
Declare non-overlapping chronological periods before inspecting their results.
If there is insufficient data for three useful periods, record that limitation
instead of manufacturing a holdout. Once validation informs a change, mark it
consumed development data and reserve new evaluation data.

A new run start requires newly prepared baskets from strictly earlier history.
Do not reuse the September 9 baskets at a later start. Full official-engine
replay additionally requires the checksum-pinned original TradeSim archive;
committed aggregate metrics do not replace the engine or raw ticks.

## Diagnostics before changing signals

`scripts/phase4_diagnostics.py` reads the committed Phase 3 evidence and checks
dates, accounting identities, metrics, common input identity and reconciliation
flags before deriving:

- Net, realized and unrealized P&L; commission/VAT; traded notional implied by
  the verified proportional fee rate; first-day versus later traded notional.
- P&L with recorded commission/VAT added back at the **same execution prices**.
  Slippage remains embedded. This is an accounting decomposition, not a zero-cost
  replay or an estimate of achievable profits.
- Completed-lot win rate, mean win/loss and profit factor; the difference between
  completed-lot P&L and total realized P&L is partial realization on still-open lots.
- Daily NAV changes, daily fee increments, largest loss days, exposure and
  protective-target days. Daily quantities are derived from cumulative records.
- Both official excess return and first-close-aligned excess return. Official
  portfolio return starts at initial capital; SET50 starts at the first close.
  Keep both definitions visible and never replace official scoring metrics.
- Fixed-fill +25% and +50% commission/VAT arithmetic stresses. These do not model
  changed cash constraints, quantities, slippage, market impact or execution.

With `--runs` pointing to recovered Phase 3 run bundles, additionally verify
report/FIFO/fill-log hashes against the committed evidence, replay the fill
ledger, and reconcile symbol P&L and completed-lot outcomes to the portfolio.
Report first-buy-to-completion session age for each completed lot. Preserve
original fill order, including the notebook's cross-symbol time ordering.
Do not infer intraday adverse excursion, entry quality, or slippage attribution
without the corresponding decision/tick evidence. Missing detail stays unknown.

## Predeclared experiments

| ID | Hypothesis / comparison | State before runs |
| --- | --- | --- |
| R76 | Raise only the original alphabetical reference target from 70% to 76%; measure whether the apparent signal gap is explained by exposure/design differences | Configuration and guarded replay command implemented; engine run pending |
| P-C2, P-C3 | Compare C2/C3 with equal-weight allocations in each identical frozen basket, at a 76% regular target and identical daily risk guard | Declared; implement after raw diagnostics and package recovery |
| H-C3 | Hold C3's initial ranked quantities without daily reranking; test whether active turnover adds value over the same initial basket/allocation | Declared; implement with the paired controls |
| B-C3 | Compare C3's 0.4%-NAV rebalance band with one 0.8% band; less turnover may improve net payoff | Declared; implement only after matched controls, retain both outcomes |

R76 changes exactly one baseline field: `target_exposure`. It retains prior-month
alphabetical selection, fixed quantities based on initial capital, existing
cash/position/exposure checks and no added daily suite drawdown guard. It is a
**target-exposure control**; actual exposure is measured, not assumed equal.
It does not isolate signal quality from basket or risk-policy differences.
The September-only wrapper refuses changed source/configuration hashes and
existing output directories. The generic replay report retains its historical
Phase 3 title; the wrapper records Phase 4 provenance separately.

P-C2/P-C3 must use the same start, basket, initial capital, historical data,
costs, daily guard, board lots, rebalance band and execution cadence as their
paired active model; only daily rank-based weights change to equal weights.
These are daily equal-weight controls, not buy-and-hold. H-C3 is the passive
control: freeze C3's first-day quantity targets and retry only residual initial
buys under the same pre-buy limits, with no subsequent sells, reranking or
daily target guard. Report actual exposure drift and the changed risk policy;
its returns cannot isolate reranking from the guard. Compare first-close-aligned
paths as well as official returns. An exposure difference above two percentage
points makes the passive comparison inconclusive for attribution.
Do not substitute a SET50 return multiplied by average exposure for a matched
basket control. No forced terminal liquidation or cosmetic round trips.

For this diagnostic/control stage retain the ten-distinct-stock limit. Broader
diversification remains a separate subsequent experiment: **15 fixed names**,
at most three per sector, selected from the top 30 by prior 20-session median
close-times-volume, no rotation or replacement during a run, and the existing
10% position/80% invested/20% cash pre-buy limits. Prepare using effective-dated
permitted membership and earlier history. This expansion is declared but not
implemented or evaluated here; do not mix it into R76 or the paired controls.

## Acceptance and decisions

For each paired comparison report all runs, actual exposure, costs, turnover,
realized/unrealized P&L, completed lots, payoff, official/initial-capital drawdown,
SET50 and both excess-return anchors. A difference of more than two percentage
points in average exposure is a comparability warning requiring explanation,
not evidence of a signal effect. The user's 70–80% average closing exposure
preference remains separate from the common minimum of 50%.

Retain a candidate for refinement only when net return exceeds both R76 and
its paired equal-weight control, expected payoff is positive, the common and
participation checks pass, average exposure is 70–80%, and results persist on
the declared later validation period with all outcomes retained. Also inspect
the fixed-fill fee stresses; surviving them alone is insufficient. Best Alpha
additionally needs nonnegative net and excess return. Zero benchmark drawdown
and unknown membership/acceptance remain unresolved, not passing checks.

Before final selection, declare and run chronological sensitivity checks with
actual replay for costs, lookbacks and liquidity; the one band comparison above
is deliberately small, not an invitation to search a grid. Do not choose new
parameter ranges after looking at a final holdout.

Current decision: **retain the original engineering reference; revise research**.
C2 and C3 remain diagnostic hypotheses. No new candidate is promoted by these
aggregate diagnostics. Phase 5 refinement awaits evidence; Phase 6 organizer
compatibility/recovery dependencies can proceed separately when inputs arrive.
