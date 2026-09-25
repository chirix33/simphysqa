> **Active supersession — 2026-09-24:** Model work follows [training contract 2.0.0-candidate.1](../../MODEL_TRAINING_CONTRACT.md) and the user's revision-3 Stage 1/P02a request. Adjacent recorded-state training uses frozen E(Q,C), trainable P of width d, the same undetached p on both sides, and full predicted 2d-vector feedback. Conflicting terminal-only, tree/readout/semantic-head, E(Q,C,A), upstream-baseline substitution and truth-forbidden-in-training instructions below are historical. Custom Coconut-inspired/CODI-inspired variants are intentional. Future phases require separate authorization. Frozen dataset/export contracts remain unchanged.

# Codex prompt: P02 - Frozen interfaces, schema semantics, and answer payloads

Updated 2026-09-23 after independent P01 source review. Give this file to the existing Codex coding session. This authorizes one small P01 portability correction followed by P02 only, subject to the correction's tests passing.

---

Implement P02 of Phi-JEPA, preserving the settled research design. Read applicable root/nested AGENTS.md, `docs/README.md`, `docs/PROGRESS.md`, `docs/reviews/P01_completion.md`, `docs/decisions/P01_data.md`, and `docs/docs/01_context.md`, `02_architecture.md`, `04_assessment_fallback.md`, `06_phases.md`, `07_workflow.md`, and `08_defaults_decisions.md`. Use the existing `docs/` handoff root, not `docs/implementation/`. Read the planner review supplied with this prompt if available; the required finding is reproduced below.

## Starting state and research boundaries

The user pushed P01 to `codex/p00-bootstrap` at `8a1b819743677c12039fcf21b803745ac28df21c`. Inspect the actual local branch, HEAD, and dirty state, and preserve newer/user work. Do not reset, silently stash, change branches unnecessarily, or overwrite old evidence. No push or merge is requested. Historical reports describing an earlier uncommitted state should remain historical; record the current state in new progress entries.

The planner independently ran all 28 current tests and reproduced the 32-family/128-record fixture outcomes. P01's functional scope is accepted with the narrow portability correction below. Separate train/selection/calibration/ID/OOD splits exist. Reuse those data interfaces and the numerical prediction envelope.

The research goal is a learned latent physical predictor conditioned on frozen language and extracted structure. Preserve terminal-only physical MSE, separate question regularization, frozen text/LLM components, and trainable structured encoding/fusion/ODE/readout in their intended later phase. No trained EBM, new target encoder, trajectory-loss objective, inference minimization, or schema-topology repair. Do not import benchmark formulas or evaluator truths into providers, encoders, answer generation, or prediction interfaces.

## Gate 0: correct P01 scaler portability

The committed Windows scaler has `scales[1] = 5.228384226033585`; independent Linux Python 3.12.14 recomputation gives `5.228384226033584`. Every other generated dataset payload hash matches the committed dataset manifest. The difference is one floating-point step, but both `evaluation.checked_dataset` and `benchmarks.dataset.validate_dataset` reject the valid stored scaler because they use exact object/digest comparison.

Make one shared numerical-verification policy and use it at both entry points:

1. Keep exact byte/hash verification in `read_run`. Do not weaken stored artifact integrity or alter old manifests/artifacts.
2. Keep scaler observable IDs, units, frames, policy, constant-coordinate flags, training family/scenario IDs, and training-target provenance hash exact. Preserve positive/finite scale validation and train-only recomputation.
3. Compare only numerical means/scales with a small documented tolerance appropriate for rounding. A starting engineering choice is `rel_tol=1e-12, abs_tol=1e-12`; justify and record the selected tolerance. This is not permission to accept material changes or replace exact training provenance with approximate comparisons.
4. Use the persisted, verified scaler for numerical evaluation and downstream normalization. Do not quietly replace it with a new runtime's recomputation. Separate exact stored content identity from numerical equivalence of a recalculated statistic.
5. Regression checks must accept the stored Windows scaler and a one-step `math.nextafter` perturbation through both validation paths, reject material changes to means/scales, reject changed provenance/layout/policy/flags, retain held-out-target independence, and preserve byte-corruption detection. These tests should work even on a machine that reproduces the original Windows value.
6. Record the fix and evidence in a dated decision/progress entry. No research architecture change is involved. Proceed to P02 once these focused checks and P00/P01 regressions pass; if not, report the precise blocker without claiming the gate is complete.

