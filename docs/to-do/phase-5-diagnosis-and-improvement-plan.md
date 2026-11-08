# Why Phase 5 failed, and the next controlled improvements

Draft — 9 November 2026 (Asia/Bangkok). This is a diagnosis and proposed research
plan, not a changed strategy or a claim of improved returns. Evidence is the
committed September development results and source merged through PR #7. No new
simulation was run for this review.

## Conclusion

Phase 5 improved auditability, universe coverage and accounting verification,
but **did not improve the strategy enough to meet its objective**. All twenty
base runs fail common criteria and Best Alpha. All pass the drawdown boundary
and exceed five FIFO round trips, but all have negative payoff and average
exposure below 50%. Net returns range from -4.495% to -2.504%; average exposure
ranges from 22.975% to 47.292%.

The implementation added rules without establishing a positive after-cost edge,
used entry conditions as ongoing holding requirements, and combined selective
entries with a risk target below the eligibility minimum. Those are design
problems, not proof that we merely need more indicators or a bigger universe.
The prior work should have distinguished engineering improvements from trading
improvements more clearly and treated those conflicts as pre-replay feasibility
checks. Passing 108 tests establishes tested mechanics, not profitable alpha.

## Evidence against the retained controls

| Run | Net return % | Average exposure % | FIFO trips | Payoff THB | Commission/VAT THB |
| --- | ---: | ---: | ---: | ---: | ---: |
| Phase 4 R76 | -3.246 | 75.691 | 0 | Undefined | 12,866 |
| Phase 4 P-C3 | -3.352 | 74.671 | 10 | +189.26 | 13,690 |
| Phase 5 C1 equal | -3.847 | 43.893 | 445 | -633.73 | 54,124 |
| Phase 5 C3 equal | -4.137 | 35.069 | 341 | -1,044.74 | 57,701 |
| Phase 5 C4 equal | -3.608 | 38.439 | 535 | -559.95 | 63,039 |
| Phase 5 T5 quality | -2.504 | 22.975 | 335 | -630.77 | 59,167 |

P-C3 passes common criteria but still loses money and fails Best Alpha. It is a
useful comparator, not a proven solution. T5 quality's smaller loss is not proof
of superior stock selection: its exposure is much lower. Basket, exposure and
policy changes prevent causal attribution between Phase 4 and Phase 5.
Quality sizing improves net return in six of ten Phase 5 pairs, but improves
payoff in only four; every pair still fails the overall requirements.

## 1. Entry eligibility was incorrectly coupled to holding eligibility

**Verified mechanism:** `_build_plan` creates targets only for currently eligible
stocks. `on_data` uses `plan['targets'].get(symbol, 0)`. Therefore a held stock
losing any entry predicate gets a zero target. `target == 0` bypasses the
rebalance band through the `emergency` condition, even without a trend failure
or volatility stop. A reversion strategy can sell simply because the pullback
ended; it can then buy again when that entry condition returns on a later day.

C4 equal closes 56 position episodes with a median holding period of one session;
47 close before five sessions. T5 quality closes 30 episodes with a one-session
median; 25 close before five sessions. C3 equal has 30 episodes with a two-session
median. These are much shorter than the five-session calibration proxy.

The sell-fill reason counts support a turnover concern: C3 equal records 305
`rebalance` sell-fill decisions versus 26 `volatility_stop` decisions. However,
`rebalance` combines signal removal, target resizing and other portfolio actions.
It does **not** prove all 305 were unnecessary signal exits. Quantifying each
cause needs more explicit reason codes and an execution replay with only the
retention rule changed.

**Proposed correction:** separate states for entry, retention, ordinary exit and
emergency exit. A failed entry predicate blocks new purchases; it does not
universally liquidate existing holdings. Define strategy-specific profit/exit
conditions, signal persistence and a cross-day re-entry cooldown. Preserve
immediate genuine risk exits. Test retention alone before adding other changes.
A minimum holding period must never prohibit a necessary risk exit.

## 2. Transaction friction consumed a large part of the outcome

