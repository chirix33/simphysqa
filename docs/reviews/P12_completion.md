# P12 expanded experimentation qualification — 28 September 2026

29 September interface follow-up: see [the shared local answer-interface conclusion](P12_answer_interface_completion.md).
It supersedes the historical answer formatting configuration for future qualification;
all historical results below remain unchanged. Expanded study launch remains separate.

Subsequent 29 September updates: [enrichment coverage is complete](P12_enrichment_recovery.md)
and [Llama runtime qualification finished](P12_llama_qualification.md), with
all eight diagnostic answers failing the frozen JSON parser. The report below
preserves the original qualification status and source identities. Expanded
training still awaits frozen-encoder preparation/re-audit and new authorization.

Implemented the release audit, local answer backends, strict failure accounting,
bounded numerical probes and a disabled expanded-study trainer. Qwen direct and
thinking conditions ran on the RTX 5090. Llama is **implemented_pending_validation**
because its gated checkpoint is unavailable. Full-population training is also
pending context preparation. No full study, paper edit, push, merge, dataset
regeneration or historical checkpoint modification occurred. This report's
qualification measurements precede the separately authorized paid pilot; its
32 requests and latest coverage are in [the pilot report](P12_enrichment_pilot.md).

The original qualification artifacts and disabled training proposal retain their
pre-pilot identities. They must be refreshed after preparation; they are not a
claim that the later enrichment implementation produced those earlier results.

## Source reconciliation

The checkout started clean on `main` at
`248575fd500947edd325836e636aebe41f9f65d0`. Changes in this report are uncommitted.
The reviewed commit `b2c19e096dadbac27d4bf6d56d10fb765a545419` lacks the P11
implementation/configuration paths. It cannot be cited as the executed P11 source.

| Result | Actual local root | Executed source authority |
|---|---|---|
| P11 main and appendix | `/home/aashraf/phi-jepa/p11-tonight-01` | Per-stage `sources/*.json` and content-addressed `sources/blobs/`; recorded base commit `d2e9fe3daba63cc0b5295fa108177628c4319098` plus archived local files |
| Later 40-question Phi/Sol comparison | `/home/aashraf/phi-jepa/manual-outputs/answers-20260925-234706` | `source/identity.json`, `source/blobs/`, `config.json`, and `selection.json`; same recorded base commit plus its own archived files |
| New qualification | `/home/aashraf/phi-jepa/p12-expanded-qualification-01` | Per-stage `sources/` snapshots of this checkout; final file identity and evidence checksums in `artifact-index.json` |

All four P11 main numerical stages used `tools/p11_numerical.py` SHA-256
`8c8cc83e89d41531d7676a46a25ac279bf2414d55e45e54c469635a97ea01a94`.
The frozen P11 plan/configuration hash is
`ca70af2e4314e0171bda1a2f08cc0bdaff83b08ee5b4f9ab880e1507c6c39a44`.
All P11 archived source blobs and all eight selected main/appendix checkpoints
passed integrity checks. P11 used 48 main training questions per domain,
eight validation questions and twelve test questions; the appendix used its
independent 16-training/four-test subset. Numerical fits used 20,000 updates
of 20 pairs. Main checkpoints were selected on validation; appendix selection
was fixed-final.

The 40-question comparison used the existing P11 main selected checkpoints,
ten ID-test questions per domain, with Phi and live vanilla Sol answers.
Its runner `tools/answer_pipeline.py` hash is
`691b88a8f2e04e2d74c1f2d5e2247ebb298dee5ac5702f3c05804570e99b9134`;
source-manifest hash
`888ab3654a408eab2156fa79d5af781a8a313b99ce14b04b76fa810f44e393d5`;
configuration hash
`f6f73249f07a6b3de715eeae6b0f2f498dc0e96795dab15f5ffacc6fd833c821`.
All 229 archived source files verified. Current checkout files are not silently
substituted for those historical snapshots.

