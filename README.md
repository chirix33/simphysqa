# SimPhysQA

SimPhysQA is a dataset contribution and evaluation study for NAACL Resources,
Benchmarks, and Evaluation: simulator-grounded structured/language trajectories,
QA/evidence/reproducible annotation, and comparisons across models/domains/families.

The bootstrap wraps actual admitted records without changing original IDs,
references, controls, units, coordinate frames, events or provenance.
Meaningful language and new QA families remain pending; generic timestamp context
does not count as annotation. See [annotation contract](docs/simphysqa/annotation.md),
[audit design](docs/simphysqa/audit.md), and [evaluation plan](docs/simphysqa/evaluation.md).

| Active directory | Role |
| --- | --- |
| src/simphysqa | Strict loading, reversible migration, schema, annotations interface, audit and public requests |
| src/phi_jepa/simulation | Retained simulator generation/verification compatibility code; optional engine dependencies |
| configs/simphysqa | Annotation/audit/evaluation plans, external path example and CPU dependency pins |
| docs/simphysqa | Active scientific contracts and pending decisions |
| docs/prompts/SPQ00_bootstrap.md | Authorized initial milestone |
| tests/test_simphysqa.py | Real four-domain offline behavioral checks |
| dataset.schema.json, SPECIFICATION.md, VALIDATION.md, licenses | Preserved source contracts/licensing |
| docs/assets, docs/references, docs/reviews/artifacts | Preserved originals and historical evidence; not new output destinations |

Other historical configs/documents/results/notebook assets are retained for provenance,
not active entry points. Unrelated learned-model source and launchers are removed
only on this branch after tracing retained dependencies. Original work survives on
main at the recorded base. New artifacts must be outside this source worktree.
Existing large tracked historical outputs are grandfathered and untouched.

## Setup

Requires Python >=3.11. Use a separate CPU environment and install editable so
preserved root schema/assets remain available to retained simulator code:

```powershell
python -m venv C:/path/outside-source/simphysqa-venv
C:/path/outside-source/simphysqa-venv/Scripts/python.exe -m pip install -r configs/simphysqa/requirements.lock.txt
C:/path/outside-source/simphysqa-venv/Scripts/python.exe -m pip install --no-build-isolation --no-deps -e .
```

The actual bootstrap uses the existing dataset Python because Python is not on
this session's PATH. Exact executed setup/smoke commands and paths are in
[SPQ00 completion](docs/reviews/SPQ00_completion.md). No GPU/API is needed.
Simulation requires separately installed pinned optional engines; full generation
requires a new reviewed source freeze. Do not replay the legacy enabled full-release
config blindly after source pruning.

## Entry points

```powershell
python -m simphysqa --help
python -m simphysqa smoke --data-root EXTERNAL_RELEASE_ROOT --output EXTERNAL_NEW_SMOKE_DIR
python -m simphysqa validate --input EXTERNAL_RELEASE_ROOT/driving/validation
python -m simphysqa migrate --input EXTERNAL_RELEASE_ROOT/driving/validation --output EXTERNAL_NEW_MIGRATION_DIR
python -m simphysqa sample-preview --input EXTERNAL_MIGRATION_DIR/records.jsonl --output EXTERNAL_PREVIEW_DIR --exclude-group PRIOR_GROUP
python -m simphysqa audit-export --input EXTERNAL_MIGRATION_DIR/records.jsonl --output EXTERNAL_PACKET_DIR --phase development
python -m simphysqa import-ratings --packets EXTERNAL_PACKET_DIR --form EXTERNAL_RETURNED_FORM.csv --output EXTERNAL_NEW_ORIGINAL.json
python -m simphysqa baseline-requests --input EXTERNAL_MIGRATION_DIR/records.jsonl --output EXTERNAL_REQUEST_DIR
python -m simphysqa score --input EXTERNAL_MIGRATION_DIR/records.jsonl --predictions EXTERNAL_PREDICTIONS.json --condition qwen3_8b_direct --output EXTERNAL_SCORES_DIR
python -m simphysqa attach-annotation --input EXTERNAL_ONE_RECORD.json --result EXTERNAL_VERSIONED_RESULT.json --output EXTERNAL_ANNOTATION_DIR
```

Audit export accepts development/calibration only; one item per physical group.
Formal export is disabled until annotation/release/rubric readiness. Provider jobs,
new QA construction, human ratings and answering-model runs are pending.
Use --output or SIMPHYSQA_OUTPUT_ROOT; configure data/models/caches with explicit
external paths (configs/simphysqa/paths.example.json). Existing data is read-only.

```powershell
$env:SIMPHYSQA_DATA_ROOT = "EXTERNAL_RELEASE_ROOT"
python -m unittest discover -s tests -p test_simphysqa.py -v
```
