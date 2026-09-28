# Four-domain first release — 24 September 2026

Authority: the user's explicit scope amendment on `dataset-prep`. This supersedes
five-domain release requirements in earlier plans and completion reports; those
reports remain historical evidence. No architecture, objective, schema, extraction
prompt, numeric registry, range, OOD definition or validation tolerance changes.

The release includes arm/MuJoCo, driving/PyBullet, objects/PyBullet and
tether/MuJoCo. Quadruped/MJX is deferred. The current quadruped configuration
failed unchanged numerical qualification, including serial finer-step repeatability;
this does not establish that MJX generally cannot support locomotion. Do not launch
further quadruped experiments as part of this task.

Investigation commit: `3fcbf8f32d6d0732c11016b67ad5b0f460f68f58`. Its compact
[inventory](../reviews/artifacts/PDS_quadruped_refinement/local-history-inventory.json)
contains exact local paths, byte lengths and SHA-256 hashes for 316 retained files
(143,867,128 bytes), including failed runs and large traces. No trajectory files
were moved, removed or newly added to Git. The shared schema and adapter retain
quadruped development access through `configs/dataset_quadruped_development.json`.
The five admitted smoke groups/nine records remain historical development data,
not release-qualified examples. Release selection rejects that domain, its
manifests/registries, and development partitions independently.

Each included domain keeps 1,000 train, 200 validation, 200 ID test, and 100 per
parameter/combination/timed-event OOD category. Planned total: 6,800 base scenarios,
up to 13,600 questions. Quadruped's 1,700 quota is removed, not redistributed.
Smoke totals 80 planned draws; calibration totals 400. These are draw budgets:
rejections reduce admitted counts and are not silently replaced.

The disabled release candidate pins arm/driving integration at 0.1 ms and
objects/tether at 2 ms, with unchanged half-step refinement. Source/config reuse
is assessed per applicable dependency; original whole-source hashes and run
identities remain unchanged. Only `corrected-smoke` and `corrected-calibrate`
tether evidence is eligible. A read-only audit reruns current record validation
and numeric/text compatibility on all admitted records. No pilot is relabeled as
production. Asset licensing, frozen manifests/configuration and scientific
readiness review still gate production. Downstream encoder/decoder work is
separate and not implemented by this scope change.
