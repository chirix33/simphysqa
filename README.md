# SimPhysQA SPQ02: verified matched omission QA

Eight development pairs (two per domain) passed exact factual replay and separate
factual/alternative coarse/fine admission. The new 0.3.0 counterfactual family
supports accepted association export 1.1.1, private paired evidence, development
auditing and typed scoring. Original 32 QA packets and 288 requests are preserved;
eight new packets and 72 prepared requests use unchanged observed prefixes.
Human quality and answering-model performance remain pending.

[Exact commands and outcomes](docs/reviews/SPQ02_completion.md),
[contract](docs/simphysqa/counterfactual.md),
[saved user prompt](docs/prompts/SPQ02_counterfactual_qa.md),
[configuration](configs/simphysqa/counterfactual.json).

New entry points: `python -m simphysqa.spq02_prepare`, `spq02_worker --preflight`,
`spq02_worker`, `spq02_export`, `spq02_verify`, `spq02_coverage` and
`spq02_arm_inspect` (each module accepts explicit external paths; use `--help`).
Simulator execution uses the pinned existing WSL environment; data/export checks
use the existing CPU annotation environment. Historical entry points follow.

# SimPhysQA

SimPhysQA is a dataset/evaluation contribution for NAACL Resources, Benchmarks,
and Evaluation: simulator-grounded structured/language trajectories, QA/evidence
and reproducible annotation, plus comparisons across models/domains/question types.
Phi-JEPA/SCLD/EBM/learned dynamics/CODI/Coconut training is outside active scope.

SPQ01a adds deterministic public event–state links and controller-aware schedule
claims to all 32 existing development packets, preserving .2 s cutoffs and QA
references. [Specification](docs/simphysqa/event_language.md),
[completion and exact commands](docs/reviews/SPQ01a_completion.md).
Use `python -m simphysqa.spq01a --help`; it is offline and makes zero model calls.
Real active-event overlap is absent in this development frame; boundary coverage
uses labeled synthetic software fixtures. Human quality remains pending.

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

## Bidirectional event-state public export

Use `python -m simphysqa.export_associations --source EXTERNAL_SPQ01A_EVENT_LANGUAGE_ROOT --output EXTERNAL_NEW_ASSOCIATION_ROOT`.
This offline derived export adds compact state linked_events /event linked_states
and separate between-state endpoint associations, keeping source records exact.
[Specification](docs/simphysqa/associations.md) and
[completion/examples/commands](docs/reviews/SPQ01a_associations_completion.md).

## Grounded public event descriptions
The versioned association CLI now emits export 1.1.1 with shared controller-grounded
event descriptions and separate public evidence. See
[specification](docs/simphysqa/event_descriptions.md) and
[completion/examples/commands](docs/reviews/SPQ01a_event_descriptions_completion.md).
Use a fresh external output root; prior versions remain preserved.