| Run | Fees + observed price concessions THB | Net loss THB | Same-fills cost add-back return % |
| --- | ---: | ---: | ---: |
| C1 equal | 223,102.80 | 384,741.80 | -1.61639 |
| C3 equal | 246,725.07 | 413,715.07 | -1.66990 |
| C4 equal | 257,687.03 | 360,813.03 | -1.03126 |
| T5 quality | 227,521.07 | 250,406.07 | -0.22885 |

Price concession means the recorded fill price versus its fill-time market
quote, measured in the direction adverse to the trade. Adding fees and these
concessions back is an **accounting diagnostic at the same fills/marks**, not a
counterfactual zero-cost strategy or a realizable improvement. All four remain
negative even on that diagnostic, so costs are important but not the only issue.
The actual doubled-commission replays also failed to produce an eligible model.

**Proposed correction:** estimate the full entry/exit friction per stock, including
both tick directions and commission/VAT. Compare it with a conservatively
estimated move over the intended holding horizon; do not call volatility an
expected profit. Suppress ordinary rotations whose supported incremental edge
does not cover costs and uncertainty. Budget gross ordinary turnover, not only
buys; risk exits remain exempt. Do not manufacture round trips to reach a quota.

## 3. Portfolio construction undermined the exposure requirement

**Verified mechanism:** `risk_target` lowers the target to 55% at the soft trigger
and 35% at the hard trigger (absolute current drawdown >=3%, or the declared
relative condition). The 35% target conflicts with maintaining >=50% average
exposure if active long enough. Selective entries, position/sector caps and slow
redeployment can lower actual exposure further; the guard alone does not explain
every shortfall. C1 equal starts with 18 eligible names and a 76% allocated target,
then ends with a 35% target.

The daily post-initial buy budget is 15% NAV, divided equally across eligible
names. Unused budgets are not reassigned. Selling can be immediate while rebuilding
exposure takes days. At an 8% per-name cap, at least seven eligible stocks are
necessary for 50% exposure and at least ten for 76%, even before tighter sector
and liquidity limits. Broad candidate coverage does not guarantee enough holdings.

**Proposed correction:** measure feasible allocation capacity before selecting a
policy. Compare an ordinary-stress target of 55% with the current 35% target,
while retaining a separately specified emergency cash override. Evaluate a
simple diversified core plus a smaller timing sleeve only if its holdings have
acceptable evidence; do not force purchases of rejected stocks. Track cumulative
average exposure and remaining feasible exposure, not just today's target.
No policy can guarantee both eligibility and a drawdown bound during all gaps.
Never use the final sample benchmark drawdown as information available earlier.

## 4. The quality score had no demonstrated positive forecast edge

The pre-start, non-overlapping five-session daily-price proxy produced **no
positive stock mean after estimated costs**. The initial positive-edge veto made
no trades. Version 2 removed that veto and used bounded relative weighting:

`clip(1 + shrunk_mean_net / max(se_net, 0.005), 0.5, 1.5)`

combined with model rank and inverse volatility. Negative estimates still receive
positive portfolio weight. This may be a risk-allocation experiment, but neither
that formula nor its name establishes high-probability profitable trades.
Furthermore, calibration conditions only on a broad long-trend state, not each
strategy's actual entry/exit rules; it uses daily-price proxies rather than IOC
fills and frequently differs from the actual holding horizon.

**Proposed correction:** retain equal weighting as the default comparison until
sizing has incremental evidence. Match calibration to the actual decision,
holding/exit policy and costs; distinguish probability of a gain from expected
net payoff. Use chronological validation, non-overlapping/embargoed outcomes,
sample counts, downside losses, uncertainty and temporal stability. Shrink weak
estimates rather than treating small samples as certainty. Do not tune thresholds
against September until the table turns green.

## 5. More round trips did not mean more independent good decisions

C1 equal's 445 FIFO completions represent 41 closed position episodes; C3 equal's
341 represent 30. IOC fragmentation and repeated orders can inflate the official
lot count. The user threshold is >5; the reported common threshold is >=5. Neither
requires hundreds of lots. THB payoff per lot is also sensitive to order size.

**Proposed correction:** optimize total net P&L, drawdown and supported payoff,
with eligibility as a constraint. Report official FIFO count, full episodes,
net return per invested baht, holding sessions, open losses and costs together.
Use symbol/time-aware uncertainty estimates; episodes also share market risk and
are not necessarily independent bets. Do not hide unrealized losses by reporting
only profitable completed lots.

