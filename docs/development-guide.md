# KGI Algo-Trading
## Development guide: goals, requirements and seven phases

Project: algo-trading | League: Chulalongkorn University (CU)
Prepared: 29 October 2026 (Asia/Bangkok)

> Status update: Phases 1–3 are merged. Phase 4 diagnostics, declared controls
> and visual reporting are complete; independent validation remains blocked by
> missing additional permitted data. Read
> [current progress](current-progress/README.md), the
> [Phase 3 comparison](result-data-visualisation/phase-3-results.md), and
> [next actions](to-do/README.md) before continuing.
> This guide and its PDF preserve the original planning snapshot;
> their progress statements below predate Phase 2 completion.

## Our objective

Build a reliable, reproducible Python trading strategy for KGI's TradeSim environment. Pursue positive returns after trading costs and outperformance of SET50 while managing portfolio risk and tracking award eligibility.

Best Alpha is our provisional primary target. We will select the final trading strategy through evidence. Profitability and award qualification are outcomes to evaluate, not promises attached to a development milestone.

## Where we are now

- Phase 1 planning is complete. Its summary is merged into main through PR #1; the temporary documentation branch has been deleted.
- Phase 2 is the next active stage. The user plans to continue it in a new chat.
- Receipt of the official TradeSim package, usable data, and current organizer instructions has not been verified in this chat. Phase 2 will establish what is available.
- Registration can proceed separately from planning. Whether registration is required to receive the package remains unconfirmed.

## The seven-phase route

1. Define objectives and constraints: establish our working brief and priorities.
2. Establish the environment: understand TradeSim and reproduce a run.
3. Build the baseline: complete the trading-to-reporting workflow.
4. Research candidates: compare a small number of justified hypotheses.
5. Refine portfolio and execution: improve sizing, risk and trading behavior.
6. Validate and rehearse: verify the exact submission and recovery process.
7. Operate and document: monitor results and prepare the final explanation.

Each phase ends with evidence we can review together. Risk controls and testing begin with the baseline; later phases deepen them. We may revisit earlier work when data or organizer instructions change. Essential submission checks can move forward if deadlines require a baseline submission before research is complete.

---

## Requirements that shape the entire project

These are working requirements from earlier reviews of the KGI materials, carried forward from the merged Phase 1 summary. The official sources were not independently reverified for this guide. Current organizer instructions and the actual engine must be reconciled with them.

### Trading and execution

- Starting capital: THB 10,000,000 in simulated funds.
- Universe: permitted SET50 stocks; verify how membership is supplied over time.
- Account: purchases must be cash funded; sales require holdings; no short selling.
- Orders: limit or market-to-limit, with IOC validity. Verify partial fills and cancellation of remaining quantities.
- Costs: commission of 0.157% of traded value, plus VAT of 7% on commission, and one-tick slippage. Verify which costs the engine applies so we do not double count them.
- Quantity rules, board lots, tick sizes, and persistence between daily runs require inspection.

### Performance and award eligibility

- Trade at least five distinct stocks, according to the earlier webpage review.
- Complete at least five FIFO round trips. These are separate from the distinct-stock requirement.
- Maintain average exposure of at least 50%, measured from daily closing portfolios. Current exposure alone does not establish compliance.
- Achieve expected payoff greater than zero on completed trades under the organizer's definitions and cost treatment.
- Keep portfolio maximum drawdown strictly below 1.5 times benchmark maximum drawdown.
- Best Alpha additionally requires nonnegative total and excess returns and the common award criteria; net excess return is the primary ranking objective reported in the earlier review.

Clarification checked against the recovered scoring PDF, page 18: **positive
total return is not a universal common prize criterion.** The common criteria
are drawdown, round trips, exposure and expected payoff. Total return ≥0 and
excess return ≥0 are Best Alpha additions; zero is allowed by those additions.
Five distinct stocks is tracked separately as a trading-participation rule.
See [award criteria and source limits](award-criteria.md) for the distinction
and the status of current organizer verification.

The exposure requirement can conflict with reducing risk by holding cash. We must measure this tradeoff explicitly. Benchmark-relative drawdown and profitability cannot be guaranteed through software checks.

### Runtime and delivery

