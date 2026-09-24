# Implementation progress

Updated from P00/P01 and the separately authorized dataset preparation task.
P02–P08 remain plans, not completed model code. The newer dataset/model contract
1.1.0 supersedes older physical-readout training assumptions for future work.

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
