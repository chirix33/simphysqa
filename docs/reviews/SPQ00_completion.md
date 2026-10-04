# SPQ00 SimPhysQA bootstrap — 4 October 2026

Initial implementation and bounded offline smoke are complete. Human annotations,
ratings, agreement, new QA families, local model qualification and benchmark
experiments remain pending.

Branch: simphysqa-naacl. Worktree:
C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa (managed worktree named simphysqa).
Base: 7dd4a64e90cfb18be743503ac8345cabf2f6e28b, clean main at start.
Implementation is recorded in the local milestone commit containing this report;
exact HEAD/source hashes are recorded after commit in the external
final-source-manifest.json. No push/merge/publication. Main checkout/HEAD are unchanged.

## Behavior and active map

- src/simphysqa: strict schema/loading, reversible v1 migration, public exports,
versioned supplied annotation-result import, private audit JSON/HTML packets,
three reviewer forms, original rating import, group-disjoint sampling preview,
tool-free request preparation and supplied-prediction typed scoring.
- src/phi_jepa/simulation plus artifacts.py/validation.py/init: retained simulator
generation/verification compatibility dependencies. No changes to their scientific
readouts or data thresholds.
- configs/simphysqa: external paths, pinned CPU dependencies, disabled annotation
plan, settled audit design and five-model/nine-condition evaluation config.
- docs/simphysqa, active SPQ00 prompt, root/nested AGENTS: pivot authority/contracts.
- tests/test_simphysqa.py: bounded real-export behavioral suite.
- Preserved dataset.schema.json, SPECIFICATION.md, VALIDATION.md, licenses,
docs/assets/references/reviews/artifacts, notebook and original generated data.
Legacy simulator tests are under tests/simulator and require optional engine
dependencies; they were not run or claimed newly validated here.

The focused import trace retained all simulation modules plus artifacts/validation.
276 unrelated source/test/launcher files were removed only on this branch; inventory
and original hashes are in docs/decisions/SPQ00_dependency_inventory.json. Historical
data/results/assets/configs/docs remain. Historic instructions are superseded rather
than past findings rewritten. New artifacts use configurable external roots; existing
large tracked historical outputs are explicitly preserved, with no moves/deletions.

## Exact executed setup and checks

Working directory for commands below:
C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa.
Artifact root used:
C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c.

Python is absent from this session PATH. The initial environment setup command was
run from the original checkout, using its existing dataset Python:

```powershell
& 'C:/Users/aashraf/Desktop/Work/phi-jepa/phi-jepa/.dataset-venv/Scripts/python.exe' 'C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/setup_offline_env.py'
```

That inspectable stdlib-only script created a dedicated external venv and copied
seven exact pinned locally installed CPU distributions, with every source file hash
in offline-environment-manifest.json. No network. Standard portable setup is also
documented in root README (venv plus locked pip dependencies and editable install).

```powershell
Set-Location 'C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa'
$spqPython = 'C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/simphysqa-venv/Scripts/python.exe'
$spqData = 'C:/Users/aashraf/Desktop/Work/phi-jepa/phi-jepa/dataset-runs/release-four-domain-v1'
$spqSmoke = 'C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/simphysqa-bootstrap-01'
& $spqPython -m pip install --no-index --no-build-isolation --no-deps -e .
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:SIMPHYSQA_DATA_ROOT = $spqData
& $spqPython -m simphysqa --help
& $spqPython -m unittest discover -s tests -p test_simphysqa.py -v
& $spqPython -m simphysqa smoke --data-root $spqData --output $spqSmoke
& $spqPython -m simphysqa validate --input (Join-Path $spqSmoke 'records.jsonl')
& $spqPython -m simphysqa score --help
& 'C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/simphysqa-venv/Scripts/simphysqa-simulator.exe' --help
& $spqPython -m pip check
git diff --check
```

Exclusive output creation prevents overwrite. To repeat smoke, choose a NEW external
directory, such as simphysqa-bootstrap-02. The existing smoke output is immutable.

