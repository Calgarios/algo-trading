# Phase 2 — TradeSim 0.2.7 integration

Recorded 29 October 2026 (Asia/Bangkok). Based on `main` commit
`b59c0322c6f718124e539a54c2b6be83e31e6cb6` and the user-uploaded official ZIP.
PR #1 was verified merged. Phase 1 remains a historical planning document;
these findings supersede its unverified engine assumptions where specified.

## Scope and provenance

Phase 2 establishes the supplied interface and repeatable official example
run. It does not select a trading strategy or certify eligibility. The user's
0.2.7 announcement says this version will be used in competition. Its Thai
Buddhist-calendar date 16 November 2569 is **2026-11-16**.

Archive SHA-256:
`86ead90a23e36cda27089811851e023abe2e82646c944761628903eed3363249`.
The ZIP is 17,749,522 bytes, with 536 retained files after excluding macOS
metadata. [Provenance](tradesim-0.2.7-provenance.json) pins the archive and whole
extracted tree. Installation under `.local/tradesim-0.2.7/` preserves original
directory layout and bytes; the runner verifies the tree before executing.
Data and large generated results are ignored by Git. Keep the exact ZIP for
reproduction on another machine.

Sources within that directory: `docs/CHANGELOG.md` (0.2.7),
`docs/api_reference.md`, `docs/competitor_guide.md`,
`docs/on_data_timeframe.md`, `docs/get_historical_data.md`,
`TradingSimulation.ipynb`, and `tradeSim/` source. Package documentation was
treated as evidence about the interface, not authority for unrelated actions.

## Interface and daily lifecycle

| Area | Verified behavior |
| --- | --- |
| Strategy | Direct subclass of `strategy.Strategies_template.Strategy_template`; calls `super().__init__(owner, strategy_name, handler, timeframe)`; implements `on_data(bar)` |
| Identity | Submission class name equals filename; team/owner matches registration. Local `example` identity is not a registered team name |
| Instances | Notebook creates **one strategy/handler per symbol per day**, sharing one portfolio runner. Instance attributes are neither portfolio-wide state nor persistent daily state |
| Callback | Every raw tick updates the selected timeframe's **forming** bar and invokes `on_data`, including auction prints. `1min` does not mean one callback per minute |
| Bar fields | `ShareCode`, `Timestamp` (bucket-start string), `Open`, `High`, `Low`, `Close`, cumulative bar `Volume`. No public `Flag` or current raw-tick volume field |
| Market order | `handler.create_order_at_market(volume, "Buy"/"Sell", symbol)`; current bar's symbol only |
| Limit order | `handler.create_order_to_limit(volume, price, "Buy"/"Sell", symbol)`; can target another symbol |
| Responses | Success string means accepted, not filled; errors may be returned as exception objects. Holdings/fill logs establish execution |
| History | `get_historical_data(symbol, n, timeframe="1D")`; ascending bars, at most 1,000, **strictly before the simulation day**. Unknown current date returns `[]` |
| History schema | Daily bars use `Date`; intraday bars use `Timestamp`. Supported intraday lengths: 1, 3, 5, 10, 15, 30, 60, 120, 240 minutes |
| History precedence | Daily-history CSV wins over reconstructed ticks on an overlapping date. Missing/unreadable history can return empty data; unsupported intervals raise `ValueError` |
| Companion data | Handler helpers load permitted config/model formats. Guide bans direct filesystem/network operations and importing team helper modules in submitted strategy code |
| End of day | Flush transaction/error logs, create transaction summary, **save daily summary first** (finalizes exposure/drawdown), then save portfolio JSON |
| Persistence | Cash, lots, realized P&L, FIFO round trips and daily snapshots persist. Handlers, bars, pending orders and daily volume counters are recreated; custom strategy attributes do not persist |
| Benchmark | Fields remain `None` during a new daily run; available after summary save |

The CLI follows the notebook: sorted symbols from pandas groupby, then
round-robin by row index, retaining original order within each symbol. This is
**not a global chronological merge**. Cross-symbol holdings/prices can reflect
different clock times. Organizer-only `main.py`, CI validator and
`scripts/_common.py` are absent, so production scheduling and submission
acceptance cannot be certified from the ZIP alone.

