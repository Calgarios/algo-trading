# Next research after the cost-aware alpha experiment

The [new report](../result-data-visualisation/phase-5-alpha/README.md) records
outcomes. The [strategy review](../../research/phase5-alpha/strategy-review.md)
explains the hypotheses. Do not interpret implementation work as a profitable
candidate or completed Best Alpha objective.

1. Obtain a new permitted tick period, including sufficient history to calculate
   signals, and effective-dated constituents. September has now been used for
   multiple development experiments. Repeatedly changing thresholds on it will
   select noise; random train/test splits would leak time dependence.
2. Before inspecting new outcomes, freeze the candidate, its configuration, the
   comparison baseline and acceptance criteria. Count every attempted variant.
   Evaluate a chronological validation period and leave a final period untouched.
3. Identify a strategy-conditional net edge before adding another technical
   indicator. Test non-overlapping holding outcomes after actual tick impact,
   commissions, taxes and stressed costs. Inspect temporal stability and block/
   symbol dependence. Do not use an unconditional negative five-day mean as a
   profitable forecast or a historical win rate as a future probability.
4. Separate risk-control changes from entry changes. Use the same target risk and
   comparable realized exposure for a retention control, a risk-enforcement-only
   version, and any new selection rule. The current bundled experiment cannot
   identify each component's contribution. Preserve genuine emergency reductions
   even when exposure eligibility would fail.
5. For weighting experiments, inspect actual fills and saturated capacities.
   Different formulas can yield identical portfolios. Do not claim quality
   weighting works when the fills and returns are identical. Evaluate whether
   there are enough independently supported entries to achieve 50% exposure
   within name and sector limits, rather than lowering entry standards to fill it.
6. Track complete position episodes, open losses and net stock attribution alongside
   official FIFO trips. Do not blacklist stocks because they lost in the inspected
   sample; formulate causal conditions and validate on new dates. Do not create
   transactions just to raise trip counts or sell only winners to improve payoff.
7. Stress the exact surviving candidate with doubled costs and perturbed parameters
   only after an initial edge survives the base comparison. Reconcile every day,
   investigate cap drift/gaps and run the Phase 6 recovery checklist before
   considering organizer submission. Reconfirm current rules and deadlines.

Keep frozen sources and original evidence unchanged. All current experimental
rules remain research hypotheses; a local Best Alpha pass would still differ
from winning a prize or obtaining organizer acceptance. Current progress contains
measured achievements only; this file and phase-6.md contain the future work.
