# Reproduction scope

Run from the repository root with Python 3.11+:

```bash
python3 analysis/reproduce.py
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

No installation or paid calls are needed. The analysis verifies inventory hashes, reaggregates all 192 saved C4 first-action predictions, checks paired correctness against the audit, recomputes M1 qualified-seed counts and checks the description-study/failed-data-gate counts used in the README. It writes no result artifacts and loads no model. The selected simulator tests check transition preconditions, task generation, goals and frame protection; they do not recreate historical model experiments.

Included evidence is a combination of byte-identical audit/prediction reports and explicitly marked scientific-field projections. Source hashes anchor projections to the preserved local originals, but absent originals cannot be reconstructed or authenticated solely from their hashes.

Not reproduced: model training/inference, tokenizer and checkpoint verification, C1 trajectory replay, M1's full episode metrics, description-study episode replay, U1's full graph/exclusions, or original sealed evaluation. The original audit programs depend on omitted snapshots, launch ledgers and large inputs and are not presented as runnable here. No claim of end-to-end reproduction is made.

The current package intentionally contains only the simulator component needed for the documented offline checks, not all historical training/cloud orchestration code. This reduces accidental external execution and keeps the reproducible scope clear.