The wider historical inventory found 88 missing/mismatched source-blob references
in P10 manifests, counted across stages. This limitation belongs to P10; it does
not affect the verified P11/comparison snapshots. Those historical manifests
were preserved, not repaired by substituting current code.

Evidence: [source reconciliation](artifacts/P12/historical-reconciliation.json),
[selected checkpoint integrity](artifacts/P12/historical-selected-checkpoints.json),
[artifact index](artifacts/P12/artifact-index.json).

## Frozen release and context audit

| Domain | Training scenarios | Questions | Adjacent pairs | Matching notes | Matching embeddings |
|---|---:|---:|---:|---:|---:|
| robotic_arm | 981 | 1,962 | 127,530 | 49 | 48 |
| driving | 740 | 740 | 66,600 | 49 | 48 |
| object_pushing_stacking | 1,000 | 2,000 | 130,000 | 49 | 48 |
| tethered_load | 1,000 | 2,000 | 130,000 | 48 | 48 |
| Total | **3,721** | **6,702** | **454,130** | **195** | **192** |

Original validation has 742 scenarios and 1,336 questions: driving 148/148,
objects 200/400, arm 194/388, tether 200/400. Each domain has nine matching notes
and eight embeddings, for 36 and 32 respectively. All 231 found enrichment
records match the approved provider request, returned model, output checksum
and exact public-bound notes. Embeddings match the frozen encoder revision,
runtime settings, serialization, complete token sequence, context and request;
the final audit also pins their file hashes.

Missing training coverage is **6,507 notes / 6,510 embeddings**; validation is
**1,300 / 1,304**. Thus training plus validation needs **7,807 / 7,814**. The
500-question confirmation cohort has no existing enrichment candidates; it
requires another 500 notes and embeddings. Combined planned preparation is
**8,307 new enrichment records and 8,314 embeddings**, subject to the same exact
identity checks. Seven existing notes could be encoded locally without an API.
No missing sample was discarded or replaced with a fixture or another provider.

[Audit](artifacts/P12/audit.json), [selection](artifacts/P12/selection.json),
[per-question coverage](artifacts/P12/cache-coverage.json),
[provider-origin verification](artifacts/P12/enrichment-origin-audit.json),
[blocked training preflight](artifacts/P12/training-preflight.json).

Split checks cover the pinned export, accepted simulation origin, metadata
partition, unique sample IDs, simulation and group isolation. All training
future states are legitimate adjacent-pair supervision. Inference uses only
the public reader and a deployment file-access guard. Quarantine/development
fixtures are outside the admitted selection.

P07 and P08 diagnostics used validation. The conservative P07–P11/manual
inventory identifies **48 inspected test simulations / 84 question records**
after propagating exposure across each simulation. The unused confirmation
cohort has **320 scenarios / 500 questions**, zero overlap, and 20 scenarios
per domain per ID/parameter/timed-event/combination partition. No test reference
values were read. Exact IDs and evidence are in
[the exposure inventory](artifacts/P12/previously-inspected-scenarios.json),
[confirmation cohort](artifacts/P12/confirmation-cohort.json), and
[common target mask](artifacts/P12/common-target-manifest.json).

## Qualification measurements

Environment: Ubuntu 24.04 WSL2, Python 3.12, RTX 5090, PyTorch 2.7.1+cu128,
Transformers 4.51.3, tokenizers 0.21.1, safetensors 0.5.3, hub 0.30.2.
The existing core environment is separate from custom Coconut/CODI environments.
No runtime upgrade was required. All GPU jobs ran sequentially.

The eight diagnostic questions are two distinct validation simulations per
domain, chosen by longest public-input byte length. Complete templated inputs
were 6,454–13,517 tokens, with output space reserved within 32,768 tokens.
No truncation, prompt adjustment, schema repair or automatic retry was used.