- Use Python 3.13 and the prescribed strategy file/class structure.
- The reviewed instructions describe a Python strategy in strategy/ on the assigned repository's main branch. Confirm the actual assigned repository and procedure before submission; our development repository is not automatically the competition submission repository.
- A daily run must not exceed 15 minutes. Aim for meaningful headroom.
- Confirm allowed dependencies, submission cutoffs, pre-competition testing, and fallback behavior.
- Earlier materials request a final report and a video of no more than 10 minutes covering stock selection, portfolio management, and risk management. Confirm current format and deadlines.

This is a development checklist, not a complete assessment of personal entry or prize eligibility. Unresolved examples include IOC versus pending-order descriptions, zero-drawdown metrics, break-even trades, and exact FIFO lot completion.

---

## Phase 1 — Define objectives and constraints

Goal: Agree what we are building, how we will judge it, and what remains unknown.

Requirements to begin: Competition materials, project context, the user's league, and a working objective. Registration and engine access do not block this planning stage.

Work:
- Define the first useful version and provisional Best Alpha objective.
- Record reported rules separately from unverified engine behavior.
- Prioritize baseline reliability, accounting, and eligibility reporting.
- Establish research standards and the seven-phase roadmap.
- Record unresolved dependencies and responsibilities.

Deliverables: Project brief, working rules checklist, prioritized backlog, and roadmap. The Phase 1 summary is already on main.

Completion checkpoint: The working plan is documented and uncertainties are explicit. This does not imply registration, complete rule verification, a configured engine, or a validated strategy.

Status: Planning complete; update the brief when organizer instructions arrive.

## Phase 2 — Establish a trustworthy environment

Goal: Understand the supplied engine and data well enough to trust our first run.

Requirements to begin: Official TradeSim package, sample market data, setup instructions, and applicable usage rules. Historical coverage and submission access can be recorded as open dependencies if initially unavailable.

Work:
- Inventory package versions, dependencies, data files, and examples.
- Establish a compatible Python 3.13 environment.
- Inspect the strategy interface, callbacks, timestamps, historical-data access, and state persistence.
- Verify order types, fills, cancellation, quantity rules, costs, and portfolio outputs.
- Check data coverage, ordering, missing values, and information availability at decision time.
- Run an organizer-compatible example and repeat it with recorded inputs.

Deliverables: Setup/run instructions, engine and data inspection notes, a reproducible example, and a list of remaining questions.

Completion checkpoint: We can explain the example's decisions, orders, fills, cash, holdings, costs, and results, and reproduce them with the same inputs.

If blocked: Document the exact missing package, data, or instruction. Prepare inspection work without inventing engine interfaces or treating synthetic results as competition evidence.

---

## Phase 3 — Build the first complete baseline

Goal: Establish one transparent, working strategy as our reference for improvements.

Requirements to begin: A verified TradeSim interface, usable sample data, and an understood accounting/execution path from Phase 2.

Work:
- Implement a simple strategy that completes data intake, selection, sizing, orders, fills, accounting, and reporting.
- Add cash, holdings, and position checks and handle incomplete fills.
- Log decisions and the information used at the time of each decision.
- Reconcile cash, fees, holdings, NAV, and completed trades on small examples.
- Report net return, SET50 excess return, drawdown, exposure, distinct stocks, completed FIFO round trips, and expected payoff.
- Record code version, data identity, configuration, and any random seed.

Deliverables: Complete baseline, performance report, eligibility tracker, and reproducible reference result.

Completion checkpoint: The sample run completes, accounting reconciles, and the artifact is compatible with the supplied interface. Missing inputs or uncertain metrics appear as unknown rather than incorrectly passing eligibility checks.

Profitability is assessed separately from whether this engineering milestone is complete.

## Phase 4 — Research and compare candidates

Goal: Identify improvements supported by evidence beyond a single attractive backtest.

Requirements to begin: Stable baseline, verified metrics, and sufficient permitted historical data. The amount of available history determines how strong our conclusions can be.

Work:
- Start with a small research set: diversified reference behavior, cross-sectional momentum/relative strength, and short-term mean reversion where feasible.
- State each hypothesis before tuning and record why it could work after costs.
- Split data chronologically into development and validation periods; reserve untouched final evaluation data where feasible.
- Prevent future-information leakage, including stock membership and publication timestamps.
- Compare net results against the baseline and SET50 across available conditions.
- Record parameters, turnover, risk, eligibility, sensitivity, and failed experiments.

Deliverables: Experiment log, comparable candidate reports, and a retain/revise/reject decision with reasons.

Completion checkpoint: Evidence supports a candidate for refinement. If no candidate improves on the baseline, retain it and revise the research hypothesis. Repeatedly tuning against validation data makes that period part of development.

