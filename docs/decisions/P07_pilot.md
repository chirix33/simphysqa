# Stage 8/P07 scope and frozen evidence policy

The user authorized sequential execution of the revision-4 implementation plan.
After completing Stage 7, use the existing bounded tethered-load training/validation
selection for the selected pilot. The user explicitly approved this scope, existing
checkpoints, seed 11, 20-transition selection and held-out question, and required a
whole-scenario exclusion and serialization/stopping audit before interpreting the
output failures. The initial manifest retains the original selection wording; the
subsequent explicit approval changes no selection, runtime or budget. The manifest is
`configs/pilot_p07.json`. This does not authorize or launch the separate full study.

This stage freezes and replays evidence from the previously configured, actually
executed Stage 3–7 correctness runs. It is explicitly **retrospective evidence
packaging**, not a newly preregistered experiment or new independent measurements
of accuracy. Checkpoints and inference outputs are unchanged. No new tuning,
optimizer updates, GPU generation, encoder/API calls or test/OOD data access are
included. An additional bounded read/hash and runtime-control pass has a 300-second
cap. Report each method's original effort, rather than pretending the language
models' two updates match 200 numerical-model updates or one least-squares fit.

One training question/scenario supplies 20 unique physical transitions, each used
once per training epoch under equal question-pair weights. The language models use
the same question and one descriptive/typed target example, not 20 new independent
questions. One distinct validation question/scenario supplies 40 future timepoints
from 0.22 through 1.00 seconds. These timepoints/targets are not independent scenario
replicates; no confidence interval, significance test or method ranking is justified.

Freeze each source configuration, model/encoder revision, source snapshot, dataset
identity, checkpoint, answer/readout policy, target/alignment policy, provider cost
ledger and decoding configuration in the exported content-addressed manifest.
Retain full augmented trajectories as original numerical artifacts; named physical
measurements and answer prose are separate. Record per-horizon physical errors,
one-step diagnostics and context/fixed-coordinate drift with their respective
meanings. No future-state injection is allowed in autonomous trajectories.

Assessment remains the accepted development familiarity measure. Empty required
typed-contract coverage makes it partial and uncalibrated; the exact scenario/schema
V1 judge is separate. No threshold, detection accuracy, uncertainty calibration or
high-score numerical replacement result is claimed. Quaternion/tether/kinematic
checks have only their documented coverage. Unsupported contact events remain work
toward complete dataset support.

Runtime removals operate on the unchanged prediction and verified cached answer.
Removing assessment skips its callback and changes diagnostic computation; numerical
and answer outputs remain identical because this pilot's assessment does not modify
them. Removing the already inactive fallback is explicitly a no-op. These controls
are not additional independent accuracy observations or retrained models. Public-only
and reversed-forecast answers retain their original live P04a provenance and limits.

Native I/O profiling reports observed first/second sequential read+hash times; the
OS cache is not flushed, so do not label these cold-disk benchmarks. Model/provider
cache/resume evidence is reused with its original recorded outcomes and no new
paid calls. All failed/missing answer components remain in full denominators.
