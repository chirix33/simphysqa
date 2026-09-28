# Run questions through Phi-JEPA and the baselines

Phi-JEPA already has selected checkpoints for all four domains. Inference does
not need retraining. These are the completed bounded P11 fits (48 training
trajectories per domain for the main checkpoints), not a claim that training
has reached convergence or that the answers are reliably correct.

The default comparison is **Phi-JEPA versus direct `gpt-5.6-sol`**, on the same
three held-out questions per domain. It prints the questions and final answers
and saves a readable report plus the underlying artifacts. The numerical
forecast is recomputed from the selected checkpoint. An exact compatible final
answer cache can be reused; each answer explicitly records its origin.

## Quick start: fresh vanilla answers, USD 5 cap

In WSL:

```bash
cd /mnt/c/Users/aashraf/Desktop/Work/phi-jepa/phi-jepa
CORE=/home/aashraf/phi-jepa/.venvs/phi-core/bin/python
OUT="$HOME/phi-jepa/manual-outputs/answers-$(date +%Y%m%d-%H%M%S)"

"$CORE" tools/answer_pipeline.py run --domains all --output "$OUT"
cat "$OUT/report.md"
```

Do not create `OUT` beforehand. Existing output directories are protected.
To run only one or several domains, replace `all`, for example:

```bash
"$CORE" tools/answer_pipeline.py run \
  --domains robotic_arm tethered_load --questions-per-domain 3 \
  --output "$HOME/phi-jepa/manual-outputs/selected-$(date +%Y%m%d-%H%M%S)"
```

Domain names: `driving`, `object_pushing_stacking`, `robotic_arm`, `tethered_load`.

The user-approved default API allowance is **USD 5 per run**. Vanilla-LLM
answers make fresh API calls by default, even when a historical answer exists.
Phi-JEPA's final answer prefers an exact compatible cache after recomputing the
numerical forecast. Use `--phi-answers fresh` to make both final answers fresh.

For a completely offline, zero-spend check, add both
`--max-api-usd 0 --vanilla-answers cache`. A missing valid cache is reported as
`cache_miss`, with no paid call. In particular, failed historical responses do
not become successful cache entries. The original failed attempt is copied as
historical evidence when it matches the current input/forecast. Such cases stay
in the report and evaluation denominator.

## Change the per-run budget or cache policy

Choose your own per-run dollar ceiling. This command uses the existing `.env`
credential configuration; never paste a key into a command or output folder.

```bash
read -rp 'Maximum API spend in USD for this run: ' API_USD
OUT="$HOME/phi-jepa/manual-outputs/live-answers-$(date +%Y%m%d-%H%M%S)"
"$CORE" tools/answer_pipeline.py run --domains all \
  --max-api-usd "$API_USD" --output "$OUT"
```

Vanilla answers remain fresh; existing valid Phi-JEPA answers can be reused.
Use `--vanilla-answers cache` to opt into cached vanilla answers, or
`--phi-answers fresh` to bypass Phi-JEPA's answer cache. Neither option changes
the numerical checkpoint, question selection or strict parsing.
Default additional caps are 120 provider attempts, 2,000,000 input
tokens and 100,000 output tokens, with one attempt per request. Override using
`--max-provider-attempts`, `--max-input-tokens`, `--max-output-tokens` if needed.
The generation limit remains 4,096 output tokens per answer; no parser repair,
automatic budget increase or hidden retry is performed. Conservative reservations
may stop requests before the nominal dollar ceiling. Unknown usage retains its
reservation. Costs use the existing recorded provider accounting policy and
are estimates rather than invoices.

Phi-JEPA uses the frozen `gpt-5.6-sol` answer layer with its numerical forecast
and qualified Boolean readout. The vanilla condition uses the same configured
model and original public question/scenario, without the forecast, and may
attempt all requested components. This is the P11 direct condition, separate
from the older Boolean-restricted P10 control. Request profiles and returned
model identities are saved; aliases do not imply a pinned provider weight
revision. Frozen Qwen remains `Qwen/Qwen3-Embedding-0.6B`, revision
`97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3`.

## Pick questions

