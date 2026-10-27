# Methods

## Environment and outcomes

The deterministic simulator represents tickets, developers, capacity, sprint state and pull requests. Tool preconditions reject invalid operations; final-state verification checks goals and protected entities. Workflow evaluation also applies its registered explicit-finish and invariant rules. A structurally valid action is not a successful transition, and a correct first query is not a completed workflow. The included core verifier handles goals/frame checks; it is not the entire historical model-evaluation wrapper.

## Qualification and selection

Original RQ1-v3 compared no support, structured skills and an executable controller, conditional on atomic qualification. Both permitted backbones failed; composition support effects were never estimated. Earlier RQ1-v1/v2 work was feasibility exploration, not confirmatory composition evidence.

M1 is a separate atomic-learning follow-up using SmolLM2-360M Base and Instruct, seeds 1729, 2718, 31415, measured at epochs 1, 2, 4 (18 checkpoints). Atomic-only adaptation uses 20,000 selected training decisions. Each checkpoint is assessed on 5,423 development decisions in 21 classes and 644 closed-loop episodes: ticket creation 256, planning 186, rollover 122, PR synchronization 80. Every class and workflow family must reach 90%, both structural measures 99%, with coverage/oracle controls. The predeclared selection rule chooses the earliest measured epoch qualifying all three seeds, then Base on ties. It is not a Base/Instruct superiority test. Epoch 3 was not measured.

Final M1 and subsequent reported diagnostics use Linux CPU FP32 reference decoding under runtime amendments. Limited CPU/GPU probes do not prove global equivalence to original GPU BF16 evaluation.

## Diagnostic controls

C1 tests 16 rollover-then-planning scenes shared across the three selected Base epoch-4 models, with a 32-step limit. C2 changes three exact task labels on fixed composite inputs (144 first predictions). C3 crosses full/reduced state and Union8/rollover4 tools on 16 fresh scenes shared across models (192 predictions). Reduced state removes priority/estimate but retains assignee. Restricting tools mechanically removes the rival backlog query.

C4 uses the lowest 16 approved M1 development episode indices per atomic family. Task, state, bindings and empty history remain fixed; only displayed signatures and allowed decoder tools expand from four native tools to their eight-tool union. There are 192 predictions, 32 distinct scenes, shared across three models. No predicted action is executed. The joint interface intervention is controlled; its displayed-tool and decoder-vocabulary components are not separated.

The coverage analysis reconstructs validation/evaluation candidate grammars for saved training/development records. It is a reanalysis, not extra training or evidence that SFT used masked tool loss: SFT uses full-vocabulary token loss.

The separate fixed-description diagnostic uses one Instruct/1729/epoch4 model, 16 historical scenes per family for planning, rollover and composition, each under label-only and one frozen description. It measures full workflows under Union8; no training or prompt search. Recovery retained 42 complete episodes and added 54 missing episodes. Possible unrecorded frontier reexposure limits independence.
