# What the investigation changed in my research practice

## 1. Qualification is a statement about test conditions

The original RQ1-v3 question concerned procedural support for composition, but its atomic prerequisites failed. Stopping preserved an important distinction: an infeasible comparison is not evidence that the proposed support methods work or fail. M1 later established atomic competence under another recipe; it did not retroactively complete that comparison.

Even M1's success had a narrower scope than a general “competent agent” label suggests. Its evaluation exposed each workflow's native tools. C4 preserved atomic tasks and expanded the tool interface, and every tested rollover first query changed from correct to incorrect. I learned to specify the interface as part of a competence claim. A future composition test needs complete atomic qualification under the joint interface, not only successful component tests under separate interfaces.

## 2. A useful control challenges the favored interpretation

C1's 0/16 successes per model established failure on the tested compositions, but the test changed several things at once. Treating the task as a composition-specific reasoning test would have outrun the design.

The subsequent controls addressed increasingly specific alternatives. C2 changed labels while keeping composite inputs fixed. C3 crossed state-field removal with tool restriction. Neither unchanged outputs under a narrow intervention nor a mechanically forced query choice identified a complete mechanism. The coverage reanalysis then exposed the absence of competing queries in reconstructed M1 candidate grammars. C4 tested the interface hypothesis directly with paired atomic inputs.

The resulting conclusion was stronger locally and narrower globally: the tested interface expansion caused a first-query error without requiring a composite task. It did not establish which added tool or prompt/decoder component mattered, explain every later action failure, or show that extra training would repair the problem. Choosing a control is therefore also choosing the level of explanation the evidence can support.

## 3. Measurement must distinguish action form, state change and completion

The simulator and evaluation gates made several superficially similar outcomes separable. A call can be structurally valid, violate a tool precondition, change state without satisfying the objective, or finish before the task is complete.

C1 illustrates why structure alone is insufficient: 510/510 saved actions were valid in form, yet no tested composition succeeded. The fixed-description diagnostic adds a different example: description rollover made 100 reads and zero writes, then prematurely finished all 16 scenes. Zero execution errors in that cell reflected the absence of attempted writes, not successful work.

The M1 selection gates also mattered before composition. At epoch 2, Base/31415 cleared the semantic-class thresholds but planning success was 164/186, below the 90% family gate. Selecting only by teacher-forced semantic accuracy would have accepted a checkpoint that the frozen complete-flow rule rejected. I learned to check whether a metric measures the capability named in the claim, rather than treating several high scores as interchangeable evidence.

## 4. Preserve the unit of evidence and the limits of a null result

C1's three models reused 16 scenes. C4's 192 predictions reused 32 scenes across models and interfaces. Counts of models, actions or predictions cannot be substituted for independent scene counts. C4's scenes also came from development qualification, so its paired contrast is not an independent final-test estimate.

Similarly, C2's unchanged first actions did not demonstrate that labels had no influence on logits. The fixed-description study's unchanged planning success did not mean the description was ignored; other behavior changed. Its lower rollover success was evidence about one checkpoint, frozen descriptions and historical scenes, not descriptions in general. Reporting direct counts and paired outcomes was more defensible than inventing a population uncertainty estimate for an unsupported sampling model.

## 5. Reproducibility and scientific adequacy are different checks

Runtime amendments and interruption recovery required preserving what actually ran. Final M1 results use CPU FP32 reference evaluation; limited probes did not establish global equivalence to the earlier GPU runtime. The description study retained 42 completed episodes and recovered 54 missing ones, while disclosing possible unrecorded exposure at the interruption frontier. A complete saved matrix does not erase that provenance limitation.

U1 made the distinction especially concrete. The saved diagnosis reproduced all 18,889 source exclusions, but every rollover stratum remained empty and planning singletons fell short of quotas. That agreement showed the computation was reproducible. It did not prove that every identity rule was scientifically ideal or that the surviving dataset could support training. Changing grouping or holdout definitions would change the claim and needed a prospective amendment rather than a silent repair.

## The question I would carry forward

Would complete atomic qualification under the joint interface change how composition outcomes should be interpreted? That remains an open question, not a result of this project. The work strengthened my interest in reliable agents and evaluation designs that separate component competence, interface transfer and complete-workflow behavior.

[Methods](methods.md) · [Research process](research-process.md) · [Results and limitations](results-and-limitations.md) · [Evidence availability](evidence-audit.md)