| Condition | Generated requests | Valid typed answers | Complete correct answers | Generation time | Input / reasoning / final tokens | Peak allocated GPU |
|---|---:|---:|---:|---:|---:|---:|
| Qwen3-8B, thinking false | 8 | 2/8 | 1/8 | 192.008 s | 81,509 / 0 / 5,771 | 18.48 GiB |
| Qwen3-8B, thinking true | 8 | 6/8 | 0/8 | 264.233 s | 81,477 / 3,502 / 4,668 | 18.47 GiB |
| Llama-3.1-8B-Instruct direct | 0 | Unavailable | Not measured | Not measured | Not measured | Not measured |

These are software/runtime diagnostics, not headline benchmark results or a
method ranking. Direct Qwen had four `supported_reason` schema failures and
two 1,024-token cap terminations. Thinking Qwen had two `target_fields` failures;
all eight reached EOS within its 2,048-token allowance. Reasoning is stored
separately and is neither a prediction nor verified explanation evidence.
Token accounting includes template/control tokens; generated closing-thinking
tokens are charged to reasoning and final EOS tokens to final output.
Model loads took 8.111 and 7.916 seconds, separately from generation.

The evaluator preserves unchanged target tolerances and reports every eligible
question/target, unsupported coverage, Boolean accuracy with all-eligible and
supported denominators, per-target physical errors, per-domain/distribution
results, and the predefined common target set. Llama's eight unavailable slots
are explicit availability failures, not fabricated model measurements.
Raw completions, input/generated token IDs and termination details remain in
`artifacts/P12/local/`. Full diagnostic tables are in
[the evaluation directory](artifacts/P12/evaluation/summary.json).

Fresh numerical probes performed 10 updates at each of batches 64, 256 and
1,024 in each domain, separately on CPU and CUDA. Each device therefore used
120 diagnostic updates and 40,320 pair presentations. All weights were discarded
without checkpoints. The unchanged trainer exercised projection gradients and
the approved equally weighted augmented objective. At batch 256, CPU updates
took 0.081–0.146 s; CUDA 0.088–0.141 s, using under 30 MiB allocated. CPU and CUDA
probe programs took 40.508 and 39.518 s including their preparation. This is
not evidence that the full population has been fitted.

Separately, full training-population numerical IO/vectorization took 354.373 s,
with process peak RSS 964,550,656 bytes (0.90 GiB). This contains no enrichment
or optimizer work. Four fresh encoder calls using existing validation notes
took 0.082–0.914 s each, for 5,690–12,902 tokens and at most 1.54 GiB allocated.
Their output was discarded. Missing OpenAI enrichment was not profiled by making
paid calls during initial qualification; see the subsequent [paid pilot](P12_enrichment_pilot.md).
Public Qwen acquisition transferred approximately 16.40 GB and its
acquisition/provenance pass took 66.469 s.

Evidence: [CPU probes](artifacts/P12/numerical-profile-cpu.json),
[CUDA probes](artifacts/P12/numerical-profile-cuda.json),
[full numerical preparation](artifacts/P12/preparation-profile.json),
[encoder timing](artifacts/P12/context-profile.json),
[model acquisition](artifacts/P12/model-acquisition.json).

## Verification and remaining gates

Commands actually run are documented in [P12 commands](../P12_pipeline.md).
The targeted offline suite passed, covering adjacent alignment, target projection
gradients, full augmented feedback, checkpointing, split/private boundaries,
equal-pair cycles, template controls, final parsing, cache identity and failure
accounting. See the authoritative [test log](artifacts/P12/tests-final.log).
Both Qwen condition resume checks accepted all eight exact request identities
without loading the model or generating additional tokens. The all-population
preflight refused to train with 7,814 missing verified contexts.

The expanded trainer itself cannot receive its full-population empirical gate
until coverage is complete. Its objective is the existing tested trainer, but
long-run memory, resume after actual full-population fitting and Llama execution
remain pending. Stage source snapshots preserve the implementation used by each
measurement; later budget/resume hardening is covered by offline tests and
zero-generation resume checks, not falsely attributed to earlier executions.

