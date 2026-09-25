# Stage 1 / P02a completion — integration revision 3

24 September 2026. Branch `full-phi-jepa-from-dataset`; inspected starting HEAD
`4f7d3e6b53009627b0b4223b2138ec5993c93726`, initially clean. No reset, stash,
simulation regeneration, provider calls, downloads, training, push or publication.
Original prompts/schemas, notebook, legacy source and all dataset outputs remain
preserved. The old architecture is archived; contract 1.1.0 stays byte-identical.

## Delivered scope

P02a offline interfaces and real-export validation are implemented. The active
model-training contract is separately versioned `2.0.0-candidate.1`; its candidate
suffix concerns contract and later discrete-outcome mechanism review, not the
settled projection decisions.
No model/checkpoint or neural performance result is claimed. Later model/provider
checks remain `implemented_pending_validation` only when their code is actually
implemented; those later stages are not implemented by this task.

`src/phi_jepa/integration/` provides immutable public/pair/prediction/failure types,
strict candidate registries, public-only inference reading, train-only recorded
sequence reading and separately labeled evaluator truth reading. Deployment has
no reference handle. Training legitimately uses recorded reference.states and
never constructs an E(Q,C,A) ODE target. Metadata stays outside learned inputs.

Active numerical scope is **state plus fixed conditioning**, explicitly selected
by the user during this phase. All selected integer/float fields participate,
including timestamps/indices, vector components, controls and fixed properties.
Booleans remain outside numeric MSE. P is trainable, width d, and shared on both
sides with target gradients; full predicted 2d-vector feedback is specified and
tested at the interface. E remains frozen. No old readout/tree/semantic-head,
trained EBM, energy descent or schema repair is restored.

The user also selected **public-only LLM enrichment, separately recorded**.
Immutable-input validation and explicit enriched/base-audit modes exist. Missing
enrichment in enriched mode fails; it does not silently substitute plain context.
No provider was called. Gold answers, private explanation/labels and named
predictions are forbidden in enrichment; answer_spec remains public.

## Real export and adjacent pairs

Resolved export path:
`C:\Users\aashraf\Desktop\Work\phi-jepa\phi-jepa\dataset-runs\release-four-domain-v1`.
It exists locally; no bottle demo or fixture substituted for release validation.
The audit pins export-index.json, release-manifest.json and CHECKSUMS.sha256,
verifies all 28,405 listed payload files (plus the checksum index itself), and
checks joined public/reference/evaluator identities, admitted counts, every state
layout, positive time order, physical overlap agreement and cross-split isolation.
Frozen licenses/assets/registries/quarantine/history are included in checksum
verification but only admitted public/reference/evaluator files are selected.

Verified 6,340 admitted scenarios and 11,105 question records: **6,702 train,
1,336 validation, 3,067 held-out**. The release's attempted/rejected ledger remains
unchanged. All 24 partitions are audited; validation/test sequences are explicitly
evaluator-only recorded-state diagnostics, never autonomous predictions.

| Domain | Active d = p width | ODE width | Train questions | Train adjacent examples | Unique train transitions |
|---|---:|---:|---:|---:|---:|
| Robotic arm | 177 | 354 | 1,962 | 127,530 | 88,290 |
| Driving | 106 | 212 | 740 | 66,600 | 66,600 |
| Objects | 86 | 172 | 2,000 | 130,000 | 90,000 |
| Tether | 140 | 280 | 2,000 | 130,000 | 90,000 |
| Total | domain-specific | domain-specific | 6,702 | 454,130 | 334,890 |

State-only comparison widths are 9/25/28/13. These are not the frozen whole-input
export registry widths. Exact columns, tagged semantic paths, integer/float types,
unit/frame bindings and manifest hashes are recorded under
`docs/reviews/artifacts/P02a/`; human-readable mapping is in
`docs/docs/P02a_state_mapping.md`.

Pairs start at the final public state at 0.2 seconds, then follow consecutive
recorded futures. All audited intervals are 0.02 seconds (allowing normal binary
floating-point representation). A 1s question has 40 pairs, a 2s question 90.
Across all partitions there are 761,200 question-conditioned diagnostic pairs.
Earlier public-history pairs are disabled to prevent context revealing targets.

Proposed weighting is explicit `inverse_transition_multiplicity`: retain distinct
questions, assigning 1/m per shared physical transition. Both horizons' first 40
transitions then have weight 0.5 per context; later transitions weight 1. No rows
are dropped. Weighting is a reviewable proposal, not a reported training result.

## Text, labels and observability

Measured training **base** Q/C lengths, before approved future enrichment:

| Domain | Q/C characters min–max | Label characters min–max |
|---|---:|---:|
| Arm | 16,927–16,996 | 264–277 |
| Driving | 30,005–30,116 | 120–127 |
| Objects | 24,372–25,145 | 416–442 |
| Tether | 14,908–15,020 | 180–193 |

Descriptive explanations are 100 characters in the audited training records.
No tokenizer/model is selected or called here; token/enriched lengths are
unmeasured, and no silent truncation is allowed. Explanations remain eligible for
custom-baseline target review; lack of official CoT traces does not reject them.
Custom Coconut-inspired/CODI-inspired variants are intentional; upstream bugs are
user-reported and were not independently reproduced.

