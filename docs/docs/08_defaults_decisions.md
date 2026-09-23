# Development defaults and decision register

[Start](../README.md) · [Architecture](02_architecture.md) · [Assessment](04_assessment_fallback.md)

These settings make implementation concrete. They are proposed plan defaults, not final experimental conclusions or additional professor quotations. Implement them configurably; validate before the main experiment freeze.

| ID | Initial default | Change/review rule |
| --- | --- | --- |
| D01 | First benchmark: passive stopping, outputs x(T),v(T) | New domains need independent oracle and target validation |
| D02 | Frozen MiniLM-L6-v2 embedding, pin downloaded revision; fixture encoder only for mechanics | Changing encoder invalidates feature/reference caches and needs retraining |
| D03 | Generic JSON graph, 2 message-passing rounds; E from encoder, C=64,H=128 | Record capacity and compare alternate structured encoder |
| D04 | Linear fusion/readout/semantic heads; ODE MLP two hidden layers width 128, smooth activation | No hidden physics or nonlinear readout without a labeled comparison |
| D05 | Fixed RK4, 32 normalized-time steps, compare 64 on development | No accuracy claim without numerical/profile validation |
| D06 | Terminal normalized MSE + beta=0.1 semantic cosine reconstruction | Test beta in {0,0.01,0.1,1} on selection validation with declared budget |
| D07 | AdamW 1e-3, weight decay 1e-5, clip 1, FP32, batch 16, seed 11 | Small CPU cap first; choose epochs/patience from pilot, not test results |
| D08 | Separate text-only model as normal ODE fallback | Count its training and deployed parameters; do not silently use an untrained zero-schema branch |
| D09 | R1 bank of selected-checkpoint predicted training latents; k=1 question-cosine retrieval | Development profile only; target-latent interpretation requires owner decision for paper claim |
| D10 | Semantic judge V1 exact supplied prompt; alpha=0.5, lambda_json=1 | V1 is scenario/schema consistency; reference-comparison/diagnosis tasks need reviewed versioned prompts |
| D11 | ID calibration 95th percentile, strict >; terminal detection first | No formal guarantee; separate thresholds for distinct profiles/layouts |
| D12 | High-score prediction substitution off initially; technical fallback on | Enable only with validation evidence, fixed policy and paired harm/correction report |
| D13 | Content attempts 1, transport retries up to 2; no test repair | Changes logged with costs; no prediction-driven constraint revisions |
| D14 | One GPU job at a time; baseline GPT-2, 6 latents, microbatch4/accum32 | Actual memory profile chooses batch; do not assume 32 GB suffices for every model |
| D15 | Main proposed seeds 11,22,33; family-level uncertainty | Dataset counts/model IDs/budgets frozen in P07 before final tests |

## Open items that do not block P00–P03

**Q1 — Target latent definition.** Does the owner accept R1 predicted training trajectories as the fixed latent-reference implementation and revise the paper description, or require a different defined mapping of physical targets to latent space? The plan does not add a trained target encoder. R1 can be coded and tested, but a ground-truth-latent claim cannot be made.

**Q2 — Judge/diagnosis prompt scope.** The adopted V1 prompt does not judge a retrieved schema pair or diagnose causes. The coding agent should prepare small, separately versioned task prompts and schemas with development examples; the planner/user reviews them before live use. Preserve original V1 intact. Do not present the new task as validated by the demo.

**Q3 — Main experiment selections.** Exact live model IDs, API/compute budget, final datasets/domains/counts, calibrated fallback policy, full target layouts and selected hyperparameters remain to be frozen after the pilot. These are bounded run-planning choices. Missing them blocks expensive/final runs, not contracts and core implementation.

**Q4 — Genuine topology and fluid claims.** Current proxy/timed-parameter cases do not establish these claims. Choose validated implementations or narrow the paper claim. Do not silently relabel an event as topology or a pendulum as a fluid simulation.

The active P00 prompt records the user-reported PyTorch GPU-check pass. Ubuntu/WSL/NVIDIA visibility and FP32/BF16 forward/backward are confirmed by that report; model-specific baseline checks remain pending. Do not ask for BIOS setup again.

## Contradiction handling

Every change record includes source, date, superseded decision and impact on runs/checkpoints. If a new paper contradicts the latest explicit professor/user decision, surface the conflict instead of automatically treating all new prose as code requirements. The original architecture choice, terminal physical loss, untrained fixed energy and no inference repair are settled and are not Q1–Q4.
