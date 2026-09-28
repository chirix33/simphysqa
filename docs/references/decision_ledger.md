# Phi-JEPA project memory and decision ledger

Updated 23 September 2026 after receiving workstation GPU, disk, and WSL diagnostic results. Purpose: durable project handoff for subsequent sessions. Read this before older notes; consult the named primary project sources for exact quotations and schemas. This document records decisions and distinguishes proposals, defects, and open implementation choices. It is not evidence of completed experiments or an update to an inaccessible internal memory store.

## Authority and conflict resolution

1. Latest explicit user/Professor clarification governs. Professor Kaushik's instruction, “We should stick with the decisions we did in the morning,” resolves the demo's contradictory reintroduction of energy minimization and inference-time schema repair: both remain excluded.
2. September 22 part 2 governs later decisions, including its final answer-generation discussion; September 22 part 1 governs the morning architecture/reviewer discussion unless superseded.
3. The current newer manuscript is the paper reference, subject to meeting corrections. The removed older manuscript is not an implementation authority.
4. The supplied demo supplies adopted prompt strings/response schemas and useful prototype components. Its implementation does not override agreed scientific decisions.
5. Initial transcripts and initial implementation remain historical context. Do not reopen resolved questions because an older file contradicts this ledger. Explicitly identify genuine new contradictions to the user.

## Settled architecture

- Implement the PDF's latent-LLM architecture, not the initial numerical pipeline with manually authored domain dynamics. Generic schemas and software types are appropriate for modularity.
- Use frozen question embeddings and frozen prompted LLM extraction, answer generation, and judging. Train the structured-schema encoder, hybrid fusion/projection, latent neural ODE dynamics, physical readout, and semantic reconstruction head as required by the agreed computation graph.
- The hybrid representation must preserve question information and the extracted structure. Exact dimensions and interchangeable structural encoders are configurable; illustrative eight-dimensional physical or 512-dimensional latent examples are not universal dimensions.
- The initial physical readout is linear, as discussed. Any nonlinear alternative is a labeled capacity comparison. Frozen LLM answer generation is separate from this numerical readout.
- Physical supervision is **terminal-state decoded MSE only**, plus the agreed terminal question-alignment/reconstruction regularizer. Do not resurrect cosine physical guidance or impose intermediate-trajectory MSE as the main objective. Semantic distance and weight are explicit implementation defaults to validate; include a no-regularizer ablation.
- A differentiable numerical solver is modular. First-/second-order solver comparisons are not the paper's main contribution and are not a prerequisite. No unsupported mathematical robustness claim should become an engineering assumption.

## Extraction, schema, and final answer

- Adopt the professor's supplied demo prompts and formal response schemas, versioned verbatim before changes. Extraction keys include `observations`, `events`, `relations`, `symmetries_or_invariances`, and `unknowns`. Observations preserve names, values, units where present, relations, and evidence; events preserve descriptions, nullable times, and evidence.
- A stable generic outer contract permits scenario-specific contents and topology. Unknown answers must remain explicitly unknown until prediction; do not encode missing physical quantities as true zeros or populate them from gold targets.
- Encode string values as well as numeric values: names, units, relation operators, event meanings, evidence, and topology matter. Tree/graph/other encoders can share an interface; a flat/linear comparison must be labeled. Concatenation alone does not establish physical invariance.
- Preserve original scenario facts and bounds during inference. No prediction-driven schema topology repair or rewritten constraints.
- The final frozen LLM receives the original question/schema and **named, unit-aware decoded predictions**, with deliberately selected rollout information. It returns `plain_text_answer` and `structured_answer` containing `final_state`, `trajectory_summary`, `structural_interpretation`, and `fallback_used`.
- The later part-2 discussion (18:35–19:53) supersedes the preliminary proposal to train a separate arbitrary-JSON decoder on 20–30 examples. The learned physical readout remains necessary. Do not confuse these two decoders.

## Energy, OOD, and fallback