---

## Phase 5 — Refine portfolio construction and execution

Goal: Turn a promising candidate into a coherent portfolio with realistic execution behavior.

Requirements to begin: A candidate or retained baseline, reliable diagnostics, and explicit knowledge of its weaknesses.

Work:
- Test position sizing, diversification, entry/exit behavior, turnover, and portfolio concentration.
- Manage the tradeoff between minimum average exposure and drawdown control.
- Account for partial fills, available cash, lot sizes, ticks, fees, and slippage.
- Review whether the competition horizon provides time for intended trades to complete.
- Recheck risk and eligibility after each material change.
- Test sensitivity to plausible cost and parameter changes.

Deliverables: Refined candidate, documented controls, and a comparison showing benefits and costs of each retained change.

Completion checkpoint: Improvements survive realistic assumptions and reasonable sensitivity checks. Remaining weaknesses are understood. Reject added complexity when its benefit is unsupported.

## Phase 6 — Validate and rehearse submission

Goal: Deliver an exact strategy artifact that behaves reliably in the organizer's environment.

Requirements to begin: Candidate version, confirmed submission instructions, representative data, and access to required validation facilities.

Work:
- Freeze the candidate before final evaluation on untouched data, where available.
- Exercise missing data, rejected orders, restarts, and state recovery.
- Measure runtime on representative input with headroom below 15 minutes.
- Verify filenames, class structure, dependencies, and repository/branch requirements.
- Rehearse the actual submission process and confirm how acceptance is reported.
- Retain a tested fallback and document recovery steps.

Deliverables: Evaluation report, compatibility/runtime evidence, identified final and fallback versions, and submission/recovery checklist.

Completion checkpoint: The exact artifact passes applicable checks, runs within limits, and has a recovery procedure. Record any validation limitations explicitly.

If a final evaluation causes strategy changes, it is no longer an untouched assessment. Essential compatibility checks can be performed earlier for the Phase 3 baseline.

---

## Phase 7 — Operate, review and document

Goal: Run reliably during the competition and preserve a clear explanation of results.

Requirements to begin: Accepted submission, verified schedule and access, tested fallback, and available daily results.

Work:
- Monitor execution completion, errors, runtime, fills, costs, and portfolio state.
- Track net performance, SET50 comparison, drawdown, average exposure, and eligibility.
- Investigate differences between expected and observed behavior.
- Make strategy changes only with recorded rationale and supporting checks; retain recoverable versions.
- Maintain daily records and experiment/decision history.
- Build the final report and video around stock selection, portfolio management, risk management, results, and limitations.

Deliverables: Daily operating records, controlled updates, recovery history when applicable, and final report/video material.

Completion checkpoint: Operations and results are documented, the final strategy is explainable, and required closing submissions are delivered under confirmed organizer instructions.

## How we will work together

- The user provides organizer information, registration/access updates, and decisions on major objectives and tradeoffs.
- The assistant handles technical inspection, implementation, experiments, verification, documentation, and recommendations.
- At each phase boundary, review the result, evidence, uncertainties, and next action.
- Maintain a roadmap, experiment log, decision log, and reproducible run instructions.
- Schedule work against confirmed deadlines. We have not assigned fixed durations without the necessary data, engine, and organizer details.

## Phase 2 handoff checklist

Bring the official package or repository link, sample data, setup documentation, current rules, submission instructions, and any registration updates to the next chat. Share only resources you are permitted to use; keep credentials out of project documents.

Start by reading docs/phase-1-summary.md on main, inventorying the available resources, and identifying the smallest reproducible organizer-compatible run.

## Sources and document status

This guide consolidates our discussions and the merged Phase 1 summary, which was checked on main when this guide was prepared. It adds phase-by-phase execution details without claiming technical work has already been completed.

Project summary: https://github.com/Calgarios/algo-trading/blob/main/docs/phase-1-summary.md

Earlier source materials: KGI competition webpage; KGI AlgoTrading 2026 ALGO workshop_08102026.pdf; [CU] KGI AlgoTrading 2026 ALGO workshop.pdf; KGI_ALGO26_Performance_TH.pdf.

Competition webpage: https://www.kgieworld.co.th/ApiUniversity/algo-trading/competition

These original sources were not reopened for this guide. Resolve conflicting or changed instructions with the organizer and record the resolution before relying on it in implementation.
