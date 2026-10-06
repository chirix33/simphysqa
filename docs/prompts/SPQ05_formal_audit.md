# SPQ05 — Prepare the 140-item human audit

The SimPhysQA foundation has been merged and published to GitHub.
Begin from current main in the existing SimPhysQA worktree, on a new
branch named simphysqa-spq05. Read the active AGENTS.md and scientific
contracts first.

Save this specification as docs/prompts/SPQ05_formal_audit.md.

We are proceeding directly to the 140-item audit. Do not create a
separate 20-item calibration set.

The reviewers will be Ashraf, Professor Kaushik and another student.
Prepare separate R1/R2/R3 forms without assuming their identity mapping.
All three reviewers inspect the SAME 140 frozen QA items independently:
140 unique items, 420 individual item ratings. Do not partition the
sample into mutually exclusive reviewer assignments.

## 1. Scope and population

This is a focused internal human audit of annotation fidelity and
soundness. It reviews physical/global context, trajectory language,
question wording/type, timestamp language and state–event descriptions.

Describe the scope precisely. It is not automatically a comprehensive
audit of every private answer, explanation, trace or benchmark outcome.

Use the existing admitted four-domain physical release as the source.
Do not regenerate the entire physical dataset or enrich the full release
during SPQ05. Preserve source records, IDs, measurements, references,
tolerances, splits, observation cutoffs and historical artifacts.

Use a balanced allocation:
- Four domains × five QA families × seven items = 140 items.
- Families: direct, predictive, counterfactual, explanation, clarification.

Document that pooled results concern this balanced audit design; do not
present them as the natural record-weighted quality of the original
11,105-record predictive release. Do not make adequately powered
domain/family subgroup claims from seven items per cell.

Exclude every existing development/inspected trajectory group in the
authoritative exclusion manifest. Select at most one formal QA item per
distinct trajectory/split group.

## 2. Freeze the sampling and generation protocol before execution

Record the source frame and hashes, eligibility rules, allocation,
sampling algorithm/seed, candidate and reserve ordering, failure policy,
producer commit, schemas, annotation model/settings, deterministic
procedures, validation rules and resource limits.

Use random selection under the documented design. Do not choose cases
because their descriptions look good or intervention effects are large.

Counterfactual and explanation items may legitimately have unchanged
Booleans or numerical contrasts within tolerance.

Clarification items require genuine information gaps, at least two
visible-input-compatible completions and incompatible requested answers
under the actual scorer. Preserve the disjoint-acceptance-region rule.
Record clarification eligibility attrition separately.

Predefine how same-stratum reserves may be used. Retain every eligibility
rejection, generation failure, retry and replacement with its reason.
Do not silently replace failures or change denominators to report success.

Qualification may require additional saved-outcome verification before
the final 140-item manifest is ready. Freeze candidate processing rules
before that work, and freeze final packet identities before human review.

## 3. Bounded generation and verification

Reuse existing admitted inputs and verified outcomes where applicable.
Use the established language, event-association, answer-annotation and
QA-family pipelines consistently.

Run only the annotation calls and simulations needed for the audit
candidate/qualified cases. New matched counterfactual outcomes must have
the established factual-replay and separate admission evidence.
Do not invent alternatives, readouts or causal mechanisms.

Preserve original observation boundaries. Do not expose private future
states as public observations or change cutoffs to manufacture coverage.

Clarification remains explicit query-gap clarification. Explanation QA
must distinguish its intentionally supplied comparison outcomes from
observed prefix states. No new OOD claim.

Print a non-secret preflight with planned requests/attempts, model and
token limits, estimated spend, simulation requirements and applicable
authorized ceilings. Use existing authorized resource budgets; do not
silently expand old ceilings. If a necessary budget or scientific choice
is genuinely unresolved, finish the concrete protocol, dry-run and
estimate before asking only for that missing decision.

Freezing the protocol does not require a new mandatory human approval
gate for every generated item. Proceed within the authorized scope.

## 4. Focused extraction for Professor Kaushik’s review program

Provide a versioned machine-readable extraction and readable index.
Use actual exported packet keys, not guessed aliases.

For each item include:
- sample_id, packet_id, domain, group_id, split and version/hash metadata;
- structured_inputs.global_context;
- language_annotations.trajectory.text and its source bindings;
- qa.question;
- canonical question_type.

For each saved public state include:
- state_id, timestamp and structured_inputs.states[].context;
- matching language_annotations.timestamps[].text, joined by state_id;
- relevant measurements/relations with entities, quantities, units/frames;
- every linked event, preserving event_id, event_type, event_description,
  event_description_status, temporal_relationship, target_entity_ids,
  link_id, matching bindings and description bindings.

Supply the original event schedule and relevant controller declarations
as evidence beside the descriptions, or through directly accessible
source pointers.

Do not substitute generic state.context for generated timestamp language.
Do not treat global physical context and trajectory language as duplicate
paraphrases: they serve different roles.

Preserve states with no linked events. Keep repeated shared event text
associated with each state’s actual temporal relationship. Do not label
scheduled-future declarations as observed application or causal effects.

Missing required fields must be reported explicitly; do not silently
replace them with empty strings. Preserve exact source values and types.

For clarification packets expose clearly labeled initial question/view,
authored clarification, recorded reply and resolved question/view.
Never present authored reference turns as executed model conversations.

Gold answers and extra private verification may remain available through
auditor-only links, but keep them separate from the focused primary
rating scope and all public model inputs. Blind generator identity.

## 5. Reviewer rubric and forms

Freeze a concise guide before formal reviewing begins.

Primary item judgment: acceptable or material_error within the stated
focused scope. Collect separate criterion findings, error categories,
source locations and comments.

Distinguish factual contradiction, unsupported claim, wrong entity/time/
unit/frame, misleading event semantics, question/type mismatch and
readability problems. Explain how explicitly declared limitations and
unresolved semantics should be assessed.

The three reviewers use separate forms and submit independently before
discussion. Blank forms are uncollected, never acceptable ratings.

Preserve original submissions immutably. Store discussion, adjudication,
rubric revisions and proposed annotation corrections separately.
Do not modify frozen packets in response to ratings.

Prepare rating import/validation and an analysis specification before
ratings arrive. Define the pooled summary, agreement estimator,
missing-rating handling and uncertainty method consistently with the
sampling design. Preserve the documented audit-power discrepancy.
Do not claim achieved power, acceptance, agreement or model performance.

## 6. Reproducibility and delivery

Export to a new external versioned root with safe resumability and
exclusive creation. Preserve all prior outputs and manifests.

Deliver:
- Frozen protocol and candidate/eligibility/failure ledger.
- Final 140-item manifest, or an explicit shortfall/blocker report.
- 140 complete private audit packets.
- Focused extraction JSON/JSONL and a readable audit entry point.
- Three separate blank reviewer forms covering identical items.
- Reviewer guide, analysis specification and rating-import commands.
- Public views kept separate from private evidence.
- Updated prompt archive and per-file generation index, distinguishing
  actual executed requests, deterministic procedures and reused outputs.
- Completion report with exact commands, hashes, resource accounting,
  validation results, final commit and inspectable examples.

Verify evidence resolution, sample/group uniqueness and exclusions,
allocation, extraction fidelity, privacy, blank forms, source preservation
and actual saved-output resume.

If 140 valid items cannot be produced under the frozen rules, report
the shortfall honestly rather than relaxing scientific requirements.

Do not execute answering-model benchmarks, generate the full enriched
release, collect/invent reviewer judgments, or merge/push this branch
during SPQ05.

The intended result is a reproducible 140-item audit package ready for
the three humans to review independently.
