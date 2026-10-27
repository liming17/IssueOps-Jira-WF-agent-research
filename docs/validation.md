# Release validation

Prepared 2026-10-26 from the existing local evidence. No new model predictions, training or external calls were made for this release.

- 33 selected simulator/oracle/verifier tests passed on Python 3.11+ using only the standard library.
- Saved C4 prediction reports are checked against their original audit hashes and reaggregated into paired correctness counts.
- M1 seed-level qualification counts, C1 structural/success counts, C2/C3 contrasts, coverage totals, fixed-description outcomes and U1 quota shortages are checked by the supplied analysis.
- Markdown relative links and balanced code fences are checked. Mermaid uses basic GitHub-supported flowchart syntax; actual GitHub rendering still requires checking after upload.
- A finite file inventory is supplied. No Git metadata, environment files, weights, downloaded corpus, launcher ledgers, manuscript PDF or cache files are included.

These are release consistency checks and simulator tests, not an independent replication of model experiments. Original frozen records and raw results were not edited.
