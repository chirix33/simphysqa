# P12 embedding preparation — 29 September 2026

Status: **complete, with zero missing embeddings**. The final public-only audit
verified all **8,038 training/validation and 500 confirmation** contexts. Reused
224 compatible vectors, generated 8,314 new vectors, and preserved every prior
vector. All 8,314 calls succeeded without retries; completed-run resume made
zero additional model calls.

Branch `main`, base commit `248575fd500947edd325836e636aebe41f9f65d0`;
existing uncommitted work and historical artifacts are preserved. The frozen
encoder and public context contract are unchanged. No paid provider, training,
Llama generation, paper edit, push or merge is part of this run.

Native run: `/home/aashraf/phi-jepa/p12-embedding-preparation-01`.
Export: `docs/reviews/artifacts/P12_embeddings/` under the actual `docs/` handoff.
All new vectors are stored natively in `embeddings/enriched/`; existing vectors
are referenced by immutable paths and hashes rather than overwritten.

## Coverage and measured cost

| Domain | Train/validation questions | Reused | Newly encoded train/validation | Newly encoded confirmation |
|---|---:|---:|---:|---:|
| driving | 888 | 56 | 832 | 80 |
| object_pushing_stacking | 2,400 | 56 | 2,344 | 140 |
| robotic_arm | 2,350 | 56 | 2,294 | 140 |
| tethered_load | 2,400 | 56 | 2,344 | 140 |
| Total | **8,038** | **224** | **7,814** | **500** |

The original 3,721 training scenarios / 6,702 training questions / 454,130
question-conditioned adjacent pairs are unchanged. Validation remains 1,336
questions. Confirmation remains the frozen 320 scenarios / 500 questions.
No simulation, horizon or question was moved between partitions.

| Scope | New vectors | Input tokens | Encoding seconds |
|---|---:|---:|---:|
| Training/validation | 7,814 | 65,768,189 | 1,119.473 |
| Confirmation | 500 | 4,334,923 | 74.182 |
| Total | **8,314** | **70,103,112** | **1,193.655** |

Token lengths were 5,502–12,916; no truncation or length failure occurred.
Peak PyTorch allocated memory was 1,657,505,280 bytes (**1.544 GiB**), reserved
memory 1,799,356,416 bytes (**1.676 GiB**), excluding driver/desktop allocations.
Encoding seconds include tokenization, synchronized model execution and atomic
vector writes per call; this conservatively charges the GPU allowance by elapsed
time rather than measuring hardware-active GPU seconds alone.

The generation process took **1,245.394 wall seconds (20.76 minutes)**, including
2.331 seconds loading the model. Tokenizer/cache preflight took 117.173 wall
seconds separately. The final audit finished at 20:34:16 UTC, following encoding
completion at 20:32:35 UTC. CPU utilization time was not separately measured.
The GPU was released after generation. Total additional paid cost: **$0**.

Run configuration SHA-256:
`db50bf67d48b12ae68559ebfe5b5b138e5dfa2b8bf771ca82f422a0038bc8998`.
Executed preparation source SHA-256:
`cdda6a44fd74099c1b0afd4b339be652be4d6c039b85bd71de849f589f8ac213`.
The configuration pins all relevant source files plus the eight local encoder
snapshot files. Later reporting/status helpers are archived separately and are
not attributed to encoder computation.

Evidence:

- [Final coverage audit](artifacts/P12_embeddings/audit.json), [configuration](artifacts/P12_embeddings/config.json), and [completion cost](artifacts/P12_embeddings/completion.json).
- [Training/validation vectors and hashes](artifacts/P12_embeddings/cache-coverage.json) and [verified enrichment origins](artifacts/P12_embeddings/enrichment-origin-audit.json).
- [Confirmation vectors and hashes](artifacts/P12_embeddings/confirmation-cache-coverage.json) and [separate enrichment origins](artifacts/P12_embeddings/confirmation-enrichment-origin-audit.json).
- [Per-attempt integrity index](artifacts/P12_embeddings/attempt-index.json), [export integrity index](artifacts/P12_embeddings/artifact-index.json), and [zero-call resume](artifacts/P12_embeddings/resume.log).

