# Phase 5 research artifacts

`strategy/DiversifiedBaseline.py` is a separate research implementation. The
original `strategy/` and Phase 4 control sources remain unchanged.

`configs/manifest.json` freezes the source, calibration and 28 configurations:
20 equal/quality comparisons and eight C1/C3 sensitivity runs. The file
`configs/calibration.json` retains every non-overlapping pre-start calibration
outcome, not only summary statistics. All 48 supplied stocks are assessed.

`positive-gate-declaration/` preserves version 1, including its exact strategy
source. Its positive-net-mean gate rejected every stock on pre-start evidence;
two C1 smoke tests made no trades. It was replaced by the explicit version 2
research declaration before full replays. Old manifest paths describe source
locations at declaration time; the original strategy is archived alongside it.
Neither the rejected gate nor version 2 has independently validated alpha.

After the checksum-pinned TradeSim installation and Python 3.13 setup in the
repository README:

```bash
.venv/bin/python -m unittest discover -s tests -v > artifacts/phase5-final-tests.log 2>&1
.venv/bin/python scripts/run_phase5_suite.py --output artifacts/phase5-suite --workers 4
.venv/bin/python scripts/run_phase5_suite.py --output artifacts/phase5-repeat --only C1-quality --workers 1
.venv/bin/python scripts/build_phase5_results.py \
  --runs artifacts/phase5-suite --repeat artifacts/phase5-repeat \
  --test-log artifacts/phase5-final-tests.log \
  --output docs/result-data-visualisation/phase-5
```

Existing experiment and report directories are refused. Use new paths when
reproducing committed results. `--only` and `--days` allow smoke checks; the final
report requires every declared run and all 16 dates. Preparation can be reproduced
with `scripts/prepare_phase5_configs.py --output artifacts/phase5-prepared`, then compare
calibration/config/source hashes with the committed manifest. Do not modify a
frozen source in place and pretend it belongs to the same experiment.

The suite checks the official 536-file tree before execution. Sensitivities use
the engine's commission class setting inside each process; no package file is
edited. Raw runs retain nine hashed deterministic artifacts, runtime logs,
engine fills and independent accounting. They remain Git-ignored. Compact
results and figures are committed under `docs/result-data-visualisation/phase-5`.

The original archive was recovered from the existing Phase 4 chat attachment on
1 November 2026. It is again retained at `.local/archives/tradeSim0.2.7.zip`; its
SHA-256 remains `86ead90a23e36cda27089811851e023abe2e82646c944761628903eed3363249`.
This adds no new tick dates or effective-dated membership.

Definitions and experiment history: [research protocol](../../docs/phase-5-research-spec.md),
[strategy explanations](../../docs/phase-5-strategies.md).

## Preparation path recovery

A reproduction check exposed a path-resolution defect in the frozen low-level
preparer: it resolves a relative output after entering the package directory.
The default absolute path used for the main declaration is unaffected. Use
`scripts/prepare_phase5_configs.py`, which resolves paths before invoking the
frozen preparer and rejects outputs inside the official package. The frozen
source remains unchanged so the original declaration stays verifiable.

The misplaced generated directory was moved out; the original 536-file tree
checksum was then reverified. No original simulator/data files changed. Four
queued T4/T5 runs failed the package preflight before trading. Their failed
statuses/logs are preserved in `artifacts/phase5-suite`; successful retries are
in `artifacts/phase5-recovery`. The report accepts this recovery explicitly and
keeps both declarations and failed-attempt evidence, rather than rewriting the
first suite status as successful. The independent preparation reproduced all
30 declared JSON files byte for byte.

To rebuild this workspace's report from the preserved initial attempts and
successful recovery runs, include the recovery directory explicitly:

```bash
.venv/bin/python scripts/build_phase5_results.py \
  --runs artifacts/phase5-suite --recovery artifacts/phase5-recovery \
  --repeat artifacts/phase5-repeat --test-log artifacts/phase5-final-tests.log \
  --output artifacts/phase5-rebuilt-report
```

A clean replay using the safe preparation command needs no `--recovery`. The
report rejects recovery evidence for partial trading runs, mismatched
configurations, missing retries or an already-successful original suite.
