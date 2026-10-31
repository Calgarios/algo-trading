# Current progress

Updated 30 October 2026 (Asia/Bangkok). Project:
[Calgarios/algo-trading](https://github.com/Calgarios/algo-trading), KGI CU league.

**Phases 1–3 are merged. Phase 3 [PR #5](https://github.com/Calgarios/algo-trading/pull/5)
merged on 30 October 2026 at 13:52 Asia/Bangkok, commit `5554194`.
Phase 4 development experiments and visual reporting are complete.
A profitable or prize-ready strategy has not been established.**
**Phase 4 is not fully closed:** independent chronological validation is blocked
by missing additional permitted ticks and effective-dated membership. All results
still use September development data. See [next actions](../to-do/README.md) for
the remaining validation work and a Phase 5 handoff using the retained baseline.

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
| Phase 4 kickoff | Validated all 160 committed daily records; generated loss/payoff/turnover diagnostics and fixed-fill fee stresses; declared the R76 control and paired comparisons |
| Phase 4 local verification | All 86 tests pass; 90/90 historical deterministic artifacts match; five behavioral artifacts and performance pass the two-day research-copy parity check |
| Phase 4 R76 control | Full 16-day replay: −3.245602% return, 75.690713% average exposure, 3.148817% official drawdown; zero completed FIFO lots and undefined payoff |
| Phase 4 paired controls | P-C2, P-C3, H-C3 and B-C3 implemented and fully replayed under predeclared configurations; all outcomes retained |
| Phase 4 visual report | 12-page PDF, matching Markdown, CSV/JSON and ten figures, including costs, symbol attribution and completed-lot quote excursions |

The official engine, market data and all six recorded Phase 2 runtime/validation
sources remain unchanged. The organizer example remains integration evidence,
not a strategy recommendation. The original alphabetical default remains the
engineering reference; research configurations explicitly select the new models.

## Phase 4 achievements and decision

Read the [complete visual report](../result-data-visualisation/phase-4/phase-4-results.md)
or its [PDF](../result-data-visualisation/phase-4/phase-4-results.pdf).
The original strategy and package remain unchanged. A separately staged research
copy passed parity before running the controls; B-C3 ran after the paired controls.

| New run | Net return % | Average exposure % | Completed lots | Payoff THB | Common |
| --- | ---: | ---: | ---: | ---: | --- |
| R76: reference at 76% target | -3.246 | 75.691 | 0 | Undefined | fail |
| P-C2: equal-weight C2 basket | -3.612 | 75.011 | 1 | 78.59 | fail |
| P-C3: equal-weight C3 basket | -3.352 | 74.671 | 10 | 189.26 | pass |
| H-C3: passive initial C3 quantities | -3.379 | 75.951 | 0 | Undefined | fail |
| B-C3: wider C3 rebalance band | -3.595 | 75.808 | 20 | -393.04 | fail |

**P-C3 is the only common-criteria pass among the seven compared portfolios.**
It improves C3 net return by 0.237349 pp and reduces commission/VAT by THB 6,214.90.
It still loses money, fails Best Alpha, and trails R76 by 0.106551 pp. Positive
completed-lot payoff does not erase its unrealized loss. No candidate meets the
full advancement gate, and none has independent validation.

Equal-weight C2 improves return by 0.097983 pp but completes only one lot.
Passive C3 improves return by 0.210810 pp but completes none. These remain
development hypotheses. The wider band saves THB 2,367.52 in fees but worsens
return by 0.005825 pp; reject that change on current evidence. All paired average
exposure differences are within the declared two-percentage-point tolerance.

The original alphabetical strategy is retained as the engineering fallback.
P-C3 is a useful research comparator, not a validated or submission-ready winner.

- [Research protocol](../phase-4-research-spec.md) declares the development period,
  pending validation/final periods, controls and acceptance criteria before new runs.
- [Development diagnostics](../phase-4-diagnostics/README.md), matching CSV and JSON
  separate commission/VAT, realized and unrealized P&L, completed-lot payoff,
  partial realization, daily loss concentrations and measurement anchors.
- All ten runs remain negative with recorded commission/VAT added back at the
  same execution prices: **−3.390450% to −5.082650%**. Slippage remains embedded;
  these are accounting decompositions, not hypothetical engine replays.
- Unrealized losses account for **66.22–96.96%** of each net loss. For C3, the
  unrealized loss is **THB 333,471.95**, or **92.90%** of its net loss. Its official
  excess return is **+0.509994 pp**; first-close-aligned excess is **−0.210980 pp**.
- The original reference's [R76 configuration](../../research/phase4/R76.json)
  changes only its target from 70% to 76%. Its full engine run reconciles all
  16 days. C2 and C3 underperform it by 0.464395 pp and 0.343900 pp respectively,
  with average exposure differences within two percentage points. Basket and
  policy differences still prevent causal signal attribution.
- R76 meets the requested exposure band but fails common criteria because it
  completes no FIFO lots; expected payoff is undefined. Its negative net return
  also fails Best Alpha. It is a comparison control, not a promoted candidate.
- Raw-bundle diagnostics verify committed artifact hashes, replay FIFO, and
  reconcile symbol P&L and completed-lot holding sessions. The
  [restored-engine report](../phase-4-replay/README.md) records recovered results
  and actual price concessions measured from the engine's fill-time quotes.
- C3's largest symbol losses are CPF, CCET and PTTEP. Its completed lots have
  a median holding period of three sessions. Commission/VAT of THB 19,905.19
  plus price concessions of THB 63,375 still leave a −2.756700% return when
  added back at the same fills/marks; this is not a counterfactual engine replay.
- [Experiment log](../phase-4-experiments.md) distinguishes completed diagnostics,
  completed replay and blocked validation. The original baseline and all Phase 3
  configuration/source hashes remain unchanged.
- Completed-lot quote MAE/MFE and holding horizons are measured from verified
  ticks, with UTC/Bangkok alignment and same-timestamp boundary handling. They
  are retrospective diagnostics, not trading inputs, executable liquidation
  returns or portfolio intraday drawdown.

The user reuploaded the original archive, retained at
`.local/archives/tradeSim0.2.7.zip` and installed at `.local/tradesim-0.2.7/`.
Both are Git-ignored; archive SHA-256 and the 536-file tree match the original
provenance. The [input receipt](../../research/phase4/input-receipt.json) records
the restoration. Full test discovery now reports **86 passing tests**, including
all engine contracts; the earlier missing-package errors are resolved. The
archive adds no new tick dates or effective-dated membership. Fresh validation
data remain absent. R76's maximum measured daily runtime was 67.410 seconds
while historical runs executed concurrently, below the 900-second local ceiling.
No repository `AGENTS.md` or `SKILL.md` was found in the checkout or workspace
instruction directories; the available cloud-runtime and PDF skills were used.

## Phase 3 completed strategy designs

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

## Phase 3 measured results

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
