# P12 Llama qualification — 29 September 2026

The approved HF access resolved the checkpoint gate. Llama completed eight
validation requests on the RTX 5090, with no runtime failures, truncation or
token/time-cap terminations. **All eight outputs failed the frozen strict JSON
parser.** Status is `complete_with_recorded_failures`: runtime qualification is
complete; valid answer production was not demonstrated. These diagnostics are
not headline benchmark results and do not establish physical prediction quality.

The checkout remains `main` at `248575fd500947edd325836e636aebe41f9f65d0`, with
uncommitted P12 work preserved. No paid API calls, training, confirmation outcome
evaluation, paper edits, pushes or merges occurred in this follow-up.

## Source and artifacts

The separate native run is `/home/aashraf/phi-jepa/p12-llama-qualification-01`.
Its export is `docs/reviews/artifacts/P12_llama/` under the actual handoff root.
The previous gated acquisition and blocked diagnostic remain untouched in
`/home/aashraf/phi-jepa/p12-expanded-qualification-01` and the original P12 export.

- [Summary and measurements](artifacts/P12_llama/summary.json).
- [Raw completions, token IDs and qualification record](artifacts/P12_llama/local/llama31_8b_direct/qualification.json), with sibling per-question JSON files.
- [Typed whole-task and predefined-common-set evaluation](artifacts/P12_llama/evaluation/llama31_8b_direct.json).
- [Configuration and budget](artifacts/P12_llama/config.json), [request ledger](artifacts/P12_llama/local-budget.json), and [artifact hashes](artifacts/P12_llama/artifact-index.json).
- [Registration provenance](artifacts/P12_llama/registration.json) and [model lock](../../configs/local_answers_p12.lock.json).

Actual generation source snapshot:
`3d3d7752094f380e7cd9921d0e38ee395d5804732a5e71036bc6554230bea555`.
Frozen wrapper SHA-256:
`c80cc392bfffbed392dbe387a93b0020fded3ff454f585d8c87d8bf3c82137b3`.
Run configuration SHA-256:
`e322dac572f141f2ab693601678810179bb8a47e50f111be8845af976c0f5a29`.
Source manifests and content-addressed blobs accompany the export. The later
artifact-registration integration has its own source snapshot; it is not
attributed retroactively to generation.

## Frozen condition and boundaries

Model and tokenizer: `meta-llama/Llama-3.1-8B-Instruct`, revision
`0e9e39f249a16976918f6564b8830bc894c89659`. The downloaded snapshot's ten files,
including four weight shards, are hashed in the acquisition manifest. Expected
download size was 16,069,722,669 bytes; acquisition plus hashing took 81.580 s.
HF credentials stayed outside project artifacts.

The checkpoint's official chat template was applied, with SHA-256
`4193666d58af6747ecfd55b2b1da103aac2bf158cde51cd0d48c1b6f6c561585`.
This is direct-answer prompting; Llama has no Qwen-style native thinking switch,
and none was passed. [Official model documentation](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct).

BF16, no quantization, SDPA, seed 11, temperature 0.6, top-p 0.9, top-k 50;
1,024 output tokens reserved, 32,768 total input/output limit, 120 s per request.
Runtime: PyTorch 2.7.1+cu128, Transformers 4.51.3, tokenizers 0.21.1,
safetensors 0.5.3, Python 3.12 in the existing WSL core environment.

The exact eight public validation questions used for Qwen were reused: two
long-input scenarios per domain, all ID distribution. No test/confirmation
questions were selected. All original public facts and requested targets were
supplied using the unchanged P11 direct-answer asset. No Phi predictions,
OpenAI enrichment, private references, tools or retrieval were supplied. The
deployment file guard remained active; only subsequent typed evaluation opened
the eight validation references. The evaluator and tolerances were unchanged.

## Measurements and failure accounting

| Domain | Requests | Input tokens per request | Generation seconds | Valid answers |
|---|---:|---|---:|---:|
| driving | 2 | 10,223; 10,227 | 10.083 | 0 |
| object_pushing_stacking | 2 | 9,898; 9,891 | 28.380 | 0 |
| robotic_arm | 2 | 6,645; 6,609 | 22.429 | 0 |
| tethered_load | 2 | 5,650; 5,667 | 24.563 | 0 |
| Total | 8 | 64,810 | **85.454** | **0/8** |

