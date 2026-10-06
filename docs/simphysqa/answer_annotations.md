# Answer refinement 1.0.3 — 6 October 2026

The [bounded user refinement](../prompts/SPQ02b_answer_refinements.md) supersedes
the explanation rendering details below. Contract/schema/renderer/export 1.0.3
adds shared_claims and per-target explanation_claim_kinds. Rendered explanations
concatenate each evidence-bound shared physical condition once, then each target's
concise evidence-bound result/interpretation. Technical controls/implementation,
solver settings, run identities, hashes, receipt details remain in private traces,
evidence context and verification. Raw references/measurements are not edited.

Orientation difference uses the existing scorer convention:
theta = 2 acos(min(1, abs(dot(q1,q2))/(norm(q1) norm(q2)))), radians, hence q and -q
represent the same rotation. For orientation, alternative_minus_factual is null;
rotation_angle_rad contains theta and difference_kind identifies the convention.
No quaternion component subtraction is described as physical orientation change.
Exact source quaternion values and comparison equality remain unchanged. Scalar
signed differences and non-orientation vector differences retain their meanings.

Export answers-1.0.3 and prompt archive 1.0.4 preserve accepted prior outputs.
The archive recovers accepted answer procedure 1.0.2 from its exact committed
source and inventories both versions separately. The worked provenance example
lists one executed request's actual outputs and later reused copies, alongside a
deterministic procedure. No new simulations, provider calls or human judgments.
Historical accepted specification follows unchanged.

# Private answer explanations and solution procedures — SPQ02b

Accepted parent 1ae35749421283e63344504dc6a5d24ce18f32e7; branch simphysqa-naacl.
The active [user instruction](../prompts/SPQ02b_answer_enrichment.md) expands
eight-only scope to all 40 development QA (16 direct, 16 predictive, 8
counterfactual), plus eight supporting alternatives with 40 total source targets.
This is enrichment of existing answers, not a new explanation-QA family.

## Preservation and schema

Private contract/schema simphysqa-answer-annotation/1.0.2, renderer
grounded-saved-solution/1.0.2; export spq02b-answer-export/1.0.2. Root wrapper
schema ID 0.3.1 adds optional private.answer_annotation; existing family
schema_version values 0.1/0.2/0.3 and their scientific/source fields stay exact.
The original private.reference and lossless restore interface are unchanged.
Removing the private overlay recovers the complete pre-enrichment wrapper.
Audit/rendered reference views replace explanation/explanation_kind/solution_trace
with the new annotation; they are derived references, not rewritten legacy v1
physical records. Supporting alternatives retain source_record, its SHA256, an
explicit multi-target annotation projection and a derived enriched reference.

Public model inputs use accepted association export 1.1.1 exactly. No gold
explanation, trace, private reference, comparison, receipt or alternative outcome
is added to public_record or answering requests. IDs, groups, splits, answers,
tolerances, observations and .2 s cutoffs remain unchanged. Generation and export
use no simulation/provider/model calls. No human generation approval gate exists.

## Target-specific procedures and evidence

Each target gets its own requested entity/channel, timestamp, unit/frame, readout,
claims and steps. Direct answers bind only public observations and target fields;
three steps identify, locate and copy the exact typed measurement, with no future
solve. Predictive traces have six steps: identify; initial conditions/effective
controller/model; actual saved numerical method/settings/run; requested saved
state or Boolean rule; exact answer; admission/replay coverage. A supported
observed-to-saved change is described where a corresponding initial channel exists.

Counterfactual traces have six steps: identify target/omitted event; unchanged
conditions and effective alternative controller; saved matched numerical run;
requested state/channel or Boolean rule; exact readout; exact original replay and
separate original/alternative admission with matched comparison. The eight
counterfactual QA annotations cover precisely their single selected target;
supporting alternative records separately cover every requested source target.

