# Annotation contract and pending construction

The two contributions are simulator-grounded structured/language trajectories,
QA/evidence/reproducible annotation, and model/domain/question-type evaluation.
Schema development means iterative creation, enrichment and human revision.
The actual dataset.schema.json 1.0.0 and admitted four-domain export are the source.
simphysqa/0.1.0 wraps rather than rewrites them. restore() is a lossless interface.
Private references, simulation settings, controls, events, units and frames stay exact.
Source file/record hashes, line, sample ID, scenario ID and split group survive migration.

Existing QA is future_state_prediction. It asks multiple typed terminal readouts.
The existing descriptive reference explanation does not establish causal claims.
Generic 'Measured simulator state at the stated timestamp' context is retained as
source data, with meaningful language explicitly pending. No new text is invented.

| Component | Starting status | Required work |
| --- | --- | --- |
| Trajectory descriptions | Pending | Describe observed motion, relations and declared schedule with public bindings |
| Timestamp descriptions | Pending | State-specific meaningful observations, units/frames; observed timestamps only |
| Direct QA | Pending | Construct observed-state questions and exact matching references |
| Predictive QA | Existing typed simulator truth | Enrich questions/language; audit temporal leakage and validity |
| Counterfactual QA | Pending | Matched alternative controls/interventions, shared initial conditions/seeds/model, or verified re-simulation and paired manifests |
| Explanation QA | Pending | Claim-level support; causal claims require intervention/mechanistic verification; allow descriptive/uncertain claims |
| Clarification QA | Pending | Genuine missing public information, underdetermination evidence, justified request; do not invent a reply |
| Evidence bindings | Readout bindings implemented | Extend to each new question/claim/intervention/gap and test evidence sufficiency |

Public exports are built from an allowlist and include the annotations actually
under evaluation. Public timestamp evidence must resolve to observed source states.
Public language bindings are JSON pointers into immutable public input only.
References, future states, simulator validation details, source paths and annotation
generator identity remain private. Pointer checks prevent structural leakage, but
semantic leakage/meaningfulness in free text still needs language validation and
human audit. The software does not pretend pointer existence proves entailment.

Annotation jobs are not implemented/launched in this milestone. Configuration is
configs/simphysqa/annotation.json. attach-annotation accepts a supplied, versioned
result only with exact model identity, prompt/schema versions, settings, attempts,
failures, retry/repair accounting. It imports language without modifying source
facts or reference values. Content-hashed output manifests and provider/cache/budget
boundaries must accompany the later provider adapter. Human review/revision is a
research activity; it is not a mandatory software approval step for generation.

## Alternative annotation-source comparison (separate from main audit)

Pending exact primary/alternative model identities and versions, subset size,
subset manifest and comparison protocol freeze. Use matched physical examples
from the same versioned source release, identical allowed public inputs, requested
annotation families, instructions, schema and comparable generation settings/budgets.
Record model-specific settings when exact settings cannot match. Include invalid
outputs/failures in denominators; retain every attempt and repair. Hash prompts,
outputs and manifests. Do not conflate model-source comparison with a change in
physical examples or prompt difficulty.

Randomize anonymized source labels/order per reviewer and keep generator identity
in an organizer-only key. Reviewers see equivalent references/private evidence and
the fixed rubric; compare paired acceptability and criterion errors by physical
example, with paired trajectory bootstrap uncertainty. Keep original judgments
separate from adjudication. Define this comparison's reviewers, overlap rules and
sample size independently; the main 20/140 design does not power this comparison.
No generator is chosen and no comparison results exist yet.
