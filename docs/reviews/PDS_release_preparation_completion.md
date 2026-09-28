# Four-domain release preparation — 24 September 2026

Branch: `dataset-prep`. **Preparation complete; licenses remain drafts pending
rights-holder identity and authority. Production is disabled.** No production
simulation, quadruped investigation, model training, push or publication occurred.

Commits: `82a5ab4e04062947e4a639ab9315b2f167db4d6e` prepares licensing, inventory
and release guards; `f70ee987abea09607260f34407f8b841753fb70d` fixes source
fingerprints across Windows/WSL and is the frozen generator revision. The
subsequent preparation commit contains the generated freeze and this report.
Earlier reviewed evidence remains at `22aacf8`, without rewriting historical runs.

## Licensing findings and the precise unresolved input

The user selected **CC BY 4.0** for the public research dataset and project-authored
scene/model assets, and **MIT** for project-authored generation code. The initial
response “Creative Comments” was clarified to mean Creative Commons, not the
name of a rights-holder. Neither an exact rights-holder name nor confirmation of
licensing authority was supplied. No grant has therefore been marked approved.

Prepared materials:

- [License scope/status](../../LICENSE.md), [exact file coverage](../../licenses/scope.json),
  and [pending decision](../../licenses/decision.json).
- [CC BY 4.0 standard text](../../licenses/CC-BY-4.0.txt), retrieved unchanged from
  Creative Commons; [MIT generation-code notice](../../licenses/MIT-generation.txt)
  with `2026 [RIGHTS_HOLDER_PENDING]`. The original MIT template is retained.
- [Attribution template](../../licenses/ATTRIBUTION.md), with title, source URL,
  license link, revision/manifest reference and modification notice. No author,
  DOI, download URL or ownership statement was invented.
- [Third-party boundaries](../../licenses/THIRD_PARTY.md), original installed
  MuJoCo/PyBullet notices, and [runtime notice hashes](../../licenses/runtime-notices.json).
  [Text source URLs/hashes](../../licenses/text-sources.json) record the exact
  standard license texts retrieved for preparation.

Only two user facts remain necessary to finalize the prepared grants: **the exact
rights-holder name to print**, and **confirmation of authority to license the
covered dataset/assets under CC BY 4.0 and covered code under MIT, including any
applicable co-owner or institutional rights**. No other license choice is being
reopened. Until supplied, the rights-holder placeholder is explicit and all domain
asset-license statuses remain `not_granted`.

## Scene/model inventory

[Machine-readable inventory](artifacts/PDS_release_preparation/asset-inventory.json)
lists every existing model instance in the eight reviewed smoke/calibration runs:
**480 asset files**, including assets from quarantined draws, with exact paths,
sizes and SHA-256 hashes. Their contents match current authored model rendering
byte-for-byte. Only corrected tether runs were used. Parameterized production
instances have not been simulated; the dry partition plan pins their model-pair
hash digests alongside the frozen rendering code.

| Domain / authored components | Source | Existing license / intended distribution |
|---|---|---|
| Arm: two box links, hinge joints, finite spherical payload, tip site, inertias and controls | `scenes.py:arm_model`, `engines.py` | No project grant found; proposed CC BY 4.0; generated MJCF and embedded model description intended for public reuse |
| Driving: box chassis, four cylindrical wheels, axles, infinite ground plane and braking/contact settings | `bullet.py:car_asset`, `link`, `joint`, `BulletAdapter._run` | No project grant found; proposed CC BY 4.0; generated URDF plus procedural-world/control description intended for public reuse |
| Objects: two box bodies, static box table, pushing and pre-stacked placements, inertia and force schedule | `bullet.py:BulletAdapter._run`, `scenes.py:box_inertia` | No project grant found; proposed CC BY 4.0; generated JSON and embedded scene description intended for public reuse |
| Tether: support, slider/pivot, pendulum joint, spherical payload, load site, taut-length approximation and support motion | `scenes.py:tether_model`, `support_motion`, `engines.py` | No project grant found; proposed CC BY 4.0; generated MJCF and embedded description intended for public reuse |

All four families are project-authored procedural constructions in the repository,
introduced with the dataset implementation (`4b997ef`). That identifies provenance,
not legal ownership. Ownership remains unconfirmed for each family. There are
**no imported third-party meshes, textures or robot scene models in these paths**.
The floor and table are authored primitives, not borrowed URDFs.

MuJoCo 3.14.0 and PyBullet 3.2.7 are runtime dependencies, not project-authored
assets. Their installed notices identify Apache-2.0 and zlib terms respectively;
MuJoCo's bundled third-party notices and PyBullet's stated exceptions are preserved.
No dependency wheels, engine binaries, or bundled data are included in the
proposed dataset/code bundle. Other runtime packages have version/notice hashes
recorded separately. These notices do not license our authored assets.

Adopted extraction prompts/schema originals and external references remain outside
the proposed license grant. They are not needed to run template-first simulation
generation; the optional extracted-JSON adapter retains its separate original
artifact dependency. Do not distribute the entire repository or complete local
source snapshots under the new license labels. The proposed code bundle uses
the explicit MIT file allowlist; dataset files/configs/model outputs use the
explicit CC BY scope. Historical quadruped assets are excluded.

## Internal generation versus public redistribution

Inspection identified **no concrete scene-asset restriction preventing internal
generation**. This is a bounded inventory finding, not proof of ownership or an
inferred grant. The blocking condition is the project's existing rule that
redistribution permission must be resolved before `generate` may run. That rule
has not been relaxed or bypassed. The user confirmed the eventual public outcome;
both effective licensing and production activation still remain pending.

