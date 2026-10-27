# Evidence audit for this release

The release was prepared from local files, not by repeating older README claims. The machine-readable [source manifest](../SOURCE_MANIFEST.json) records original SHA-256 values and whether a file is byte-identical or a derived field selection.

| Evidence | Role | Availability here |
| --- | --- | --- |
| M1 CPU result summary | Completed atomic follow-up audit | Selected scientific fields from all 18 cells |
| C1/C2/C3/C4 result audits | Completed composition / diagnostic audits | Byte-identical small audit reports in reports/generated |
| C4 per-model evaluation reports | Saved first-action predictions | Three byte-identical reports; reaggregated offline |
| Action competition audit | Posthoc saved-record reanalysis | Group summaries; row-level hashes omitted |
| Instruct recovered audit | Completed exploratory full-flow study | Scientific summary and recovery fields |
| U1 exclusion diagnosis | Saved-data reanalysis; failed gate | Counts, quotas and exclusion summaries |
| Simulator and selected tests | Environment / verifier inspection | Selected original source and tests |

## Mapping readable experiment names to archived identifiers

The README uses descriptive names. Original filenames retain their historical identifiers for traceability:

| README name | Archived identifier |
| --- | --- |
| Initial procedural-support study | RQ1-v3 |
| Component-learning experiment | M1 |
| Composition pilot | C1 |
| Task-label control | C2 |
| State and tool controls | C3 |
| Paired tool-interface experiment | C4 |
| Joint-interface follow-up data preparation | U1 |

## Conflicts resolved

- Older evidence-pack sections call the description study “pending”; the completed 96-episode audit supersedes them.
- Older U1 updates report an audit in progress; the saved exclusion diagnosis reproduces all 18,889 decisions and confirms failure. A grouped-holdout amendment is a draft, not evidence or an executed repair.
- High syntax validity is not workflow success: C1 has 510/510 structurally valid actions and no success.
- Original RQ1-v3 and M1 use different execution/qualification contexts; later M1 success does not complete the original support comparison.
- Final M1 results use amended CPU FP32 evaluation, not original GPU BF16 completion.
- Coverage grammars omit joint queries; the SFT loss still spans the full token vocabulary. A training-time hard mask is not established.

## Evidence still missing from the public bundle

Complete M1 checkpoint outputs, full C1 replay traces, all historical training records, model weights and the entire U1 candidate graph are not packaged. Therefore this release checks summary arithmetic and C4 predictions, but cannot independently reconstruct every historical provenance check or rerun all goal/invariant evaluations. No missing input is filled by invented results. The original feasibility protocols/results and preparation receipts remain in the private working archive; their public summaries here are retrospective, not original preregistrations.

The current release checks do not certify the scientific validity of every historical audit. Recomputed agreement establishes consistency of the supplied saved evidence, not independent replication.
