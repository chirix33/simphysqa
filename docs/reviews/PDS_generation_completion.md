# Four-domain production generation completion

Status: **complete for authorized generation and local export**. Branch: `dataset-prep`.
Generation/enablement commit: `a8920b23dfbdb089b95cee5c00a47758b942d4ce`.
License-preparation commit: `3d99eeb9c7508f8549b9baa017364d31d93a1132`.
Frozen generator revision: `9df13b4d715b8a0d367ebe023c763fdc418aa9bb`.
The documentation commit containing this report is the handoff commit; its hash is reported in the task response.

## Results

The unchanged plan attempted exactly **6,800 base scenarios**, admitting **6,340** and quarantining **460**.
There are **11,105 admitted question records** and **495 quarantined question records** (11,600 total authored question records).
All attempts have receipts and complete two-run diagnostics: **13,600 rollouts**, **229,500,000 recorded simulator steps**.
No replacements, threshold relaxation, development inclusion, quadruped experiments, LLM/embedding calls, training, push, or publication occurred.

| Domain | Attempted | Admitted | Rejected | Admitted questions |
| --- | --- | --- | --- | --- |
| driving | 1700 | 1279 | 421 | 1279 |
| object_pushing_stacking | 1700 | 1700 | 0 | 3300 |
| robotic_arm | 1700 | 1661 | 39 | 3226 |
| tethered_load | 1700 | 1700 | 0 | 3300 |

Each domain retained its 1,700-attempt quota: train 1,000, validation 200, ID test 200, and 100 in each of three OOD categories.
These were attempted-draw budgets, not admission quotas. No quadruped quota was redistributed.

| Partition | Planned/attempted | Admitted | Rejected | Questions |
| --- | --- | --- | --- | --- |
| ood_parameter_extrapolation | 400 | 367 | 33 | 662 |
| ood_timed_event | 400 | 381 | 19 | 381 |
| ood_unseen_combination | 400 | 394 | 6 | 692 |
| test_id | 800 | 735 | 65 | 1332 |
| train | 4000 | 3721 | 279 | 6702 |
| validation | 800 | 742 | 58 | 1336 |

## Actual partition results

| Domain | Partition | Attempted | Admitted | Rejected | Questions |
| --- | --- | --- | --- | --- | --- |
| driving | ood_parameter_extrapolation | 100 | 72 | 28 | 72 |
| driving | ood_timed_event | 100 | 85 | 15 | 85 |
| driving | ood_unseen_combination | 100 | 96 | 4 | 96 |
| driving | test_id | 200 | 138 | 62 | 138 |
| driving | train | 1000 | 740 | 260 | 740 |
| driving | validation | 200 | 148 | 52 | 148 |
| object_pushing_stacking | ood_parameter_extrapolation | 100 | 100 | 0 | 200 |
| object_pushing_stacking | ood_timed_event | 100 | 100 | 0 | 100 |
| object_pushing_stacking | ood_unseen_combination | 100 | 100 | 0 | 200 |
| object_pushing_stacking | test_id | 200 | 200 | 0 | 400 |
| object_pushing_stacking | train | 1000 | 1000 | 0 | 2000 |
| object_pushing_stacking | validation | 200 | 200 | 0 | 400 |
| robotic_arm | ood_parameter_extrapolation | 100 | 95 | 5 | 190 |
| robotic_arm | ood_timed_event | 100 | 96 | 4 | 96 |
| robotic_arm | ood_unseen_combination | 100 | 98 | 2 | 196 |
| robotic_arm | test_id | 200 | 197 | 3 | 394 |
| robotic_arm | train | 1000 | 981 | 19 | 1962 |
| robotic_arm | validation | 200 | 194 | 6 | 388 |
| tethered_load | ood_parameter_extrapolation | 100 | 100 | 0 | 200 |
| tethered_load | ood_timed_event | 100 | 100 | 0 | 100 |
| tethered_load | ood_unseen_combination | 100 | 100 | 0 | 200 |
| tethered_load | test_id | 200 | 200 | 0 | 400 |
| tethered_load | train | 1000 | 1000 | 0 | 2000 |
| tethered_load | validation | 200 | 200 | 0 | 400 |

## Rejections and filtering

All **460 rejected draws failed `refined_timestep`**; no additional domain-physics or semantic rejection category occurred.
Among the driving rejections, 77 also had event disagreement; no other domain had event disagreement. These overlap the refinement failures and are not extra rejected draws.
The append-only per-partition rejection logs, every rejected receipt, original physical outcomes and quarantine records are retained.
The consolidated ledger links each rejected scenario to its original evidence.

