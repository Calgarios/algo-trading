# algo-trading

KGI Algo Trading Bootcamp & Competition 2026, CU league.

- [Current progress](docs/current-progress/README.md)
- [Next actions and lessons](docs/to-do/README.md)
- [Ten-strategy Phase 3 results](docs/result-data-visualisation/phase-3-results.md)
- [Phase 3 comparison PDF](docs/result-data-visualisation/phase-3-results.pdf)
- [Phase 1 plan](docs/phase-1-summary.md)
- [Phase 2 interface, execution findings and limitations](docs/phase-2-summary.md)
- [Official package provenance](docs/tradesim-0.2.7-provenance.json)
- [Phase 3 baseline specification](docs/phase-3-baseline-spec.md)
- [Phase 3 results and limitations](docs/phase-3-summary.md)
- [Phase 3 follow-up and prize criteria](docs/phase-3-followup.md)
- [Common criteria versus Best Alpha](docs/award-criteria.md)

## Reproduce Phase 3

The ten-strategy comparison adds five custom signals and five indicator signals
under one risk/execution layer. Each run freezes ten stocks using only history
available before September 9, targets 76% exposure, and can reduce that target
to 72% or 55% under its drawdown guard. The realized 70–80% exposure preference
is reported separately from the ≥50% common criterion. Exact definitions and
selection rules are in the [predeclared specification](docs/phase-3-ten-strategy-spec.md).

After installing the Phase 2 environment below:

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/run_strategy_suite.py --output artifacts/comparison --workers 3
uv pip install --python .venv/bin/python -r requirements-reporting.txt
.venv/bin/python scripts/build_phase3_results.py --input artifacts/comparison
```

This uses the frozen configurations in `research/phase3-suite/`. The suite checks
their hashes and the preparation sources before running. Regenerate the baskets
independently with `scripts/prepare_strategy_suite.py --output artifacts/prepared-baskets`
and compare with the recorded manifest. A changed hypothesis needs a new declared
experiment, not an overwritten result. The report explains a fresh-process repeat
and the optional `--repeat` argument for including that evidence in the PDF/Markdown.
Reporting packages are local research tools, not strategy runtime dependencies.

All ten use the same official tick dates, benchmark, costs, capital and event
ordering. The baskets differ by strategy; each simulation trades at most ten
distinct names. Daily reports now include all portfolio and SET50 metrics.
September is development data, not untouched validation. The default companion
below remains the original engineering reference; explicit suite configurations
select the new strategies without changing that reference.

Install the pinned environment and original package using the setup commands
below, then run from the repository root:

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/run_phase3.py --output artifacts/baseline-1
.venv/bin/python scripts/run_phase3.py --output artifacts/baseline-2
diff artifacts/baseline-1/reproducible-hashes.json artifacts/baseline-2/reproducible-hashes.json
```

The separate Phase 3 path runs `strategy/DiversifiedBaseline.py` with its
`baseline.json` companion. It selects up to ten names alphabetically using
prior-month history, targets 70% of initial capital, and checks cash, costs,
position count, concentration and exposure before buying. Monthly quantities
and 15-minute execution slots prevent repeated per-tick trading. These are
reference design choices, not tuned alpha signals.

The follow-up adds two explicitly configured development experiments:

```bash
.venv/bin/python scripts/run_phase3.py --config research/configs/baseline-exits.json --output artifacts/exits
.venv/bin/python scripts/run_phase3.py --config research/configs/momentum20-exits.json --output artifacts/momentum
```

Both use net +2% profit-taking, −4% loss exits and a ten-session holding limit;
the second ranks eligible stocks by their 20 prior-month closes. A triggered
exit prevents same-day re-entry, and partial exits retry only actual holdings.
These thresholds can be exceeded between decision slots or during incomplete
fills. Defaults retain the original alphabetical reference; configurations
and outcomes are reported separately. The run copies the exact strategy and
selected configuration into its output bundle for inspection.

Outputs include a readable `report.md`, machine-readable `report.json` with
daily accounting and pass/fail/unknown eligibility, `plans.json` with selection
inputs, `decisions.jsonl` with order responses and actual quantities,
`fifo.json` with independent open/completed lots, engine fills/portfolio files,
and `environment.json` with code revision and daily runtime. Source/config and
package hashes identify the exact inputs. Wall-clock logs and runtime are
excluded from deterministic comparisons. Existing output directories and
skipped dates are refused; `--days 2026-09-09 2026-09-10` runs a smoke check.

Common performance criteria and Best Alpha additions are reported separately:
negative total return does not alone fail the common criteria, but it fails
Best Alpha. Positive expected payoff remains a common requirement.

The local owner `baseline` is not a registered team identity. The single-file
structure is checked locally; actual organizer validation, submission access
and current rules remain open. No sample-end liquidation is forced, so this
reference can fail the completed-round-trip and payoff requirements.

## Reproduce Phase 2

Use Linux and Python **3.13.5** (the runner requires Python 3.13). Obtain the
original organizer `tradeSim0.2.7.zip` shared with this project. The archive and
market data stay local; the installer verifies the exact archive SHA-256 and
extracted file tree. No organizer files are patched.

From the repository root, with `uv` installed:

```bash
uv venv --python 3.13.5 .venv
uv pip install --python .venv/bin/python -r requirements-phase2.txt
.venv/bin/python scripts/install_tradesim.py /path/to/tradeSim0.2.7.zip
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/audit_sample.py --output artifacts/sample-audit.json
.venv/bin/python scripts/run_phase2.py --output artifacts/run-1
.venv/bin/python scripts/run_phase2.py --output artifacts/run-2
diff artifacts/run-1/reproducible-hashes.json artifacts/run-2/reproducible-hashes.json
```

If your home cache is read-only, prefix `uv` commands with
`UV_CACHE_DIR=/workspace/.uv-cache`. A conventional Python 3.13 virtualenv plus
`pip install -r requirements-phase2.txt` also installs this dependency set.
The minimal requirements cover the headless run, not Jupyter or optional
research libraries.

The runner uses the **unchanged official `Example_strategy`**, all 16 supplied
days by default, THB 10 million initial cash and notebook event ordering.
It creates a new simulator and strategy handlers each day, reloads the saved
portfolio, then finalizes and saves that day. Every invocation starts a new
experiment and refuses an existing output directory, preventing accidental
double-counting of days. For a quick two-day check:

```bash
.venv/bin/python scripts/run_phase2.py --output artifacts/smoke \
  --days 2026-09-09 2026-09-10
```

Outputs include:

- `report.json`: configuration, code/input hashes, dependency versions, daily
  metrics and holdings, raw account values, fill-ledger reconciliation and fees.
- `engine/example/`: original fills, portfolio JSON, daily summaries and errors.
- `environment.json`: code revision/dirty status, platform and measured runtimes.
- `reproducible-hashes.json`: hashes of report, portfolio and fill log. Upstream
  wall-clock error/summary timestamps and runtimes are excluded.

Script hashes identify code even in an uncommitted working tree. Use raw values
for precision: upstream display metrics round cash/NAV and drawdown to two
decimals and exposure to four decimals.

Phase 2 establishes execution and reproducibility. Its original runner and
contract tests remain unchanged. The official example's performance is not a
strategy recommendation; Phase 3 uses the separate team baseline described above.
