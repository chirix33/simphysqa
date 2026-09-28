# Clarification v1 — offline implementation complete

25 September 2026. Implemented after completing the separate
[P08 diagnosis](Post_P08_diagnosis.md). No training, paid calls, new model
generation or empirical benchmark was performed. P08 stays closed as a bounded
pilot with learning quality and research claims unresolved.

The preserved [P08 correction/proposal](P08_clarification_correction_and_proposal.md)
records the prototype's `answer_question_with_clarification_demo` in notebook
cells 45 and 51 (one-based): initial answer and clarification request, scripted
reply, then another LLM answer using existing predictions. Its historical status
was: **Interactive clarification exists in the prototype; production integration,
its trigger, and its connection to OOD assessment remain unfinished.** The user's
new approval supersedes the proposal-only restriction. The answer-layer service
is now implemented and mock-verified; live effectiveness and connection to
calibrated OOD recognition remain unfinished. Assessment explanation is not being
presented as a replacement for the interaction.

## Implemented behavior

`ClarificationService.start` accepts an immutable `PublicProblem`, existing named
forecast and matching deterministic readout. It performs one frozen-answer call
returning a typed initial answer and an optional structured request. Requests name
the specific information gap, affected target IDs, resolution rationale, one
question, existing public JSON-pointer evidence and relevant readout target IDs.
There is no assessment score input or threshold. Null means no useful question;
unsupported/unresolved components remain explicit. Public/readout bindings are
validated. Prompt instructions prohibit requests for outcomes, private state or
missing model capability; contact/support capability alone is rejected by code.
Pointer validity is not proof of semantic relevance, which remains reviewable.

The actual-user interface is `submit_reply(Reply(...))`, with actor/message ID,
source, channel and timestamp. A no-network command-line intake is also provided:

```text
python tools/clarification_reply.py show --root SESSION_ROOT --attempt ATTEMPT_ID
python tools/clarification_reply.py reply --root SESSION_ROOT --attempt ATTEMPT_ID --actor USER_ID --message-id MESSAGE_ID --reply-file REPLY.txt
python tools/clarification_reply.py unavailable --root SESSION_ROOT --attempt ATTEMPT_ID --actor USER_ID --message-id MESSAGE_ID
```

The host must authenticate identity claims. Unavailable information is an explicit
null reply. The `ReplySource` protocol is replaceable, but v1 accepts only actual
users or separately labeled scripted demonstrations; no retrieval is implemented.

Free-text semantics are handled conservatively through `ReplyReview`: a human
reviewer records category, exact reply quote, reason, and checks for unchanged
task/physical assumptions, conflict, supplied outcomes and gap relevance. The
service routes this review deterministically. It does not infer permission from
words such as "usable" in a reply, use fragile keyword classification, or spend a
third LLM call on classification. Unreviewed replies remain pending/unresolved.
This is an explicit operational limitation, not a claim of automatic semantic
classification. Reviewer adjudication is distinct from independent scientific
labels of trigger quality and reply grounding.

| Reviewed category | Status / action |
| --- | --- |
| Usable, original task and physical assumptions preserved | One additional frozen answer call |
| Changed physical assumptions | `reforecast_required`; no new forecast |
| Changed task or answer definition | `revised_task_required`; no original-task improvement claim |
| Conflicting | `unresolved_conflicting_reply` |
| Unusable | `unresolved_unusable_reply` |
| Unavailable | `unresolved_reply_unavailable` |
| Outcome supplied | `unresolved_outcome_supplied`; no success evidence |

The second call receives original public evidence unchanged, initial answer,
request, separately attributed reply and review. It cannot ask another question.
The existing strict answer parser enforces target bindings, Boolean policy and
unsupported statuses. Refinement additionally rejects supported numerical values
that differ from the existing readout; it may abstain, but cannot repair inaccurate
trajectories. It cannot supply stable-stack/support-lost evidence. The 0.02-second
sampled-event/no-interpolation limitation stays in both prompts.

## Persistence, calls and evaluation

Append-only hash-chained records preserve creation/configuration identity,
original schema/forecast/readout, initial answer, request, reply, human review,
refined answer and raw completions separately. Exclusive locks serialize writers;
calls are reserved durably before dispatch. A timeout, malformed completion or
process interruption cannot trigger an automatic retry. At most two call
reservations exist in a normal attempt. Interrupted calls retain unknown usage;
stale locks fail closed and need operational inspection. The records are not an
authentication or adversarial storage system.

`FrozenClarificationAnswer` reuses the settled `gpt-5.6-sol` answer choice, an
explicit versioned prompt and strict response schemas. A budget/authorization
callback must run before its one transport dispatch. There is no hidden retry,
tool invocation or credential loading on import. The host can supply the existing
OpenAI transport only with a newly authorized live budget; existing P08 configs
do not authorize calls. Provider-returned model identity is logged. The configured
alias does not establish access to immutable provider weights.

