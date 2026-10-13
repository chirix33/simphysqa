# SPQ06 qualification and held-out preparation /1.0.0

Authorized on 9 October 2026 after cleanup PR #3 merged. Base main is
5e1355d63b6829395b266a18edec198603e10932; normal branch simphysqa-spq06 in the existing
checkout. Earlier SPQ06 drafts were never sent and supply no prior implementation,
qualification or evaluation evidence. Cleanup-session restrictions are dated receipts;
the current user instruction authorizes this milestone. No main benchmark launch.

## Parallel tracks and frozen boundaries

Track A selects 20 accepted development items, one per four-domain/five-family cell,
with Python Random(20261009) over sorted accepted identities. Small family pools are
visited first and unused development groups preferred. The source has only 16 groups,
so the pilot does not imply 20 independent trajectories. Save all selected IDs/groups,
source hashes and public requests before generation. Nine conditions retain the
authoritative configs/simphysqa/evaluation.json identities. Pin each artifact, runtime,
license, template and quantization before its first attempt; an unavailable condition
is blocked, not substituted or counted as qualified. GPU conditions execute serially.

The pilot permits 180 initial requests and at most 36 actual clarification continuations;
18 GPU hours including loading, at most 600 seconds per model load. Per-condition
limits inherit existing configured small-model settings; previously unspecified larger
conditions use 32,768 total tokens, 1,024/4,096/8,192 output tokens and 120/240/360
seconds for direct/prompted CoT/native reasoning. Sampling defaults: seed11, temperature
.6, top_p .9 (native .95), top_k20 for Qwen, otherwise50. Existing non-null settings
remain unchanged. No truncation, answer repair, retry, hard-item exclusion or fixture
fallback. Preserve reserved failures, all raw text/token IDs, requests, latency,
memory, completion status, parsing, private factual scores and separate reasoning
diagnostics. Pilot results qualify execution and forecast timing, not empirical quality.

Answering is workstation-only, tools=[], public inputs only; no hosted answering,
simulator tools, gold, traces or private rollouts. Model workers import no scientific
pipeline and read only public requests/configuration. Clarification stage1 is the
actual model output. Only an accepted structured supported-slot request is routed
through recorded replies; actual raw assistant text enters stage2. Unsupported,
ineffective, absent, premature, invalid or timed-out clarification stays separate.
Authored reference questions never replace stage1. Automatic routing checks structure;
semantic relevance, compound questions and disguised prose answers need human review.

Track B inventories all original 11,105 QA/6,340 groups, preserving source shards and
split labels. Original test_id is the prespecified held-out frame. Exclude the
authoritative 20 development groups, every overlapping group/sample in the actual
historical prompt-use receipt, and all 140 SPQ05 groups conservatively while human
feedback is processing. SPQ05's same140/three-reviewer design is distinct from this
20-item model pilot; no human calibration was created and no feedback is inferred.
Other original splits remain inventoried but are not silently borrowed to fill cells.

Shuffle sorted eligible groups independently by domain using seed20261009, allocate
round-robin to disjoint canonical family pools (direct, predictive, counterfactual,
explanation, clarification), and choose one random sorted original source QA/group.
"Explanatory" is the paper label for canonical question_type=explanation. Process up
to the first40 candidates/cell or its entire smaller pool. Select first20 qualified;
first10 form the nested200 core and next10 its400 extension. One unique trajectory
group per final evaluation item. Same-cell reserves follow saved order only. Preserve
every eligibility rejection, failure, repair, retry, replacement and unused reserve.
Exhausted quotas cause an explicit cell shortfall and remedy proposal, no relaxation.

Freeze the source release, code/schema/provider/prompt hashes, candidate order and
admission rules before new generation. Source qualification precedes simulations.
Directs use observed readouts; predictive references retain original outcomes.
Counterfactuals use established matched omissions, canonical exact factual replay,
and separate original/alternative coarse/fine admission. No effect-size requirement
for counterfactual or explanation. Explanations disclose only intentionally selected
supplied comparison evidence. Clarification requires genuine whole-visible-input-
compatible completions with scorer-disjoint acceptance regions and explicit attrition.
Retain numerical tolerances and sign-invariant quaternion scoring; no OOD inference.
Never extend cutoffs or expose private future states as observations.

Annotation reuses accepted grounded language/event/association/answer/family pipelines.
Only candidate-specific new requests/simulations are eligible; no full-release enrichment.
Print a concrete dry-run count/token/spend/simulation estimate before requesting a
distinct bounded SPQ06 paid-generation authorization. SPQ05 ceilings do not authorize
SPQ06. Unknown attempts retain full reservations. New requests, outputs and deterministic
procedures have exact per-file provenance and versioned exclusive/exact-byte resume.

## Prespecified main design, size decision and assessment

All nine conditions evaluate identical enriched inputs on the final frozen set.
Matched structured-only ablation covers all items for qwen3_8b_direct and
qwen3_32b_awq_on: same architecture family, small BF16/direct versus larger
AWQ/native reasoning. Chosen before main scores. Remove derived language while
preserving physical facts, controller/schedule/predicate semantics, supplied outcomes,
ambiguous initial queries and answerability; retain any unique factual text.
Validate ablation projections against original public facts and clarification erasure.

400-item maximum: 3,600 main initial +720 clarification continuations +960 ablation
calls =5,280. 200-item maximum: 1,800+360+480=2,640. Turns/conditions do not add
independent QA items. Forecast each condition/family from all four pilot items,
including failed/time-limited work and clarification continuations. Include measured
loading overhead and 25% runtime reserve. Use conservative maximum-per-cell timing
where variation is high; blocked/unmeasured conditions prevent a claimed complete
forecast. 400 requires20 qualified/cell, all-condition measured forecast <=48 GPU
hours and preparation completion leaving at least12 hours for analysis/writing
before 12 October2026 23:59 AoE (13 October11:59 UTC). Otherwise choose a qualified
prespecified200 core, or explicitly report no ready size when qualifications fail.
Freeze decision before any main-set model output, never use main accuracy.

Use accepted typed numerical/Boolean scorers, explanation structured factual checks,
and clarification behavior/resolved-answer adapters. Keep prose quality unassessed
automatically. If reporting model prose quality, use first2 qualified explanation
items per domain in core (8 unique questions), all conditions, shuffled/blinded
condition identities, independent claim-level human rubric; separate original
submissions, missingness and adjudication. SPQ05 annotation audit is not that study.

Balanced benchmark claims concern the balanced qualification-conditioned design,
not original record frequency. Report missing/invalid/blocked/time-limited cases
in denominators, separate valid-only errors from coverage, and paired within-cell
whole-trajectory bootstrap (10,000 replicates,95% intervals, seed20261009).
Retain all model-condition outcomes for an item together; report condition comparisons
on the same items. Seven- or ten-item cells do not automatically support strong
subgroup claims. Human acceptability, explanation quality, OOD and main results
remain unclaimed until corresponding evidence exists. No automatic merge/push.