## P02 deliverables

### 1. Preserve adopted prompts and external schemas

Load the exact versioned `docs/assets/prompts.json`, `extract_schema.json`, `judge_schema.json`, and `answer_schema.json`. Verify original hashes using the existing manifest policy. Preserve both source-file identity and exact prompt strings. Package resources so installed execution does not depend accidentally on the current working directory, without editing the authoritative originals.

The archived `REPAIR_PROMPT` must remain unreachable from inference, retry, and failure paths. Frozen extraction uses the original question; no hidden generated answer, truth, split/OOD label, or oracle output may enter a request.

Implement typed immutable response wrappers, strict structural validation and explicit failure types. Preserve external-schema semantics, including numeric observation values, nullable units/event times, and allowed empty arrays/strings where the original schema permits them. Do not blindly reuse P00's blanket nonempty-string rule if it would silently tighten the adopted external contract. Extra semantic restrictions need separately labeled validation outcomes.

Unknown physical numbers belong in `unknowns`, not numeric zero or an invented observation. Keep internal output-slot missingness/masks separate from the unchanged external response schema. Evidence substring checks measure provenance, not physical correctness; do not require an exact numeric spelling inside a substring to establish a value.

### 2. Frozen provider and embedding boundaries

Implement explicit offline replay and configurable live interfaces for extraction, the existing V1 scenario/schema consistency judge, answer generation, and frozen embeddings. Select a supported provider adapter consistent with existing project plans; pin verified optional dependencies and document APIs used. Leave offline mechanics runnable without network credentials, downloaded models, or a GPU.

No paid calls or automatic model downloads are authorized by this prompt. If live credentials/model/budget are absent, complete offline behavior and mark actual live SDK/model execution pending. Do not infer a real model ID from the old demo's conversational name. Document any unsupported live-adapter behavior honestly.

Distinguish successful output, refusal, incomplete/truncated generation, malformed JSON, schema rejection, timeout, rate limit, unavailable provider, and terminal transport failure. Defaults remain one content attempt and at most two transport retries. Avoid multiplying SDK retries by wrapper retries. Invalid content/refusal must not trigger semantic repair, a second content attempt, or an oracle/fixture substitution.

Define finite request/input/output/retry budgets and enforce them before dispatch where possible. Capture actual attempts, cache hits, provider calls, reported tokens, latency, failures, and unknown usage; do not invent token counts for a failed request. Never store credentials, authorization headers, or environment dumps in errors or manifests.

Frozen embedding interfaces must expose model/revision, width, preprocessing, truncation and normalization metadata. Fixture embeddings are explicit test mechanics, not real semantic evidence. Do not train or download the real encoder in this slice. Any later real implementation must stay eval-mode and gradient-disabled.

### 3. Cache identity and separation

Cache keys include exact request content, task, original prompt and schema hashes, provider/model/revision, decoding settings, relevant layout/context, and feature/preprocessing versions. Embedding keys also include model and tokenizer/preprocessing revisions. A changed question, prompt, schema, model, relevant setting or task must invalidate reuse. A reused scenario ID alone is insufficient.

Keep fixture and live caches disjoint and labeled. Verify payload integrity when loading. Failed or malformed responses cannot be served as successful entries. Preserve original production-cost provenance separately from current cache-hit execution cost. A missing live credential must not automatically activate fixtures. Do not cache trainable encoder outputs for future reuse across optimizer updates.

### 4. Generic JSON features for the later trainable encoder

Build a deterministic generic tree/graph representation preserving container/key/value types, parent-child structure, sequence positions, actual string values, signed numerical values, units, operators, event descriptions/times and evidence. Handle arbitrary supported topology without assuming eight physical fields or a stopping-specific schema.