Generation never imports the evaluator or reads references. The separate
`evaluate_original_reference` bridge verifies a caller-pinned original reference
hash, uses the unchanged public answer specification/tolerances and scores before
and after with the shared typed evaluator. Changed tasks/conditions and supplied
outcomes cannot become original-task after scores. No-question attempts retain
initial results; unanswered requests and failed refinements remain in all-attempt
denominators. Unknown evaluation results/relevance labels are explicitly counted,
not treated as measured errors or model-supplied correctness labels.

Accounting retains initial and refinement latency, token usage, cost and failures;
unknown usage stays unknown rather than zero. Autonomous, scripted and actual
interactive modes are separated, as are independently reviewed and unreviewed
evidence. Call reservations include attempts that fail before transport and are
therefore a conservative upper bound on provider dispatches. There were **zero
actual provider dispatches** in this implementation work.

## Review set and verification

[Ten representative traces](artifacts/P09_clarification/review-v2/evaluation.json)
cover useful wording clarification, no question needed, unavailable reply,
conflict, changed physical conditions, supplied outcomes, changed task, unusable
reply, unanswered request and failed refinement. Each trace contains original
evidence, mock provider payloads, journal and status. The useful case clarifies
"BC" as the already defined boundary-crossing target; its numerical evidence
does not change. This demonstrates software routing and attribution, not improved
physical prediction or scientifically established usefulness.

These are **software fixtures**, not independently reviewed scientific examples.
Scientific trigger-relevance, unnecessary-question, reply-grounding and accuracy
labels are unset. No model decision supplies its own correctness label. The first
fixture export is retained; `review-v2` is the final export after evaluation
accounting additions. All failures stay in the ten-attempt denominator.

Targeted verification command (core environment, CPU, offline):

```text
PYTHONPATH=src:tests python -m unittest test_post_p08_diagnosis test_clarification test_p04a test_p04b -v
```

**55 targeted tests passed.** The tests cover one reply/refinement across restarts, concurrent writers and
journal tampering, interrupted reservations, source-mode separation, initial and
refinement failures, unknown cost, provider identity, explicit authorization,
private-data rejection, false Boolean/numeric invention, changed-task evaluation,
reference identity and actual-reply CLI intake. Exact final results and hashes are
recorded in `artifacts/P09_clarification/final_verification.json`.

## Changed files

| File | Purpose |
| --- | --- |
| `src/phi_jepa/inference/clarification.py` | Interfaces, immutable evidence, journal, one-round workflow and reply routing |
| `src/phi_jepa/providers/clarification.py` | Single-dispatch frozen-answer payload/schema adapter with explicit budget boundary |
| `src/phi_jepa/clarification_evaluation.py` | Original-reference bridge, mode separation and failure-inclusive accounting |
| `docs/assets/clarification_v1.json` | Separate initial/refinement prompts; original adopted assets untouched |
| `tools/clarification_reply.py` | Actual-user intake/inspection without network capability |
| `tools/review_clarification_fixtures.py` | Reviewable mock traces, explicitly nonempirical |
| `tests/test_clarification.py` | Behavioral offline verification |
| `docs/decisions/Post_P08_and_P09_scope.md`, active prompt and progress | Authorization, scope and durable handoff |

The diagnosis has separate scripts, tests, report and evidence. No model,
training, solver, readout, original answer-parser or P07/P08 evidence file changed.
Base source is `c6922b16a254a72be58482773e3410fa6eecd0c8`; these changes are local,
with no commit/push performed by the agent.

## Proposed live evaluation — not authorized or executed

Preselect 12 independently reviewed public cases (two per required six-category
review-set class), with original references/tolerances frozen outside generation.
Use actual user replies with provenance, not scripted benchmark outcomes posing
as interaction. Independently label whether a useful question exists before
seeing the model trigger; review relevance and grounding without treating the
model's request as the correctness label. Report task changes separately. Obtain
real replies only where appropriate; retain all unavailable/unanswered cases.

Compare autonomous initial answers with the interactive condition on those same
12 tasks, at unchanged decoding/readout policy. Allow at most **36 provider
attempts**, **400,000 input tokens**, **80,000 output tokens**, **USD 5**, **one CPU
hour**, **zero GPU training/time**, and **250 MB** new artifacts; stop at the first
cap. Use max 4,096 output tokens per call and no retries. Total cap exhaustion
leaves unfinished cases in the denominator. These are proposed caps, not a cost
quotation or permission to spend. Before dispatch, the host must enforce current
pricing and worst-case reservations. No calibration or OOD detection performance
claim belongs to this small evaluation.

RQ1: interaction adds attributed explanations and explicit unresolved statuses;
accuracy/usefulness remain unmeasured and it cannot correct failed forecasting.
RQ2: clarification now has an implemented interaction mechanism, but no calibrated
recognition trigger or evidence of OOD clarification effectiveness. Recognition
calibration, contact/support capability and broader learning remain pending.

No additional policy decision is needed to finish this implementation. Future
live evaluation or frozen-checkpoint experiments require new execution approval;
neither is silently started here.
