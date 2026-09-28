# Run Phi-JEPA and baselines yourself in WSL

For questions **and final prose answers**, use the newer
[end-to-end answer runner](Run_answers_WSL.md). This page documents lower-level
numerical replay; its `forecast` command alone does not call the answer LLM.

These commands use the installed environments and cached models. Manual replay
writes new files; it does not change P10/P11 checkpoints, budgets or reports.
The old P11 scheduler has an absolute deadline and is not a manual-run launcher.

## Setup

```bash
cd /mnt/c/Users/aashraf/Desktop/Work/phi-jepa/phi-jepa
export CORE=/home/aashraf/phi-jepa/.venvs/phi-core/bin/python
export COCONUT=/home/aashraf/phi-jepa/.venvs/phi-coconut-custom/bin/python
export CODI=/home/aashraf/phi-jepa/.venvs/phi-codi-custom/bin/python
export HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export OUT="$HOME/phi-jepa/manual-outputs/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUT"
```

Domain names: `driving`, `object_pushing_stacking`, `robotic_arm`, `tethered_load`.
Use `--cohort main` for main Phi-JEPA checkpoints and `--cohort appendix` for
the matched smaller comparison. Do not treat those as interchangeable models.

## Fresh Phi-JEPA inference on every domain

```bash
for D in driving object_pushing_stacking robotic_arm tethered_load; do
  "$CORE" tools/replay_pipeline.py forecast \
    --domain "$D" --cohort main --index 0 \
    --output "$OUT/phi-$D.json" || break
done
```

This actually loads each selected checkpoint and computes a new autonomous
trajectory, named physical readout and supported/unsupported event values.
It uses cached public Qwen embeddings. It makes no LLM/API calls, trains
nothing and cannot open evaluator references. Each output contains `public`,
`results.phi_jepa.trajectory`, `named`, `readout`, checkpoint identity and runtime.
It does not regenerate the answer LLM's prose/JSON.

List available questions and choose an exact ID (or another zero-based index):

```bash
"$CORE" tools/replay_pipeline.py list --domain driving --cohort main
"$CORE" tools/replay_pipeline.py forecast --domain driving \
  --sample-id YOUR_SAMPLE_ID --output "$OUT/another-driving.json"
"$CORE" -m json.tool "$OUT/phi-driving.json" | less
```

The default split is P11 `test_id`. `--split train` or `--split validation`
selects a different existing public example. These commands replay selected
dataset cases; arbitrary new scenarios need schema validation and new public
context/embedding preparation, not a sample-ID substitution.

## Matched Phi-JEPA, Coconut and CODI on every domain

Run GPU commands sequentially. The five-minute `timeout` is a manual execution
cap, not a change to the 2048-token generation limit. A strict parsing failure
returns exit code 1 and remains saved; `timeout` exits 124 if execution is capped.

```bash
for D in driving object_pushing_stacking robotic_arm tethered_load; do
  "$CORE" tools/replay_pipeline.py forecast --domain "$D" --cohort appendix \
    --index 0 --output "$OUT/appendix-phi-$D.json"
  timeout 300s "$COCONUT" tools/replay_pipeline.py generate \
    --domain "$D" --cohort appendix --custom coconut --index 0 \
    --output "$OUT/coconut-$D.json"
  timeout 300s "$CODI" tools/replay_pipeline.py generate \
    --domain "$D" --cohort appendix --custom codi --index 0 \
    --output "$OUT/codi-$D.json"
done
```

Use a shell without `set -e` if you want to continue after expected parsing
failures. For a given domain, the same appendix index selects the same question
for all three methods. CODI is student-only with no teacher fallback. The
custom models are notebook-derived implementations, not official reproductions.

## Vanilla LLM and saved benchmark outputs

The saved gpt-5.6-sol condition covers all four domains. This command displays
previous outputs, including the direct LLM, Phi answer LLM, and available custom
generations for exactly the selected question:

```bash
"$CORE" tools/replay_pipeline.py saved --domain driving --cohort appendix --index 0 \
  > "$OUT/saved-driving-answers.json"
"$CORE" tools/replay_pipeline.py summary --study p11 > "$OUT/p11-summary.json"
"$CORE" -m json.tool "$OUT/saved-driving-answers.json" | less
less docs/reviews/P11_benchmark_report.md
```

