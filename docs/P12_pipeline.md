# P12 qualification and proposed-study commands

Current numerical execution is authorized: see the
[bounded training wrapper](#authorized-numerical-execution--29-september-2026).
The run is now [complete, with preserved curves and checkpoints](reviews/P12_training_completion.md).
Historical preparation-time authorization statements below remain for provenance.

The subsequent paid enrichment work and its completed recovery have
[separate commands and budgets](P12_enrichment_pipeline.md). The original
qualification artifacts below retain their historical stage/source identities.
The [Llama follow-up](reviews/P12_llama_qualification.md) uses a separate root,
as documented below; do not rerun the historical stages to replace their artifacts.
The separately authorized [embedding preparation](reviews/P12_embedding_preparation.md)
is complete and preserves the original audits. All 8,538 contexts passed the
identity audit; no embeddings are missing. Use `tools/p12_embeddings.py` for its frozen
preflight, bounded generation, resume and tokenizer-only final audit.

Run in Ubuntu 24.04 WSL, using the existing core environment. The repository is
`/mnt/c/Users/aashraf/Desktop/Work/phi-jepa/phi-jepa`; qualification artifacts are
`/home/aashraf/phi-jepa/p12-expanded-qualification-01`. The Windows handoff remains
`C:\Users\aashraf\Desktop\Work\phi-jepa\phi-jepa\docs`.

```bash
cd /mnt/c/Users/aashraf/Desktop/Work/phi-jepa/phi-jepa
source /home/aashraf/phi-jepa/.venvs/phi-core/bin/activate
```

Executed qualification stages (historical P11 budgets are never imported):

```bash
python tools/p12_reconcile.py
timeout 300 python tools/p12_audit.py
timeout 300 python tools/p12_cache_origins.py
python tools/p12_confirmation.py
python tools/p12_confirmation_cache.py
python tools/p12_cache_origins.py --confirmation
timeout 2700 python tools/p12_models.py
timeout 1500 python tools/p12_local.py qwen3_8b_direct
timeout 1500 python tools/p12_local.py qwen3_8b_thinking
python tools/p12_local.py llama31_8b_direct
timeout 600 python tools/p12_numerical.py cpu
timeout 600 python tools/p12_numerical.py cuda
timeout 300 python tools/p12_context_profile.py
timeout 650 python tools/p12_preparation_profile.py
python tools/p12_evaluate.py
python tools/p12_train.py preflight
PYTHONPATH=src:tests:tools python -m unittest test_p12 test_p03 test_p10 test_p11 test_p02b_live_boundaries -v
python tools/p12_report_data.py
python tools/p12_export.py
```

GPU stages were sequential. Llama recorded its access failure without generating.
Diagnostic numerical weights were discarded. The structural preparation profiler
has an internal 600-second limit and does not train or synthesize context.

To verify/resume Qwen diagnostics without duplicate generation:

```bash
python tools/p12_local.py qwen3_8b_direct
python tools/p12_local.py qwen3_8b_thinking
```

Existing records must match the full model/tokenizer/template/runtime/decoding,
public-input and token identity. Mismatch fails closed. A reserved attempt left
by interruption requires cost reconciliation and new permission before retry;
there is no automatic retry or paid fallback. Do not re-run numerical profiling
to extend a study budget or treat it as main training.

Llama follow-up, executed after approved HF access and WSL login on 29 September:

```bash
python tools/llama_qualification.py prepare
timeout 2700 python tools/llama_qualification.py acquire
timeout 1500 python tools/llama_qualification.py generate
python tools/llama_qualification.py evaluate
python tools/p12_register_llama.py
python tools/llama_qualification.py report
```

Its native root is `/home/aashraf/phi-jepa/p12-llama-qualification-01`; export is
`docs/reviews/artifacts/P12_llama/`. The original blocked record and Qwen results
remain unchanged. All eight generations reached EOS, but all failed strict JSON
parsing. The registry records `complete_with_recorded_failures`, including the
official template/runtime and separate qualification/acquisition hashes.

A second generation invocation within the original window verified matching
caches and made zero model calls. All eight requests are consumed; the persisted
wall window is not renewed on resume. Do not rerun acquisition/generation to
extend that budget. To re-export completed evidence without model or API calls:

```bash
python tools/p12_register_llama.py
python tools/llama_qualification.py evaluate
python tools/llama_qualification.py report
```

Registration is idempotent and retains the prior model lock. Any new generation
must use a new authorized bounded run. Never paste HF tokens into chat or project
files. The qualification used 20 GB download allowance and a 2,700-second limit.

Current [training-run preparation](reviews/P12_training_preparation.md), executed
in a separate native plan root while preserving the original proposal:

```bash
python tools/p12_train.py plan
python tools/p12_train.py preflight --approved-plan /home/aashraf/phi-jepa/p12-training-plan-01/proposed-training-plan.json
python tools/p12_training_plan_verify.py
```

The new proposal and preflight are at `/home/aashraf/phi-jepa/p12-training-plan-01`,
exported under `docs/reviews/artifacts/P12_training_plan/`. Data is ready: all
8,038 train/validation and 500 confirmation contexts passed. These commands make
zero model or API calls; the verification helper deliberately attempts a disabled
CLI launch and confirms rejection before any study artifacts are created.

`--approved-plan` does not itself authorize execution. A later approved copy must
bind the prepared proposal checksum and only activate `training_enabled` with
the user's explicit authorization. Global `enabled` and `evaluation_enabled`
remain false. Source/runtime/layout/cache identities and immutable settings must
match. Numerical training need not wait for an unrelated answer-interface change.

Future bounded training/resume commands, not executed in this task:

```bash
python tools/p12_train.py train --approved-plan /home/aashraf/phi-jepa/p12-approved-training-plan.json --domain driving
python tools/p12_train.py train --approved-plan /home/aashraf/phi-jepa/p12-approved-training-plan.json --domain robotic_arm
python tools/p12_train.py train --approved-plan /home/aashraf/phi-jepa/p12-approved-training-plan.json --domain object_pushing_stacking
python tools/p12_train.py train --approved-plan /home/aashraf/phi-jepa/p12-approved-training-plan.json --domain tethered_load
```

Run domains sequentially. The approved-copy path above does not yet exist.
Repeating a domain command resumes a clean matching optimizer/RNG checkpoint
within its persisted deadline. Unresolved/uncheckpointed updates or interrupted
pass validation stop for explicit reconciliation; they are not silently replayed
or skipped. Preserve all partial histories and cost records. Execution is pending
numerical-training authorization, not missing context coverage.

Historical command templates for later confirmation integration, not executed
and **not authorized by the new training-only proposal**:

```bash
python tools/p12_local.py qwen3_8b_direct --approved-plan /home/aashraf/phi-jepa/p12-approved-plan.json
python tools/p12_local.py qwen3_8b_thinking --approved-plan /home/aashraf/phi-jepa/p12-approved-plan.json
python tools/p12_local.py llama31_8b_direct --approved-plan /home/aashraf/phi-jepa/p12-approved-plan.json
```

These use the frozen public-only 500-question cohort, its checksum, separate
study directory and new shared evaluation budget. All four completed fits and
selected checkpoints must be locked first. They do not launch Phi prose generation.
After identity-verified confirmation contexts exist, future numerical inference
and separate matched evaluation commands are:

```bash
python tools/p12_predict.py /home/aashraf/phi-jepa/p12-approved-plan.json
python tools/p12_evaluate.py --approved-plan /home/aashraf/phi-jepa/p12-approved-plan.json
```

The inference process enforces the public-only file guard and preserves complete
raw augmented trajectories/readouts separately from text. Only the evaluator
opens references. Without `--approved-plan`, evaluation remains restricted to
the eight validation diagnostics. Full-cohort execution is implemented but its
empirical gate awaits a separate evaluation proposal binding the complete embedding
caches, final agreed answer conditions and new authorization. The original
evaluation tools must be integrated with that finalized proposal; do not point
them at the new training-only plan. Future
approved local evaluation must also pin `local_answers_lock_sha256`, so changed
model registries cannot silently redirect it.

Details: [decisions](decisions/P12_expanded_qualification.md),
[qualification report](reviews/P12_completion.md),
[full-run proposal](reviews/P12_full_run_plan.md).
# Authorized numerical execution — 29 September 2026

The user authorized the completed-context proposal with SHA-256
`13cc4b3cbe8578abe22ebe8faa0987b2de2b3309639bf5e7a9988f4e0542add3`.
The approved copy now exists at
`/home/aashraf/phi-jepa/p12-approved-training-plan.json`. The historical commands
and pending-authorization descriptions above record preparation-time state.
Use the aggregate-budget wrapper for this authorized run:

```bash
cd /mnt/c/Users/aashraf/Desktop/Work/phi-jepa/phi-jepa
source /home/aashraf/phi-jepa/.venvs/phi-core/bin/activate
python -u tools/p12_training_execution.py run
# Read-only progress:
python tools/p12_training_report.py --status
# After completion or a preserved failure, verify/export artifacts:
python tools/p12_training_report.py
```

The wrapper holds an exclusive lock, preserves the exact approved settings,
and never renews its persisted four-hour allowance. Domains run sequentially
within conservative one-hour dispatch windows. A previously stopped dispatch
requires explicit reconciliation; do not bypass it with a direct domain command.
Reinvoking a successfully completed wrapper performs no optimizer updates.
Preflight reports are saved separately under
`/home/aashraf/phi-jepa/p12-training-execution-01/preflights/`.

Confirmation evaluation and local-baseline generation stay disabled. The later
evaluation proposal must include Llama direct and Llama prompted CoT alongside
Qwen thinking-off/on, with fresh qualified settings and an explicit budget.
See [execution decisions](decisions/P12_training_execution.md).
