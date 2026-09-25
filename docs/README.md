> **Active supersession — 2026-09-24:** Model work follows [training contract 2.0.0-candidate.1](../MODEL_TRAINING_CONTRACT.md) and the user's revision-3 Stage 1/P02a request. Adjacent recorded-state training uses frozen E(Q,C), trainable P of width d, the same undetached p on both sides, and full predicted 2d-vector feedback. Conflicting terminal-only, tree/readout/semantic-head, E(Q,C,A), upstream-baseline substitution and truth-forbidden-in-training instructions below are historical. Custom Coconut-inspired/CODI-inspired variants are intentional. Future phases require separate authorization. Frozen dataset/export contracts remain unchanged.

# Phi-JEPA: Codex implementation handoff

Prepared 23 September 2026. **This is a specification and phase-prompt package, not an implemented system.** It incorporates the active manuscript, September 22 meetings, professor's later correction, reviewed demo/source, CoConuT/CODI requirements, and workstation progress.

## Start here

Implementation can proceed. The active P00 prompt records a user-reported PyTorch 2.7.1+cu128 FP32/BF16 forward/backward pass; model-specific GPU verification remains pending. CPU contracts, dataset/oracle validation, provider fixtures, numerical components, evaluation, and checkpoint round trips do not require that workstation GPU. Mark GPU-only verification pending; never convert a fixture pass into an empirical result.

The user coordinates this work. A separate Codex coding agent implements one authorized phase at a time. The planning assistant reviews Codex's reports, resolves questions, and supplies the next prompt. No implementation is launched by distributing this package.

1. This handoff is installed directly in `docs/`, preserving its subdirectories. Use a phase branch and preserve existing work; do not create a duplicate installation.
2. Read the existing repository-root [AGENTS.md](../AGENTS.md). Preserve applicable instructions and flag genuine conflicts.
3. Give Codex [the Phase 0 prompt](prompts/P00_bootstrap.md). This phase inspects the actual checkout and establishes the smallest working executable slice.
4. Return Codex's completion report to the planning assistant. Continue using the prompt for the next authorized phase only after the preceding acceptance gate has been assessed.

The root package is deliberately small to read. Follow the relevant detailed links rather than pasting the entire package into every Codex session.

`SHA256SUMS.txt` is the preserved original distribution snapshot, not an index of
edited installed documentation; its `AGENTS.md` entry describes the original template.
Current instructions are at repository-root `AGENTS.md`. Verify preserved assets and
installed links with `python tools/verify_p00_handoff.py` from repository root.

## Document map

| Document | Purpose |
| --- | --- |
| [Context and decision authority](docs/01_context.md) | Research goal, what is settled, superseded ideas, prototype audit and reusable parts |
| [Architecture and contracts](docs/02_architecture.md) | Module boundaries, shapes, losses, output binding, checkpoints, data leakage protection |
| [Data and evaluation](docs/03_data_evaluation.md) | Oracle validation, initial domain, splits/OOD, metrics, annotations and dataset candidates |
| [Assessment and fallback](docs/04_assessment_fallback.md) | Fixed scores, retrieval, calibration, judge scope, runtime policy and remaining scientific gaps |
| [Baselines and experiments](docs/05_baselines.md) | Independent baselines, CoConuT/CODI, comparable inputs, ablations and experiment matrix |
| [Phases and acceptance gates](docs/06_phases.md) | Deliverable slices, prerequisites, tests and hardware gates |
| [Codex workflow](docs/07_workflow.md) | Completion reports, blocker protocol, branch discipline and user/planner handoff |
| [Defaults and open decisions](docs/08_defaults_decisions.md) | Concrete starting values; adjustable engineering choices versus scientific decisions |
| [Source index](docs/09_sources.md) | Primary files, hashes, official links, source limitations and notebook contract provenance |
| [Workstation state](docs/10_environment.md) | What is already verified, what remains pending, CPU/GPU environment separation |
| [Progress tracker](PROGRESS.md) | Initially unstarted phases and evidence required to advance |

Detailed prior work is included for selective reference: [baseline setup runbook](references/baseline_runbook.md), [demo/source audit](references/demo_review.md), and [decision ledger](references/decision_ledger.md). These snapshots provide context. Future phase reports and approved decision updates must record any newer state.

## Non-negotiable scientific core

Frozen question/text embedding and prompted LLMs → semantics-preserving structured encoding → hybrid projection → trainable latent ODE → **linear physical readout** and semantic reconstruction. Train on terminal decoded physical MSE plus question-alignment regularization. Generate the final answer using a frozen LLM with named physical predictions.

At inference: fixed assessment, evidence-supported diagnosis and bounded fallback. **No EBM training, test-time energy descent, Langevin refinement, prediction-driven schema repair, or Bregman component.** The professor's explicit morning-decisions confirmation overrides contradictory demo/paper passages.

One JSON envelope describes extracted scenario facts; another contains the final answer. Preserve both. The initial extraction and final numerical predictions must remain available independently of generated prose.

## Phase overview

| Phase | Completed slice | Can start without workstation GPU? |
| --- | --- | --- |
| P00 | Repository audit, package/CLI, configuration, run manifest and tiny fixture flow | Yes |
| P01 | Verified first-domain data generator, label-free inputs, splits and physical evaluator | Yes |
| P02 | Frozen provider interfaces, exact prompts/schema, structured features and compact answer payload | Yes; live calls conditional on credentials/budget |
| P03 | Differentiable predictor, terminal training, text-only fallback model and checkpoint inference | Yes, small CPU runs |
| P04 | Fixed assessment, calibration, diagnosis interface, bounded fallback and final answers | Yes, fixtures; real judge validation remains a gate |
| P05 | Independently trained conventional baselines and fully labeled ablations | Yes for implementation/small numerical runs |
| P06 | CoConuT/CODI adapters and pinned launchers | Yes for adapters; their GPU checks/training need the workstation |
| P07 | One-domain live pilot, resource profile and reproducible result exports | GPU/live-model gates apply |
| P08 | Additional domains, approved ID/OOD experiment matrix and paper-ready evidence | GPU/compute/data gates apply |

Detailed acceptance criteria and prerequisites are in [the phase specification](docs/06_phases.md). P00–P06 code does not have to wait for the model-specific CUDA checks, but a phase with required unexecuted verification is `implemented_pending_validation`, not complete. Independent preparation may proceed while that specific check is pending; dependent scientific results may not.

## Two scientific details to keep visible

The manuscript does not fully define how physical labels become its reference latent target. The supplied judge prompt also does not perform the manuscript's retrieved-schema comparison. [Assessment/fallback](docs/04_assessment_fallback.md) defines bounded development modes and the exact claims they cannot support. Early implementation can proceed. Before claiming full paper-faithful hybrid-energy results, resolve these with the user/planning assistant; do not silently invent an additional trained component or relabel a different judge task.
