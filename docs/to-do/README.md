# Next actions and lessons

Updated 30 October 2026 (Asia/Bangkok). Achievements and present status belong in
[current progress](../current-progress/README.md); this file holds future work.

## Phase 4 closeout and Phase 5 continuation

Start with the [Phase 4 visual report](../result-data-visualisation/phase-4/phase-4-results.md),
its [PDF](../result-data-visualisation/phase-4/phase-4-results.pdf), and the
[experiment log](../phase-4-experiments.md). The declared development experiments
are finished. **Independent Phase 4 validation remains blocked**, so do not mark
the entire phase validated or claim a profitable strategy.

1. Preserve the original alphabetical strategy as the engineering fallback.
   P-C3 is the best new control to study further: equal weighting improves C3,
   and it passes common criteria, but its return remains negative and below R76.
   It is a research comparator, not a promoted submission. P-C2 has only one
   completed lot, H-C3 has none, and B-C3's wider band did not improve net return.
2. Obtain additional permitted tick data and effective-dated SET50 membership.
   Record data permission, adjustments and when membership was available; declare
   chronological development, validation and final-evaluation periods before
   viewing results. September is consumed development data. Prepare new baskets
   using only history preceding each new start date. Do not recycle the September
   basket or rename a September slice as a holdout.
3. Run the frozen candidate and R76/matched controls on those new periods. Require
   positive payoff, adequate exposure, controlled drawdown and improvement over
   simple controls before promotion. Best Alpha additionally requires nonnegative
   total and excess return. If a candidate reaches that gate, predeclare actual
   replay sensitivities for costs, lookbacks and liquidity before final selection.
   Fixed-fill fee stresses are diagnostics, not substitutes for those replays.
4. The development guide permits **Phase 5 engineering from a retained baseline**.
   Continue with one predeclared change at a time: sizing/concentration, guard
   recovery after drawdown, and turnover/partial-exit behavior. Compare with the
   untouched baseline, R76 and P-C3; keep the Phase 4 validation dependency open.
   Do not automatically add exits to manufacture completed lots.
5. The 15-name fixed-basket expansion is declared but awaits effective-dated
   membership. Keep the current ten-name budget until that requirement is met.
   The intended expansion uses the top-30 prior liquidity pool, at most three
   names per sector and no within-run rotation; declare any revision before testing.

The archive is restored and retained at `.local/archives/tradeSim0.2.7.zip`.
Full evidence is in `artifacts/phase4-recovered-suite`, `artifacts/phase4-R76`
and `artifacts/phase4-controls`. Exact configurations and source hashes are in
`research/phase4/` and `research/phase4-controls/configs/`. Use the repository
README reproduction commands; do not overwrite frozen declarations or outputs.
Project `AGENTS.md`/`SKILL.md` locations remain unresolved; neither was in the ZIP.

Keep the measurement distinctions from this phase: positive completed-lot payoff
can coexist with large unrealized losses, first-close-aligned excess can differ
from official excess, and quote MAE/MFE do not measure executable returns or
portfolio intraday drawdown. Same-time endpoint ticks are deliberately excluded
except the actual fill quotes. Never feed these post-trade diagnostics into a
historical trading decision.

## Portfolio constraints to carry forward

- **Phase 3 is capped at ten distinct traded stocks per simulation**, not merely
  ten simultaneous holdings. Expand the distinct-stock budget in a later phase
  as the user requested. Declare the revised cap, membership/rotation policy,
  liquidity filter and diversification limits before testing. Do not silently
  introduce an eleventh name when replacing a stock.
- User preference: **70–80% average daily closing exposure**, with a 76% regular
  target. Common criterion: at least 50%. Exposure drift, first-day partial fills
  and protective reductions affect the realized average; report target and actual.
- Official maximum drawdown must be **strictly below 1.5× SET50 maximum drawdown**.
  The present guard has daily lag and uses maximum drawdown observed so far, so
  crossing a trigger can keep the lower target active after a recovery. Study
  a separately declared recovery/hysteresis policy and more timely risk updates.
  Assess gaps, partial exits and the conflict between de-risking and exposure.
