# Current progress and Phase 4 handoff

Updated 29 October 2026 (Asia/Bangkok). Project:
[Calgarios/algo-trading](https://github.com/Calgarios/algo-trading), KGI CU league.

**Phases 1 and 2 are merged. Phase 3 is complete as a local engineering
milestone in [PR #5](https://github.com/Calgarios/algo-trading/pull/5), pending
review/merge. No tested strategy yet meets all measured prize criteria.**
The next active work is Phase 4 research and chronological validation, alongside
confirmation of organizer access and deadlines.

Read [the Phase 3 follow-up](../phase-3-followup.md) first. It explains the risk
controls, corrects the prize-criteria distinction, reports all requested metrics
and records two failed attempts to improve eligibility. Do not confuse a
complete baseline with a profitable or accepted competition submission.

## Objective and rules clarification

Build a reliable Python strategy using the supplied TradeSim engine, pursuing
positive returns after costs and outperformance of SET50 while controlling risk.
Best Alpha remains the provisional primary target; the user also wants practical
prize eligibility established as early as evidence allows.

The recovered scoring PDF, page 18, lists four common performance criteria:

- Portfolio maximum drawdown strictly below 1.5 times SET50 maximum drawdown.
- At least five completed FIFO round trips.
- Average daily closing exposure at least 50%.
- Expected payoff greater than zero.

**Positive total return is not a universal common criterion.** Best Alpha adds
*nonnegative* total return and excess return (zero qualifies for those additions).
Five distinct stocks is tracked separately as a trading-participation rule.
See [award criteria and source limits](../award-criteria.md). Entry eligibility,
ranking, available prizes and organizer acceptance remain separate questions.

## Completed work

| Milestone | Evidence and status |
| --- | --- |
| Phase 1 planning | Objectives, working rules, priorities and roadmap; PR #1 merged |
| Development guide | Seven-phase Markdown/PDF guide; PR #3 merged; historical progress statements are superseded here |
| Phase 2 integration | Pinned TradeSim 0.2.7, Python 3.13.5, six dependencies, data audit, 17 contract tests and two identical organizer-example runs; PR #2 merged |
| Earlier progress handoff | PR #4 merged; Phase 3 started from main commit 9e9b0d7 |
| Phase 3 original baseline | Deterministic diversified strategy, risk checks, decision/fill logs, independent accounting and eligibility; original reference commit 5bc8859 |
| Phase 3 follow-up | Category-specific prize reporting, optional trade exits, one momentum comparison, restoration-risk fix, 51 passing tests and refreshed deterministic reference; PR #5 updated |

The official engine/data and all six recorded Phase 2 runtime/validation sources
remain unchanged. The workshop example remains integration evidence only: it
lost 99.65% through excessive churn and is not the team's strategy.

## Retained strategy and requested results

The default remains the transparent alphabetical reference: ten eligible names,
20 prior-month closes, monthly quantities worth roughly 7% of initial capital
each, 70% total target allocation. It does not maximize returns or contain an
alpha forecast. Pre-buy caps are 10% per stock, 80% total investment, 20% cash
reserve and ten held names. Fees, slippage, lots, cash and actual fills are checked.
Only one own-symbol IOC is attempted per 15-minute slot. Later price movements
can exceed pre-buy limits; no guaranteed portfolio drawdown cap is claimed.

All results below use the same already-inspected 16 days, 9–30 September 2026,
and 2,906,167 ticks. SET50 returned −4.099496%.

| Metric | Retained original | Alphabetical + exits | Momentum + exits |
| --- | ---: | ---: | ---: |
| Net return | −2.991564% | −4.227932% | −5.550515% |
| SET50 excess return | +1.107932 pp | −0.128436 pp | −1.451019 pp |
| Official maximum drawdown | 2.899616% | 3.794080% | 5.845328% |
| Average closing exposure | 69.693722% | 57.033105% | 54.948217% |
| Distinct traded stocks | 10 | 10 | 10 |
| Completed FIFO round trips | 0 | 349 | 378 |
| Expected payoff | Undefined | −THB 999.31 | −THB 1,390.41 |
| Common performance criteria | Fail | Fail | Fail |
| Best Alpha | Fail | Fail | Fail |

The original payoff is undefined, while the official engine displays 0.00.
Drawdown uses the official daily-close anchor; including initial capital gives
2.991564%, 4.227932% and 5.845328%. Exposure is an average, not the final value.

The first experiment adds net +2% profit-taking, −4% loss exits, ten-session
maximum holding age and no same-day re-entry after a sell intent. The second
uses identical controls with selection by the strongest 20 prior-month closes.
Both complete trades and maintain sufficient average exposure, but negative
payoff still fails the common criteria. Fees rise from THB 11,837 to THB 59,568
and THB 72,957. **Reject both as replacements; keep their configurations and
negative results for research.** No profitable trades, losses or test outcomes
are hidden to manufacture a pass.

## What was verified and what remains limited

- 51 local tests cover the official contracts, selection/history, sizing,
  partial/zero fills, daily state, exit behavior, FIFO accounting and scoring
  boundaries. No GitHub CI workflow is configured in this development repo.
- Independent cash, holdings, raw open costs, NAV, fees, realized P&L, completed
  lots, payoff and portfolio/benchmark metrics reconcile on all sample days.
- Two fresh retained-reference runs match all nine deterministic artifacts and
  preserve the original economic result. The two rejected configurations have
  separate full-sample evidence; they are not validated competition candidates.
- The runner saves exact strategy/config bundles, input/code hashes, plans,
  decisions, actual fills, FIFO records, daily reports, runtime and git context.
- A newly tested engine restoration quirk can misstate a partially sold lot's
  displayed price. Our pre-buy check uses its correct saved market value for
  other symbols until fresh quotes arrive; the official source is not patched.

The sample universe has 48 supplied names, not effective-dated historical SET50
membership. History excludes the current day; callbacks are forming bars on
every tick. Notebook events are symbol/row-index round robin, not globally
chronological. One-symbol IOC orders avoid the known multiple-limit daily-cap
bug. Submission owner, production event order, restart behavior and organizer
validation remain open. Intraday exit latches do not persist through process
restarts; later daily runs re-evaluate actual lots.

## Phase 4: exactly where to continue

Phase 4 has begun only with preliminary negative experiments. The research and
validation milestone is not complete. Continue in this order:

1. Review PR #5 and its evidence; keep the original reference available. Confirm
   its review/merge status before building subsequent branches from main.
2. Establish additional permitted historical ticks and effective-dated universe
   data, then define chronological development and validation periods. September
   has been inspected repeatedly and must not be called untouched validation.
3. Diagnose the recorded exits/momentum failures: entry quality, turnover,
   realized losses and holding horizon. Declare each next hypothesis and its
   acceptance criteria before changing parameters. Consider the planned relative
   strength and mean-reversion families where available history supports them.
4. Compare after fees and slippage using all seven metrics and category-specific
   eligibility. Seek positive payoff with adequate exposure and controlled
   drawdown; Best Alpha additionally needs nonnegative total/excess returns.
   Do not choose a candidate simply because it passes this small sample.
5. Advance a candidate to Phase 5 only when comparison and chronological evidence
   justify it. Otherwise retain the reference and record the failed hypothesis.

Phase 5 portfolio/execution refinement, Phase 6 submission rehearsal and Phase 7
operations remain ahead. The new exits and reporting reduce future engineering
work; they do not remove the need for a strategy with positive net expectancy.

## Open dependencies and urgency

Earlier materials report CU competition dates **2–27 November 2026** and daily
updates before **09:00 Thai time**. These dates and the pre-competition testing
cutoff have not been freshly confirmed. As of 29 October, the reported start is
four calendar days away. Confirm access/deadlines alongside research.

- User/organizer: registration, team/roster identity, personal eligibility,
  assigned competition repository, current schedule/testing cutoff and fallback.
- Technical/organizer: production scheduling, current scoring interpretations,
  permitted longer data, adjustments and historical membership.
- Closing deliverables: earlier guidance calls for a report and video ≤10 minutes;
  current deadline and exact format remain unconfirmed.

The development repository is not automatically the competition repository.
Local owner `baseline` must be replaced by the verified registered identity
before organizer submission. No submission or competition acceptance is claimed.

## Files and reproduction

- [README](../../README.md): installation and default/experimental replay commands.
- [Original specification](../phase-3-baseline-spec.md) and
  [original result](../phase-3-summary.md): unchanged design/reference history.
- [Experiment declaration](../phase-3-exit-experiment.md),
  [follow-up assessment](../phase-3-followup.md),
  [follow-up evidence](../phase-3-followup-evidence.json): current comparisons.
- [Original evidence](../phase-3-run-evidence.json): historical 5bc8859 reference.
- [Phase 2 findings](../phase-2-summary.md) and
  [provenance](../tradesim-0.2.7-provenance.json): verified engine/data foundation.
- `strategy/DiversifiedBaseline.py`, `strategy/baseline.json`: retained default.
- `research/configs/baseline-exits.json`, `research/configs/momentum20-exits.json`:
  rejected development configurations, runnable explicitly with `--config`.
- `scripts/run_phase3.py`, `scripts/phase3_reporting.py`, `scripts/phase3_support.py`:
  local replay, independent reporting and structure checks; not strategy imports.

The original ZIP and large artifacts are not tracked on GitHub. Fresh checkouts
need the original `tradeSim0.2.7.zip` and README setup. Archive SHA-256:
`86ead90a23e36cda27089811851e023abe2e82646c944761628903eed3363249`.

For the next chat:

> Continue Phase 4 of Calgarios/algo-trading. Read docs/current-progress/README.md,
> docs/phase-3-followup.md and its evidence, then check PR #5 status. Phase 3's
> engineering is complete, but all three tested configurations fail measured
> prize criteria. Keep the default reference, record the two rejected experiments,
> and establish permitted chronological research/validation data before tuning.
> Distinguish common criteria from Best Alpha additions. Preserve the official
> engine and Phase 2 integration, and confirm organizer access/deadlines in parallel.
