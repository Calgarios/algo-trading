# Current progress

Updated 30 October 2026 (Asia/Bangkok). Project:
[Calgarios/algo-trading](https://github.com/Calgarios/algo-trading), KGI CU league.

**Phases 1 and 2 are merged. Phase 3 is complete as a local engineering
milestone; its work is in draft [PR #5](https://github.com/Calgarios/algo-trading/pull/5),
not yet merged. A profitable or prize-ready strategy has not been established.**
The research comparison structure is complete; Phase 4 validation is not complete.

This page records achievements and measured status only. Future actions and
lessons are separated into [docs/to-do](../to-do/README.md).

## Completed milestones

| Milestone | Completed work |
| --- | --- |
| Phase 1 | Objectives, working rules and priorities; PR #1 merged |
| Development guide | Seven-phase guide and PDF; PR #3 merged |
| Phase 2 | Pinned TradeSim 0.2.7 / Python 3.13.5, data audit, 17 official contract tests, two identical organizer-example runs; PR #2 merged |
| Progress documentation | Earlier handoff merged through PR #4; achievements and future guidance now have separate directories |
| Phase 3 baseline | Standalone strategy and companion JSON, official-engine replay, risk checks, decision/fill logs, independent accounting and eligibility reporting |
| Phase 3 earlier experiments | Alphabetical and momentum exit variants tested; both rejected after increased costs and negative payoff |
| Phase 3 ten-strategy comparison | Five custom and five indicator models, frozen ten-stock baskets, common 76% allocation/risk layer, all ten full-sample results retained |
| Visual reporting | 17-page PDF, matching Markdown, comparison CSV, daily evidence JSON and 14 figures generated from verified run artifacts |
| Verification | 61 passing tests; all 160 comparison strategy-days reconciled; C1 fresh-process repeat matches nine deterministic artifacts |

The official engine, market data and all six recorded Phase 2 runtime/validation
sources remain unchanged. The organizer example remains integration evidence,
not a strategy recommendation. The original alphabetical default remains the
engineering reference; research configurations explicitly select the new models.

## Completed strategy designs

Custom models: **C1 risk-adjusted momentum, C2 downside defence, C3 efficient
breakout, C4 trend pullback, C5 balanced ensemble**.

Indicator models: **T1 SMA trend, T2 EMA trend, T3 MACD acceleration, T4 RSI
pullback, T5 Bollinger reversion**.

The [comparison specification](../phase-3-ten-strategy-spec.md) was fixed before
these ten full runs. Each strategy selected ten names using only pre-start daily
history, from a liquidity pool of 30, with at most two names per sector. Baskets
remained fixed; daily ranks changed allocations without introducing an eleventh
stock. These are ranked allocation models, not binary crossover systems.

The regular target is 76% of opening NAV. Buy checks cap a position at 10%,
total investment at 80%, and preserve 20% cash. The daily drawdown guard can
reduce the target to 72% or 55%. A 0.4%-of-NAV rebalance band, 100-share lots,
15-minute execution slots and actual residual-fill handling constrain turnover.
No end-of-sample liquidation or artificial round trips were used.

## Measured results

All ten simulations used **9–30 September 2026, 16 days, 2,906,167 ticks,
THB 10 million, the same official package, costs and notebook event order**.
SET50 return was **−4.099496%**, and SET50 maximum drawdown was **4.099496%**.

- **10/10** achieved the user's 70–80% average exposure band: **72.087–74.899%**.
- **10/10** traded exactly ten distinct stocks and completed at least five FIFO lots.
- **10/10** met the strict final drawdown boundary of **6.149244%**;
  official maximum drawdowns ranged from **3.718% to 5.288%**.
- **0/10** passed all common criteria: expected payoff was negative in every run.
- **0/10** passed Best Alpha. All ten had negative net return.

**C3 had the best net return among the new strategies. It is a development
comparison lead, not a qualified winner.**

| Requested metric | C3 efficient breakout |
| --- | ---: |
| SET50 return | -4.099496% |
| Net return | -3.589502% |
| SET50 excess return | +0.509994 pp |
| Official portfolio maximum drawdown | 4.310476% |
| SET50 maximum drawdown | 4.099496% |
| Average closing exposure | 74.154089% |
| Distinct stocks | 10 |
| Completed FIFO round trips | 34 |
| Expected payoff | −THB 603.88 per completed non-breakeven lot |

The original reference returned **−2.991564%** at **69.693722%** average exposure.
None of the ten new models improved its net return in this sample. The new work
establishes the requested exposure and comparison structure, not demonstrated
profitability. Different baskets and exposure also limit causal attribution.

Two strategies each recorded one closing position above the pre-buy 10% cap:
C3 reached 10.07%, T3 reached 10.11%. No daily closing portfolio exposure exceeded
80%. Price drift after an accepted buy is visible in the evidence; pre-buy caps
and the daily guard are not guarantees of continuous risk limits.

## Verified reporting and eligibility

Independent cash, holdings, raw open costs, NAV, fees, realized P&L, completed
FIFO lots, expected payoff and benchmark/portfolio metrics reconcile every day.
The runner saves exact strategy/config bundles, input/code hashes, daily plans,
decisions, actual fills, FIFO records and runtime. The maximum measured daily
runtime among the ten runs was **43.213 seconds**, including concurrent execution.

The 61 tests include the original 17 contracts, past-history validation, indicator
mathematics checked against pandas, sector selection, sizing and caps, partial
fills, allocation guards, restoration behavior, FIFO accounting and scoring
boundaries. The C1 repeat reproduces all nine deterministic artifacts byte for
byte; wall-clock timings are excluded. No GitHub CI workflow is configured.

The [working award criteria](../award-criteria.md) distinguish common requirements
from Best Alpha. Positive total return is **not** a universal common requirement;
positive expected payoff **is**. Best Alpha additionally requires nonnegative
total and excess returns. Distinct-stock participation is tracked separately.

Expected payoff is a sample average of net P&L on completed non-breakeven FIFO
buy lots, not a future-profit forecast. Excess return is an arithmetic difference
between percentages, so it is shown in percentage points (pp).

## Current evidence and limits

- [Full comparison Markdown](../result-data-visualisation/phase-3-results.md)
- [17-page comparison PDF](../result-data-visualisation/phase-3-results.pdf)
- [Machine-readable metrics](../result-data-visualisation/phase-3-results.csv)
- [Daily metrics, configuration and hash evidence](../result-data-visualisation/phase-3-results.json)
- [Frozen configurations and preparation evidence](../../research/phase3-suite/)
- [Original baseline](../phase-3-summary.md) and [earlier experiments](../phase-3-followup.md)
- [Setup and reproduction commands](../../README.md)
- [Separate next-action and lessons record](../to-do/README.md)

September has been reused and is development data, not untouched validation.
The supplied 48-stock universe is static, without verified effective-dated
membership. The historical API excludes the current day; callbacks are forming
bars on every tick. Notebook events use symbol/row-index round robin, so
cross-symbol marks are not synchronized. Official drawdown uses daily closes;
initial-capital drawdown is also reported separately.

Organizer acceptance, registered identity, production scheduling/restarts,
current amendments and submission access are not established. The local owner
is still `baseline`. Phase 3 engineering completion does not establish prize
qualification, future profitability or Phase 4 completion.