- Use fixed, untrained energy scoring for assessment/OOD diagnosis and the agreed fallback policy. No separately trained EBM or denoising-score-matching objective. Bregman is deferred.
- **No inference-time energy minimization**, latent gradient steps, Langevin updates, anchor/radius optimization, K1 adaptation, or K2 schema/topology repair. Older ROSW/Krylov/SVD/basin/replica-exchange ideas are outside the approved implementation.
- Implement the described latent-reference similarity plus structured contract-severity/semantic assessment explicitly. Reference pools come from training data; thresholds/calibration come from validation. No test ground truth enters deployment inference. Define a consistent score direction, component scaling, retrieval rule, and missing-component handling rather than inheriting contradictory verbal energy signs.
- Generic contract checking and evidence-based external judging are allowed. Semantic judging may produce a bounded score and supporting evidence; it is not automatically calibrated probability or a physical correctness oracle.
- Diagnose anomalies across selected rollout states and supply evidence-supported possible causes. Do not claim autonomous correction/control, chaos detection from energy alone, or detection of wholly unobserved causes without available evidence.
- Fallbacks are bounded and reason-coded: text-only or an explicitly supported unconstrained/zero-schema ODE path according to the failing stage. No hand-crafted replacement physics JSON or injected oracle fixture. Track extraction, initialization/readout, solver, answer-generation, and terminal failure separately.
- “Untrained energy” is an agreed design choice. It is not a general theorem that training any EBM would necessarily introduce domain engineering.

## Data and scientific evaluation

- Build one verified domain end to end, then expand to roughly three manageable categories. Current examples are driving, robotic arm, and slosh. The demo's slosh is a mechanical proxy, not a validated fluid/CFD model. Exact domain count is not itself the contribution.
- Verify simulator forces, initial conditions, event semantics, units, time origin/grid, and labels independently. Paper and demo sampling rates differ; choose and record a justified common grid rather than treating either as automatically binding.
- Split base scenarios/families before paraphrases or transformations. Separate parameter extrapolation, unseen combinations, timed events, and genuine topology shifts; avoid calling all perturbations structural OOD.
- No gold answer, held-out trajectory, OOD label, or reference solution in inference inputs. Keep evaluation-only objects behind a separate interface.
- Physical endpoint MSE/RMSE requires per-quantity normalization and unscaled reporting where useful. Full-trajectory error is a separate metric and requires genuinely comparable time-grid predictions. Define normalized cosine similarity explicitly.
- PCVR must check actual predictions against independently specified physical constraints for every method. Extraction evidence/provenance, schema validity, judge agreement, and physical violation are distinct metrics. Empty coverage is not perfect compliance.
- Report OOD detection errors, false alarms, diagnosis quality, fallback coverage and terminal failures; measure stage-level latency, calls, tokens, numerical function evaluations, training compute, and cache policy.
- Keep simulator/evaluator/annotation engineering distinct from inference-method engineering in DEO. No hidden authored physics in the learned method; generic software contracts are permitted. A hard-coded DEO number is not an audit.
- Empty manuscript tables await the user's experiments. Existing numerical expectation ranges are not empirical findings. Professor handles revisions to theoretical claims; code must not turn speculative guarantees into asserted properties.

## Baselines and new September 22 addition

