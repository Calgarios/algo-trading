# Phase 4 inputs and declarations

- `R76.json`: original reference configuration, with only `target_exposure`
  changed from 0.70 to 0.76.
- `manifest.json`: frozen pre-run R76 source/configuration hashes, September
  development sessions and pending comparison identifiers. Preserve this
  declaration; record outcomes in the experiment log rather than rewriting it.
- `input-receipt.json`: receipt for the user-reuploaded TradeSim archive,
  verified against the original archive/tree checksums on 30 October 2026.

The uploaded archive is saved in the repository workspace at
`.local/archives/tradeSim0.2.7.zip`. The unchanged package is installed at
`.local/tradesim-0.2.7/`. Both are Git-ignored. A Git checkout alone therefore
does not include the archive or market data; retain/transfer the ZIP separately
when moving to a new workspace and run the checksum-pinned installer again.

The archive contains the same 16 September tick dates already used in Phase 3.
It does not supply an untouched validation period or effective-dated universe
membership. No project `AGENTS.md` or `SKILL.md` was included in the archive.

Local run evidence:

| Path | Contents |
| --- | --- |
| `artifacts/phase4-R76/` | Declaration receipt, run log and R76 full replay bundle |
| `artifacts/phase4-recovered-suite/` | Ten frozen Phase 3 replays and their full raw bundles |
| `artifacts/phase4-controls/` | Research-copy parity checks and four completed paired/sensitivity controls |
| `artifacts/phase4-final-tests.log` | Final full-suite test output |

These generated artifacts are also Git-ignored. Compact, reproducible findings
are kept in [the final visual report](../../docs/result-data-visualisation/phase-4/phase-4-results.md).
The [experiment log](../../docs/phase-4-experiments.md) holds current status;
the [research protocol](../../docs/phase-4-research-spec.md) remains the pre-run
declaration. Reproduction commands are in the [project README](../../README.md).
