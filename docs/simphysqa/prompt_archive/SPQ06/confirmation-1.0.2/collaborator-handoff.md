# Unassigned collaborator execution handoff

No condition or executor is assigned. `ownership-template.json` contains 2,640 stable possible-stage keys for the unchanged 200-item main core: 2,200 initials and 440 conditional continuations. Every `owner` is null and `execution_authorized` is false. The eleven logical shards are the nine enriched conditions and the two prespecified structured-only conditions; these are organizational identities, not eleven independent samples.

## Future ownership agreement

After the humans agree on a division, create a separately versioned ownership manifest referencing the unchanged evaluation, request, condition, worker and scoring hashes. Assign exactly one executor to every initial key. Keep a condition/representation and its conditional stages together unless a different transfer is explicitly agreed. An initial and conditional stage cannot acquire conflicting owners. Each assigned condition evaluates all 200 items under its planned representation. Conditions may be divided between executors without dividing the benchmark population.

Validate exhaustive coverage and uniqueness of `sample_id|condition_id|representation|stage`, with stage2 allowed only for clarification. Conditional keys do not mandate a call: stage2 runs only after an actually supported first turn. An unroutable first turn produces an explicit unexecuted-conditional receipt. Never use the authored reference question as the assistant turn. All inputs, decoding settings, public/private boundaries and accepted scoring functions are identical across executors. Assignment alone does not authorize an inference run.

## Another workstation's qualification

Record GPU identity, device UUID where available, VRAM, compute capability, driver, OS/WSL, CUDA/runtime libraries, compiler or binary source, Python and full package versions. Verify original model repositories/revisions/weight digests, tokenizer/template digests, licenses, quantization and KV/activation precision. Match generation limits, sampling, EOS/stop behavior, full chat rendering/token IDs, actual clarification history and context behavior. Check CPU fallback, memory availability, loading time and interruption/resume receipts. Save differences explicitly; they are not substitutions to hide.

Current workers enforce `NVIDIA GeForce RTX 5090`, and current launch paths are tied to the qualified WSL workstation. A different RTX or OS cannot run the frozen workers unchanged. This package does not remove those checks. A later portable executor adapter needs a versioned implementation and review; hardware-specific differences require explicit qualification. Numerical nondeterminism across GPUs remains a limitation even with seed11. Setup/import success does not establish task qualification. No qualification inference is authorized here.

Before inference is later authorized, address the measurement discrepancies listed in the measurement contract. The current main runner lacks an owner filter and shared multi-executor budget scheduler. Agree on per-executor reservations under the unchanged overall ceiling; do not give each executor an independent48-hour allowance and double the limit.

## Returned artifacts

Each job returns an immutable directory or transport archive containing:

- Assignment/qualification receipt, hardware/runtime provenance, condition and worker bytes/hashes, original request-list bytes/hashes.
- Per-stage reservation, executed public request, rendered prompt/token IDs, raw generated text/token IDs and result; Gemma actual loopback request/stream and server log.
- Loading metadata, source/interval/sample-count-aware memory evidence, process reservation/result, complete or interrupted status, routing decision and actual first turn for a continuation.
- Every relative file path, SHA256 and kind; one return envelope for each reserved key and explicitly unexecuted conditional key.

`return-envelope.schema.json` defines proposed transport metadata; it is not a raw worker-result schema or proof of execution. Known fields can be null only with an explicit unavailable reason in job evidence. Never create an empty completed result for an interruption. Do not transmit credentials or private gold to answering workers. Supplied explanation comparisons remain public task evidence.

## Duplicate detection and central combination

Central ingest must validate assignment, qualification, request/condition/worker hashes, stage history, known IDs and every file hash before scoring. Preserve all returned bytes in exclusive source roots, including failures. Compare keys against an append-only registry:

- Same key and identical hashes: duplicate transport; log it and count one stage once, not a retry.
- Same key and different hashes: conflict; halt that key, preserve both submissions and request a disposition. Never select the better answer, latest file or successful attempt automatically.
- No unique prior reservation, changed request/config, unqualified CPU/runtime result or stage2 without supported actual first turn: invalid execution; retain the reason.

A future immutable import layer can expose canonical job paths expected by `main_analysis` while retaining source hashes and names. The current analyzer rejects duplicate raw paths and evaluates every selected item/configured condition. Missing/failing stages remain in the fixed denominators. Maintain separate interface-failure, target/factual/clarification and coverage tables before the frozen paired bootstrap. No importer or merge is implemented/executed here; the schema and validation policy are preparation.

## Interruptions and resume

Reserve a stage before inference. Never rerun a reserved key automatically when its result is missing. An orphan retains unknown status and full reserved work. Resume creates an exclusive job root and schedules only never-reserved keys. Record startup failure before item reservations separately. Persist the shared registry before a second executor starts. Loading/process overhead and unknown work count toward the aggregate ceiling.

The local runner follows never-reserved-stage resume within its own root, but cannot prevent overlapping second-root execution. Ownership registry, portable qualification and central importer are distributed-execution prerequisites. Frozen prompts, selected IDs, main size decision and previous outputs are unchanged.
