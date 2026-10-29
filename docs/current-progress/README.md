# Current progress and Phase 3 handoff

**Updated: 29 October 2026 (Asia/Bangkok).**
Project: [Calgarios/algo-trading](https://github.com/Calgarios/algo-trading).
Competition: KGI Algo Trading Bootcamp & Competition 2026, CU league.
Reviewed repository baseline: `78e117f897f4ecfe15fb2df3dce72cc8fc262a1b` on `main`.

**Phases 1 and 2 are complete and merged. We are ready to begin Phase 3:
our first complete baseline strategy. Phase 3 implementation has not started.**
We have a verified local integration and reproducible organizer-example run;
we do not yet have a team strategy, a validated profitable approach, an
eligibility tracker, or an accepted competition submission.

Use this file as the current handoff. The earlier phase summaries and
development guide retain their historical context. In particular, statements
in the guide and its PDF that Phase 2 is next or that the package is missing
are superseded by this file and the Phase 2 evidence.

## 1. Our objective and agreed approach

Build a reproducible Python strategy for the organizer's TradeSim environment
that pursues positive returns after costs and outperformance of SET50, manages
portfolio risk, and measures award eligibility. **Best Alpha remains the
provisional primary target**, not a promise or a final strategy selection.

The first useful version must complete:

**Available data → stock selection → position sizing → orders → fills →
portfolio accounting → performance and eligibility report.**

Keep the initial strategy transparent and diversified. Test momentum/relative
strength and short-term mean reversion later as hypotheses, where data permits.
State hypotheses before tuning, compare after costs, split data chronologically,
record unsuccessful experiments, and preserve untouched evaluation data where
feasible. The September sample has already been inspected and used for
integration; do not present it as an untouched final assessment.

The workshop strategies and exercises are demonstrations; the user did not
request their completion or choose them as our strategy. Early suggestions to
build our own matching engine were superseded by inspection of the supplied
TradeSim package. Keep the official engine unchanged.

## 2. Completed work and GitHub history

| Milestone | What was delivered | Status |
| --- | --- | --- |
| Initial research and setup | Reviewed the supplied competition materials, clarified CU league, established GitHub/cloud access | Context recovered from earlier project chats |
| Phase 1 | Objective, working rules, first-version requirements, priorities, research standards and open dependencies | [PR #1](https://github.com/Calgarios/algo-trading/pull/1) merged; branch deleted |
| Development roadmap | Seven-phase guide in editable Markdown and six-page PDF | [PR #3](https://github.com/Calgarios/algo-trading/pull/3) merged; branch deleted |
| Phase 2 | TradeSim 0.2.7 inspection, pinned setup, data audit, execution/accounting checks and reproducible full-sample example | [PR #2](https://github.com/Calgarios/algo-trading/pull/2) merged; branch deleted |

PR #3 merged before PR #2 even though its number is higher. Both are present
in the reviewed `main`. At review, only `main` remained on the remote; no
GitHub Actions workflow is tracked. The reported tests were run locally, not
by GitHub CI. All three PR discussion timelines were checked and had no comments.

The user has authorized publishing this progress summary through a PR and
merging it into `main`. This documentation update does not implement Phase 3.

## 3. What Phase 2 established

The exact uploaded `tradeSim0.2.7.zip` is pinned by archive and extracted-tree
SHA-256 hashes. The installer retains 536 non-metadata files under
`.local/tradesim-0.2.7/`, preserving their bytes and original layout. Python
3.13.5 and six headless dependencies are pinned. The official engine, data,
notebook and example strategy were not patched.

The runner reproduces the official notebook's event order, starts from THB
10 million, reconstructs the simulator each day, reloads saved portfolio state,
and saves the daily summary before saving the portfolio. It refuses existing
output directories and skipped dates within the selected sample interval.
Reports record code/input hashes, dependencies, configuration, daily metrics,
holdings and runtime. Cash and quantities reconcile independently from fills;
daily NAV reconciles to cash plus marked holdings.

**Recorded validation: 17 tests passed and two fresh full-sample runs produced
byte-identical reports, portfolio JSON and fill logs.** Wall-clock log timestamps,
machine details and runtime measurements are intentionally excluded from that
comparison. This documentation review checked that all six recorded runtime
and validation source hashes still match the tracked files; it did not rerun
the unchanged simulations.

### Sample data

| Item | Verified coverage |
| --- | --- |
| Tick sample | 16 trading days, 9–30 September 2026; 2,906,167 rows |
| Supplied tradable universe | 48 stocks; not an effective-dated history of all SET50 membership |
| Daily history | 49 files including SET50, collectively 21 September 2023–21 October 2026; 54–747 rows per symbol |
| Intraday history | Nine intervals, 49 files each; coverage varies by symbol and interval |
| Short-history limitation | 1-minute history begins 24 September, 3-minute 23 September, 5-minute 21 September; unavailable at the start of the sample |
| Benchmark | 16 SET50 daily closes matching sample dates |
| Audit | No null cells, nonpositive prices, negative volumes or backwards timestamps within a symbol |
| Repeated rows | 1,046,005 identical rows retained; no trade identifiers establish whether these are erroneous duplicates |

### Official example result — integration evidence only

| Metric | Result |
| --- | ---: |
| Final NAV | THB 34,504.36 |
| Net return | −99.654956% |
| SET50 return under the official anchor | −4.099496% |
| Excess return | −95.555461 percentage points |
| Official daily-close maximum drawdown | 99.610502% |
| Average daily exposure | 44.626387% |
| Completed FIFO round trips | 66,872 |
| Expected payoff | −THB 149.022583 |
| Distinct traded stocks / fill rows | 5 / 133,745 |
| Commission plus VAT | THB 3,633,491.64 |

The example repeatedly buys 100 shares of five named stocks and sells when
Close is below its fee-inclusive purchase cost. Running that rule every tick
causes severe churn through spread and fees. **This is not our baseline or a
competition candidate.** It fails several working performance requirements.
The first full run took 162.895 seconds across days, with a slowest day of
16.638 seconds on the shared worker; this is not a production-runtime guarantee.

## 4. Rules and limitations the next implementation must respect

| Finding | Consequence for Phase 3 |
| --- | --- |
| Every tick calls `on_data` with a forming OHLCV bar | Add explicit decision cadence; a `1min` setting does not prevent repeated orders in a minute |
| One strategy instance per symbol per day | Do not rely on instance attributes for shared portfolio state or persistence across days |
| History API excludes the entire current day and caps requests at 1,000 bars | Use bounded history, handle empty/short results, and avoid reading future-dated CSVs into decisions |
| IOC, partial fills and shared tick liquidity | Success means accepted, not filled; reconcile actual holdings before retrying or resizing |
| Positive 100-share lots and valid price grids | Validate sizing and prices; include the 16 November 2026 tick-table change |
| Latest price ± one tick for market and limit fills | A limit at Close does not fill; account for slippage without charging it twice |
| Commission 0.157% plus 7% VAT on commission | Fee is 0.16799% of filled notional per side, before slippage; avoid unnecessary turnover |
| Auction prints do not fill | Do not assume opening/closing auction orders execute; the public bar has no raw `Flag` field |
| Whole requested buy quantity is checked against cash; sales require holdings | Size conservatively, keep a cash buffer, prohibit shorting and reconcile partial fills |
| Multiple limit orders can reuse the same daily allowance | Avoid the documented upstream defect; start with at most one own-symbol order per callback and no overlapping cross-symbol pending orders |
| Notebook uses symbol/row-index round robin, not a global time sort | Avoid treating other symbols' live prices as synchronized; confirm production scheduling before cross-symbol intraday logic |
| Portfolio return, benchmark return and drawdown have different first-day anchors | Preserve official measures and separately label independent economic measures; do not silently replace scoring definitions |
| Display fields round accounting values | Use raw values for reconciliation and strict thresholds |
| Delayed cross-symbol limit fills may have different `Placed` and `Timestamp` | Do not assume the changelog's timestamp-equality claim holds for every order |

The engine's FIFO completion, exclusion of breakeven lots from win-rate/payoff
calculations, and daily-average exposure behavior were inspected. Competition
interpretation of zero benchmark drawdown and other scoring edge cases still
requires confirmation. See the [Phase 2 findings](../phase-2-summary.md) for
the exact behavior and controlled examples.

## 5. Where the seven phases stand

| Phase | Current state | Next output |
| --- | --- | --- |
| 1. Define objectives and constraints | Complete | Maintain assumptions as organizer information changes |
| 2. Establish the environment | Complete | Preserve the verified package and reference run |
| 3. Build the baseline | **Next; not started** | Team strategy, risk checks, decision/fill logs, accounting and eligibility report |
| 4. Research candidates | Not started | Chronological comparisons and experiment log |
| 5. Refine portfolio and execution | Not started | Evidence-backed sizing, turnover and risk improvements |
| 6. Validate and rehearse submission | Not started | Exact-artifact validation, submission rehearsal and tested fallback |
| 7. Operate and document | Not started | Daily monitoring and final report/video material |

Local integration checks from Phase 2 do not constitute Phase 6 organizer
acceptance. Bring essential Phase 6 checks forward if confirmed deadlines
require an early baseline submission.

## 6. Next work: Phase 3

The agreed direction is a simple diversified reference. A reasonable proposed
starting design is deterministic selection from eligible stocks with sufficient
prior-day history, explicit target weights, a cash reserve and infrequent
rebalancing. **Exact selection, number of positions, weights, exposure target,
rebalance cadence and exits have not been chosen or tested.** Record those
choices before measuring performance; do not optimize against the example loss.

Implement in this order:

1. **Specify the baseline.** Fix the selection rule, decision timing, sizing,
   entry/exit rules, missing-history behavior and risk limits. Explain how
   daily reconstructed symbol instances use one consistent portfolio plan.
2. **Build the team strategy and a separate runner path.** Keep the Phase 2
   replay available unchanged. Use the supplied template and matching file/class
   names. Keep research/reporting helpers outside the submitted strategy file;
   do not assume those helpers can be imported on the organizer's runner.
3. **Add execution and risk controls.** Check cash including costs, holdings,
   permitted symbols, lots, per-stock/portfolio limits and actual filled
   quantities. Prevent repeated per-tick churn, duplicate intents and use of
   the daily-cap defect. Use own-symbol execution to limit scheduling ambiguity.
4. **Add inspectable logs and reporting.** Record the information behind each
   decision, intended quantity, accepted/rejected orders, actual fills, costs,
   holdings and daily NAV through a local harness that respects submission
   restrictions. Reconcile cash and FIFO lots independently.
5. **Add eligibility tracking.** Report measured values, thresholds, and
   pass/fail/unknown status. Track five distinct stocks separately from five
   completed round trips; average closing exposure ≥50%; expected payoff >0;
   portfolio drawdown strictly <1.5× benchmark drawdown; and nonnegative total
   and excess return for Best Alpha. These remain working award requirements
   pending current organizer confirmation. Do not manufacture trades solely
   to claim readiness or convert unknown eligibility into a pass.
6. **Validate and record the reference.** Test meaningful risk, partial-fill,
   history, state and metric edge cases; complete the sample twice; compare
   deterministic outputs; measure runtime and produce a Phase 3 handoff PR.

Phase 3 is complete when the baseline runs end to end, its decisions are
explainable, accounting reconciles, risk controls are exercised, results are
reproducible, and the report states performance and eligibility honestly.
Positive returns are evaluated separately from engineering completion. Full
submission acceptance remains conditional on the organizer's actual checks.

## 7. Open dependencies and urgency

Earlier reviewed workshop materials report **CU competition dates of
2–27 November 2026**, daily updates before **09:00 Thai time**, and testing
roughly one week before competition. These were recovered from prior chats,
not freshly confirmed with KGI. As of 29 October, that reported start is four
calendar days away; the literal earlier testing window would already have
passed. **Confirm actual access and deadlines now, alongside baseline work.**

| Open item | Responsibility / next action |
| --- | --- |
| Registration and personal/team entry eligibility | User planned to register; no completion confirmation was found. Obtain organizer confirmation, team identity and roster |
| Assigned competition repository and acceptance process | User supplies access/instructions; assistant verifies exact file/class, branch, dependency and CI requirements. This development repository is not automatically the assigned submission repository |
| Current CU schedule, testing deadline, submission cutoff and fallback | Obtain current organizer instructions; do not infer acceptance from the reported dates or a successful local run |
| Production event ordering, daily-cap defect and scoring anchors | Prepare precise questions/reproduction evidence for organizers; no resolution has been received |
| Permitted data, price adjustments and historical membership | Confirm before expanding research beyond the supplied integration sample |
| Final report/video | Earlier guidance calls for a report and video ≤10 minutes; exact deadline and format remain unconfirmed |

These gaps do not prevent a local Phase 3 baseline. They prevent claims that
we are registered, accepted for competition, prize-eligible, or production-ready.
The assistant handles implementation, verification, experiments and documents;
the user supplies organizer information and guides major goals and tradeoffs.

## 8. Repository map and resuming work

All 15 files tracked at the reviewed baseline were inspected, including the
PDF's extracted text:

| File(s) | Purpose |
| --- | --- |
| [README.md](../../README.md) | Exact environment installation and replay commands |
| [docs/phase-1-summary.md](../phase-1-summary.md) | Phase 1 decisions and working rules |
| [docs/development-guide.md](../development-guide.md), [PDF](../development-guide.pdf) | Seven-phase roadmap; progress text is a pre–Phase 2 snapshot |
| [docs/phase-2-summary.md](../phase-2-summary.md) | Verified interface, data, execution and known discrepancies |
| [docs/phase-2-run-evidence.json](../phase-2-run-evidence.json) | Full reference configuration, daily/final metrics, hashes and runtime evidence |
| [docs/tradesim-0.2.7-provenance.json](../tradesim-0.2.7-provenance.json) | Exact archive and extracted-tree identity |
| [.python-version](../../.python-version), [requirements-phase2.txt](../../requirements-phase2.txt) | Python and dependency pins |
| [scripts/package_support.py](../../scripts/package_support.py) | Paths, file hashes and package-integrity verification |
| [scripts/install_tradesim.py](../../scripts/install_tradesim.py) | Verified installation without overwriting project files |
| [scripts/audit_sample.py](../../scripts/audit_sample.py) | Data coverage/quality inventory |
| [scripts/run_phase2.py](../../scripts/run_phase2.py) | Official-example replay and accounting reconciliation |
| [tests/test_tradesim_contract.py](../../tests/test_tradesim_contract.py) | 17 execution/interface/accounting checks |
| [.gitignore](../../.gitignore) | Excludes environments, raw package/data, ZIPs and generated artifacts |

The original ZIP, installed `.local/` package and large `artifacts/` outputs
are not stored on GitHub. A fresh checkout needs the original upload and the
README setup steps. The recorded archive SHA-256 is
`86ead90a23e36cda27089811851e023abe2e82646c944761628903eed3363249`.
Earlier chats mention `docs/materials-review.md`, `docs/tradesim-inspection.md`
and original workshop files in other workspaces; none is tracked on this
reviewed `main`. Do not assume those files will exist after cloning.

For the next chat:

> Continue Phase 3 of Calgarios/algo-trading for the KGI CU competition. Read
> docs/current-progress/README.md, docs/phase-2-summary.md and the recorded run
> evidence on main. Phases 1 and 2 are complete; PRs #1, #2 and #3 are merged.
> Build our first transparent diversified baseline with risk controls,
> decision/fill logging, accounting reconciliation and eligibility reporting.
> Preserve the unmodified TradeSim 0.2.7 package and Phase 2 replay. Treat the
> organizer example as integration evidence only. Confirm organizer access and
> deadlines in parallel; do not claim submission readiness without their checks.

## 9. Review basis and limits

This summary reconciles the accessible project-chat records for **Start
algorithm trading project**, **Summarize competition rules**, **Locate
algo-trading repository**, **Plan project phases** (including older turns),
**Check project context**, **TradeSim Phase 2**, and both archived **Set up
algo-trading** chats. Unrelated personal chats are outside this project summary.
It also reviews the complete tracked repository, merged PRs #1–#3 and their
discussion timelines. Retrieved chat records and historical assertions are
distinguished from checked-in code and recorded test evidence.

The original workshop PDFs and live competition webpage were not independently
reverified for this update. Historical rule/date statements are attributed
accordingly. No registration confirmation, later organizer ruling, Phase 3
implementation or accepted submission was found in the reviewed material.
