# Retention experiment declaration

9 November 2026. Reused September development sample; no independent validation.
Compare C3-equal and C4-equal with their committed Phase 5 controls. The sole
policy change retains the opening share quantity for held stocks that fail a
new-entry filter, instead of targeting zero. Eligible stocks keep their existing
allocation logic. Existing stops, profit exits, risk scaling, order constraints,
fees and execution remain in force. Risk exits can liquidate retained holdings.
No new buys are targeted in an ineligible stock. No end-of-sample liquidation.

Staged strategy SHA-256: 197a97f2ddbec8120513214b280c6e8dfac7988008386966eb896603807985d0. Use the original engine and phase 5 runner. Compare
return, exposure, FIFO count, payoff, drawdown, fees and open losses; report any
exposure difference and do not promote without independent validation. Retention
may increase concentration and leave less cash for new eligible stocks.

Results: [retention comparison](../../docs/result-data-visualisation/phase-5-retention/README.md).
Both official replays and all 32 daily reconciliations completed. Source and
metric hashes are saved in the results JSON. This experiment does not pass the
profitability or promotion gate.