| Domain | Shift | Attempted | Rejected | Rejection rate |
| --- | --- | --- | --- | --- |
| driving | parameter_extrapolation | 100 | 28 | 28.00% |
| driving | timed_event | 100 | 15 | 15.00% |
| driving | unseen_combination | 100 | 4 | 4.00% |
| driving | id | 1400 | 374 | 26.71% |
| object_pushing_stacking | parameter_extrapolation | 100 | 0 | 0.00% |
| object_pushing_stacking | timed_event | 100 | 0 | 0.00% |
| object_pushing_stacking | unseen_combination | 100 | 0 | 0.00% |
| object_pushing_stacking | id | 1400 | 0 | 0.00% |
| robotic_arm | parameter_extrapolation | 100 | 5 | 5.00% |
| robotic_arm | timed_event | 100 | 4 | 4.00% |
| robotic_arm | unseen_combination | 100 | 2 | 2.00% |
| robotic_arm | id | 1400 | 28 | 2.00% |
| tethered_load | parameter_extrapolation | 100 | 0 | 0.00% |
| tethered_load | timed_event | 100 | 0 | 0.00% |
| tethered_load | unseen_combination | 100 | 0 | 0.00% |
| tethered_load | id | 1400 | 0 | 0.00% |

Arm OOD rejection is 11/300 (3.67%) versus ID 28/1,400 (2.00%): filtering removes a larger fraction of arm OOD cases.
Driving OOD overall is 47/300 (15.67%) versus ID 374/1,400 (26.71%); its parameter OOD alone is 28%, slightly higher than ID.
Objects and corrected tether have zero rejections in every category. Pooled OOD loss is 58/1,200 (4.83%) versus ID 402/5,600 (7.18%).
These are observed filtering rates, not significance claims. Retention varies by domain and shift; released counts must not be described as balanced admission quotas.

## Verification actually executed

- Initial committed-license/freeze/runtime preflight passed, then the enable switch was committed before launch. All four release manifests and registries were committed and qualified.
- Native-storage preflight ran `release_gates(configs/dataset_release_four_domain.json)`, including historical calibration validation, exact freeze/license/runtime checks, and exact resume source identity.
- The production CLI completed with exit code 0. It validated all 24 exports and the combined dataset, including duplicate sample/physical-scenario detection and group/split isolation.
- `dataset-runs/release-execution/audit_release.py` completed across all partitions: artifact hashes, schema/named labels, exact frozen draw plans, four-domain selection, actual public/private exports, registry equality, target-text contract, equal numeric input/target blocks, global sample uniqueness, development exclusion, every receipt and rejection ledger.
- `dataset-runs/release-execution/audit_extra.py` passed: all 6,800 attempted groups globally unique, strict JSON and quarantine semantics, linked model-asset hashes/licenses, exact per-record generation revision/config/engine/seed. It verified 6,800 asset files. No unaccounted partial rollouts remain.
- `dataset-runs/release-execution/copy_export.py` copied the export; `verify_windows_export.py` independently verified **28,406 files** against the checksum inventory and reverified all **3,085** original pre-migration files. The redundant slow WSL-side verification was stopped only after this native Windows verification passed in 7.266 s.
- No unit-test suite was rerun in this generation task; prior preparation test results remain historical evidence. The checks above ran on the actual production data, not fixtures.

An initial independent-audit assertion compared JSON arrays directly with Python tuples. It was corrected to compare canonical JSON, then the full audit passed; no generator/data/registry change was made.
Native-copy Git metadata initially reported line-ending/file-mode differences. Matching checkout settings and refreshing its index yielded no staged/content changes; all 289 tracked files were independently byte-verified.

## Execution, resume, and measured cost

The original invocation stopped after 711 completed attempts, immediately after a receipt during the next disk-budget scan, before another simulation.
Its outputs remain in `dataset-runs/release-four-domain-v1-pre-native/`. The native copy verified 3,085 file hashes before resuming.
Resume reused those exact 711 receipts (500 in completed partitions, 211 training draws); no completed attempt was simulated again.
The unchanged per-draw disk scan measured 4.6066 s on the Windows mount versus 0.01593 s on native WSL storage.
Only storage location changed; the serial runtime, source bytes, configuration, seeds, thresholds, question policy and registries stayed fixed.

