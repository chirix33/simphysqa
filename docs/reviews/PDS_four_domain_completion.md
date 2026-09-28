# Four-domain release-readiness completion — 24 September 2026

Branch: `dataset-prep`. Status: **scope implementation and readiness review
complete; production disabled pending licensing, freeze and review**.

Investigation commit: `3fcbf8f32d6d0732c11016b67ad5b0f460f68f58`.
Scope implementation commit: `e56804d440ed44301c9069b2659e97b07498ab9f`.
No push, production generation, training, new quadruped experiments, threshold
relaxation or architecture/loss changes occurred.

## Preserved investigation and release boundary

The investigation commit preserves the MJX adapter, fixed physical controller
clock, event/force timing checks, synchronized diagnostics, regression tests,
failed configurations, later qualification revocation, and compact evidence.
The current quadruped configuration failed unchanged numerical thresholds; this
does not imply that MJX generally cannot support locomotion.

[Historical file inventory](artifacts/PDS_quadruped_refinement/local-history-inventory.json)
records exact paths, sizes and SHA-256 hashes for 316 local files totaling
143,867,128 bytes. Large traces remain under their original `dataset-runs/`
locations and are not added to Git. Existing compact evidence checksums were
verified before the inventory was added. Prior reports remain historical.

Release selection is exactly arm/MuJoCo, driving/PyBullet, objects/PyBullet,
and tether/MuJoCo. Defaults and the disabled release candidate omit quadruped.
Release gates reject extra domains, manifests and registries, mismatched domain
identities, engine overrides, and development partitions. Manifest and registry
files must also be committed. Development runs cannot write release splits.
The audit explicitly rejected the actual five historical quadruped smoke groups
(nine admitted development records) from all four release split types.

The common schema retains development compatibility, as do all numeric
registries and the MJX adapter. Explicit development access uses
`configs/dataset_quadruped_development.json`; retained MJX tools use that config.
The old evidence collector now dispatches the current read-only four-domain
review, so it cannot restore obsolete five-domain active manifests.

## Planned counts versus measured counts

Per-domain quotas, ID/OOD definitions, parameter ranges, seeds, split rules,
question policy and tolerances are unchanged. Quadruped's quota is removed
without redistribution. Counts below are base scenarios unless marked questions.

| Partition | Per included domain | Four-domain planned total |
|---|---:|---:|
| Train | 1,000 | 4,000 |
| Validation | 200 | 800 |
| ID test | 200 | 800 |
| Parameter OOD | 100 | 400 |
| Combination OOD | 100 | 400 |
| Timed-event OOD | 100 | 400 |
| Total | 1,700 | **6,800** |

At most 13,600 planned questions; actual question counts can be lower. Smoke
budgets total 80 draws; calibration budgets total 400. Release budgets are draw
counts, not a guarantee of admitted counts after numerical rejection.
**Production generated: 0; production admitted: 0.**

| Domain | Smoke admitted/attempted | Calibration admitted/attempted | Development questions | Qualification |
|---|---:|---:|---:|---|
| Arm | 20/20 | 98/100 | 213 | Development numerical/physics checks pass; release pending |
| Driving | 16/20 | 87/100 | 103 | Development checks pass with disclosed contact-sensitive rejects; release pending |
| Objects | 20/20 | 100/100 | 217 | Both pushing and pre-stacked subfamilies checked; release pending |
| Corrected tether | 20/20 | 100/100 | 217 | Corrected onset, tautness, length and limiting-case checks pass; release pending |
| Total | 76/80 | 385/400 | **750** | **461 admitted / 480 attempted development groups** |

These existing pilots were audited, not regenerated or relabeled as production.
The 15 new targeted solver/repeat rollouts are additional development diagnostics,
not new dataset admissions. They cover five existing scenarios, including both
object subfamilies.

## Rejection and OOD filtering review

Entries are rejected/attempted. Every rejected draw remains preserved; no
resampling was performed. All 19 rejects failed the unchanged refined-timestep
gate. Two driving rejects also have event/discrete-label disagreement (one ID
smoke case and one parameter-OOD calibration case); these are overlapping
reasons, not two additional rejections. No domain-physics or parser failures
were found among these rejected records.

| Domain / run | ID | Parameter OOD | Combination OOD | Timed-event OOD |
|---|---:|---:|---:|---:|
| Arm smoke | 0/10 | 0/4 | 0/3 | 0/3 |
| Arm calibration | 2/40 | 0/20 | 0/20 | 0/20 |
| Driving smoke | 3/10 | 1/4 | 0/3 | 0/3 |
| Driving calibration | 9/40 | 1/20 | 1/20 | 2/20 |
| Objects smoke | 0/10 | 0/4 | 0/3 | 0/3 |
| Objects calibration | 0/40 | 0/20 | 0/20 | 0/20 |
| Corrected tether smoke | 0/10 | 0/4 | 0/3 | 0/3 |
| Corrected tether calibration | 0/40 | 0/20 | 0/20 | 0/20 |

Combined smoke/calibration arm rejection is 4% ID versus 0% OOD; driving is
24% ID versus 7.14% OOD. Objects/tether are 0% in both. Thus these samples do
**not** show disproportionate OOD removal. Driving instead loses substantially
more ID cases. Filtering still changes the admitted distribution, so these
small development samples do not establish absence of selection bias or justify
silently filling quotas with easier draws. Review of the rejection policy and
reported admitted distributions remains part of release approval.

## Evidence reuse and checks actually executed

[Readiness audit](artifacts/PDS_four_domain/readiness.json) contains per-run paths,
manifest hashes, original source/config identities, per-shift reasons, and
applicable dependency comparisons. All original run manifests and identities
remain unchanged. Only these tether paths were used:
`dataset-runs/final/tethered_load/corrected-smoke` and `corrected-calibrate`.
All older tether outputs remain superseded.