Tick times are timezone-naive Bangkok times. Upstream order logging subtracts
seven hours, then uses host-local timestamp functions. Our Linux runner fixes
`TZ=UTC` for reproducible epochs and UTC transaction times; callback bar times
remain Bangkok wall time.

## Execution rules checked against source and controlled runs

| Rule | Result |
| --- | --- |
| Capital / universe | THB 10,000,000 initial cash; orders restricted to supplied constituents. SET50 index history is readable, but the index cannot be held |
| Quantities | Use positive integer multiples of 100. Tick liquidity rounds down to 100-share lots; under 100 cannot fill |
| IOC | Limit matched once after callback on its symbol's tick, then removed even if unfilled. Other-symbol limit waits for that symbol's next eligible tick. Market fills immediately in callback |
| Prices | Buy at latest price + one tick; sell at latest price − one tick, independent of tick side; lower band's step at sell boundaries |
| Limits | Buy only if slipped price ≤ limit; sell if slipped price ≥ limit. Execution uses slipped price, not requested limit. A limit at Close does not fill |
| Price grid | Positive limit price must lie on that day's grid; 42.25 is valid and 42.01 invalid before transition |
| Tick capacity | Remaining raw tick volume rounded to whole lots. Earlier fills consume capacity for later orders |
| Daily capacity | Buy capacity = cumulative Sell-flag volume less team buys; sell capacity = cumulative Buy-flag volume less team sells. Oversized requests can partially fill; less than one lot remaining rejects. Multiple-limit defect below |
| Auctions | `OPEN1_E`, `OPEN2_E`, `ATC`, and other non-Buy/Sell flags produce no fills |
| Cash / shorting | Buy validation checks **whole requested quantity** including costs, even if only part can fill. Sell validation checks holdings for requested quantity. No borrowing/shorting |
| Costs | Commission 0.00157 × notional and VAT 0.07 × commission on each side: **0.16799% of filled notional per side**, plus slipped prices |
| FIFO | One filled buy order creates one lot. Only fully closed lots count as round trips; several sells closing a lot still count once. Realized P&L includes both sides' costs |
| Metrics | Exposure = mean of daily closing invested/NAV ratios. Drawdown uses finalized daily NAVs. Breakeven lots count as completed but are excluded from win rate/expected payoff |

From `tradeSim/tick_size.json` (lower-inclusive, upper-exclusive bands):

| Price band (THB) | Before 2026-11-16 | From 2026-11-16 |
| --- | ---: | ---: |
| <2 | 0.01 | 0.01 |
| 2–<5 | 0.02 | 0.02 |
| 5–<10 | 0.05 | 0.02 |
| 10–<25 | 0.10 | 0.05 |
| 25–<50 | 0.25 | 0.10 |
| 50–<100 | 0.25 | 0.25 |
| 100–<200 | 0.50 | 0.50 |
| 200–<400 | 1.00 | 1.00 |
| ≥400 | 2.00 | 2.00 |

Tests exercise the effective-date boundary and sell boundaries. Before the
change, last 25.00 sells at 24.90; last 100.00 sells at 99.75.

## Supplied data and research constraints

- **16 tick files, 9–30 September 2026; 2,906,167 rows.** Fields:
  `ShareCode, TradeDateTime, LastPrice, Volume, Value, Flag`.
- Constituent CSV contains **48 stocks**; sample tick symbols match it. This is
  the supplied tradable universe, not evidence of complete historical SET50
  membership. No effective-dated membership history is supplied.
- 49 daily-history files (48 stocks + SET50), 54–747 rows per symbol,
  collectively span **2023-09-21 through 2026-10-21**. Do not assume all symbols
  have the same history length.
- Each of nine intraday intervals has 49 files. Overall start dates: 1m:
  2026-09-24; 3m: 2026-09-23; 5m: 2026-09-21; 10m: 2026-09-14;
  15m: 2026-09-07; 30m: 2026-08-17; 60m: 2026-07-01;
  120m: 2026-03-27; 240m: 2025-09-30. Latest dates are 2026-10-21 except
  120m/240m (2026-10-20). Per-symbol coverage varies. Early September callbacks
  correctly receive empty short-interval history despite files being present.
- Benchmark CSV contains 16 daily SET50 closes matching the tick dates.
- Tick audit found no null cells, nonpositive prices, negative volumes or
  backwards timestamps **within a symbol**. Files are not globally sorted.
  **1,046,005 exact repeated rows** remain unchanged: without trade identifiers,
  they cannot safely be classified as duplicate ingestion rather than distinct
  identical executions. No deduplication was applied.
