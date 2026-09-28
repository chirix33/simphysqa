# Clarification correction and integration proposal

25 September 2026. This corrects the prototype omission in the post-P07 audit;
that original report and its checksum manifest are preserved as historical evidence.

**Interactive clarification exists in the prototype; production integration, its
trigger, and its connection to OOD assessment remain unfinished.**

Source inspected: `Phi_JEPA_Final_+_Baselines.ipynb`, cells **45 and 51**, counting
from one, `answer_question_with_clarification_demo`. The first LLM call returns
an initial answer, `needs_clarification` and `clarifying_question`. When requested,
the demonstration supplies a scripted clarification response and makes a second
LLM call for a refined answer. Both calls reuse the existing predictions. The
prompt forces clarification; no automatic OOD trigger or validated OOD improvement
is demonstrated. Stage 4 of `Phi_JEPA_Codex_Implementation_Plan.md` already requires
an actual permitted information source, demo-only scripted replies and separate
reporting of interactive runs. Describing assessment status is useful diagnostics,
but is not a replacement for this interaction or a completed clarification task.

## Remaining decisions (proposal only; not implemented in P08)

| Decision | Recommended initial integration | Limit / evaluation requirement |
| --- | --- | --- |
| Trigger | Separate explicit missing-public-information/ambiguity triggers from any future calibrated OOD alarm. Ask only a question whose answer could address the stated uncertainty; allow no useful question/abstention | Current partial, uncalibrated familiarity assessment cannot authorize an automatic OOD alarm. Evaluate trigger precision, unnecessary-question rate and missed useful opportunities separately |
| Permitted reply source | Actual user or an explicitly authorized public information source; record reply provenance and availability at inference time | No private simulator state, future reference trajectory, gold label or scripted benchmark answer. Scripted demonstrations stay a separate condition |
| Refinement behavior | Preserve initial answer, question, real reply and refined answer. Reuse original forecasts and label their limitations; keep original immutable schema/predictions and unsupported target policy | No trajectory correction, hidden contact inference or schema repair. A reply that changes physical conditions would require separately approved reforecasting semantics, not silent reuse as if predictions were recomputed |
| Evaluation | Paired before/after typed accuracy, complete-answer success, support/abstention, question relevance, reply grounding, failure rates, latency and both-call cost | Separate autonomous, scripted-demo and actual interactive results; retain unavailable replies and failures. OOD connection needs independent calibrated recognition evidence and an explicit OOD clarification task |

These are future scientific/interface decisions. The learning pilot does not
implement or execute clarification, and is not delayed by this proposal.
