# SPQ04: clarification QA — complete user specification

Its central requirement should be a demonstrable information gap:

1. Construct a separately versioned incomplete question/view.
2. Identify at least two admissible interpretations or completions consistent with everything visible.
3. Show that they produce different requested answers—beyond the existing scoring tolerance for numerical answers.
4. Ask the smallest clarification that distinguishes them.
5. Supply a recorded reply that resolves the ambiguity, followed by the supported answer, explanation and solution trace.

Missing information must also be absent from descriptions, controller text, associations and other redundant fields. Removing one JSON field while leaving its value elsewhere would not create a genuine gap.

Use existing records and verified outcomes where possible. The pushing/stacking and tethered examples whose selected contrasts fall within tolerance should not automatically become clarification witnesses for those same targets. Choose a supported target or ambiguity that actually changes the answer.

Keep this development work separate from OOD claims and the fresh formal audit sample.

## SPQ04 execution addendum

Continue in the existing session on simphysqa-naacl from 395139d3ee9717df0cb48b480daafa40b691b5f8.
Read the active AGENTS.md and save the complete SPQ04 specification as docs/prompts/SPQ04_clarification_qa.md.

Scope:
Target eight development clarification items, two per domain, using existing engineering trajectories and saved verified outcomes.
Preserve the accepted 48 QA items and all prior artifacts.

Record candidate selection, ambiguity type and qualification results.
Do not force eight passing cases by weakening the information-gap requirement. Report completed, failed and pending counts.

Witness qualification:
Both admissible completions must agree with the entire initially visible input and differ in the information the clarification resolves.

For Boolean answers, require different values.
For numerical answers, require disjoint acceptance regions under the actual scorer—not merely a difference exceeding one tolerance.
For scalar or Euclidean-vector targets with radii r1 and r2, require separation greater than r1+r2. Handle other answer types using their actual scoring and target-binding semantics.

Keep the completion witnesses and their answers organizer-private.
Document how the clarification removes the answer-relevant ambiguity.

Two-stage interaction:
Stage 1: incomplete public question/view; expected behavior is one focused clarification question, without an unjustified unique answer.
Stage 2: recorded clarification reply followed by the resolved question, supported answer, answer explanation and evidence-backed solution trace.

Use a dedicated versioned partial-input contract. Do not fill missing fields with invented defaults simply to pass an existing complete-input schema.

Check every model-visible surface for accidental disclosure, including language annotations, event associations, answer specifications, response schemas, identifiers and task metadata. Regenerate or remove affected derived text consistently in the new view; preserve original artifacts.

Define acceptable equivalent clarification questions and deterministic reply routing. Do not require an exact reference wording. Replies supply the missing information, not the gold answer or private verification.

Prepare initial requests for all nine answering conditions and templates for conditional continuations. Keep tools=[].
Do not present a reference clarification question as an actual model response or count prepared conversations as executed interactions.

Evaluation:
Separate gap recognition, clarification relevance/sufficiency, premature answering, and post-reply answer correctness.
Retain the existing typed scorer after resolution.
Human judgments assess clarification wording and explanation adequacy; do not invent ratings or add a mandatory human generation gate.

Delivery:
Export new private records/witnesses, initial and resolved public views, eight audit packets if all qualify, and three blank reviewer forms.
Update the prompt archive and per-file generation index.
Include one inspectable two-stage example per domain, validation results, exact commands and final commit.

Use no new simulations or provider/model calls for this milestone.
If existing evidence is insufficient, document the limitation and the concrete additional work needed.

Run appropriate cross-family integration checks and document readiness for the later merge. Do not merge to main during SPQ04.
No full-release generation, formal sampling, benchmark execution or OOD claim is part of this milestone.
