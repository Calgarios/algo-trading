# Next actions and lessons

Updated 30 October 2026 (Asia/Bangkok). Achievements and present status belong in
[current progress](../current-progress/README.md); this file holds future work.

## Start Phase 4 here

1. Read the [ten-strategy comparison](../result-data-visualisation/phase-3-results.md)
   and its [PDF](../result-data-visualisation/phase-3-results.pdf), including failures.
   Review [PR #5](https://github.com/Calgarios/algo-trading/pull/5) and its current
   merge status before branching from main. The default alphabetical baseline
   remains an engineering reference; run a research candidate with its explicit
   `research/phase3-suite/<ID>.json` configuration.
2. Obtain additional permitted tick data and effective-dated SET50 membership.
   Declare chronological development, validation and final evaluation periods.
   September 9–30 has been inspected repeatedly; it cannot be reused as untouched
   validation. A new start date needs a basket prepared using only earlier history.
3. Diagnose return and payoff at the symbol/lot level before adding complexity:
   entry quality, adverse price moves, fee/slippage burden, rebalance turnover,
   holding horizon, and realized versus unrealized P&L. Test whether any apparent
   improvement survives a passive portfolio with matched exposure and basket.
4. Declare the next hypothesis and acceptance criteria before running it. Compare
   a small set of defensible changes, retaining all outcomes. Use chronological
   sensitivity checks for lookbacks, rebalance bands, liquidity and costs; do not
   search repeatedly against the same final holdout.
5. Advance a candidate only when results support positive net expectancy with
   adequate exposure and controlled drawdown across more than this short sample.
   Best Alpha additionally needs nonnegative total and excess return. A common
   criteria pass, competition acceptance, prize ranking and robust profitability
   are separate conclusions.

The completed comparison makes the first research priorities concrete: all ten
models have negative completed-lot payoff, and none beats the original reference's
net return. C3 has the best new return; C2 has the lowest new official drawdown.
Treat them as hypotheses for diagnosis, not approved candidates. Include a
separately declared 76%-target version of the original reference as an
exposure-matched control before attributing changes to more elaborate signals.

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