## 6. Risk limits and experiment design need tightening

Pre-buy caps were not continuous holding caps: across 320 base strategy-days,
26 closing position breaches and one sector breach occur, with maxima 8.5833%
and 20.0157%. `emergency` noticing a position breach does not itself recompute a
smaller cap-compliant quantity; if the old target still equals holdings, the
`at_target` branch can hold. This is a code-level weakness to test, not proof of
the cause of each recorded breach. Intraday marks are asynchronous, execution
can be partial, and restart latches remain process-local.

Phase 5 changed universe, selection, sizing, exits, guard and turnover behavior
together relative to Phase 4. Equal/quality pairs isolate desired sizing within
the new policy, not those other changes. There is no controlled estimate of the
net benefit of each added rule. Risk containment by holding cash also cannot be
credited automatically to forecasting skill.

**Proposed correction:** recompute position/sector breach targets from current
values, apply explicit risk-priority sells, and verify partial-exit retries and
same-day restart state. Preserve the historical implementation as a comparator.
Test one change at a time, at comparable exposure, with all variants retained.

## Ordered research plan and acceptance gates

| Order | Change to test | Control / evidence required | Reject or revise when |
| --- | --- | --- | --- |
| 1 | Add distinct exit reasons, exposure-capacity/budget diagnostics and episode histories | Frozen Phase 5 behavior must reproduce identical fills before any policy change | Instrumentation changes decisions or accounting |
| 2 | Separate entry and retention conditions | C3 and one reversion model (C4), equal weights; only retention changes | After-cost return/payoff worsens, drawdown fails, or improvement relies on accumulating hidden open losses |
| 3 | Cost-aware ordinary rotation and re-entry cooldown, separately | Step 2 retained candidate; actual fee/liquidity stresses; turnover and episode horizons | Costs saved do not translate into net improvement or opportunities cannot complete within the competition horizon |
| 4 | Exposure-feasible guard and redeployment, separately | Same stock policy; report average exposure, cash path and DD | >=50% average exposure cannot coexist with strict DD and positive payoff; report infeasibility rather than force entries |
| 5 | Live cap enforcement and durable restart state | Gaps, partial/rejected orders, cap drift, same-day recovery; official-engine tests | Controls allow duplicated buys, lost exits, cash borrowing or unhandled failures |
| 6 | Risk sizing versus equal weights | Freeze policy; matched-exposure pairs and independent chronological periods | Incremental benefit is unsupported, unstable, or disappears after costs |

Specify exact parameter values and data periods in a new declaration before
running these experiments; this draft does not authorize selecting parameters
from future outcomes. Freeze an untouched final evaluation period where possible.
September remains consumed development data. Additional permitted ticks and
effective-dated membership are still needed; available sample coverage is 48
stocks, not all 50. Historical adjustments and production event order also need
confirmation.

Promotion requires >5 FIFO trips for the user's target, >=5 distinct stocks,
average exposure >=50%, positive expected payoff, portfolio DD strictly below
1.5 times benchmark DD, and nonnegative net and excess returns for Best Alpha.
Also report the 70–80% preferred exposure band separately. Require improvement
against the retained control under comparable exposure, plausible execution
sensitivities and independent evidence. If no candidate qualifies, keep the
engineering fallback and explicitly keep the research gate open.

## Sources and verification

- [Phase 5 results and definitions](../result-data-visualisation/phase-5/phase-5-results.md)
- [Machine-readable Phase 5 evidence](../result-data-visualisation/phase-5/phase-5-results.json)
- [Phase 4 evidence](../result-data-visualisation/phase-4/phase-4-results.json)
- [Strategy source](../../research/phase5/strategy/DiversifiedBaseline.py):
  `_build_plan`, `risk_target`, `_exit_signal`, `on_data`
- [Calibration implementation](../../scripts/phase5_support.py)
- [Existing Phase 6 handoff](phase-6.md)

Review method: recomputed selected cost/P&L comparisons from committed JSON and
traced the described branches in source. These observations explain failure
mechanisms but do not quantify counterfactual improvement. The experiments above
are proposals, not completed tests or promised profitable strategies.
