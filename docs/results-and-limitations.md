# Results and limitations

## Atomic learning

| Initialization | Epoch 1 qualified / 3 | Epoch 2 | Epoch 4 |
| --- | --- | --- | --- |
| Base | 0 | 1 | 3 |
| Instruct | 0 | 2 | 3 |

At epoch 4, all Instruct seeds and Base 1729/2718 have perfect recorded semantic/family performance. Base 31415 has 99.9447% semantic accuracy, 99.5192% minimum class accuracy and 184/186 planning success; other families are perfect. Development qualification cannot estimate held-out composition generalization.

## Composition and controlled diagnostics

C1 success is 0/16 per seed. Structurally valid actions: 289/289, 105/105, 116/116. Step-limit episodes: 6, 0, 1; unsuccessful explicit finishes: 10, 16, 15. All 48 first actions query backlog. These are 16 shared scenes, not 48 independent environments.

C2 yields 0/16 paired first-action changes for every label contrast and seed. C3 yields 0/16 changes under tested field removal; tool restrictions yield 16/16 changes per seed. These bounded null observations do not establish absence of label/state effects, unchanged logits or semantic incapacity. No significance test or equivalence margin was registered here.

C4 planning remains 16/16 correct under Native4 and Union8; rollover changes from 16/16 to 0/16 per seed, with all 16 pairs native-correct/union-wrong. On the tested inputs the interface expansion causes a first-query change. This does not separate displayed tools from decoder vocabulary or establish a population effect. It does not prove joint-interface training repairs composition.

## Complete-flow description diagnostic

| Family | Label / 16 | Description / 16 | Both / label only / description only / neither |
| --- | --- | --- | --- |
| Planning | 10 | 10 | 10 / 0 / 0 / 6 |
| Rollover | 4 | 0 | 0 / 4 / 0 / 12 |
| Composition | 0 | 0 | 0 / 0 / 0 / 16 |

The observed rollover difference is −25 percentage points, not a general estimate that descriptions are harmful. Neither condition passes the complete atomic sample check. Description rollover makes 100 reads and zero writes, then prematurely finishes all 16 episodes. All 948 saved actions are structurally valid. Recovery uncertainty means physical predictions may exceed the saved count (upper bound 964). One checkpoint, historical reuse and fixed descriptions limit inference.

## Data feasibility and unfinished work

U1's saved 18,889 sources form 4,983 components; 502 span partitions and 57 touch history. All exclusions are reproduced, but all rollover strata have zero eligible representatives. Planning singletons have 13 train / 1 development representatives against 128 / 32 required. Reproducible exclusions do not validate every identity definition. No U1 learner qualification, continuation, repair or grouped-holdout result exists. Qualification worlds/reference goals were already accessed and cannot be called unopened; historical sealed final partitions remain outside the reported follow-up evidence.

## Uncertainty and external validity

Samples are small, paired, synthetic and often development/historical scenes; scene selection is not a random population sample. Three training seeds characterize these runs, not broad model-family uncertainty. Counts are reported directly without invented p-values or confidence intervals whose sampling assumptions are unsupported. Zero observed success is not proof of zero capability, and unchanged outputs are not equivalence evidence. No live-service deployment, cross-environment transfer, support-method efficacy, model-scale effect or Base/Instruct ranking is established.
