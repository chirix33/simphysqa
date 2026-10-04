# SimPhysQA

SimPhysQA is a dataset/evaluation contribution for NAACL Resources, Benchmarks,
and Evaluation: simulator-grounded structured/language trajectories, QA/evidence
and reproducible annotation, plus comparisons across models/domains/question types.
Phi-JEPA/SCLD/EBM/learned dynamics/CODI/Coconut training is outside active scope.

SPQ01 delivers an actual release inventory, 16 live human-unreviewed public
annotations, 16 verified direct QA plus 16 unchanged predictive QA, audit packets
and separate blank forms. No human agreement/annotation-quality or answering-model
result exists. See [SPQ01 report and exact executed commands](docs/reviews/SPQ01_completion.md),
[annotation](docs/simphysqa/annotation.md), [audit method](docs/simphysqa/audit.md),
[evaluation plan](docs/simphysqa/evaluation.md) and [remaining work](docs/simphysqa/pending.md).

| Active directory | Role |
| --- | --- |
| src/simphysqa | Loader/lineage schema; inventory/selection; provider/job; direct QA; audit/ power checks; public requests/scoring |
| src/phi_jepa/simulation | Retained simulator generation/verification compatibility; optional engines |
| configs/simphysqa | Annotation/budget settings, alternative-source draft, exclusions, audit/evaluation plans and pins |
| docs/simphysqa | Current contracts, estimator/test reconciliation and pending decisions |
| docs/prompts/SPQ01_annotations.md | Authorized bounded milestone |
| docs/references/spq01_audit | Byte-preserved supplied audit package/provenance |
| tests/test_simphysqa.py, tests/test_spq01.py | Existing-source offline checks and test-only transports |
| dataset.schema.json, SPECIFICATION.md, VALIDATION.md, licenses | Preserved source contracts/licensing |

Historical assets/work remain on main/history and retained directories. SPQ01 does
no further cleanup. New data/cache/weights/run outputs use configurable external,
versioned, content-hashed roots.

## Setup

Python >=3.11; separate CPU environment; editable installation for retained root
schema/assets. Existing SPQ00 environment can be reused. No GPU is needed here.

~~~powershell
python -m venv C:/path/outside-source/simphysqa-venv
C:/path/outside-source/simphysqa-venv/Scripts/python.exe -m pip install -r configs/simphysqa/requirements.lock.txt
C:/path/outside-source/simphysqa-venv/Scripts/python.exe -m pip install -r configs/simphysqa/audit-requirements.lock.txt
C:/path/outside-source/simphysqa-venv/Scripts/python.exe -m pip install --no-build-isolation --no-deps -e .
~~~

Actual interpreter/artifact paths and commands are in SPQ01_completion.md.
Engines are optional/separate; annotation does not regenerate simulation.
Legacy full-release freezes need requalification before new generation.

## Runnable bounded pipeline

~~~powershell
python -m simphysqa.spq01 --help
python -m simphysqa.spq01 inventory --data-root EXTERNAL_RELEASE_ROOT --output EXTERNAL_NEW_INVENTORY
python -m simphysqa.spq01 select --inventory EXTERNAL_INVENTORY --exclusions configs/simphysqa/spq01_selection_exclusions.json --seed 20261004 --output EXTERNAL_NEW_SELECTION
python -m simphysqa.spq01 audit-check --output EXTERNAL_NEW_POWER_CHECK --seed 20261004 --replicates 200000
python -m simphysqa.spq01 dry-run --records EXTERNAL_SELECTION/predictive-records.jsonl --output EXTERNAL_NEW_DRY_RUN
python -m simphysqa.spq01 annotate --records EXTERNAL_SELECTION/predictive-records.jsonl --output EXTERNAL_AUTHORIZED_JOB
python -m simphysqa.spq01 export-development --records EXTERNAL_SELECTION/predictive-records.jsonl --job EXTERNAL_JOB --output EXTERNAL_NEW_DEVELOPMENT
python -m simphysqa.spq01 verify-development --selection EXTERNAL_SELECTION --job EXTERNAL_JOB --development EXTERNAL_DEVELOPMENT --output EXTERNAL_NEW_CHECKS
python -m simphysqa.spq01 compare-prepare --records EXTERNAL_SELECTION/predictive-records.jsonl --output EXTERNAL_NEW_COMPARISON
~~~

Only annotate contacts the provider. SPQ01's authorized live run has completed;
another job needs a new authorized budget. Identical jobs resume and preserve
completed outputs; failures remain explicit without synthetic fallback.
Formal export stays disabled. No mandatory human annotation-generation gate.

Selection-prior exclusions reproduce engineering selection; fresh sampling
separately enforces all 20 inspected groups from development_exclusions.json plus
caller exclusions. Development direct/predictive pairs may share a group;
calibration/formal avoid related records.

Existing python -m simphysqa commands remain: smoke, validate, migrate,
sample-preview, audit-export, import-ratings, baseline-requests, score and
attach-annotation (use --help). Baseline requests include the public annotations
under evaluation. Answering-model experiments remain workstation-only/tool-free.
The five-model/nine-condition plan remains; artifact/runtime qualification and
new-family metrics are pending.
