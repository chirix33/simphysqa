Implement SPQ03: bounded matched-intervention explanation QA.

Continue on simphysqa-naacl from accepted commit 10ace28. Read the active
AGENTS.md and scientific contracts. Save this complete instruction as
docs/prompts/SPQ03_explanation_qa.md.

Goal
Create eight explanation-QA development items, two per domain, using
the eight frozen, verified SPQ02 matched pairs. Preserve the accepted
40-item export, answer annotations 1.0.3, historical artifacts and main.

These are questions explicitly requesting an explanation. They are
distinct from explanations accompanying direct/predictive/counterfactual
answers.

1. Selection and task design

Reuse the eight frozen pair identities and their existing selected
targets. Retain parent trajectory groups, splits and formal exclusions.
Do not replace unchanged outcomes or small contrasts to obtain more
dramatic examples.

Construct readable questions referring to the actual intervention,
entity, quantity and time, rather than relying only on opaque event IDs.

Each question should ask the model to explain:
- What changed between the factual and omission conditions.
- What remained fixed.
- What the supplied outcomes show for the selected target.
- What interpretation is supported and what remains undetermined.

For unchanged Booleans, ask about the unchanged predicate outcome.
Do not imply that all physical behavior was unchanged.
For small numerical contrasts, distinguish numerical difference from
distinguishability under the existing answer tolerance.

2. Public evidence

Provide the original public scenario and unchanged observed prefix.
Retain the established observation cutoff.

Add a separately identified supplied_comparison containing only the
selected factual and alternative target readouts, with condition labels,
quantity, time, unit and frame. These are intentionally supplied
simulation outcomes for an explanation task.

Do not insert them into observed states, relabel them as observations,
or change existing predictive/counterfactual inputs.

Document this task-specific disclosure explicitly. Gold explanations,
solution traces, private rollouts, verification receipts and organizer
identity remain excluded from answering-model requests.

Use tools=[] for all answering conditions.

3. Reference explanation and solution trace

Build concise, case-specific reference explanations from existing
controller definitions, implementation evidence, matched outcomes and
verification receipts. No new simulations or provider/model calls are
needed.

Use claim-level evidence bindings and explicit factual/alternative
namespaces. Include a structured solution trace explaining how the
evidence supports each required claim.

Separate:
- Declared control semantics.
- The controlled change actually implemented.
- The measured matched outcome.
- Any supported physical interpretation.
- Remaining uncertainty.

Matched simulation supports an intervention comparison within the
specified simulator. Do not infer an unverified detailed mechanism from
timing, invent forces/contact histories, or claim real-world causality.

An explanation must do more than repeat the two numbers. It must connect
the actual intervention change, fixed conditions and outcome comparison,
while respecting the available evidence.

For Boolean targets, use their actual threshold/history/duration rules.
Do not infer a duration-based outcome from one terminal measurement.

Keep answer explanations and solution traces meaningful for these new
items, following the accepted cross-family annotation contract.

4. Evaluation contract

Define a versioned explanation rubric with required supported claims,
acceptable paraphrases, material contradictions and unsupported claims.

Separate checks of structured factual content from judgments of prose
quality and explanatory adequacy. Do not use exact text matching, MSE,
or keyword presence as proof that an explanation is correct.

If automatic evaluation covers only factual components, report that
coverage explicitly. Human explanation judgments remain uncollected
until supplied. Do not invent ratings or introduce a mandatory human
generation approval gate.

Ensure the nine answering conditions have a compatible response
contract for explanation QA. Prepare requests only; execute no models.

5. Provenance and export

Assign new explanation-QA sample identities while retaining parent
groups and existing pair identities.

Extend the consolidated prompt/procedure archive and per-file generation
index. Record this milestone as deterministic generation when no
annotation-model request occurred. Preserve all historical provenance.

Export to a new external versioned directory:
- Eight private organizer QA records.
- Eight development audit packets.
- Three separate blank reviewer forms.
- Eight public QA views and 72 prepared requests.
- An index linking the new items to the existing 40 development items.

Do not overwrite prior outputs or select a definitive formal audit sample.

6. Validation and delivery

Validate evidence resolution, target/time/unit/frame fidelity, supplied
comparison disclosure, public/private separation, parent-group
preservation, reference claim consistency and resumability.

Clearly distinguish software tests from empirical simulations and
human judgments.

Deliver:
- One inspectable explanation question/reference/trace per domain.
- Counts of completed, failed and pending items.
- The explanation rubric and evaluation limitations.
- Updated prompt-archive entry point and per-file mappings.
- Exact commands, verification results and final commit.

Clarification QA, full-release generation and answering-model benchmarks
remain subsequent milestones.
