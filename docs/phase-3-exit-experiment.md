# Phase 3 follow-up: exit policy experiment

Declared 29 October 2026, before running this variant. The original monthly
quantity baseline at commit `5bc8859c8a0642c4ce580f5dbd2d1b01511fbc38` and its
reference evidence remain available for comparison.

The original reference has no return-prediction model: alphabetical selection,
roughly 70% allocation and low turnover explain its behavior. Cash reduces
market exposure, position limits constrain concentration, and execution checks
avoid overspending and duplicated intents. They do not maximize returns or
guarantee drawdown, profitability or prize qualification.

Hypothesis: explicit profit, loss and holding-period exits can make completed
trade accounting useful and limit stale losing positions without excessive
turnover. Keep the same selection, targets, cash limits and decision cadence.
Do not select only winners, force liquidation at sample end, or stop counting
trades once five round trips have been reached.

Fixed variant:

- Estimate immediate net sale proceeds using the effective sell-side tick and
  commission/VAT; compare with the raw fee-inclusive cost of current holdings.
- Exit the entire symbol at a net gain of at least 2%, a net loss of at least
  4%, or when the oldest remaining lot is at least ten trading sessions old.
  Count prior sessions through bounded handler history, not calendar days.
- Once an exit triggers, keep that symbol exit-only for the rest of the day,
  retrying actual remaining quantities in later 15-minute slots. Never rebuy
  the same symbol that day. A new daily instance re-evaluates the saved lots;
  any still-aged lot continues to trigger the time exit. Intraday threshold
  latches do not persist across a process restart/day boundary.
- When history is missing, do not fabricate holding age. Price-based risk
  exits still operate on held stocks even if the selection plan is unavailable.
- Re-enter the monthly basket on a later day when no exit applies, subject to
  the original cash/position checks. This can incur additional losses and fees.

This is one declared development experiment using already-inspected September
data, not independent validation. Report every result, including failures.
Promote only if it offers a useful improvement in risk/eligibility without
misrepresenting negative payoff or total return. Positive payoff, drawdown and
future eligibility cannot be enforced by adding orders alone.

## Second hypothesis, declared before its run

The exit-only run showed negative realized payoff by September 24. To test
whether selection adds value, pull forward one Phase 4 hypothesis: rank the
same eligible universe by the return from the first to last of its 20
prior-month closes, highest first, with alphabetical ties. Keep ten stocks,
the same 70% capital target, risk limits, execution cadence and exact exit
thresholds. Recompute the monthly plan only from data before month start.

This `momentum20` score spans 20 observed closes (19 close-to-close changes).
Hypothesis: relative strength can favor persistent trends over an arbitrary
alphabetical basket after costs. This is one fixed comparison, not a parameter
search. The sample has already been inspected, so even a passing result is
development evidence and requires chronological validation in Phase 4.