Boolean targets include joint-limit occurrence, stopped-by-time, stable_stack,
support_lost, left_table and boundary_crossed. Private event types/counts are in
the audit. Dwell-time/contact-history outcomes are not necessarily recoverable
from one numerical endpoint. State/history contains observed positions/velocities
and known forcing, but does not expose all contact solver or event-memory state.
No missing velocity or simulator-internal variable was added; Markov sufficiency
and forecast quality remain empirical questions for later stages.

## Commands and evidence

Executed from repository root, using the existing isolated Windows runtime and
only standard-library integration dependencies; no dependency was installed:

```powershell
.\.dataset-venv\Scripts\python.exe tools/audit_p02a_export.py --root dataset-runs/release-four-domain-v1
.\.dataset-venv\Scripts\python.exe -m unittest discover -s tests -p test_p02a.py -v
.\.dataset-venv\Scripts\python.exe -m unittest discover -s tests -p test_p00.py -v
.\.dataset-venv\Scripts\python.exe -m unittest discover -s tests -p test_p01.py -v
.\.dataset-venv\Scripts\python.exe tools/verify_p00_handoff.py
```

P02a tests cover semantic reordering, collision-free bindings, complete vectors,
missing/extra/duplicate/null/nonfinite/Boolean behavior, units/frames, prediction
float indices, pair alignment/time ordering, split isolation, provenance,
question-context identities, immutable enrichment, forbidden target fields,
missing-enrichment failure and full augmented feedback. Public inputs are unchanged
when reference files change or disappear; training targets change when next
recorded numerical states change. The notebook's zero-fill and path-sanitizer
mechanics are addressed without executing/copying its credential. A separately
hashed sanitized review is in `docs/references/P02a_notebook_sanitized_review.md`.

## Failures and remaining decisions

An initial audit incorrectly required fixed categorical contact-relation count.
That candidate-reader bug was corrected with strict separate categorical validation;
no numeric field or release record changed. Intermediate successful audits are
recorded in audit-history.json and superseded by the final stable-source audit.
Documentation verification caught Windows encoding and relocated historical-link
issues, which were corrected. It also flagged a pre-existing negative instruction
spelling; wording was made compatible without changing its meaning.

The user selected a **separate Boolean/event mechanism proposal for a later phase**.
The concrete options, interfaces and missing-contact-history limits are documented
in `docs/docs/P02a_boolean_event_proposal.md`. There is no unanswered P02a policy
question. The actual mechanism and its qualification remain later-stage work. Numeric scope, enrichment role, projection width/gradients, adjacent
training and full feedback are settled and must not be reopened. No new answer
head, Boolean casting or extra loss is approved. Independent P02a work is complete;
that mechanism is required for later complete-answer evaluation. Training remains disabled.

Next step: review P02a contracts/evidence, review the Boolean/event proposal, then authorize
the next interface/model phase with selected model revisions and applicable live
budgets. No later-stage launch is implied by this report.

## Changed-file groups

- Active contract/config: MODEL_TRAINING_CONTRACT.md, configs/model_training_p02a.json.
- Reader/type/layout code: src/phi_jepa/integration/{contracts,layout,readers,__init__}.py.
- Verification: tests/test_p02a.py, tools/audit_p02a_export.py, compact P02a artifacts/logs.
- Authority/docs: AGENTS.md, README.md, docs/README.md, docs/PROGRESS.md,
  docs/docs/01–09 and archived prior architecture, P02a mapping/decision/prompt,
  future P02–P08 prompt supersession notices and sanitized notebook review.
- No generator, frozen export contract, source prompt/schema, dataset payload,
  provider credential, model weight or unrelated legacy source is changed.

## Final measurements and checks

Final stable-source audit: **188.131772 seconds**, Python **3.12.14**, Windows CPU.
15 P02a + 8 P00 + 20 P01 offline tests passed (**43 total**). Handoff verification
passed 9 preserved source hashes, 4 original prompt strings and 53 Markdown files.
The P00/P01 tests exercise existing offline fixtures; they are not new release
simulations or empirical model performance. No model/GPU/provider/download cost
was incurred and no checkpoint exists. P02a compact evidence is approximately
330 KiB; trajectories and embedding caches were not materialized or added to Git.

Final audit validates source/config hashes at both start and end. Its exact source
file hashes and config identity, active layout manifests, counts and real-reader
smoke identities are retained in export-audit.json. CHECKSUMS.json indexes compact
evidence; artifact-inventory.json additionally binds phase source/config and the
sanitized notebook reference. Original notebook contents are not included.

Boolean/event update (24 September 2026): the user selected a separate mechanism
proposal for later review. No Boolean casting, new head or objective is implemented
here. See `docs/docs/P02a_boolean_event_proposal.md` from the repository root.

## Committed source and artifact identity

Implementation/evidence commit: `cd6497856a94b3d01e0500ac54134a844e01e003`. The subsequent report-only commit
records this identity; it does not change tested implementation or configuration.
The audit ran on the inspected base HEAD with the exact new source bytes, which
were checked against the staged Git blobs before commit.

Final export-audit SHA-256:
`b64c5aa892e276bd822596876fa3812da4b9c901bf64646c8c19d03332954281`.
Compact evidence CHECKSUMS.json SHA-256:
`616c684617a2369972973157ee64a1cfda50b86ee3bc850cabf875b7a14dc77c`.
Compact evidence totals 337,036 bytes. No model checkpoint was produced.

All three user choices are recorded. P02a is complete for offline implementation
and real-export verification; the next model/provider phase and separate Boolean/
event mechanism remain unlaunched and require their own review/qualification.