- Required comparison families: direct LLM; separately trained standard neural ODE; properly implemented physics-informed ODE; full Phi-JEPA; and agreed ablations including energy assessment, fallback, semantic regularization, and structured encoding.
- Professor additionally requires **CoConuT** (`facebookresearch/coconut`) and **CODI** (`zhenyi4/codi`). These are trainable continuous-reasoning methods, not prompting variants.
- Keep representative high-, moderate-, and non-reasoning LLM categories; exact provider/model IDs remain to be selected and logged. CoT/ReAct are applicable controlled conditions, not a mandatory Cartesian product over every architecture. ReAct requires an explicit fair tool/action budget.
- New baseline source pins: CoConuT `27273cb8cca4bb763c041a63b036d0c3b7cbbb48`; CODI `2c2314662c63e9f482ebc46614ffe9af17a241e5`.
- CoConuT's documented native path trains CoT first, then a staged latent curriculum. CODI offers released GPT-2 and Llama-3.2-1B checkpoints and self-distillation training. Their original benchmark interfaces require verified text solution traces, not just numerical terminal labels.
- Both need physics dataset/output adapters and common numeric evaluation. Released arithmetic checkpoints alone do not establish a fair trained physics comparison. Account for trace generation, all training stages, and parameter/compute differences.
- **Proposed, not yet approved empirical optimum:** start both with GPT-2/six latent steps; use separate pinned environments; initial microbatch 4 and accumulation 32 (effective batch 128), reducing microbatch if necessary. Evaluate at batch 1 first. Consider a matched 1B expansion after profiling. Workstation details are now recorded below; do not keep asking for the GPU/OS already supplied.
- Author settings, executable preparation examples, epoch-schedule nuance, known launcher issues, and launch gates are recorded in `Phi_JEPA_Baseline_Runbook.md`. No baseline dependencies/weights were installed and no training was run in this review.

## Workstation: supplied facts and compatibility plan

- User reports one NVIDIA GeForce RTX 5090, Windows Task Manager dedicated capacity 31.5 GB (nominal 32 GB model); Intel integrated Graphics is also listed. Intel shared GPU memory shows a 47.5 GB limit. This is not extra NVIDIA VRAM or a second CUDA GPU.
- OS is Windows 11 Enterprise. System memory counters: 16.7 GB used and 46.7 GB available, about 63.4 GB accounted for. Treat roughly 64 GB as an inference, not confirmed installed capacity; the shared-GPU limit does not reconcile with those counters. C: is now measured at 2,025,740,824,576 bytes total and 1,887,890,018,304 bytes free (about 1.89 TB / 1.72 TiB free).
- Windows nvidia-smi confirms RTX 5090, 32,607 MiB total and driver 610.60. The earlier virtualization blocker is resolved: user output shows Ubuntu-24.04 Running at VERSION 2, and Ubuntu nvidia-smi detects the RTX 5090. It reports NVIDIA-SMI 610.47.03, KMD 610.60 and CUDA UMD 13.3, with 1,585 / 32,607 MiB used at that snapshot. This verifies GPU visibility, not yet PyTorch computations. CPU model/core count and exact physical RAM remain unverified; obtain free VRAM when profiling.
- Recommended execution environment: WSL2/Ubuntu 24.04, one CUDA GPU, Linux filesystem for active I/O, separate Python 3.12 environments. The current walkthrough uses Ubuntu venv at ~/phi-jepa/.venvs/phi-coconut and phi-codi; Conda is optional if already configured, not a prerequisite. Use the Windows NVIDIA driver; do not install a Linux display driver in WSL. No initial need for Docker or an independently installed CUDA compiler.
- **RTX 5090 compatibility changes the original installation plan:** use PyTorch 2.7.1 CUDA 12.8 wheels as a conservative initial compatibility target in both environments. CoConuT's original Torch 2.5.1 and CODI's explicit CUDA 12.6 package pins must not be installed unchanged. Retain different Transformers versions, remove CUDA/Triton pins only in versioned requirements copies, let the selected Torch wheel resolve its runtime dependencies, and run `pip check` plus actual CUDA/model tests. This is a documented environment adaptation, not a proven installation or latest-version claim.
- Hardware assessment: GPT-2 baseline pair and compact Phi-JEPA training are reasonable local pilot targets. CODI 1B LoRA and CoConuT 1B full tuning are candidates for measured small-batch profiles; no fit/time guarantee or automatic need for rented A100s. Run GPU-heavy jobs sequentially at first.
- Initial precision: preserve FP32 for CoConuT GPT-2 reference check; CODI BF16. Any CoConuT BF16 change is a recorded variant. Start workers at 2, evaluation batch 1, no initial quantization/optional kernel changes, and retain effective batch 128 through accumulation. Keep WSL's initial memory cap until measurements justify a change.
- `Phi_JEPA_Baseline_Runbook.md` now contains revised install commands, Windows/WSL checks, CUDA BF16 forward/backward smoke check, and profile gates. Nothing has been installed or executed on the workstation by this assistant. The original unmodified requirements install instructions are superseded for this hardware.

