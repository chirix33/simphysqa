# Implementation progress

Four-domain production generation and local export completed on 24 September 2026.
Generation revision `a8920b23dfbdb089b95cee5c00a47758b942d4ce`: exactly 6,800
attempted base scenarios, 6,340 admitted, 460 quarantined, 11,105 admitted questions.
All 24 partitions and combined-data checks passed; frozen thresholds and rejection
policy were preserved. Native-storage resume reused 711 completed attempts.
See [completion report](reviews/PDS_generation_completion.md) for counts, measured
runtime/storage, hashes and commands. No training, push or publication occurred.
Earlier preparation/disabled-state entries below are historical.

License finalization, 24 September 2026: user confirmed rights-holder Kaushik Roy
and authority for the scoped CC BY 4.0 dataset/assets and MIT generation code.
Notices and frozen legal metadata finalized; production remains disabled.
See [authorization decision](decisions/License_authorization.md). Earlier pending
licensing entries below describe the historical preparation state.

Release preparation, 24 September 2026: CC BY 4.0 dataset/asset and MIT code
licenses prepared with explicit file scope; rights-holder name and authority
remain pending. Frozen source `f70ee987abea09607260f34407f8b841753fb70d`; 6,800
attempted draws, no resampling, production disabled. 74 offline tests passed.
See [preparation report](reviews/PDS_release_preparation_completion.md).

Four-domain scope amendment, 24 September 2026: quadruped/MJX deferred; current
configuration failed unchanged qualification thresholds. Investigation preserved
in commit `3fcbf8f32d6d0732c11016b67ad5b0f460f68f58`. Release selection now includes
only arm, driving, objects and corrected tether. Planned total 6,800; production
generated/admitted 0. Production remains disabled. See
[readiness review](reviews/PDS_four_domain_completion.md). Earlier entries below
are historical and their five-domain release blocker is superseded.

Updated from P00/P01 and the separately authorized dataset preparation task.
P02–P08 remain plans, not completed model code. The newer dataset/model contract
1.1.0 supersedes older physical-readout training assumptions for future work.

Quadruped follow-up, 24 September 2026, `dataset-prep`, starting commit
`4b997efd1dcbc8199c5981e44c71bd39fa8b7cb9`: fixed the controller-frequency
confound in timestep refinement. A 24-run fixed-clock/one-factor MJX study
initially qualified the 0.2 rad hip-amplitude gait at 0.5/0.25 ms under unchanged
nominal endpoint/event thresholds. A later repeat audit failed those original
tolerances, revoking that provisional qualification. Two serial 0.125 ms runs
also fail: terminal base velocity differs by 0.016544569 m/s versus 0.01 m/s.
Intermediate trajectory discrepancies remain explicit.
Real force-duration/torque-hold checks and all 26 trace audits passed; Linux
regression: 65 tests passed. Varied smoke completed with 5/20 admitted and 15/20
quarantined (nine development records); these do not qualify a release. Calibration
remains gated, with zero calibration scenarios simulated. Status remains
`implemented_pending_validation`. See the
[follow-up report](reviews/PDS_quadruped_refinement_completion.md) and
[decisions](decisions/Quadruped_fixed_clock.md). Earlier quadruped comparisons
changed controller frequency and are preserved as historical raw evidence, not
isolated integration-convergence measurements.

Dataset preparation, 24 September 2026, branch `dataset-prep`, starting commit
`983feaec76acfd923cc7b7d18844ddd92696daff`: **implemented_pending_validation**.
Five simulator adapters and the strict numeric/text/extraction contracts exist;
four domains have admitted smoke/calibration artifacts. The MJX quadruped executes
on GPU but fails controller/refinement qualification; its 100-case calibration
and final generation remain blocked. Final Linux suite: 55 tests passed. No
model training or production generation occurred. See the
[dataset report](reviews/PDS_completion.md), [decisions](decisions/Dataset_preparation.md)
and [measured summary](reviews/artifacts/PDS/summary.json). Earlier tether pilots
are superseded by the corrected-onset runs identified in the report. Changes
remain uncommitted for review; the pre-existing user assets are preserved.

| Phase | Status | Evidence/report |
| --- | --- | --- |
| P00 | complete | [Completion report](reviews/P00_completion.md), [repository audit](reviews/P00_repo_audit.md); eight CPU tests passed; offline editable install and CLI verified |
| P01 | complete | [Completion report](reviews/P01_completion.md); 28 CPU tests passed, 32-family dataset and independent oracle/evaluator verification |
| P02 | not_started | — |
| P03 | not_started | — |
| P04 | not_started | — |
| P05 | not_started | — |
| P06 | not_started | — |
| P07 | not_started | — |
| P08 | not_started | — |

Environment evidence: the active P00 prompt records the user-reported WSL check PASS: PyTorch 2.7.1+cu128, CUDA runtime 12.8, RTX 5090 capability (12, 0), BF16 support and FP32/BF16 forward/backward. The coding agent did not run that GPU check; model-specific gates remain pending. P00 was verified locally on Windows CPU with Python 3.12.14 and setuptools 84.0.0. Scientific decision items Q1–Q4 remain open in [defaults and decisions](docs/08_defaults_decisions.md).

P00 branch: `codex/p00-bootstrap`; base/current HEAD `8e1cd56feb8f9fb0ec8aee92b0d0365b32722066`; changes uncommitted for review. No unresolved P00 blockers. Fixture manifests/results and exact commands are linked in the completion report. [Engineering decisions](decisions/P00_bootstrap.md) record installation, environment, packaging and artifact choices. Next step: planner/user review of P00; P01 requires separate authorization.

For every change: date, phase/substep, exact commit, actual checks, artifacts, remaining blockers and next step. Do not replace this with a list of aspirational completed checkboxes.

P01: authorized by the user after planner acceptance of P00. Started at `dbff9573fa3d13adf4edafa42976afc2e5208e90` on `codex/p00-bootstrap` with only the expanded P01 prompt dirty; preserved it unchanged. P01 additions are uncommitted. See [P01 decisions](decisions/P01_data.md) and the completion report for exact checks, artifacts and limitations. No unresolved P01 blockers. Next: review P01; P02 requires separate authorization.
