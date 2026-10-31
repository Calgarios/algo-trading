# Phase 4 control implementation

Implementation declaration, 30 October 2026 (Asia/Bangkok), before these runs.
The hypotheses and acceptance criteria remain those in the frozen
[research protocol](phase-4-research-spec.md). All runs are September development.

The research strategy under `research/phase4-controls/strategy/` is a separate
copy of the frozen Phase 3 file, with only control validation and the following
behavior changes. The original strategy, package and replay/accounting sources
are preserved byte for byte.

| ID | Only intended change from its paired reference |
| --- | --- |
| P-C2 | C2 frozen basket, daily equal weights summing to the same guard-dependent target |
| P-C3 | C3 frozen basket, daily equal weights summing to the same guard-dependent target |
| H-C3 | C3 initial ranked quantities frozen from pre-start features; retry residual buys without the band; no sells or subsequent daily guard |
| B-C3 | C3 rebalance activation band is 0.8% of opening NAV instead of 0.4%; active residual intents still retry |
| R-C3 | No behavioral change; two-day parity check for the research copy only |

P-C2/P-C3 retain the original daily risk guard and all fee, cash, quantity,
position, execution-cadence and IOC checks. The basket does not rotate. H-C3's
76% is its initial allocation target, not a promise of constant daily exposure.
Its lack of de-risking is an explicit difference. All use at most ten names.

Preparation reads the recorded pre-start features and original configurations.
The passive targets use only features ending before September 9, THB 10 million,
the C3 ranking and the original 1.2-to-0.8 weight formula. No realized return
or later close is used to prepare any configuration. All configurations and
implementation/replay-source hashes are recorded before execution.

The runner stages the frozen replay scripts and research strategy under each
new output directory, links to the verified package, and invokes the original
replay/accounting code. Each output bundle contains the exact strategy and
configuration used. The unchanged replay report retains its historical generic
Phase 3 title; outer experiment metadata and the comparison report identify the
Phase 4 experiment. Source hashes distinguish the research implementation.

Before full runs, R-C3 must match a fresh original C3 two-day replay for decisions,
plans, FIFO, portfolio and transactions, and for all performance fields. Config
and code hashes intentionally differ. Then P-C2/P-C3/H-C3 run concurrently;
B-C3 runs only after those three finish successfully. Failure results and logs
are retained, and no failed experiment is silently excluded.

Additional cost/lookback/liquidity sensitivity before final selection and the
15-name expansion remain conditional on a candidate and the membership/data
requirements in the protocol. Do not turn the existing September sample into
an untouched validation claim. If no candidate qualifies, record that outcome
and retain the reference instead of extending a parameter search until it wins.
