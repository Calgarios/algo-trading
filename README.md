# algo-trading

KGI Algo Trading Bootcamp & Competition 2026, CU league.

- [Current progress and Phase 3 handoff](docs/current-progress/README.md)
- [Phase 1 plan](docs/phase-1-summary.md)
- [Phase 2 interface, execution findings and limitations](docs/phase-2-summary.md)
- [Official package provenance](docs/tradesim-0.2.7-provenance.json)

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

Phase 2 establishes execution and reproducibility. The team strategy,
eligibility monitor and organizer submission validation are later work.
The official example's performance is not a strategy recommendation.
