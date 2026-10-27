# Phase 1 Summary — Project Definition and Development Priorities

- **Project:** `algo-trading`
- **Competition:** KGI Algo Trading Bootcamp & Competition 2026
- **League:** Chulalongkorn University (CU), confirmed by the user
- **Recorded:** 28 October 2026 (Asia/Bangkok)
- **Status:** Phase 1 planning complete; organizer-specific confirmations remain open.

## 1. Purpose and working objective

Build a reproducible Python strategy for the organizer's TradeSim environment that pursues positive returns after costs and outperformance of SET50, manages portfolio risk, and tracks award eligibility.

**Best Alpha is the provisional primary target.** This is a working planning decision, subject to revision. No trading strategy has been selected or validated, and no profitability or award eligibility has been demonstrated.

Registration does not block Phase 1. The actual TradeSim package and sample market data are needed for Phase 2 integration and verification. Whether KGI requires registration to obtain these resources remains unconfirmed.

## 2. First useful version

Deliver one transparent baseline strategy that completes this workflow:

**Available data → stock selection → position sizing → orders → fills → portfolio accounting → performance report.**

The baseline is complete when it:

- Runs through the available sample using the supplied TradeSim interface.
- Checks cash, holdings, and position limits before submitting orders.
- Records decisions, orders, fills, costs, and portfolio values.
- Reports net return, SET50 excess return, drawdown, exposure, completed trades, and eligibility status.
- Reproduces results from recorded code, data, configuration, and any random seed.
- Produces a submission candidate compatible with the organizer's requirements.

The baseline establishes a trustworthy reference for experiments. Its completion is separate from achieving positive returns or qualifying for prizes.

## 3. Working rules checklist

The following rules were recovered from earlier reviews of the supplied KGI materials and competition webpage. They have not been independently reverified for this summary. Current organizer instructions and the actual engine must be reconciled with them.

| Area | Reported requirement | Implementation consequence |
| --- | --- | --- |
| Starting capital and assets | THB 10,000,000; SET50 stocks | Validate the permitted universe and available cash |
| Positions | Cash-funded purchases; no short selling | Prevent purchases beyond available cash and sales beyond holdings |
| Orders | Limit or market-to-limit; IOC | Verify partial fills and cancellation of unfilled quantities |
| Costs | 0.157% commission plus 7% VAT on commission; one-tick slippage | Evaluate returns after costs and verify engine treatment |
| Stock participation | At least five distinct stocks, reported by the earlier webpage review | Track separately from completed round trips |
| Completed trades | At least five FIFO round trips | Reconcile lot completion with the organizer's definition |
| Average exposure | At least 50%, measured from daily closing portfolios | Track the cumulative average, not just current exposure |
| Expected payoff | Greater than zero | Evaluate completed trades with applicable costs |
| Maximum drawdown | Portfolio drawdown strictly below 1.5 × benchmark drawdown | Monitor both; future compliance cannot be guaranteed |
| Best Alpha | Nonnegative total and excess returns, plus common award criteria | Report both and compare net excess return |
| Runtime and submission | Python 3.13; daily runtime no longer than 15 minutes; prescribed strategy file/class structure in the assigned repository | Verify compatibility, measure runtime, and retain a tested fallback |

Formal IOC requirements conflict with introductory pending-order examples in the earlier materials. TradeSim behavior needs inspection and any unresolved rule conflict needs organizer clarification.

This checklist covers development constraints, not a complete determination of personal entry or prize eligibility.

## 4. Research and evaluation decisions

Start with a simple diversified reference strategy. Investigate cross-sectional momentum/relative strength and short-term mean reversion as candidate improvements if the available data supports them.

For each experiment:

1. State the hypothesis and rationale before tuning.
2. Record the data period, configuration, parameters, and code version.
3. Use chronological development and validation periods; reserve an untouched final evaluation period where data permits.
4. Restrict every decision to information available at that time, including stock-universe membership.
5. Compare results after costs against the reference strategy and SET50.
6. Examine drawdown, eligibility, turnover, parameter sensitivity, and performance across available market conditions.
7. Record the decision to retain, revise, or reject the change, including unsuccessful experiments.

Repeatedly tuning against a validation period makes it part of development; it can no longer serve as an untouched final assessment.

Risk controls and meaningful checks begin with the baseline. Later phases deepen them.

## 5. Prioritized backlog

P0 items establish a trustworthy first version. P1 items improve and prepare it for operation.

| Priority | Deliverable | Completion evidence |
| --- | --- | --- |
| P0 | Inspect TradeSim and sample data | Document inputs, callbacks, timestamps, execution, state, and outputs |
| P0 | Reproduce an organizer-compatible example | Repeatable run with recorded inputs and inspectable results |
| P0 | Verify accounting and metrics | Cash, holdings, fees, NAV, and trade counts reconcile on small examples |
| P0 | Implement the baseline | Complete sample run with decision logs and a performance report |
| P0 | Add eligibility reporting | Each measurable criterion has a value and clear status |
| P1 | Compare research candidates | Consistent evaluation across chronological periods |
| P1 | Refine sizing and execution | Measurable benefits with understood costs and risk tradeoffs |
| P1 | Rehearse submission and recovery | Exact artifact passes checks and a tested fallback is retained |

## 6. Development roadmap

| Phase | Main output |
| --- | --- |
| 1. Define objectives and constraints | This brief, working rules, priorities, and open questions |
| 2. Establish the environment | Verified TradeSim interface and reproducible example run |
| 3. Build the baseline | Complete strategy with accounting and eligibility reporting |
| 4. Research candidates | Evidence-based comparisons and a selected candidate |
| 5. Refine portfolio and execution | Tested sizing, diversification, turnover, and execution improvements |
| 6. Validate and rehearse | Final evaluation, compatibility checks, runtime checks, and fallback |
| 7. Operate and document | Daily monitoring, controlled updates, and material for the final report/video |

The schedule will follow confirmed organizer deadlines. Essential submission checks from Phase 6 can be brought forward for the baseline when necessary.

## 7. Open dependencies and handoff

| Open item | Next action |
| --- | --- |
| Registration, assigned repository, and exact testing/submission instructions | User will register and share organizer information when available |
| TradeSim package, sample data, and historical coverage | Obtain official resources and inspect them in Phase 2 |
| Permitted data and decision timing | Verify available fields, publication timing, and historical universe membership |
| Engine behavior | Verify quantity/lot rules, ticks, fills, costs, and state persistence between daily runs |
| Metric edge cases | Clarify break-even trades, zero drawdown, and FIFO completion where documentation is ambiguous |
| Rule discrepancies | Record unresolved differences and obtain organizer clarification as needed |

The assistant will handle technical inspection, implementation, experiments, verification, and documentation. The user will guide major objectives and tradeoffs and provide organizer access and information.

**Phase 1 completion means the working plan is documented. It does not mean registration, rule verification, engine setup, or strategy validation is complete.**

The next implementation step is Phase 2: inspect the official TradeSim package and sample data, then establish the first reproducible run.

## 8. Basis of this summary

This document summarizes the project discussions through 28 October 2026, including the user's confirmation of the CU league and decision to continue planning before registration.

Rule details originate from earlier reviews of:

- The [KGI competition webpage](https://www.kgieworld.co.th/ApiUniversity/algo-trading/competition).
- `KGI AlgoTrading 2026 ALGO workshop_08102026.pdf`.
- `[CU] KGI AlgoTrading 2026 ALGO workshop.pdf`.
- `KGI_ALGO26_Performance_TH.pdf`.

These sources were not reopened during creation of this summary. Working assumptions should be updated when current organizer instructions and the actual engine become available.