### September 23 immediate setup status

- **Resolved:** WSL2 virtualization/startup and Ubuntu installation; Linux NVIDIA GPU visibility confirmed by user output. Do not repeat firmware instructions or describe WSL as blocked.
- Keep driver 610.60 and PyTorch 2.7.1+cu128 as the initial test target. CUDA UMD 13.3 in nvidia-smi is driver information; it does not establish an installed CUDA toolkit or the PyTorch runtime. NVIDIA driver backward compatibility permits the older cu128 runtime.
- Next: create the first isolated Python 3.12 environment, install cu128 Torch and matching baseline NumPy, then execute FP32/BF16 CUDA matrix operations with backward gradients. Capture actual torch/runtime versions, device capability, BF16 availability and result. No model weights are needed for this check.
- Then install adapted baseline requirements, validate checkpoint/model execution, and profile before training. No PyTorch test or training result has yet been supplied. The assistant has not installed software on the workstation.

## Phased implementation handoff — September 23

The user explicitly chose a separate Codex coding agent to implement phase-by-phase, with this planning assistant supplying prompts and reviewing returned reports/blockers. Core implementation may start while the workstation CUDA check is pending. GPU/live-model evidence remains an explicit later gate; fixtures are not empirical evidence.

The handoff is Phi_JEPA_Codex_Implementation_Handoff.zip, with a linked README, repository-root AGENTS template, detailed architecture/data/assessment/baseline/environment specifications, P00–P08 prompts, completion/blocker review templates, exact original prompt/schema assets and source references. Import under docs/implementation/; merge AGENTS policy without overwriting existing rules; begin only P00. No user repository implementation, commit, push or experiment was performed while authoring it.

Proposed defaults are explicitly distinguished from settled professor decisions: first-domain passive stopping, generic JSON graph, linear fusion/readout, terminal physical MSE plus semantic cosine regularizer, RK4 and a separately trained text-only fallback model. High-score numerical substitution is off in the development default pending validation evidence; technical fallbacks remain defined. These are configurable plan choices, not reported experimental findings.

Two bounded scientific gaps are tracked for later claim/run review: R1 uses predicted training latents because a ground-truth physical-to-latent reference mapping is not fully defined; the exact supplied V1 judge checks scenario/schema consistency, not retrieved-schema comparison or cause diagnosis. Development modes and interfaces can be implemented now; full-paper-faithfulness claims require an explicit target-reference decision and reviewed versioned judge/diagnosis tasks. Do not silently add a trained target encoder, change the adopted V1 prompt or reopen settled no-optimization/no-repair policy.

## Implementation organization and acceptance

- Modular provider adapters, immutable schemas, configurable encoders/solvers/heads, isolated baseline environments, common dataset/evaluator contracts, and reproducible experiment runners are required.
- Preserve prompts, model/data/code revisions, split IDs, seeds, solver/dtype settings, full checkpoint state, normalization, tokenizer/readout metadata, and run provenance.
- Validate the computation graph and gradients, tensor batch/time/state contracts, signed/multi-value numeric parsing, failure paths, and leakage boundaries with meaningful targeted checks.
- Separate upstream-reference settings from intentional fixes and physics-adapted settings. Do not silently alter an upstream method and call the result a reproduction.
- Next implementation order: verified dataset/oracle and contracts → minimal correct trainable Phi-JEPA → fixed assessment/fallback → shared evaluator → independent baseline adapters → one-domain pilot → ID/OOD/ablation expansion.
- Full implementation planning can proceed. Exact semantic-loss settings, reference aggregation, validation thresholds, resource budgets, and remaining model selections are concrete plan choices to validate, not reasons to reopen settled architecture.

## Existing implementation and demo status

