# Active architecture — P02a / training contract 2.0.0-candidate.1

Updated 24 September 2026 by explicit user authority. The [previous architecture](02_architecture_pre_P02a.md) is preserved as historical context.

The authoritative computation, shapes, gradient rules and prohibitions are in
[MODEL_TRAINING_CONTRACT.md](../../MODEL_TRAINING_CONTRACT.md). Exact per-domain
candidate bindings are in [P02a state mapping](P02a_state_mapping.md). Data schema
1.0.0 and frozen export contract 1.1.0 remain unchanged.

Frozen E(Q,C) feeds trainable P to produce d context coordinates. Concatenate with
recorded numerical n_k of width d. Train the ODE over actual adjacent physical
intervals against concat(n_(k+1), the same current p), with gradients through both
copies of p. Carry every predicted numerical and context coordinate forward at
inference. No answer embedding target, tree encoder, physical readout or semantic
regularizer is part of this accepted direction.

`phi_jepa.integration` contains public/training/evaluator readers and immutable
interfaces. Public inference receives only a PublicProblem and numeric/prediction
layout. Training alone joins recorded future states. EvaluatorTruthReader marks
its output as recorded-state diagnostics, never autonomous forecasting. Metadata
is routing/provenance, not learned input. Deployment imports no simulator physics.

Interfaces include PublicProblem, Identity, RecordedPair, FullAugmentedPrediction,
PhysicalRollout, TypedAnswer and StageFailure. Candidate StateLayout supports
state-only and state-plus-fixed-conditioning explicitly; missing/extra/duplicate
or nonfinite values and unit/frame mismatch fail. Boolean outcomes remain a
separate unresolved representation decision. Context has no answer-bearing data.

Custom Coconut-inspired and CODI-inspired baselines are intentional future work;
independent upstream methods are not substituted. Existing descriptive targets
need review but not automatic official-CoT rejection. No live models, training,
providers, generators or later stages are launched in P02a.
