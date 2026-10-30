# Phase 3 baseline specification

Recorded 29 October 2026, before the first baseline backtest. Version: `baseline-v1`.
This is an engineering reference, not an alpha hypothesis or optimized strategy.

- Universe: the 48 symbols supplied in TradeSim 0.2.7, recorded in the companion
  `strategy/baseline.json`. This is a static integration universe, not historical
  membership. The runner checks it against the pinned package.
- Selection: alphabetically first ten symbols with at least 20 valid daily
  closes before the current calendar month. Read at most 60 daily bars through
  the handler; reject unordered, repeated, nonfinite or nonpositive history.
  The last eligible close must be within seven calendar days of month start.
  Require at least five eligible names; otherwise pause all trading that day.
- Targets: each selected stock receives 7% of the initial THB 10 million divided
  by its last prior-month close, rounded down to 100 shares. Unused allocations
  stay in cash. Targets are constant within a month and rebuilt from history
  after daily reconstruction. No shared mutable strategy state is needed.
- Rebalance: work toward those quantities, selling excess/excluded holdings
  and buying deficits. No stop loss or sample-end liquidation. The capital
  base is fixed; this reference does not compound allocations automatically.
- Execution: one own-symbol market-to-limit IOC at most per 15-minute slot,
  at the first available callback in 10:05–12:25 or 14:35–16:20 Bangkok time
  (inclusive start, exclusive end). These windows avoid expected auctions but
  cannot identify raw flags. Re-read actual holdings and cash before every
  attempt; accepted orders may fill partially or not at all. Retry only in a
  later slot or day; never accumulate pending cross-symbol orders.
- Pre-buy limits: maximum ten held names, 10% per stock, 80% invested, and 20%
  cash reserve. Include both commission and VAT and the applicable one-tick
  slippage in affordability. Estimate NAV from actual cash and latest available
  marks (own symbol updated to current Close); use the smaller of that and
  opening NAV. Account for the immediate cost-induced NAV reduction in limits.
  Quotes across symbols are not synchronized. These are pre-buy controls,
  not guarantees against later price drift; daily breaches are reported.
- Missing/invalid price or history: no invented prices, no borrowing/shorting.
  A completely unusable plan pauses orders. A valid monthly plan can exit
  names that no longer qualify. No trades are forced to meet round-trip rules.
- Submission shape: one direct template subclass with matching file/class
  name, one permitted JSON companion, no filesystem/network operations or
  imports of team helpers. Local owner is `baseline`; registered identity and
  actual organizer validation are still required before submission.

The local harness records the monthly selection inputs, target quantities,
decision inputs, order responses and actual fills; it independently reconciles
cash, fees, holdings, NAV and FIFO lot completion. Official scoring anchors
are preserved; initial-capital drawdown and aligned first-close returns are
reported separately. Missing benchmarks and undefined payoff are unknown.
Working eligibility is separate from confirmed competition acceptance.

Validation will cover partial/zero fills, no per-tick duplicate intent, cash
and concentration caps, history availability, daily restoration, month change,
tick-table transition, FIFO partial closes/breakeven, missing benchmarks and
strict eligibility boundaries, then two full 16-day deterministic replays.
The September sample is integration data already inspected in Phase 2.