Results: editable install successful; help commands successful; pip check reports
no broken requirements; diff whitespace check clean. Initial 12 behavioral tests
passed; after adding typed scoring, final suite **15 passed in 4.739 seconds**.
Final test log: behavioral-tests.log. Four-record schema reload passed.
Synthetic annotation/rating/prediction values exist ONLY in temporary software tests,
are explicitly labeled test-only and are not human/model empirical results.

## Smoke evidence and inspectable packet

Source: existing admitted release validation shards, first real record per domain.
No dataset regeneration, simulator solve, provider/model call, download or benchmark.

| Domain | Preserved sample ID | Preserved trajectory ID |
| --- | --- | --- |
| robotic_arm | 4482c5ca2997831294037852ecf01d5f | 01b027129031d73959d13f7d9c32c3dc |
| driving | bcaf3e8d888747fcb87f314022fdd782 | 011b345ec243f7f04d96eeaa736567ed |
| object_pushing_stacking | a990aa5c487cbf36c02f675291b67c31 | 01059e1a1226e0b1a70e998504fcafeb |
| tethered_load | a0d91b472b22f16175ef472eda15332c | 03008ccae19defb9e935b8b614025d14 |

For all four: original schema/semantic/admission checks pass; source input, every
reference value, provenance and ID survive exact roundtrip; new schema validates;
readout evidence binds to each target time. Public exports exclude references,
metadata, source paths and generator identity. Requests include actual annotations
under evaluation and tools=[] for all nine configured conditions.

External output is at the spqSmoke path above:
- smoke-evidence.json and manifest.json: domain IDs/source/reference hashes/checks.
- records.jsonl and public.json: migrated private/public records.
- audit-development/packets/: four real private-evidence JSON/HTML packets.
- audit-development/forms/R1.csv, R2.csv, R3.csv: separate blank forms.
- R1-blank-import.json, R2-blank-import.json, R3-blank-import.json: each 0 collected,
4 blank; no ratings were invented.
- baseline-requests/: nine public request files, preparation only.

Inspectable robotic-arm packet:
[HTML packet](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/simphysqa-bootstrap-01/audit-development/packets/SPQ-74a6863c547dc932.html)
and [JSON packet](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/simphysqa-bootstrap-01/audit-development/packets/SPQ-74a6863c547dc932.json).
It displays the actual question/reference, pending language status, fixed draft
rubric, structured inputs and private verification evidence. Generator identity
is kept in organizer-private/identity-key.json.

Sampling preview on this development frame is deterministic and reports 4 groups,
a 156-record shortfall against the 20+140 design, and no formal identities exported.
These four inspected groups are DEVELOPMENT examples, not selected calibration
or formal cases, and must be excluded from future fresh formal sampling.

## Limits, pending decisions and next step

Meaningful trajectory/timestamp language, direct/new QA families and claim/intervention/
gap bindings are pending. Annotation model/source adapter, live budgets and controlled
alternative-source comparison model/subset are pending. No mandatory human generation
approval gate was introduced. Formal export remains disabled during this milestone.

Settled audit counts/settings are preserved. Original kappa power formula/estimator
was not supplied/found; provisional Fleiss kappa must be reconciled before analysis
freeze. No achieved power, 90% pass threshold, human agreement or subgroup-power
claim is made. Missing-rating policy and bootstrap parameters remain pending.

The other three local-model artifacts/revisions/quantized runtimes are pending.
Historical Qwen/Llama settings are retained, but SimPhysQA task requalification is
pending. Supplied-prediction scoring exists for current typed readout tasks;
new-family scorers and uncertainty computation are pending and labeled unavailable.

Dedicated CPU packaging is validated; optional simulators/CUDA/WSL/model-specific
execution is not newly tested. Retained root assets currently require editable
install. Historical full-generation source freeze must be updated before new runs.
No long-term data storage migration was performed.

See docs/simphysqa/pending.md for prioritized work and the precise scientific blocker.
The next research slice is budgeted public language/QA development plus calibration
rubric preparation, after selecting annotation identity/settings and a release frame.
No full annotation, definitive formal sampling or answering-model run is authorized
by this bootstrap completion.