Whole source/config hashes differ from the historical pilots. Reuse is based on
exact included-domain config/time/seed/sampling agreement and unchanged applicable
physics source and functions. The only relevant record-builder difference is
license lookup with the identical default when no license is supplied. The added
readable-answer check was rerun on every admitted record. The audit verifies the
unchanged numerical comparison logic after excluding its new quadruped-only
precondition. Other pipeline changes add release isolation and select the existing
domain timesteps. No stale identity was rewritten to claim a clean historical run.

Executed this task:

- `.dataset-venv/Scripts/python.exe tools/inventory_quadruped_history.py`:
  compact checksum verification and 316-file inventory; no simulation.
- `.dataset-venv/Scripts/python.exe tools/review_four_domain_release.py`:
  all eight datasets passed integrity/current record validation and all 750
  records passed the selected fixed numeric registry and equal numeric-target
  contract. Source/config comparisons and actual historical quadruped exclusion
  passed. Early audit attempts stopped at source differences; those differences
  were inspected and narrowly accounted for as described above before rerunning.
- WSL Ubuntu-24.04, `PYTHONPATH=src .dataset-bullet-venv/bin/python
  tools/check_four_domain_solvers.py`: **15 CPU rollouts, 4.16 seconds**,
  bounded to 15 calls/300 seconds. Five scenes each received a same-timestep
  serial repeat and a half-timestep/tighter-solver check. MuJoCo used 200 iterations
  and tolerance 1e-12; PyBullet used 200 solver iterations. All ten comparisons
  passed unchanged gates. Baseline timesteps were 0.1 ms for arm/driving and 2 ms
  for objects/tether. This is selected-case evidence, not a full tighter-solver pilot.
- WSL `PYTHONPATH=src .dataset-bullet-venv/bin/python -m unittest discover
  -s tests -v`: initial **70 passed**; after manifest/registry identity coverage,
  final **71 passed in 16.35 seconds**, no skips. Includes real native/Bullet
  limiting cases, public/private isolation, extraction identity/failure policy,
  numeric/text contract, resume checks, and pure quadruped regression tests.
  No MJX rollout or GPU experiment was part of this suite.
- `.dataset-venv/Scripts/python.exe -m phi_jepa.simulation.cli generate --config
  configs/dataset_release_four_domain.json`: expected exit 1, disabled-generation
  message before dispatch. No production output was created.
- `git diff --check`: passed (line-ending advisories only).
- Compact checksums: 38 investigation files and five readiness files verified.
  Final handoff pins exact-byte Git storage for both artifact directories so
  Windows line-ending conversion cannot invalidate the inventories.

[Solver evidence](artifacts/PDS_four_domain/solver-check.json) contains local
diagnostic artifact paths/hashes and actual overrides. The PyBullet override is
explicitly separate from the baseline asset description. Large diagnostic outputs
remain under `dataset-runs/four-domain-solver-check/`. Compact evidence and final
test logs are covered by [checksums](artifacts/PDS_four_domain/CHECKSUMS.json).

## Remaining blockers — release only

- **Phase/substep/status:** Four-domain production admission;
  `implemented_pending_validation` until release approval/freeze.
- **Branch/revision/paths:** `dataset-prep`, scope commit above;
  `configs/dataset_release_four_domain.json`, `configs/dataset_domains/*.json`,
  `src/phi_jepa/simulation/release.py`.
- **Expected:** four approved frozen manifests, granted asset redistribution
  license, committed frozen generation settings and reviewed numerical/filtering
  evidence before dispatch; SPECIFICATION sections 9 and 11.
- **Observed/reproducer:** the generate command above rejects the disabled
  candidate. All four domain manifests still say `asset_license_status=not_granted`
  and `development_validated_release_pending`; config is
  `release_candidate_pending_review`, `final_generation_enabled=false`.
- **Diagnosis/evidence:** native/Bullet pilots and targeted checks pass for
  admitted data. The missing license grant is not supplied by simulation tests.
  Manifest/config freeze and scientific review have not been asserted on the
  user's behalf. Review must explicitly accept or revise the disclosed numerical
  rejection policy without hiding rejected draws or loosening thresholds.
- **Impact:** no production data may be generated. Deferred quadruped is no
  longer a dependency of the four-domain release.
- **Next step/evidence to close:** user/planner reviews this report and rejection
  tables, supplies the actual asset license, and approves freezing the four
  manifests/config with their checked evidence. Keep production disabled until
  that is done and reviewed. No additional experiment is proposed by this report.
- **Downstream, not a JSON-generation blocker:** real frozen text encoder/token
  accounting and semantic answer decoder remain model-integration dependencies.
  Contract 1.1.0, its immutable numeric block and terminal objective are unchanged.

## Changed files

Investigation files are enumerated by `git show --stat 3fcbf8f`; the source,
tests, configs, tools and compact history are committed separately from this scope.
Scope changes cover `src/phi_jepa/simulation/{scope,pipeline,release}.py`,
`tests/test_release_scope.py`, active pilot configs, the new four-domain release
candidate and explicit quadruped development config, four domain manifests,
`tools/{run_dataset_pilots,collect_dataset_evidence,review_four_domain_release,
check_four_domain_solvers,study_dataset_quadruped,verify_quadruped_clock,
profile_dataset_mjx}.py`, README, SPECIFICATION, PROGRESS, the scope decision,
this report and compact review artifacts. The locally supplied, already ignored
`DATASET_CODEX_PROMPT.md` was scope-amended locally; its existing Git ignore rule
is preserved. Original extraction assets, shared schema, registries,
MODEL_DATA_CONTRACT.md, architecture, losses and unrelated legacy work are unchanged.