`saved` is deliberately not a fresh provider call. There is no new paid-call
allowance or arbitrary hosted-model switch in this manual replay interface.
The P11 direct condition attempts every requested Boolean component; historical
P10 `public_only` follows the older restricted Boolean policy.

## Other numerical baselines: train and compare in any domain

ODE/LR/RNN and the two ablations already have tethered-load P10 checkpoints:

```bash
"$CORE" tools/replay_pipeline.py forecast --study p10 --methods all \
  --index 0 --output "$OUT/p10-six-methods.json"
```

To obtain independently trained checkpoints in **any of the four domains**, use
the following preparation command and the existing budgeted supervisor. Do not
apply a tethered-load checkpoint to another domain's layout.

This example sets a separate **60 CPU-worker-minute, 20 GPU-worker-minute,
5 GB, zero-provider-call** cap for one domain. `--domain all` creates four
separate configs; their caps add up across runs. Preparation does not train.
The 4000-update setting is a bounded user experiment, not a convergence claim.

```bash
export D=robotic_arm
export NAME=my-baselines
"$CORE" tools/prepare_manual_pipeline.py --name "$NAME" --domain "$D" \
  --cohort main --updates 4000 --cpu-minutes 60 --gpu-minutes 20 --artifact-gb 5
export CFG="configs/manual/$NAME-$D.json"

# Cached enrichment/enriched embeddings are copied and verified at preparation.
# Encoding fills the public-only embeddings required by no_enrichment, offline.
"$CORE" tools/run_pipeline.py --config "$CFG" encode
"$CORE" tools/run_pipeline.py --config "$CFG" numerical biasinit_conditioned_full
"$CORE" tools/run_pipeline.py --config "$CFG" baselines
"$CORE" tools/run_pipeline.py --config "$CFG" forecast
"$CORE" tools/run_pipeline.py --config "$CFG" evaluate --refresh
"$CORE" tools/run_pipeline.py --config "$CFG" export --refresh
"$CORE" tools/run_pipeline.py --config "$CFG" status

"$CORE" tools/replay_pipeline.py forecast --config "$CFG" --methods all \
  --index 0 --output "$OUT/fresh-six-$D.json"
"$CORE" tools/replay_pipeline.py summary --config "$CFG" \
  > "$OUT/fresh-summary-$D.json"
```

Methods: `phi_jepa`, `text_ode`, `lr`, `rnn`, `no_enrichment`,
`no_text_conditioning`. `--methods all` selects these six; it does not silently
add custom text models or paid answer generation. `baselines` independently
fits the other five with the approved objectives, layouts and weighting.

Repeat with each domain, or prepare `--domain all` once and iterate over its
four configs sequentially. A name cannot be reused to overwrite a run. Resume
by rerunning the stage commands with the same config, not preparation. Existing
completed stages are skipped; do not reset an exhausted ledger. Select a new
name/config for a new experiment. Inspect `status` and stage logs after failures.

The new runs use the frozen P11 training and separate validation selections,
48/8 per domain with `--cohort main` or 16/8 with `appendix`. Validation is used
for checkpoint selection: these metrics are **not a new sealed-test result**.
The main-cohort new numerical fits are not matched to P11's smaller custom-model
training set. P11's completed matched appendix remains the comparison for those
custom checkpoints. New conventional-baseline training has not been executed
by the agent while preparing these commands.

Results live under `/home/aashraf/phi-jepa/manual-runs/NAME-DOMAIN/`:
`numerical/METHOD/forecasts`, `evaluation/summary.json`,
`evaluation/physical_summary.json`, `evaluation/physical_by_time.json`, and
`budget.json`. The evaluator retains unrun answer/custom conditions as missing;
use `condition: numerical_readout` for this numerical-only experiment. Export
goes to `docs/reviews/artifacts/manual/NAME-DOMAIN/`.

Do not invoke the historical `all` or `study` convenience bundles for these
manual numerical profiles: they additionally schedule custom training and
provider/report stages. The explicit commands above keep the scope clear.