Loading took 7.514 s; the measured qualification loop including loading took
93.084 s. Peak PyTorch allocated memory was 18,633,136,640 bytes (17.35 GiB),
reserved memory 19,306,381,312 bytes (17.98 GiB). These exclude driver/desktop
allocations. All inputs fit with the complete output reserve; none was truncated.

All eight generations terminated at EOS. There were zero runtime/OOM failures,
zero token-cap terminations, zero time-cap terminations and zero retries.
There were 3,414 generated/final-candidate tokens and zero separately identified
reasoning tokens. Those final-candidate tokens did not yield valid predictions.
Raw completions and generated token IDs remain available.

Each output begins with a Markdown JSON fence, so the strict parser records
`malformed_json`. Some outputs also contain multiple objects, an incorrect
top-level structure or extra prose. No fences were stripped, schema fields
repaired, prompts changed or outputs regenerated. The observed failure category
is the first parser failure; this report does not imply that removing fences
would make every answer valid or correct.

Whole-task complete-answer accuracy is **0/8**, supported-target coverage
**0/40**, and Boolean accuracy including failures **0/12**. The predefined
common set contains 36 targets across these eight questions; its complete-answer
accuracy is also **0/8**, with zero supported targets. Each domain is 0/2.
All numerical errors/RMSE are unavailable (`null`), because no valid numerical
prediction reached evaluation. Supported-only Boolean accuracy is likewise
undefined. All failures remain in complete-answer denominators. No OOD evidence
was collected in this diagnostic cohort.

A domain-weighted extrapolation to the frozen 500-question confirmation cohort
is 1.58 generation GPU hours. This is a planning estimate from eight malformed,
often short outputs; it is neither measured confirmation time nor a valid-answer
throughput estimate for a different prompt. The existing per-request and shared
full-study caps must remain binding.

## Verification and integration

Executed in the existing WSL environment:

```bash
python tools/llama_qualification.py prepare
timeout 2700 python tools/llama_qualification.py acquire
timeout 1500 python tools/llama_qualification.py generate
python tools/llama_qualification.py generate
python tools/llama_qualification.py evaluate
PYTHONPATH=src:tests:tools python -m unittest test_p12 test_p11 -v
python tools/p12_register_llama.py
python tools/llama_qualification.py report
```

The second generation invocation, within the original window, verified exact
cache identities and made **zero model calls**. All **15 offline tests passed**
in 1.039 s ([log](artifacts/P12_llama/integration-tests.log)); the earlier nine
P12 tests also passed before generation. Tests cover templates/thinking controls,
length reserves, public-input and target binding, strict parsing, token/runtime
failure accounting, equal-pair exposure, study authorization, checkpoint sealing,
cache identities and the separate qualification-root hash check. These tests are
software checks, not empirical accuracy evidence.

All 144 indexed export files passed SHA-256 verification. Both Qwen registry
entries matched their archived predecessor, registration reran idempotently
without calls, and the original native Llama qualification still records its
historical `GatedRepoError`. Documentation links passed local existence checks.

The lock now refers Llama to the separate completed diagnostic and hashes its
qualification/acquisition manifests. Both Qwen entries are unchanged. The prior
lock is archived. Future approved evaluation must pin the entire updated lock;
changed/unpinned registries fail closed. The old disabled proposal remains
historical and must be regenerated after preparation. No valid-output threshold
was invented to suppress unfavorable results.

The eight-request authorization has been consumed. Read-only evaluation/report
and idempotent registration can be repeated; additional model requests need a
new bounded run, not renewal of this expired qualification window. See
[commands](../P12_pipeline.md) and [decisions](../decisions/P12_llama_qualification.md).

## Remaining work

Enrichment coverage remains complete: 8,038 training/validation and 500
confirmation records. Frozen-encoder preparation and identity/coverage re-audit
remain before the expanded study. Full training/evaluation are still disabled.
The [full-run plan](P12_full_run_plan.md) incorporates this runtime measurement.
Retaining the frozen condition means counting malformed outputs as failures;
changing the prompt would create a separately versioned condition requiring
training/validation-only qualification, not overwrite these results.