Claim/step bindings contain namespace, JSON pointer, value SHA256 and state/event/
run IDs where relevant. Namespaces public, factual, alternative, pair and context
resolve against the packet's private verification.answer_evidence_roots. State
IDs may coincide across worlds, so readout bindings carry explicit run IDs.
Context embeds actual saved receipts, execution reservations/diagnostics/hashes
and exact source snapshots, not invented numerical steps. Source text hashes
are checked. Validation rerenders and compares the complete annotation canonically,
checks each bound value, and requires receipt equality for verification claims.

Arm removes only the additive +.5 N*m pulse; both base torques remain. Saved
implementation and compiled-model/header evidence resolve scalar generalized
hinge coordinates; inherited world/joint_local declarations remain unchanged.
Driving omits scheduled zero-velocity braking with a maximum .25 N*m limit;
friction/contact dynamics remain, and maximum torque is not realized torque.
Objects omit only the +x COM force on block_1; block_2 remains contextual. Gravity,
contacts/friction remain. Tether removes both acceleration phases and subsequent
prescribed support displacement while retaining gravity/load/cable dynamics.

Boolean explanations retain exact source rules, thresholds, hysteresis/intervals
and recorded event history. The simulator's saved flag and numerical admission
are evidence; sparse observations cannot reconstruct every integration-step
accumulator or continuous-duration predicate. No trace substitutes one
instantaneous value for a historical predicate or invents substep states.

## Verification status and comparisons

Each trace status is evidence_checked_human_unreviewed, with a non-null real
verification_record. Explanation kinds are observed_evidence_readout,
saved_numerical_prediction or matched_omission_numerical_comparison, never a claim
of human-validated quality or a newly authored analytical/causal derivation.
Original source admission is recorded for all predictive trajectories. Exact
factual replay is additionally available for the selected eight SPQ02 groups;
no additional exact replay was performed on the other eight. All alternative
references have separate saved coarse/fine and domain-physics receipts.

The private comparison table distinguishes exact canonical equality, signed
scalar/component difference, typed scorer error and whether a factual answer
passes the alternative scorer. Vector orientation scoring remains sign-invariant
rotation angle; component differences are not presented as rotation angles.
Three Boolean answers are unchanged; two numeric differences are nonzero yet
within answer tolerance. Neither establishes absence of physical effects.
Prose uses Python .8g float formatting (eight significant digits, Boolean
true/false, vectors component-wise). Exact typed numbers are never rounded in
matching, source recovery, structured values, hashes or scoring. Accepted public
event descriptions retain their separate six-significant decimal display rule.

## Resumability and later families

Cache identity includes full original wrapper, evidence context, contract/renderer/
display versions and code/schema hashes. Completed item/export writes are exclusive
create or byte equality checks; stale or modified content fails, never overwrites.
The preliminary 1.0.0 and 1.0.1 exports are retained externally and superseded by 1.0.2. Source-code fingerprints normalize line endings to LF, consistently with .gitattributes, so Git/Windows checkout formatting cannot change cache identity. Evidence bindings select relevant engine/controller modules; complete source snapshots remain private.
Partial packaging stays visible rather than deleting failed work.

Future explanation QA needs supported claims, evidence and connecting steps;
future clarification QA needs a genuine gap, demonstrated underdetermination and
why a requested clarification resolves it. No unique numerical gold answer is
manufactured before missing information is supplied. These families remain
pending, with no new examples created here. Human assessment of all enriched
explanations is pending until independent judgments exist.

## Prompt provenance

[Prompt archive entry point](prompt_archive/README.md) contains exact executed
SPQ01 instructions and all 16 instantiated public inputs, plus pinned
deterministic templates/rules and a deduplicated per-file mapping. One actual
request produced one summary and 11 timestamps; later copies did not incur new
requests. Responses wire instructions/input are preserved without inventing role
messages. Prepared answering prompts are clearly separate and unexecuted.
All 16 executed payloads are recovered, zero unavailable/reconstructed. One
preliminary 1.1.0 association/description source revision is unrecoverable; its
executed hashes and output hashes remain explicit, with accepted successor
templates separate. Exact preliminary association 1.0.0 code was recovered from
a saved installer payload matching its executed SHA256. Credential locations,
headers and organizer-private gold/evidence are excluded from the paper archive.
