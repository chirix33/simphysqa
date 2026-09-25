# Stage 6 independent comparisons — 24 September 2026

User approved all three definitions explicitly. They share the accepted numerical
layouts (complete n, including fixed conditioning), immutable public Q/C/enrichment,
frozen pinned Qwen encoder, equal weight per question transition and scenario
splits. Each owns its projection and fit. No primary model weights are borrowed.
Primary Phi-JEPA's full-2d loss, both P gradient paths and full feedback are unchanged.

| Method ID | Learned component and target | Context and recurrence |
| --- | --- | --- |
| `constant_context_text_ode` | Own P and d-output numerical ODE; adjacent numerical MSE | Initial p held constant inside every solve and across rollout; P learns through numerical prediction |
| `fixed_projection_lr` | Least-squares map [n;p;1] to next n | Own fixed seeded random P; constant p; no iterative neural updates |
| `constant_context_text_rnn` | Own P, one-layer tanh RNN and linear d-output readout; numerical MSE | Chronological teacher forcing; hidden carried within each question trajectory and reset between trajectories; predicted n only after initialization |

Projection initialization is independent CPU seed 11, Xavier uniform, zero bias,
1024 -> d, FP32. Neural hidden width 128, Adam 0.001, clipping 1. ODE uses two
hidden tanh layers, absolute physical time and RK4 one substep. These are explicitly
approved adapted comparisons, not unchanged notebook results. Notebook RNN layer
kind is preserved; state persistence is now explicit instead of reset on every
single-step forward. At both training sequence start and autonomous inference,
RNN hidden is zero and the first input is the cutoff state. Earlier observed
history is available to public text but receives no extra recurrent warm-up.

RNN loss averages over all transitions/coordinates, not over per-sequence means.
It rejects reordered, discontinuous or interleaved sequences and changed context
embeddings within a trajectory. It does not inherit inverse-multiplicity weighting.
No RNN state crosses scenario/question boundaries. Discrete models reject intervals
other than 0.02 seconds. All models predict every coordinate of n without clamping.

LR fitting uses NumPy 2.2.4 `linalg.lstsq`, float64 design/coefficient solve, explicit
intercept, rcond 1e-12, minimum-norm SVD solution. State inputs and fixed random P
originate in FP32, shared with neural methods; no feature normalization. Rank,
singular values and underdetermination are reported. Fixed P is not learned.
The fitted coefficient matrix is separate from gradient-trainable parameter counts.

User-approved bounded correctness profile: exact 20 P03 training pair IDs, at most
200 updates or 900 seconds for each neural model; one LR fit. Same separate tether
validation question and physical horizon. Independent training and deployment
checkpoint formats preserve method, layout, context, optimizer/RNG, sampler and
provenance; cross-method and primary-checkpoint loading are rejected.

All numerical forecasts pass through the shared named physical/readout interface
and the same frozen gpt-5.6-sol answer prompt/parser. Raw numerical results and
generated answers are evaluated separately. Direct public-only LLM QA reuses the
actual P04a answer on this identical question, with its constrained unsupported
Boolean policy explicitly disclosed. Do not compare its full-answer coverage as
though it were an unrestricted Boolean-generating method.

Runtime controls have unique IDs and explicitly are not retrained models:
`without_fixed_assessment`, `without_fallback`, `public_only_answer`. Their provider
callbacks preserve cost ledgers; disabled branches do not execute. Context/schema
removal retraining definitions were subsequently supplied by the user:

- `no_enrichment`: independent primary-architecture model, original public Q/C only,
  no generated enrichment in any forecasting-model input. Frozen Qwen, trainable P,
  d/2d widths, full augmented target, both P gradient paths and full feedback remain.
  Reuses the historical `public_base_for_offline_audit` cache/reader mode identifier.
  The trainer now explicitly accepts that configured mode; its default remains
  enriched with unchanged primary loss/gradient behavior.
- `no_text_conditioning`: independent numerical-only d-state ODE. No E/P/p or
  contextual target. All accepted numerical and fixed-conditioning fields remain;
  no zeroing. Numerical adjacent MSE and full predicted n feedback. This is a
  component ablation, not a text-based baseline or PIN-ODE.

Both preserve the same question-conditioned physical transitions, equal weighting,
solver/time policy and separate validation question. The base-context pair hashes
differ because context content differs; matched primary IDs and physical transition
IDs are both recorded. Each receives the existing 20-pair, 200-update/900-second
per-method cap. Downstream public Q/C and answer settings remain unchanged.
Do not compare raw losses of different coordinate widths or claim capacity parity.

Removing an already inactive assessment/fallback component is explicitly marked a
no-op. In the current primary profile assessment only annotates and is partial;
removing it changes computation, not predictions. High-score replacement is already
disabled; its removal is a no-op. Runtime controls remain separate from retraining.
There is no undefined `no_schema` variant. A structural-schema ablation requires a
future representation-level definition and is not a blocker. PIN-ODE stays excluded.

One observed engineering failure: LR's NumPy Boolean rank flag could not serialize
to JSON after its successful fit/checkpoint/forecast. Fixed conversion to Python
bool. Recovered diagnostics from saved coefficients by read-only SVD, with no
second fit or forecast; original fit duration is unavailable. ODE artifacts were
reused; only the pending RNN was trained during resume. Failure is preserved in
the method summary, not hidden as a clean first-pass run.
