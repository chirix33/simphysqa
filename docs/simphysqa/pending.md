# Prioritized annotation work and unresolved choices

All items below are pending; no annotation/human/benchmark result is asserted.

1. Pin primary annotation model identity/version and prompt; implement the budgeted
provider/cache/attempt ledger, semantic language validation and generation adapter.
Create meaningful observed-trajectory and timestamp descriptions. Current generic
context remains incomplete.
2. Construct direct QA from observed states. Enrich predictive QA and audit language
for future-outcome leakage. Extend evidence bindings from readout IDs to relevant
claims, controls and event definitions. Freeze a meaningful annotation version
only after development/revision work.
3. Construct matched counterfactual intervention/re-simulation records with paired
initial conditions, seeds, model/control manifests and numerical verification.
Add explanation questions with claim-level support and distinct causal/descriptive
claims. Construct genuine clarification gaps and justified requests.
4. Finalize release population/inclusion/allocation and rubric using the shared
20-item calibration. Keep all inspected bootstrap physical groups out of fresh
formal sampling. Do not freeze/export the 140 formal identities now.
5. Obtain the original agreement power calculation and reconcile estimator/variance
assumptions. Lock incomplete-rating policy, bootstrap seed/replicates and pooled
estimand/weighting; no subgroup power claim.
6. Select and document the separate alternative annotation-source model/subset,
controlled instructions, source blinding, reviewers and paired analysis.
7. Pin and locally qualify Qwen3-32B-AWQ, Gemma-3-27B-IT QAT, and a quantized
DeepSeek-R1-Distill-Qwen-32B artifact. Requalify inherited Qwen/Llama interfaces on
SimPhysQA public annotations/tasks and hardware. Implement qualified tool-free
runners and new-family metrics/uncertainty, then request bounded experiment budgets.

## Machine-specific pending decisions

The dedicated Windows CPU environment is validated on Python 3.12.14. Exact
dependency distributions were reused locally with hashes, not downloaded.
No new CUDA, WSL, PyBullet/MuJoCo generation or model-specific validation occurred.
Historical user-reported RTX 5090 CUDA/PyTorch qualification is not a new result.
The main checkout release is the available read-only data root; a long-term external
storage location, portable path convention and portable wheel packaging for retained
root schema/assets are pending. Editable installation is the supported bootstrap.

Historical enabled full-release configs carry old source hashes. Source pruning
changes those hashes; re-freezing/qualification is necessary before new generation.
No frozen simulator thresholds, source references or rejected cases were modified.

## Scientific blocker: original agreement power calculation

- Phase/substep and status: SPQ00 audit analysis; infrastructure complete, power reconciliation pending.
- Branch/commit/files: simphysqa-naacl, base 7dd4a64e90cfb18be743503ac8345cabf2f6e28b; configs/simphysqa/audit.json and docs/simphysqa/audit.md.
- Expected/source: preserve supplied 80% confidence/.20 two-sided alpha/.80 power/.90 prevalence/.60 vs .80 kappa settings and consistently use original calculation's estimator.
- Minimal command: rg -n 'kappa|statistical power|two.sided alpha|acceptable.rating prevalence' docs/docs docs/prompts docs/decisions -g '*.md' -g '!SPQ*'
- Observed: only historical generic seed-variability/power caveat; no original kappa formula, variance, estimator or calculation artifact. No software traceback.
- Environment: Windows, Python 3.12.14, jsonschema 4.26.0; offline CPU.
- Attempts: checked relevant data/evaluation specs, phase/power references and decision documents; retained supplied assumptions/counts in versioned config.
- Root cause: missing original calculation artifact; its estimator/dependence assumptions cannot be inferred from counts alone.
- Impact: blocks claiming achieved power or locking an estimator as consistent with the original calculation. Migration, packets, sampling preview and independent form imports are complete and may continue.
- Option A: obtain original calculation, then reconcile provisional unweighted Fleiss kappa/three-rater analysis; preserves the stated planning provenance.
- Option B: explicitly approve/document a new three-rater power analysis and any changes, preserving original assumptions separately; requires scientific choice and may alter design.
- Recommendation: A; retain settled 20/140 counts and do not invent a formula or achieved power.
- Smallest question to relay: What original source/formula/software, agreement estimator and variance/dependence assumptions produced the kappa .60 vs .80 power calculation?
- Evidence to close: original calculation and estimator specification, independently reproducible calculation, and a matching locked analysis protocol.
