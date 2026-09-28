# Manual WSL commands and verification

Branch: `full-phi-jepa-from-dataset`; base commit
`d2e9fe3daba63cc0b5295fa108177628c4319098`. Interface additions are uncommitted;
no push or merge was performed.

The user's follow-up requests executable commands for Phi-JEPA and baselines
across the available domains. This is a manual interface addition, separate
from the completed P11 study and its preserved evidence.

Changed files: `tools/replay_pipeline.py`, `tools/prepare_manual_pipeline.py`,
`tests/test_manual_pipeline.py`, `docs/Manual_WSL.md`, documentation entry links.
The replay command loads existing checkpoints without constructing historical
run/budget objects. It writes a new file and rejects historical output paths
and overwrites. Forecast inference installs the existing reference-open guard.
Saved-output viewing is explicitly distinct from fresh generation and evaluator
summary viewing. No model, loss, solver, parser or scientific layout was changed.

Availability: P11 Phi-JEPA, custom Coconut/CODI and saved gpt-5.6-sol outputs span
all four domains. Existing P10 conventional numerical checkpoints cover tethered
load. The preparation command creates separate domain-specific runs for the
other conventional comparisons; it reuses verified P11 public caches and only
the selected train/validation supervision. It does not train. Per-domain CPU,
GPU and artifact caps are explicit; provider calls are disabled. Validation
selection metrics are not relabeled as sealed-test results.

Actual checks:

- Preparation `--dry-run --domain all`: 56 main-cohort contexts/domain passed
  public/enrichment/encoder identity checks; no run was created.
- Fresh CPU Phi-JEPA inference on one P11 test question in each of driving,
  object pushing/stacking, robotic arm and tethered load: all succeeded.
- Each fresh trajectory, named output and readout exactly matched its saved
  checkpoint's prior output (content-hash comparison).
- Fresh CPU replay of all six active P10 numerical methods on one validation
  question: all succeeded.
- `python -m unittest discover -s tests -p test_manual_pipeline.py -v`:
  four tests passed, covering preserved historical output paths, overwrite
  refusal, matched-cohort filtering and new per-domain config selection.

Replay logs/results are under `outputs/manual-cli-check/`. The custom GPU
generation command reuses the existing checkpoint/codec/branch paths but was
not empirically rerun for this command-only follow-up. New per-domain training
and new provider calls were not launched. Historical P11 source snapshots and
results are unchanged; these interface additions have their own working-tree
source and are not part of the original P11 execution identity.