### Blocker: Llama qualification

- Phase/substep and status: P12 local Llama backend, `implemented_pending_validation`.
- Repository and paths: `main` / `248575fd500947edd325836e636aebe41f9f65d0`;
  `tools/p12_models.py`, `tools/p12_local.py`, `configs/local_answers_p12.lock.json`.
- Expected: load the pinned official checkpoint/tokenizer and run eight validation requests.
- Reproducer: `python tools/p12_models.py`, then `python tools/p12_local.py llama31_8b_direct` in the documented WSL environment.
- Observed: public model metadata resolves revision `0e9e39f249a16976918f6564b8830bc894c89659`; protected `config.json` access raises `GatedRepoError`. The qualification runner records `blocked`.
- Environment: WSL/core runtime above; no local Llama checkpoint or authenticated access was found. No credential contents were read or logged.
- Attempts: local cache inventory, public revision/size resolution, one gated file probe, and fail-closed runner check. No repeated unauthorized download attempts.
- Root cause: missing authorized gated model access; model/runtime compatibility remains untested.
- Impact: Qwen, numerical diagnostics, cache audit and planning completed independently. Llama template hash, latency, memory and actual generation remain unmeasured.
- Option A: authenticate an account already approved for the model in WSL, then resume the pinned download and eight diagnostics.
- Option B: supply an authorized local snapshot of that exact revision; verify its file identities before using it.
- Recommendation: A if access already exists; otherwise B. Do not substitute another checkpoint.
- Smallest question: can the user make approved access or an authorized snapshot available? Do not send a token in chat.
- Closure evidence: pinned snapshot/tokenizer/template hashes and eight raw validation diagnostic records with costs.

### Blocker: expanded Phi context coverage

- Phase/substep and status: P12 full-population preparation, blocked before training.
- Repository and paths: same branch/commit; `tools/p12_audit.py`, `tools/p12_cache_origins.py`, `tools/p12_train.py` and the coverage artifacts linked above.
- Expected: identity-matching contexts for all 8,038 train/validation questions, then 500 confirmation questions for inference.
- Reproducer: `python tools/p12_train.py preflight`.
- Observed: `missing_identity_verified_contexts: 7814`, `can_train: false`; confirmation has zero enrichment candidates.
- Environment: frozen Qwen embedding encoder is locally available and qualified; adopted enrichment remains OpenAI `gpt-5.6-sol`.
- Attempts: full release/public binding audit, exact token/request/runtime matching, provider-cache provenance audit and independent local encoder timing. Initial qualification made no paid calls. The subsequently authorized pilot added 32 compatible notes, with no incompatible fallback.
- Root cause: existing runs prepared only small subsets; this is missing population coverage, not a GPU failure.
- Impact: broad fitting and matched Phi confirmation inference cannot start. All independent qualification above can and did continue.
- Option A: import existing compatible, provenance-verifiable caches if they exist elsewhere; no new API expense.
- Option B: the separately authorized pilot is complete. A further 8,275 notes and local encoding of 8,314 questions remain; the [concrete preparation proposal](P12_enrichment_pilot.md) is disabled pending its new cap approval.
- Recommendation: review that proposal; changing enrichment provider remains a separate scientific decision, not implied by local answer baselines.
- Smallest question: approve the additional $475 maximum for both stated scopes, or request a training/validation-only $425 configuration?
- Closure evidence: a new full coverage audit with zero missing identities, followed by newly authorized full-run configuration. Do not enable the current incomplete proposal.

Next step: close these two prerequisite gates, refresh source/cache identities,
and review the [bounded full-run plan](P12_full_run_plan.md). Existing Sol answers
and Phi prose dependencies remain disclosed; only the new direct-answer backends
are local. No newly trained study model or matched confirmation result is claimed.
