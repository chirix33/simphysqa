# P03 adjacent-pair training — 24 September 2026

Authority: revision-4 sequential plan and the user's explicit selection of equal
weight per question-conditioned pair. The earlier inverse-transition-multiplicity
proposal remains historical/optional, not the active objective. No question
context is dropped to deduplicate physical transitions.

Use one model/P per accepted domain layout. E settings and exact frozen outputs
come from P02b. P is FP32, width d, recomputed once per batch with both input and
target gradient paths intact. The ODE evolves all 2d coordinates. Raw coordinate
MSE is averaged equally across coordinates and question-conditioned examples.
There is no block rescaling, auxiliary loss, time normalization or physical
regularizer. Absolute physical time is a separate vector-field input.

Reversible engineering settings: two hidden tanh layers, width 128; Xavier
initialization with final-layer weights multiplied by 0.01; seed 11; FP32 RK4,
one substep per recorded 0.02-second interval; Adam lr 0.001, gradient norm cap
1.0, no weight decay/scheduler. Settings are explicit in
`configs/model_training_p03.json`. Choosing these defaults does not assert
adequate optimization or forecast quality.

The authorized correctness run used exactly 20 adjacent pairs from one existing
tether training question, 200 updates, 2.8435 seconds, with actual checkpoint
save/load at update 100. The separate validation question is from a different
scenario group. No new E/provider call, simulated data, full training or baseline
run occurred. The unit-weight population in this small fit is explicitly those
20 examples, not the complete dataset.

Deployment loads a minimal model/layout/context/solver checkpoint. It receives
only the public problem, frozen embedding and an external physical time grid.
Every predicted augmented coordinate is passed unchanged into the next solve;
integer-like state coordinates are not rounded. Evaluator reference access occurs
only after the autonomous trajectory is saved, for separately labeled metrics.

Training checkpoints also store Adam state, RNG, selected pair IDs, epoch/position,
selection history, split/release/enrichment provenance and actual solve counts.
Content-addressed tensor files are published before an atomic pointer. Corrupt,
wrong-role, wrong-E or wrong-layout checkpoints fail. An overflowing optimizer
step restores the previous finite model/optimizer and reports failure explicitly.

The tiny run has weak autonomous forecasts and practically zero tested Q-to-
numeric-forecast sensitivity. These are preserved negative diagnostics, not
permission to introduce normalization, resets, new losses or hidden correction.
See the phase completion report for exact measurements and limits.