Retain presence/type/padding masks and original numeric values alongside any sign-log features. Zero and unknown must remain distinct. Null event time is different from time zero. Stable object-key handling may canonicalize dictionaries; ordered arrays must retain position. Keep bindings to original immutable source nodes.

Integrate the frozen text-feature interface so equal numbers with different names, units, relation operators, event meanings or topology are distinguishable. Hash-only fixture features establish mechanics, not learned semantic quality. Never evaluate extracted expressions or dispatch a physics solver based on schema text.

P02 creates features and interfaces. Training the message-passing encoder and latent predictor belongs to P03; do not start it here.

### 5. Compact answer payloads and numeric fidelity

Build answer context from the original question/schema, permitted initial observations, named physical predictions, units/frames, physical horizon, a bounded selection of actual rollout information and explicit fallback status. Use existing `ObservableSpec` and `PhysicalPrediction` where appropriate. Values must be in physical units before they reach the answer LLM.

Require explicit `[B,T,D]` shape validation and sample selection before slicing time. Each initial/terminal/minimum/maximum vector must have D values, never flattened T*D or the entire batch. Pair samples with their correct metadata; validate physical times and terminal consistency. Distinguish observed initial facts from a predicted initial readout. If only an endpoint exists, do not fabricate a trajectory or its extrema.

Keep the exact adopted external answer envelope (`plain_text_answer` plus `structured_answer` containing `final_state`, `trajectory_summary`, `structural_interpretation`, `fallback_used`). Store named metadata and comparison results in an internal sidecar rather than changing that schema.

Check generated `final_state` length, order and numeric agreement against the authoritative prediction with declared tolerances; check fallback-status agreement. On mismatch retain the original prediction and the unmodified LLM answer, flag the discrepancy, and never rewrite the numerical prediction to improve metrics. Refusal/missing numerical output gets an explicit failure result, not a fake valid numeric answer. Full assessment, calibrated fallback selection and new diagnosis prompts belong to P04; do not silently implement them here.

## Required evidence

Use targeted offline tests with socket/DNS blocking or injected transports. Cover original asset hashes; immutable schemas; schema-valid edge cases; unknown versus zero; distinct semantic strings/topology at equal numbers; graph masks/edges; negative/scientific numeric values; explicit offline/live separation; cache invalidation; retry counts/budgets; refusal/incomplete/malformed output; redacted errors; and the unreachable repair path.

Payload regression tests must include B=1 and B>1, explicit sample selection, differing sample values, wrong dimensions/grids, absent trajectories, named units/frames, terminal bindings, output length/numeric mismatch, and no evaluation truth in any request. A synthetic prediction is sufficient and must be labeled a fixture; it must not be generated by an oracle imported into provider/encoding code.

Expose a bounded offline CLI or documented executable that runs explicit replay extraction -> features -> answer payload -> replay answer validation and saves reviewable artifacts. Reuse P00 artifact machinery and P01 input contracts. Fixtures establish interface correctness only. Keep the existing P00 round-trip fixture's meaning unchanged.

Run relevant existing regressions and the new tests. Record exact environment and optional dependency status. The user already passed WSL2/RTX 5090 FP32/BF16 checks; do not ask for BIOS/GPU setup to finish this phase. The narrow P01 fix and P02 need no GPU.

## Completion and stopping point

Write `docs/reviews/P02_completion.md`, update `docs/PROGRESS.md`, and record consequential choices in `docs/decisions/`. Include:

- Actual starting/ending branch and HEAD, preserved user changes, and changed files.
- The P01 portability fix, numerical tolerance, exact-vs-tolerant verification boundary, and regression evidence.
- Original asset/prompt hashes and package-resource behavior.
- New interfaces, feature semantics, payload example with physical labels and dimensions, cache policy and retry accounting.
- Exact commands/results and artifact paths/hashes; paid calls, downloads and neural training should all remain zero.
- What was independently executed versus mocked/replayed, and which live/model gates remain pending.
- Any unresolved contradiction, deviation, or blocker, using the existing blocker-report format.

Stop after P02. Do not start P03 training, implement energy optimization/repair, change the research objective, run a large dataset cache, or push/merge. The user will bring the completion report back for planner review.