The original `chirix33/phi-jepa` implementation was a numerical/schema prototype; fixture mode works and the user confirmed failures occur in OpenAI mode. Do not claim the later demo fixes that execution path. Do not reuse hand-crafted domain enforcement as evidence for zero domain engineering.

The supplied notebook is `Phi_JEPA_COMPLETE_OpenAI_MuJoCo_SMOKE20_WITH_ANSWERS_Colab.ipynb`, SHA-256 `a66b96b69c304268218d058235d4a1f5669164cd5cb0535323c6e6cce44668d6`. Its reviewed archive contains a 20-case development run, split 9/3/8, one seed, two epochs, and 32 evaluation records across four labels. The saved configuration says `gpt-5`; “GPT-5.5-Instant” is not verified by those artifacts.

Verified blockers to carrying that notebook forward unchanged:

1. It trains full-trajectory losses, not the agreed terminal objective plus question regularizer. An online target-state encoder is unused in the differentiable loss, so its EMA copy is not the intended learned target.
2. Schema features ignore string values. Different names/units/relation meanings with matching numbers/paths can be encoded identically.
3. `[1,T,D]` is passed to a decoder expecting `[T,D]`. Initial/final/min/max payloads become repeated whole trajectories: 4,032 numbers rather than the intended 32 in this demo. Supply explicit dimensions and physical metadata.
4. Its PCVR checks evidence substrings, not physical trajectories. The arm's 1/11 penalty arises from `2` versus `two-joint`; an empty schema receives zero. Replace that metric and retain provenance separately if useful.
5. Its energy is learned input-value reconstruction rather than the intended fixed reference score. It treats relations as equalities, leaves a weighting parameter unused, and disables semantic judging in saved evaluations. Its adaptation/repair loops are excluded by the latest decision.
6. All four labels reuse a full-model checkpoint. The standard label is a schema-removal ablation, not independently trained; without-EBM still scores/falls back; no genuine PIN-ODE experiment was run. All eight full cases fall back and share the standard/no-EBM trajectories.
7. Car force remains a fixed negative friction-like force after stopping, causing reversal. Slosh is a proxy. Time-zero labeling is inconsistent with post-step sampling. Verify these before making datasets.
8. Validation is not used for selection; checkpoint metadata is incomplete; caches/paths can collide; numerical-call counters and timing separation need correction. Reported DEO is declared, not audited.

These are known implementation TODOs, not missing Professor decisions. The full audit is `Phi_JEPA_September_22_Demo_Review_and_Decisions.md`. No project source was modified in that audit or in the baseline review; pure-function replay was used to verify selected artifact findings.

## Project source references

- `transcript_september_22_part_2.docx` — latest full meeting, particularly final decoding and semantic ablation.
- `transcript_september_22_part_1.docx` (uploaded name includes `-1-`) — morning reviewer/architecture decisions.
- `LA_PRM__PHI_JEPA___ICLR_2026_Newer_Version.pdf` — active manuscript, subject to later corrections.
- `phi_jepa_results.zip` and the supplied generating notebook — prompts/contracts and prototype evidence.
- Prior September 20 transcripts and original repository review — historical context only where not superseded.
- `Phi_JEPA_September_22_Demo_Review_and_Decisions.md` — detailed verified source audit.
- `Phi_JEPA_Baseline_Runbook.md` — official baseline setup, proposed experiment settings, and workstation prerequisites.

For future sessions: retrieve the latest ledger and runbook rather than assuming any proposed setting has been tested. Update this ledger when the user supplies a newer paper, meeting correction, workstation specification, selected configuration, or actual run result. Never replace measured results with manuscript estimates.


## Installation correction — 2026-09-23 P00

The historical import destination above is superseded by the user: the installed handoff root is `docs/`, with root `AGENTS.md`. Current paths are `docs/README.md`, `docs/PROGRESS.md`, `docs/docs/`, `docs/prompts/`, `docs/assets/`, and `docs/references/`. The original paragraph remains historical evidence.