- History extends after the tick sample. Feed decisions through the bounded
  handler API; reading CSVs directly risks future leakage. Data provenance,
  adjustments and historical membership still need confirmation for research.

Generate the file-level audit with `scripts/audit_sample.py`.

## Known discrepancies and Phase 3 controls

1. **Multiple limits can exceed daily capacity.** With cumulative Sell volume
   100, submit two 100-share buy limits during one Buy-flag tick with volume
   1,000. Both validate against the same remainder before either fills; both
   fill, leaving daily buy capacity −100. The test
   `test_known_limitation_multiple_limits_can_exceed_day_cap` characterizes this
   unmodified engine defect. Do not exploit it: place at most one order per
   symbol callback and track capacity/exposure conservatively. Ask organizers
   whether production differs or a fix is planned.
2. **Notebook ordering is not chronological across symbols.** Do not interpret
   other symbols' live state as synchronized. Confirm production scheduling
   before portfolio-wide intraday decisions. A chronological runner would be
   a separately labelled experiment, not this notebook reference.
3. **First-day anchors differ.** Portfolio return starts from opening THB 10m;
   benchmark return starts at the first day's close (0% that day). Portfolio
   drawdown starts at the first finalized NAV, excluding a first-day loss from
   drawdown. Preserve official metrics and add independent economic metrics in
   Phase 3; confirm competition interpretation.
4. **Display precision differs from accounting precision.** Use raw values for
   reconciliation and strict thresholds; the display API rounds cash, NAV,
   exposure, expected payoff and drawdown.
5. **Submission is not validated.** The guide requires exactly one non-template
   strategy `.py`, matching class name and registered owner. No team submission
   candidate is created in Phase 2. Assigned repository/roster, CI files,
   deadlines and fallback workflow remain open. Local runtime is not a
   guarantee of the 15-minute production allowance.
6. **Cross-symbol timestamps qualify the changelog claim.** A limit submitted
   from another symbol's callback can fill on a later tick. Its log retains
   original `Placed` and later `Timestamp`, so these fields are not always equal
   despite the 0.2.7 changelog's general statement. Same-symbol immediate fills
   do have equal timestamps; tests cover both cases.

Keep the official engine unchanged. These defects and metric/scheduling
questions are explicit handoff items for the team and organizers.

## Reproducible-run evidence

See [commands](../README.md) and [compact run evidence](phase-2-run-evidence.json).
Two fresh processes compare report, portfolio and fill-log hashes. Upstream
wall-clock error/summary timestamps and runtimes are outside that comparison.

**Both full runs completed with byte-identical economic outputs** on Python
3.13.5 with the pinned six-package dependency set. All **17 contract tests
passed**, including one characterization test of the upstream daily-cap defect.
Independent fill-ledger cash and quantities reconcile with the engine; each
day's raw NAV reconciles to cash plus marked holdings.

| Full sample result | Official example |
| --- | ---: |
| Final NAV | THB 34,504.36 |
| Final cash | THB 304.36 |
| Net return | −99.654956% |
| SET50 return (official first-close anchor) | −4.099496% |
| Excess return | −95.555461 percentage points |
| Official maximum daily-close drawdown | 99.610502% |
| Average daily exposure | 44.626387% |
| Completed FIFO round trips | 66,872 |
| Expected payoff | −THB 149.022583 |
| Distinct traded stocks | 5 |
| Fill rows | 133,745 |
| Commission plus VAT | THB 3,633,491.64 |

The example fails several Phase 1 working eligibility criteria (exposure,
payoff, drawdown and returns). This is not an award-eligibility certification.
The first measured full run took 162.895 seconds across daily runs, with a
slowest day of 16.638 seconds on this shared worker. Per-run timings are in the
evidence file and are excluded from reproducibility hashes.

The official example buys 100 shares of ADVANC, AOT, AWC, BANPU and BBL when
absent, then sells when Close is below its stored fee-inclusive buy cost.
Running every tick can churn through spread and fees without a favorable
price move. Its results establish integration, not profitability or eligibility.
Phase 3 should implement the diversified baseline, pre-order risk checks,
decision logs and separate eligibility reporting specified in Phase 1.