## Frozen settings and compatibility

Prepared [configuration](../../configs/dataset_release_four_domain.json) has
`status=frozen` and **`final_generation_enabled=false`**. Its four prepared domain
manifests live under `configs/frozen_dataset_domains/`, separately from historical
development manifests, and say `validation_frozen_license_pending`.

[Freeze manifest](../../configs/dataset_release_freeze.json) pins the committed
generation dependency source, schema/contract, numeric and extracted registries,
sampling rules, legal drafts/notices, evidence hashes, runtime versions, budget,
and [24 partition plans](artifacts/PDS_release_preparation/partition-plan.json).
Source hashes use UTF-8/LF text to avoid Windows/WSL line-ending false differences;
model assets, notices and frozen artifacts retain exact-byte hashes. Verification
passed in WSL with installed runtime checks and in Windows without runtime checks.
Frozen source coverage is the generation dependency allowlist, not unrelated
legacy/model-training code. Full local provenance is preserved separately.

The nominal freeze values are unchanged: MuJoCo arm and PyBullet driving use
0.1 ms with 0.05 ms refinement; objects and corrected tether use 2 ms with 1 ms
refinement. Numerical gates remain half the requested target accuracy:
0.005 for other continuous channels, 0.01 for velocities, exact discrete agreement,
and 0.01 s event agreement. Domain physics checks, quaternion comparison, parameter
ranges, OOD definitions, master seed `20260924`, grouping and question rules remain
unchanged. No architecture, loss, schema or adopted prompt was changed.

The existing `model` fields in the prepared domain manifests are representative
reviewed pilot provenance, not fabricated production records. Production source
revision and settings are explicitly separate. Every future draw will record its
actual config, parameters and generated model hash. The dry plan hashes deterministic
scenario objects and coarse/refined model descriptions; it creates no trajectories,
labels or admitted records.

**6,800 attempted base scenarios** = four domains × (1,000 train + 200 validation
+ 200 ID test + 100 parameter OOD + 100 combination OOD + 100 timed-event OOD).
No redistribution of the excluded quadruped quota. Rejected draws remain failures;
no replacement sampling occurs. Release manifests now explicitly sum attempted,
accepted, rejected and question counts and check the 6,800 attempt total.
Production generated/admitted counts are both **zero**. Historical development
counts remain 461 admitted / 480 attempted, with their prior rejection analysis.

## Runtime, storage and command

Measured calibration runs contained 100 attempted scenarios per domain, including
their numerical refinement and retained failures. Linear ×17 extrapolation:

| Domain | Measured calibration seconds | Estimated 1,700-attempt minutes | Estimated GiB |
|---|---:|---:|---:|
| Arm | 111.53 | 31.60 | 0.57 |
| Driving | 268.96 | 76.20 | 0.75 |
| Objects | 121.35 | 34.38 | 1.05 |
| Corrected tether | 32.14 | 9.10 | 0.54 |
| Total | 533.98 | **151.29 (2.52 hours)** | **2.92 (3.14 GB)** |

[Estimate inputs and hashes](artifacts/PDS_release_preparation/cost-estimate.json)
preserve measurements. These are estimates, not production performance results:
release shift mix differs, native pilots used a different host environment, and
validation, filesystem scanning and serialization can scale nonlinearly. Pilot
peak RSS was roughly 68–144 MiB; this does not bound production aggregation memory.
No admitted-count estimate is treated as a quota or guarantee.

Prepared execution is serial CPU in the existing WSL environment, capped at two
hours per partition and six hours per invocation, with resumable receipts. Keep
the 100 GiB release disk cap and 200 GiB minimum free disk. The aggregate disk cap
is now checked over the release root, not merely one partition. A budget stop
preserves completed draws; it does not create replacement samples.

Exact eventual command, from the repository root in WSL Ubuntu-24.04:

```bash
PYTHONPATH=src .dataset-bullet-venv/bin/python -m phi_jepa.simulation.cli generate --config configs/dataset_release_four_domain.json --resume
```

**It currently refuses to run.** Once the rights-holder and authority are supplied,
finalize the copyright/attribution notices and decision, update the four manifest
license statuses, refresh the freeze to bind those finalized files, verify and
commit it, and only enable generation when authorized. Flipping the enable flag
alone cannot bypass the frozen legal artifacts and license-evidence checks.

## Verification and remaining blocker

- Inventory preparation matched all 480 existing model files to current renderers;
  no engine initialization or stepping was used by inventory/freeze preparation.
- Full offline WSL suite: **74 tests passed in 17.836 seconds**. These include
  existing bounded native/Bullet unit checks, freeze drift, explicit-grant rejection,
  and preservation of failed draws across resume without replacement/retry.
- Actual frozen-config targeted release tests: **9 passed**.
- Actual freeze verification passed on WSL (including package versions) and
  Windows (source/artifacts only). Initial WSL preparation correctly stopped on
  line-ending provenance before preparation; it passed after the documented fix.
- Disabled generate CLI returned expected exit 1 before dispatch. No production
  output directory exists. `git diff --check` and Python compilation passed.

**Blocker:** Dataset/public release finalization on `dataset-prep`; exact
rights-holder identity and authority confirmation are missing. Relevant files:
`licenses/decision.json`, `MIT-generation.txt`, `ATTRIBUTION.md`, four prepared
domain manifests and the disabled release config. Expected evidence to close:
the rights-holder's exact name and an explicit authorized grant covering the
scoped CC BY 4.0 dataset/assets and MIT generation code, including applicable
co-owner/institutional rights. Preserve pending status until then. No further
scientific or licensing-choice question is required for these prepared files.
