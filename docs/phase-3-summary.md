# Phase 3 — First complete baseline

> This records the original `5bc8859` reference. See the
> [follow-up assessment](phase-3-followup.md) for the clarified award rules,
> exit-policy/selection experiments and current Phase 4 handoff.

Recorded 29 October 2026 (Asia/Bangkok), based on `main` commit
`9e9b0d7e71cda4088f570ed7ec35eeefee186f28`. Phase 3 implementation and local
validation are complete; the proposed change is prepared for review. This is
not an accepted competition submission or a validated profitable strategy.

## Fixed design and implementation

The [specification](phase-3-baseline-spec.md) was written before the first
baseline backtest. No selection/weight/cadence parameters were changed after
seeing its results. The strategy takes the alphabetically first ten eligible
symbols from the supplied universe, using 20 closes strictly before month
start. It targets fixed monthly quantities worth 7% of initial capital each
at the prior-month close, retaining cash and handling incomplete IOC fills.
Alphabetical selection is a transparent reference, not a predictive signal or
a guarantee of sector diversification.

The sample selected ADVANC, AOT, AWC, BBL, BCP, BDMS, BEM, BH, BJC and CCET.
BANPU lacked 20 prior-month closes and was excluded by the predeclared rule.
Every symbol instance independently reconstructs the same plan using only
handler-provided historical data. The runner asserts that their plans agree.
No shared custom state or team-helper imports are required by the artifact.

`strategy/DiversifiedBaseline.py` is one direct subclass of the supplied
template, with matching filename/class name and a permitted JSON companion.
Pre-buy controls include actual cash and holdings, 100-share lots, ten held
names, a 10% per-stock limit, an 80% invested limit and a 20% cash reserve.
Affordability includes commission, VAT and the effective-date slippage table.
One own-symbol market IOC per 15-minute decision slot avoids pending orders
and the documented multiple-limit daily-cap defect. Actual quantities, rather
than success messages, determine the next outstanding target.

The official engine, data, example, Phase 2 runner and Phase 2 contract tests
remain unchanged. All six Phase 2 runtime/validation source hashes still match
the earlier evidence. No dependencies were added to the six pinned packages.

## Sample result

Full original sample: 16 days, 9–30 September 2026, 2,906,167 ticks. This sample
was already inspected during integration; it is not untouched validation.

| Measure | Baseline result |
| --- | ---: |
| Initial / final NAV | THB 10,000,000 / THB 9,700,843.62 |
| Final cash | THB 2,941,685.62 |
| Net return | −2.991564% |
| Official SET50 return | −4.099496% |
| Official excess return | +1.107932 percentage points |
| Official daily-close maximum drawdown | 2.899616% |
| Drawdown including initial capital | 2.991564% |
| Average closing exposure | 69.693722% |
| Distinct traded stocks | 10 |
| Completed FIFO round trips | 0 |
| Expected payoff | Unknown; no completed non-breakeven lots |
| Commission plus VAT | THB 11,837.38 |
| Order attempts / fills | 141 / 140 |
| Partial fills / zero fills | 130 / 1 |

Targets were reached during the first two days; the remaining sample held
those quantities. The zero-fill attempt returned a rejection. There were no
closing exposure/concentration breaches of the pre-buy limits. Later price
drift can still breach these limits; the strategy does not promise to maintain
them continuously or enforce a benchmark-relative drawdown limit.

Official portfolio return starts at initial cash, whereas SET50 return starts
at the first sample close. Official drawdown starts at the first portfolio
close. Separate aligned first-close measures are −2.552111% portfolio return
and +1.547385 percentage points excess return. The report preserves both
definitions instead of quietly changing the scoring anchor.

## Accounting, logs and verification

- **43 tests pass:** the original 17 engine contracts plus 26 strategy,
  independent accounting and metric tests. Scenarios cover partial/zero fills,
  duplicate cadence, costs and cash, position/exposure limits, missing and
  future history, consistent plans, daily persistence, monthly selling,
  FIFO partial/full closure, tick-table transition and strict scoring edges.
- Cash, quantities, raw open-lot cost, daily NAV, realized P&L, FIFO completion,
  payoff, exposure, drawdown and benchmark metrics reconcile independently.
  Displayed lot costs are rounded; reconciliation uses raw cost values.
- Two fresh full-sample processes produce byte-identical reports, plans,
  decisions, independent FIFO records, saved portfolio and engine fill log.
  Wall-clock engine logs, platform details and runtime are excluded.
- First full replay: 192.900 seconds total, slowest day 20.574 seconds on this
  worker, including local logging/reconciliation. This has local headroom
  below 15 minutes per day, but is not a production-runtime guarantee.

See [compact evidence](phase-3-run-evidence.json) for exact hashes, daily
metrics, test source identities and timings; [README commands](../README.md)
reproduce the run. Large artifacts and the organizer ZIP remain local.

`plans.json` records selected/excluded stocks, prior-month closes and targets.
`decisions.jsonl` records each decision's bar time, quote, target, held quantity,
cash, applicable risk inputs, requested quantity, response and actual fill.
Engine fill logs retain execution prices/times. `fifo.json` contains independent
lot records. Daily reports distinguish cumulative metrics from closing risk.

## Working eligibility and next phase

| Working requirement | Status |
| --- | --- |
| Five distinct traded stocks | Pass: 10 |
| Five completed FIFO round trips | Fail: 0 |
| Average exposure ≥50% | Pass: 69.69% |
| Expected payoff >0 | Unknown: no completed non-breakeven lots |
| Drawdown strictly <1.5× SET50 drawdown | Pass: 2.90% <6.15% |
| Nonnegative total return | Fail: −2.99% |
| Nonnegative excess return | Pass: +1.11 percentage points |

**Common working criteria and Best Alpha status: fail.** Missing benchmark
coverage, undefined payoff and the unresolved zero-benchmark-drawdown edge are
unknown, never a fabricated pass. The official engine's zero payoff for no
completed trades remains visible separately. Organizer eligibility and
submission acceptance remain unknown regardless of these local checks.

Phase 3's engineering checkpoint is satisfied: the artifact runs through the
supplied interface, decisions are inspectable, accounting reconciles, risk and
execution scenarios are tested, and results repeat. Profitability is a separate
outcome. Selling and FIFO completion are exercised by controlled engine tests;
we did not force sample-end sales to manufacture eligibility.

Phase 4 should preserve this reference, record momentum/relative-strength and
mean-reversion hypotheses before tuning, and establish chronological research
and validation periods with sufficient permitted data. The supplied September
tick sample alone cannot establish robust alpha. Use realistic exits justified
by the hypothesis and measure completed trades over the competition horizon.
Do not select a candidate solely because it beats this integration sample.

In parallel, confirm registration, assigned repository, current CU schedule,
testing/submission cutoffs and owner identity. The earlier reported competition
dates remain 2–27 November 2026, unconfirmed with the organizer. The organizer's
production runner/validator and effective-dated membership data are unavailable.
The local structural checks do not certify organizer acceptance; `baseline`
must be replaced with the actual registered identity before submission.