```bash
"$CORE" tools/answer_pipeline.py list --domains tethered_load

"$CORE" tools/answer_pipeline.py run --domains tethered_load \
  --sample-id 337b9ff1f5c00610845cea856af91c3d \
  --output "$HOME/phi-jepa/manual-outputs/one-question-$(date +%Y%m%d-%H%M%S)"
```

Repeat `--sample-id` for several IDs. Explicit IDs replace the count rule.
Otherwise selection prefers prepared P11 cases, sorted by sample ID, then adds
sample-ID-sorted release cases when needed, without inspecting outputs. Default `--split test_id`
is held out from training and selection. `--split train` and `--split validation`
are available, but their results must be labeled accordingly.

The default `--inventory auto` reuses the prepared P11 inventory when sufficient,
and expands to the original release partition for larger counts or additional
sample IDs. For example, `--questions-per-domain 20` selects 20 questions in each
domain without changing partitions or training checkpoints. Available original
`test_id` questions: driving 138, objects 400, arm 394, tethered load 400. Counts
are questions, not necessarily distinct trajectories; all views of a trajectory
retain their original partition. Requests exceeding the actual available count
produce a clear CLI error, with no silent reduction or training-data substitution.

Use `--inventory release` to select from the release explicitly, or `--inventory
p11` to retain the old prepared-only limit. `list` shows the full partition by
default. `--cohort appendix` preserves its matched smaller P11 cohort (four
held-out questions/domain); it does not automatically expand.

Validate a larger request without files, models, GPU work or paid calls:

```bash
"$CORE" tools/answer_pipeline.py run --domains all --questions-per-domain 20 --dry-run
```

Missing public enrichment is now generated using the approved provider within
the **same per-run API budget**. Missing embeddings are computed locally with
the existing frozen Qwen model. Valid old caches are copied into the new run's
`context/` directory after identity checks. No dataset regeneration, training or
model download occurs. Reference answers are still opened only by evaluation.

The default USD 5, token and 120-attempt caps are unchanged. Eighty questions
can require 80 fresh vanilla requests plus enrichment and Phi final-answer calls;
the complete run may exceed those caps. Unavailable contexts/answers stay in the
denominator. Set larger limits explicitly only when you intend to authorize
them; the runner does not increase limits to satisfy the requested count.

## Other existing checkpoints

```bash
OUT="$HOME/phi-jepa/manual-outputs/appendix-$(date +%Y%m%d-%H%M%S)"
"$CORE" tools/answer_pipeline.py run --domains all --cohort appendix \
  --methods phi_jepa coconut codi vanilla_llm --output "$OUT"
```

Custom models run sequentially in their separate installed GPU environments.
They use the pinned `google/flan-t5-small` revision
`0fc9ddf78a1e988dac52e2dac162b0ede4fd74ab`, with no teacher fallback for CODI
student. Their weights were trained on the P11 appendix cohort. Use appendix
Phi-JEPA for a matched training-data comparison; selecting them with main
Phi-JEPA is an explicitly unequal-data comparison. Do not infer model rankings
from three questions or from these limited custom training runs.

Coconut generates a description and typed predictions. CODI student deliberately
generates typed predictions only. Valid typed predictions receive a clearly
labeled plain-text display rendering; it is not an added LLM explanation. Invalid
generations remain failures, with raw text/token IDs preserved. No duplicate
rows are deleted or values repaired.

Additional method names: `text_ode`, `lr`, `rnn`, `no_enrichment`,
`no_text_conditioning`. Their historical checkpoints currently cover only
`tethered_load`. Other domains receive explicit `unavailable` results. A required
public cache that is absent also causes an explicit failure; another domain's
checkpoint is never substituted. Different historical training cohorts remain
identified in checkpoint/job provenance.

## Files in each run