- First invocation: **4537.713 s**; resumed invocation: **6769.381 s**.
- Total generation-process time: **11307.093 s** (3.141 h).
- Wall time from first launch to successful generation finish, including relocation: **11382.157 s**.
- Independent audit processing: **924.675 s**, overlapping generation; extra final audit: **37.961 s**.
- Verified export copy: **671.378 s**. Peak recorded partition RSS: **5,444,661,248 bytes** (5.071 GiB).
- End-to-end wall time from first launch through installed, checksum-verified export: **12214.200 s** (3.393 h).
- Final local export: **3,184,522,867 bytes** (2.966 GiB), **28,406 files**. Preserved original and native copies are additional local storage.
- Runtime: WSL Ubuntu-24.04, Python 3.11.16, MuJoCo 3.14.0, PyBullet 3.2.7, NumPy 2.4.6, jsonschema 4.26.0, psutil 7.2.2. Measured preflight records are attached.

The original shell's exit-status capture was malformed; its preserved traceback establishes the intentional `KeyboardInterrupt` during `budget()`. The resumed Python wrapper records the successful exit code and timestamps directly.

## Outputs and reproduction

Project export: `C:\Users\aashraf\Desktop\Work\phi-jepa\phi-jepa\dataset-runs\release-four-domain-v1`.
Native working copy: `/var/tmp/phi-jepa-release-a8920b2` in WSL Ubuntu-24.04.
Execution/audit evidence: `dataset-runs/release-execution/` and `dataset-runs/release-execution/native-results/`.

Use `export-index.json` to select admitted input/reference/evaluator/target-text/registry files and their model assets.
Quarantine is excluded from that selection. `rejection-ledger.jsonl` preserves failures; `release-manifest.json` preserves the generation result;
`CHECKSUMS.sha256` covers all export files except itself. Public inputs contain no private reference/evaluator payloads.
The model-data contract remains 1.1.0; no embedding model, architecture, or loss was changed.

Exact successful generation/resume command from the preserved native working copy:

```bash
cd /var/tmp/phi-jepa-release-a8920b2
PYTHONPATH=src .dataset-bullet-venv/bin/python -u -m phi_jepa.simulation.cli generate --config configs/dataset_release_four_domain.json --resume
```

For fresh reproduction use the generation revision and frozen runtime/configuration in a separate checkout; retain the byte-exact source snapshots for exact resume identity.
Do not rerun merely to fill rejected quotas. Resuming completed data revalidates/re-exports receipts and may update operational manifest timestamps; original scientific outcomes remain preserved.

Key SHA-256 values:

- Enabled configuration (canonical): `a7ee7f42f9ce6041c33592a6757e8cab2f0ea76e5a74c3e9e37fd09027ccc01e`.
- Frozen manifest: `ceeb21d4548ff9c8ea5745a15f409310fecfeba598b43edae7d91030b7632319`.
- Export index: `4192accf85724bcabe858f692eae87648ce06d7b6e78b81d5c959659f02d63d6`.
- Checksum inventory: `a30ec578272a2c3764aee9e1f99db5d9f5806cf60d34aacbb704adcc4e2b4c13`.
- Consolidated rejection ledger: `fd6f3ef9962744c49b47e3c1f239c0e653a5d09f34502573f68e05fb98f2b3d3`.

## Licensing, scope, and remaining work

The finalized authority record names **Kaushik Roy**. Dataset/project-authored scene assets use CC BY 4.0; the scoped project-authored generation code uses MIT.
Existing third-party notices and scope exclusions are retained in the export. No unconfirmed grant was added and no third-party binaries were redistributed.
The four domains use MuJoCo/PyBullet; MJX and quadruped remain deferred. Their historical source, failed evidence, timing fixes and qualification history were not modified or admitted.

There are **no remaining blockers or incomplete work for this authorized generation/local-export task**.
Public publication and model training were not performed and require separate instructions. This handoff is ready for review; it does not claim public publication or model validation.

Changed tracked files are `configs/dataset_release_four_domain.json` in the enablement commit; `.gitattributes` to preserve evidence bytes; `docs/PROGRESS.md`; `docs/decisions/Four_domain_generation.md`; this report; and the 11 compact JSON evidence files under `docs/reviews/artifacts/PDS_generation/`.
Large records, trajectories, quarantine, logs and source snapshots remain outside Git. Unrelated work is preserved.
