# Phi-JEPA coding-agent instructions

## Installation and scope

The handoff is installed directly in `docs/`; this repository-root file is the applicable policy. Read [the package index](docs/README.md), `docs/PROGRESS.md`, the active prompt in `docs/prompts/` and relevant specifications in `docs/docs/`. Preserve applicable existing instructions and the original assets/references. Do not duplicate the handoff into another directory.

These instructions govern implementation work for this project. The current user instruction and newest explicit professor clarification take precedence over older drafts/prototype code. Report conflicts and preserve unrelated work.

## Scientific invariants

- In the primary Phi-JEPA method, freeze the question/text encoder and prompted LLMs; train schema encoder, linear hybrid projection, latent ODE, linear physical readout and semantic reconstruction head. CoConuT/CODI separately train the backbones/adapters required by their own baseline definitions.
- Physical MSE is terminal-only. Semantic regularization is separate and ablated. Do not add trajectory/derivative/EMA/EBM objectives to the primary method silently.
- Preserve the adopted extraction, judge and answer prompt/schema originals. Input facts/schema are immutable. Unknown values are not physical zeros.
- No trained EBM/DSM, Bregman, inference latent optimization/Langevin updates, prediction-driven schema repair, or hidden recovery/control claim.
- Core prediction/inference must not import benchmark oracle dynamics, evaluator truths or PIN-specific residuals. Typed metadata is permitted; authored domain physics is disclosed and isolated.
- Keep original numerical predictions separate from LLM prose/JSON and fallback outputs. A generated answer cannot silently replace numerical truth for metrics.
- Respect R1/V1 development scope and pending scientific decisions. Do not invent a ground-truth latent encoder or pretend V1 judges a different task.

## Engineering conduct

Inspect actual checkout, nested instructions and git status. Preserve user changes and legacy source/results. Implement only the authorized phase; stop with a reviewable report. Resolve routine reversible choices autonomously. Do not reset/clean the repository or replace the whole project because the package suggests different module names.

Keep provider/network operations at explicit boundaries, use typed inputs, content-hashed caches and reproducible configs. No network in offline tests. No automatic fixture fallback for a failed live scientific run. No credentials in code/logs/manifests. Never execute extracted formulas as code.

Use separate core/CoConuT/CODI environments. Pin source/model/data revisions. The RTX 5090 requires a compatible CUDA build; use the documented starting profile and verify it. WSL2 GPU visibility and the PyTorch 2.7.1+cu128 FP32/BF16 forward/backward check are user-reported passed in the active P00 prompt; model-specific validation remains pending. CPU work may proceed independently.

Keep optimizer/solver states finite and shapes explicit. Count every solve/model call/retry; preserve units, time grids and train-only scaling. Do not suppress failed cases or silently substitute thresholds/scorers.

## Verification and claims

Write targeted tests that check behavior: oracle accuracy, leakage, gradients, terminal-only loss, checkpoints, parsing, failure policy and cost accounting. Report commands actually run and their results. Do not count mock/fixture success as empirical model performance. A missing GPU/API prerequisite is `implemented_pending_validation` when code exists, not complete.

Independently train declared baselines. Label retraining ablations versus runtime interventions. PCVR checks physical predictions independently; provenance and empty check coverage are separate. No fabricated numbers, placeholders presented as measurements, or desired-outcome acceptance gate.

Live/long runs require an explicit configured budget and authorized credentials in the coding session. Do not push/merge/publish or message others unless requested. Local phase implementation and bounded CPU verification can proceed without repeated confirmation.

## Durable handoff

For each phase, update `docs/PROGRESS.md`, write `docs/reviews/PXX_completion.md`, and record consequential choices in `docs/decisions/`. Include branch/commit, changed behavior, tests/artifacts, deviations, pending gates and next step. For blockers use the package's precise blocker template, attempt bounded safe diagnosis, and continue independent authorized work. The user will relay unresolved questions to the planning assistant.