```text
report.md                         question, gold-vs-prediction table, prose, scores
summary.json                      validity, complete success, failures, usage
selection.json / config.json      exact cases, methods, source roots and caps
completion.json / budget.json     completion and resource accounting
source/                           current source hashes and content blobs
context/                          verified reused/new public enrichment and embeddings
logs/                             isolated worker logs
evaluation/                       separate reference-based metrics and coverage
evaluation/private/gold_answers.json  exact requested gold values and provenance
DOMAIN/SAMPLE_ID/public.json       original public scenario and answer spec
DOMAIN/SAMPLE_ID/question.txt
DOMAIN/SAMPLE_ID/METHOD/
    answer.txt / answer.json       readable answer and original typed envelope
    prompt.json / request.json    exact final prompt and request, no credentials
    forecast.json                 full raw trajectory, named channels, readout
    selected_checkpoint.json      checkpoint identity (numerical methods)
    model_job.json                 training configuration provenance
    context_config.json           frozen embedding configuration
    enrichment*.json              cached public enrichment and its prompt
    embedding.json                cached frozen embedding (when used)
    provider_ledger.json           attempt and returned-model metadata
```

Files vary by method. A complete numerical readout is not itself an LLM answer.
After inference, the evaluator adds the gold answers beside every method's typed
predictions in `report.md` and prints the same comparison tables to the terminal.
`evaluation/private/gold_answers.json` is keyed by sample ID and contains the
requested gold values, units, frames, query times, original tolerances and
reference-file provenance. No future reference trajectories are copied into it.
Gold outputs are never passed to the models. `--skip-evaluation` omits gold
export until you explicitly run `evaluate`.

`supported` describes evidence/channel availability, not correctness. Contact
outputs can remain unsupported and therefore fail complete-answer success.
Every requested method/question remains in the denominator. Evaluation retains
the original units, binding and tolerances. Numerical errors are separate from
answer scores. References are opened only by the separately launched evaluator;
deployment workers install the existing reference-access guard.

Assessment remains uncalibrated and incomplete in the underlying system; this
comparison does not recompute assessment or claim OOD recognition. Clarification
is the separate human-reviewed workflow, not an unattended benchmark action.

## Resume and evaluation

Repeat the exact command and output path with `--resume`. Completed successes
**and failures** are retained. A different budget, selection, checkpoint training
config or source revision requires a new output directory; it does not rewrite
old evidence. For an interrupted worker, first ensure no process is still using
the run before removing its `.running` lock.

`--skip-evaluation` runs public-only inference without opening evaluator
references. Evaluate separately afterward:

```bash
"$CORE" tools/answer_pipeline.py evaluate --output "$OUT"
```

This also adds gold comparisons to an existing answer-runner output directory
and rebuilds its report, without rerunning forecasts or making API calls. It
preserves the saved model answers and original inference source provenance.

The runner supervises CPU workers and GPU workers sequentially, with a ten-minute
per-worker ceiling, aggregate one-hour CPU/GPU worker-wall ceilings and a 2 GB
answer artifact cap. These include startup overhead and are not measured device
utilization. Local custom generation may hit its time or output cap; failures
remain visible. No default run launches training.

## Explicit train-and-run mode (optional)

You do **not** need this for the existing four-domain Phi-JEPA checkpoints.
This mode trains numerical models in a new directory with explicit training
caps, then answers the selected held-out questions. Training uses the original
train/selection split; the inference test cases never select checkpoints.

```bash
NAME="my-arm-$(date +%Y%m%d-%H%M%S)"
"$CORE" tools/prepare_manual_pipeline.py --name "$NAME" --domain robotic_arm \
  --cohort main --updates 4000 --cpu-minutes 60 --gpu-minutes 20 --artifact-gb 5

"$CORE" tools/answer_pipeline.py train-and-run --domains robotic_arm \
  --training-config "configs/manual/$NAME-robotic_arm.json" \
  --methods phi_jepa vanilla_llm --max-api-usd 0 --vanilla-answers cache \
  --output "$HOME/phi-jepa/manual-outputs/$NAME-answers"
```

The command above permits no paid calls. Its new forecasts generally will not
match old answer caches; supply your own `--max-api-usd` if you want fresh final
answers. Training and answering budgets are recorded separately. The configuration
controls actual updates and checkpoint selection; capped/failed training is not
silently called completed. This mode supports numerical methods; custom T5
retraining remains the existing explicit [P10 training pipeline](P10_pipeline.md).
Neither training mode nor new provider calls were launched to implement this UI.
