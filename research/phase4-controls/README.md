# Frozen Phase 4 controls

`strategy/DiversifiedBaseline.py` is the explicitly separate research copy.
The original `strategy/DiversifiedBaseline.py` and all Phase 3 configurations
remain unchanged. See the [implementation declaration](../../docs/phase-4-control-implementation.md).

`configs/manifest.json` freezes implementation/replay-source hashes and the
five generated configurations. Four are full development comparisons:
P-C2 and P-C3 use equal weights in their existing baskets; H-C3 holds initial
ranked C3 quantities; B-C3 widens C3's rebalance activation band. R-C3 is only
the two-day behavioral parity check with no intended trading change.

The runner stages the research copy beside unchanged replay/accounting scripts,
verifies the official package, checks parity, and executes all declared outcomes.
Run bundles contain the exact source and configuration. The outer declaration
identifies Phase 4; the inherited generic replay report keeps its older Phase 3
title. These controls are research artifacts, not a promoted competition submission.

See the [visual report](../../docs/result-data-visualisation/phase-4/phase-4-results.md)
for results and [next actions](../../docs/to-do/README.md) for independent validation
and Phase 5 continuation. Do not retune these frozen configurations or overwrite
their outcomes after reading the results.
