# Phase 5 closeout and Phase 6 handoff

Updated 1 November 2026 (Asia/Bangkok). This file contains future work and
lessons. Completed work and measured status belong in
[docs/current-progress](../current-progress/README.md).

## Decision before promotion

Read the [Phase 5 comparison](../result-data-visualisation/phase-5/phase-5-results.md),
[strategy explanations](../phase-5-strategies.md) and
[declared protocol](../phase-5-research-spec.md). Do not interpret the existence
of twenty replays as evidence that a profitable candidate has been established.
Keep the original alphabetical implementation as the engineering fallback and
P-C3 as a historical common-criteria comparator. Neither is a validated profitable
submission. Retain any Phase 5 improvement only as a development hypothesis until
it passes costs, risk, eligibility and new-period evaluation.

The full Phase 5 improvement checkpoint and independent Phase 4 validation stay
open when those conditions are not met. Phase 6 compatibility/recovery work may
proceed in parallel using an explicitly named fallback; production promotion and
claims of successful validation remain blocked.

## Retention experiment follow-up

The [retention-only comparison](../result-data-visualisation/phase-5-retention/README.md)
raised exposure and reduced fees on C3 and C4, but payoff remained negative;
C4 return worsened and C3 accumulated larger open losses. Compare changes at
matched exposure, add explicit risk-cap enforcement and cost-aware turnover,
and test on independent permitted data before promoting any strategy.

## Research that must precede a stronger claim

1. Obtain additional permitted tick sessions and effective-dated constituents.
   The original archive has 48 static names and only September 9–30 ticks. Obtain
   the missing constituents before claiming a complete SET50 universe. Do not
   fabricate names or treat historical daily bars as executable tick validation.
2. Resolve adjustment/corporate-action treatment and historical membership
   availability. Declare development, chronological validation and untouched
   final periods before inspecting their trading outcomes. September has already
   been reused and cannot become a holdout by relabeling a slice.
3. Reassess the forecast horizon and transaction-cost hurdle using only new
   development history. The five-session daily proxy had no positive stock mean
   after ticks/fees. Do not turn an uncertain negative estimate into a claimed
   high win probability. Evaluate strategy-conditional outcomes with sufficient
   samples, non-overlap/embargo, uncertainty and temporal stability before making
   predictive claims. Historical confidence intervals alone do not correct all
   strategy selection or membership biases.
4. Diagnose full net P&L and stock episodes, including unrealized losses. Positive
   completed-lot payoff can coexist with an overall losing portfolio. IOC splits
   can create hundreds of FIFO trips without hundreds of independent ideas.
   Keep both official FIFO count and the user's stricter >5 target explicit.
5. Study the exposure/selection conflict without relaxing filters just to pass.
   A narrow reversion signal cannot sustain 50% exposure under 8% per-name caps
   if only a few names qualify. Compare a predeclared diversified core plus a
   smaller timing sleeve with matched exposure; account for core losses and do
   not manufacture rotations to reach round-trip counts.
   Explicitly compare a guard that targets at least 55% during ordinary stress
   with Phase 5's 35% hard target, while allowing an emergency exit if justified.
   A target alone is not an exposure guarantee: entry scarcity and actual fills
   also matter. Do not use the final sample benchmark drawdown as a live input.
6. Decompose any next change: broader universe, entry filter, turnover rule,
   sizing, and risk guard one at a time. The Phase 5 equal/quality pair isolates
   sizing within the new policy, but comparison with Phase 4 changes multiple
   components. Use actual execution replays for fees, slippage/liquidity and
   parameter sensitivities, keeping all failed variants.
   Test separate entry and retention conditions, minimum signal persistence and
   a cooldown after stop-outs. Phase 5's daily loss of entry eligibility sets a
   zero target and can liquidate a still-viable holding, then allow re-entry on a
   later day. A buy budget and rebalance band alone do not solve that churn.
   Keep genuine risk exits available while testing retention; report closed
   episodes and their holding sessions alongside fragmented FIFO lots.

## Exact artifact and recovery rehearsal

- Freeze the final candidate and fallback by source/config hash, permitted
  dependency versions and data provenance. Record which is a research comparison
  and which, if any, is submitted. Regenerate calibration for the real start date;
  do not ship the September-start companion unchanged for November.
- Implement durable intraday state for consumed execution slots, buy budgets,
  sell/re-entry latches and partial-exit intent through an organizer-supported
  state mechanism. Current engine holdings/cash reload does not persist these
  strategy latches. Test same-day restart before/after partial buy and partial
  stop, next-day restart, idempotency and missing/corrupt state.
- Exercise rejected orders, stale quotes, missing bars, auction ticks, absent
  closing marks, gaps, lot/tick boundary changes (including 16 November), and
  interruptions during save/finalize. Confirm what the actual scheduler permits
  and preserve an inspectable fail-safe procedure.
- Confirm globally chronological versus notebook round-robin events in production.
  Marks from different symbols are currently asynchronous. Review actual sector,
  position and drawdown drift, and the possibility that gaps/partial exits exceed
  intended limits. Do not describe sampled controls as a guaranteed drawdown cap.
- Measure the exact artifact's runtime and memory in the organizer environment
  with headroom below 900 seconds per day. Concurrent local timings are useful
  evidence, not a production guarantee.
- Confirm registered owner/team, roster eligibility, assigned competition
  repository and branch, accepted file/class/dependency format, submission cutoff,
  validation facility, acceptance receipt and rollback. The local owner remains
  `baseline`; the development repository is not automatically the assigned one.
- Rehearse submission and rollback using the permitted procedure; keep exact
  artifacts and acceptance evidence. Do not silently publish or operate a
  strategy on the assumption that local replay equals organizer approval.

## Operations preparation

Earlier materials report competition dates 2–27 November 2026 and updates before
09:00 Asia/Bangkok. As of 1 November, that reported start is tomorrow; the schedule
has not been freshly verified. Confirm it and the testing cutoff before planning
submission. A deadline does not establish profitable evidence.

Prepare daily monitoring for runtime, failures, rejected/partial fills, fees,
realized and unrealized P&L, drawdown, closing/average exposure, symbol/sector
concentration, distinct stocks, FIFO trips, position episodes and award criteria.
Confirm report/video format and deadline; earlier guidance limits the video to
ten minutes. Reuse the Phase 5 PDF and explanation only with their limitations.

## Reproduction and continuation

Use [research/phase5/README.md](../../research/phase5/README.md) for the exact
commands. Keep the original archive outside Git and retain it separately when
moving workspaces. Never overwrite frozen experiment directories; changed
hypotheses need new declarations. Store future lessons here, and put only
completed achievements and measured status in current-progress.