- Keep portfolio and benchmark measurement anchors explicit. Official daily-close
  drawdown omits first-day loss against initial capital and intraday troughs.
  Record the initial-capital measure separately; obtain intraday risk evidence
  under a confirmed production event order before claiming stronger protection.
- Two names per sector reduces concentration but does not cap correlated risk.
  A ten-name fixed basket cannot replace deteriorating names within this phase.
  Compare broader diversification and explicit covariance/beta controls later.
- C3 and T3 each drifted above the 10% pre-buy position cap for one closing
  observation (10.07% and 10.11%). If a continuous concentration cap is desired,
  design and test an explicit sell/recovery policy, including its turnover cost.
  T3 and T5 each used the 55% protective target for one day while their overall
  average exposure remained in the user's band; inspect those episodes before
  changing the guard.

## Lessons from the completed experiments

- Expected payoff is average net P&L per completed non-breakeven FIFO buy lot,
  not a predicted future return. Small IOC fills create many lots. Do not confuse
  a larger completed-lot count with more independent profitable decisions.
- Fixed profit/loss/age exits in the earlier experiments increased fees and
  worsened returns. More exits did not solve negative payoff. Preserve those
  failures as evidence instead of adding trades solely to reach the minimum.
- Daily rank changes need a turnover budget. The current 0.4%-of-NAV rebalance
  band and 15-minute execution cadence are initial controls, not optimized values.
  Comparisons should include costs, turnover and residual target quantities.
- Indicator methods currently rank allocations within a frozen basket. They are
  not conventional binary SMA/EMA/MACD crossover strategies. A future binary
  entry/exit comparison needs an explicit plan to maintain the exposure minimum.
- The supplied historical API excludes the current day; decision callbacks are
  forming bars on each tick. Keep prior-data validation, aligned return intervals,
  stable ties and date-specific basket preparation when adding features.
- Saved partially sold lots can display misleading restored prices. Use saved
  market value until a fresh quote arrives, and keep the raw-cost reconciliation.
- Notebook replay is symbol/row-index round robin, not globally chronological.
  Preserve it for reproducibility but confirm production scheduling before
  interpreting cross-symbol execution or changing the event order.

## Later engineering and organizer dependencies

Phase 5 covers portfolio/execution refinement; Phase 6 covers exact-artifact
submission and recovery rehearsal; Phase 7 covers operations and closing material.
Use the [development guide](../development-guide.md) for their checkpoints.

- Confirm team/roster registration, personal eligibility, assigned repository,
  current rules and how organizer acceptance is reported. Local owner `baseline`
  is not a verified registered identity, and this development repository is not
  automatically the competition repository.
- Confirm production callback scheduling, restart behavior, allowed dependencies,
  data adjustments, historical membership, zero-benchmark-drawdown interpretation,
  and any rule amendments. Current local working rules are documented in
  [award criteria](../award-criteria.md).
- Add durable decision/exit state and exercise same-day restarts, missing data,
  rejected orders and recovery under the actual organizer environment. Intraday
  latches currently do not persist through process restarts.
- Rehearse the exact strategy/config bundle, verified owner, repository branch,
  runtime ceiling and fallback. Local timing has substantial headroom relative
  to 15 minutes per day, but does not guarantee production runtime.
- Earlier materials report competition dates **2–27 November 2026** and updates
  before **09:00 Thai time**. As of October 30, that reported start is three
  calendar days away. Confirm the schedule, pre-competition testing cutoff and
  fallback with the organizer; these dates are not freshly verified.
- Confirm the final report/video deadline and format. Earlier guidance limits
  the video to ten minutes. The comparison PDF provides reusable explanation
  material, not an already-approved final competition submission.

## Commands and evidence

The [repository README](../../README.md) explains setup and replay. Configurations
and pre-start feature evidence are in `research/phase3-suite/`. Per-run immutable
strategy/config bundles, fill logs, plans, daily metrics and deterministic hashes
are saved under ignored `artifacts/`. The committed comparison includes CSV/JSON,
figures and a reproducible `scripts/build_phase3_results.py` generator.

Keep future guidance here. Update `docs/current-progress/README.md` with completed
work and measured status only.