Full vectors and individual attempt records remain under the native run root;
the export includes their identities/checksums and aggregate measurements. The
reused vectors retain their original historical paths.

## Scope and execution

Prepare 8,038 original training/validation questions and the 500 frozen public
confirmation questions. All enrichment already exists and is verified before
use. No test outcomes enter context preparation. The public-only file guard
forbids opening reference/evaluator files and credential files.

Qwen3-Embedding-0.6B revision `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3`,
unchanged CUDA adapter, BF16, SDPA, single unpadded records, final-token pooling,
float32 L2 normalization, width 1,024 and a 32,768-token ceiling. No truncation.
Frozen runtime is PyTorch 2.7.1+cu128, Transformers 4.51.3, tokenizers 0.21.1
and safetensors 0.5.3. Detailed settings, source and model-file hashes are recorded
in the run configuration. Local model inference does not make Phi-JEPA fully
local: its retained enrichment was generated by OpenAI.

Budgets are in [the decision record](../decisions/P12_embedding_preparation.md).
The selected population is not reduced if a cache, token or runtime check fails.

## Commands and resume

Use the existing WSL core environment:

```bash
cd /mnt/c/Users/aashraf/Desktop/Work/phi-jepa/phi-jepa
source /home/aashraf/phi-jepa/.venvs/phi-core/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
timeout 1200 python -u tools/p12_embeddings.py prepare
timeout 5400 python -u tools/p12_embeddings.py run
timeout 1200 python -u tools/p12_embeddings.py audit
python tools/p12_embedding_finalize.py
```

These commands were executed successfully. `prepare` freezes the exact missing inventory. Repeating it verifies frozen
inputs. `run` reuses completed matching records, retaining the original persisted
deadline and attempt cap. An interrupted/failed attempt stops automatic replay.
After completion, repeating `run` makes zero model calls. `audit` is tokenizer-
only and refreshes this run's coverage/export; it does not overwrite historical
P12 qualification audits or open outcome references.

Progress during preflight is in `prepare.log`; encoding progress is written to
`status.json` every 25 calls and on state changes. In WSL:

```bash
tail -5 /home/aashraf/phi-jepa/p12-embedding-preparation-01/prepare.log
cat /home/aashraf/phi-jepa/p12-embedding-preparation-01/status.json
python tools/p12_embedding_status.py
```

`waiting_for_gpu` means the worker detected another compute process. Its wall
deadline continues to run. A stale `running` file alone is not evidence that a
worker survived a workstation restart. The read-only status helper checks the
exclusive worker lock and reports saved-vector counts by scope/domain, reserved
attempts, and whether a running label is stale. It makes no model/API calls.

## Verification

Executed before model preparation:

```bash
PYTHONPATH=src:tests:tools python -m unittest test_p12_embeddings test_p02b_live_boundaries -v
```

The initial 11 offline tests passed in 0.052 s. After adding the restart-aware
status check, **12 tests passed in 0.065 s** ([log](artifacts/P12_embeddings/tests-final.log)).
They check exact context/token binding,
vector identity/normalization/finiteness, population and scenario-group isolation,
budget reservations, approved enrichment origin/model, and existing public-only
provider boundaries, plus stale-worker detection. These are software tests,
not prediction performance. Finalization reconciles every successful attempt's
time with the audit total and hashes all 8,314 individual attempt records.

The final audit rebuilt every context and token identity, revalidated enrichment
provenance, checked all vectors and verified all reused file hashes. It opened no
outcome references. Full numerical training remains disabled; any future plan must reference the new
coverage and origin manifests, preserve the original population, and receive its
own explicit execution authorization.

The original disabled P12 proposal still references historical incomplete cache
audits. It is not ready to enable unchanged. A fresh study plan must bind this
run's complete manifests and the final agreed local-answer configuration after
the user's Llama diagnostics. This preparation did not alter Llama outputs,
prompts or parser behavior.
