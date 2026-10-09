# SimPhysQA foundation â€” contract /1.0.0

The accepted five-family foundation is integrated in main. Current repository
workflow/authorization is [AGENTS.md](../../AGENTS.md); dated merge-preparation
restrictions are historical. [SPQ05 protocol](formal_protocol.md) and
[verified audit delivery](../reviews/SPQ05_completion.md) supersede earlier
20/140 calibration planning within that internal audit. Three reviewers receive
the same 140 items with no calibration set; judgments remain uncollected.
SPQ06 has not been sent or started. No experiment is authorized by this document.
Learned-method contracts do not govern this dataset paper.

## Data, privacy and family boundaries

Source schema `dataset.schema.json` 1.0.0 and original admitted physical records
remain immutable. Preserve IDs, groups/splits, typed answers, tolerances, units,
frames, controls, event definitions, raw metadata and observation cutoffs.
Development views end at 0.2 s; no cutoffs were expanded for event coverage.
Schema development means iterative creation, enrichment and human revision.
Human review is research, not a mandatory generation gate.

| Family | Accepted development count | Public task | Reference/evaluation boundary |
|---|---:|---|---|
| Direct | 16 | Observed readout | Deterministic observed evidence, typed scorer; no future solve required |
| Predictive | 16 | Original scenario/prefix and declared controls | Original private future reference; typed scorer |
| Counterfactual | 8 | Explicit scheduled-intervention omission, same prefix | Verified matched alternative; typed scorer, exact replay distinct from admission |
| Explanation | 8 | Same prefix plus selected `supplied_comparison` readouts | Explicit task-specific outcome disclosure; fact-component checks do not grade explanatory prose |
| Clarification | 8 | Initially absent query selector; reply resolves it | Two private disjoint witnesses, partial contract, focused question then typed resolved answer |

These 56 items are engineering development in 16 train groups, not an unbiased
quality sample, release population or OOD evidence. Each domain has 14 items:
4 direct, 4 predictive and 2 of each later family. The actual inventoried source
release has 11,105 predictive QA / 6,340 groups; meaningful release-wide language
enrichment remains pending. Partition labels in the legacy release do not establish
new five-family OOD performance.

Clarification is presently **explicit query-gap** development: five missing
execution conditions, one missing block/entity and two missing readout times.
The original base scenario remains visible; its schedule does not select the
intended query condition. It does not demonstrate missing mass/friction/controller
parameters or general dialogue competence. Completion witnesses agree with the
entire initial surface, including descriptions, associations, IDs, metadata and
response contracts. Booleans differ; numerical acceptance balls are strictly
disjoint under the actual scorer (separation > sum of radii). Equal or overlapping
omission contrasts remain rejected candidates. Recorded replies supply the absent
query information, never the answer. Reference questions are authored, not model
responses. Human wording/relevance and explanation judgments remain uncollected.

Gold explanations, solution traces, rollouts, receipts, paired witness answers and
organizer identities are private. Explanation QA intentionally supplies only its
selected comparison in a separate field; this never changes predictive/CF inputs
or observed states. All answering requests use `tools=[]`. Annotation generation
and private verification have separate tool access; no answering benchmark ran.

## Authoritative artifact registry and versions

[All 56 items, paths and exclusions](development-index.md) and its
[machine-readable index](development-index.json) are the authoritative snapshot.
Its producer is `python -m simphysqa.foundation`; relative aliases are configured
in `configs/simphysqa/development_artifacts.json`. Pass an external artifact root;
source data independently uses `SIMPHYSQA_DATA_ROOT`. Moving artifacts is unnecessary.
The registry is organizer material, not an answering-model input.

| Layer | Accepted version | Contract |
|---|---|---|
| Physical source | dataset 1.0.0 | Original root schema/assets and simulator admission |
| Wrapper | predictive 0.1.0 / direct 0.2.0 / CF 0.3.0 / explanation 0.4.0 | `src/simphysqa/record.schema.json`; lossless source restoration |
| Clarification envelope / partial input | 1.0.0 /1.0.0 | [Clarification contract](clarification_qa.md), dedicated clarification schema |
| Public language / event matching | 1.0.0 / event language 2.0.0 | [Annotation](annotation.md), [event language](event_language.md) |
| Bidirectional association / shared event descriptions | 1.1.1 | [Associations](associations.md), [event descriptions](event_descriptions.md) |
| Answer annotations / renderer / export | 1.0.3 | [Answer contract](answer_annotations.md), 40 items plus eight multi-target alternative records |
| Counterfactual export | 1.0.0 | [Matched omission contract](counterfactual.md); eight saved pairs |
| Explanation procedure / export | 1.0.0 | [Explanation contract](explanation_qa.md) |
| Clarification procedure / export | 1.0.0 | [Clarification contract](clarification_qa.md) |
| Prompt archive | 1.0.7 | [Archive entry](prompt_archive/README.md), [catalogue](prompt_archive/catalogue.md), [per-file mappings](prompt_archive/file-generation-index.json) |

Versions deliberately differ across layers. Dated stage contracts saying a later
family was pending describe that stage, not current integration. The original
`private.reference` may retain historical placeholder prose: accepted overlay and
packet rendering supply enriched gold without rewriting original artifacts.
Scientific producer/schema hashes remain pinned. This review does not cosmetically
revise association 1.1.1 or regenerate cached annotations.

The sealed archive covers 1,740 files, 1,352 mapping definitions, 34 deterministic
procedures and 16 executed annotation requests. All 16 complete historical payloads
are recovered; none is reconstructed or unavailable. Preliminary association1.1.0
and event-description1.0.0 implementation sources are explicitly unrecoverable,
not missing executed prompts. [Worked request/output mappings and deterministic
example](prompt_archive/provenance-example.md) distinguish executed requests,
reused outputs, deterministic procedures and unexecuted answering preparation.
Paper-facing archive excludes gold/witness values and credentials; full evidence
stays external. The byte-sealed archive is preserved, rather than relabeled by this
documentation-only integration step. No new annotation prompt was executed.

## Active directory map

- `src/simphysqa/`: loading/lossless migration, grounded annotations, matching,
  five-family generation from saved evidence, privacy projections, packet/rating
  interfaces, scoring adapters, prompt lineage and foundation registry.
- `src/phi_jepa/simulation/` plus artifacts/validation: retained simulator
  compatibility namespace; numerical engines, source schema admission and assets.
- `configs/simphysqa/`: versioned generator/evaluation/rubric/exclusion settings.
- `tests/`: CPU saved-data integration and synthetic software boundary probes;
  `tests/simulator/` is separately qualified optional-runtime coverage.
- `docs/simphysqa/`, `docs/prompts/SPQ*`, `docs/reviews/SPQ*`: scientific contracts,
  authoring specifications and completed-stage evidence. Original adopted assets and source-generation evidence remain;
  obsolete method docs/results are recoverable through [history](../history.md).
- External artifact roots: source data, runs, weights, caches, annotations and
  packets. No generated datasets or large weights are tracked/moved by this review.

## Reproducible setup

Supported setup is **editable installation in the source checkout**, Python >=3.11;
this machine verifies Python3.12.14. Root source schema/assets/configs are used by
the retained pipeline. A standalone wheel installed away from the checkout has
not been qualified. Schema package-data is included, but that alone does not make
all root assets portable.

Normal network-enabled installation (not exercised in this offline review):

```powershell
python -m venv C:/external/simphysqa-cpu
& C:/external/simphysqa-cpu/Scripts/python.exe -m pip install -e .
& C:/external/simphysqa-cpu/Scripts/python.exe -m pip check
```

Direct core requirement is jsonschema4.26.0; build requirement setuptools84.0.0.
The exact tested transitive CPU pins are `configs/simphysqa/requirements-cpu.lock`.
For an offline reconstruction using an already provisioned interpreter with those
pins, the helper verifies versions, copies only installed distribution files into
a fresh isolated venv, records hashes, then performs real editable installation:

```powershell
& $ProvisionedPython scripts/bootstrap_cpu_offline.py --output $FreshEnv
& "$FreshEnv/Scripts/python.exe" -m pip install --no-index --no-build-isolation --no-deps -e .
& "$FreshEnv/Scripts/python.exe" -m pip check
& "$FreshEnv/Scripts/python.exe" -m simphysqa --help
& "$FreshEnv/Scripts/python.exe" -m simphysqa.foundation --artifacts $Artifacts --output "$Artifacts/merge-review/foundation-1.0.0" --validate-records
./scripts/simphysqa_spq04.ps1 -Mode check -Python "$FreshEnv/Scripts/python.exe" -Artifacts $Artifacts -SourceData $SourceData
```

The offline copy verifies reconstruction from exact local distributions, not a
new public-package-index resolution. Save its hash manifest and pip logs. Existing
exports are read-only; the index command resumes byte-identically and fails on
changed output. Tests require the original external saved artifacts; missing
artifact environment variables produce explicit skips, never synthetic scientific
fallbacks. The helper refuses an existing target environment.

Separate optional environments are necessary: simulator extra pins numpy2.4.6,
mujoco3.14.0, psutil7.2.2 and Bullet extra pybullet3.2.7; audit extra pins numpy2.5.3
and scipy1.18.1. Their conflicting numpy pins must not be combined. Simulator
execution also needs source assets and pinned environment/config/solver/seed.
Audit numerical planning runs use the supplied preserved package separately.
GPU answering artifacts/runtimes are not dependencies of CPU export/tests; all
five models/nine conditions still require SimPhysQA-local task qualification.

## Historical audit planning, evidence and remaining research

The 20/140 planning paragraphs below describe foundation-era proposals. Current
SPQ05 uses its separate no-calibration protocol and has delivered a verified
140-item package. This is not a comprehensive answer/explanation audit. See
[pending research](pending.md) for current unresolved work.

[Audit method](audit.md) retains three reviewers, 20 shared calibration and 140
fresh shared formal records (160/reviewer; 60/420 ratings). Alpha.20, target power.80,
expected acceptable prevalence.90 and kappa.60 versus.80 are planning assumptions,
not observed acceptance or a threshold. Its fixed-prevalence conditional test and
finite-sample receipts are distinct from provisional empirical Fleiss kappa.
The trajectory-balanced group-then-question sampler does not yield uniform
release-wide QA-record estimates. All 20 inspected/development groups stay
excluded; no definitive formal sample is exported. Freeze annotation version,
release population, rubric, inclusion/missingness rules and analysis before sampling.
The allocation does not power every domain-by-family subgroup.

Prior saved SPQ02 receipts qualify exact replay on eight selected groups and
separate factual/alternative admission across 32 executions. They do not establish
exact replay on all 16 groups or human explanation quality. All current prefixes
have future-only scheduled events; boundary/overlap tests are labeled software
fixtures. New event-observed views need separate task identities/cutoffs and study
approval, not edits to these items.

[Outstanding research](pending.md) prioritizes human rubric calibration and
independent judgments; release-wide enrichment and population definition; blinded
matched alternative annotation-source study; larger event/target and ambiguity
coverage; qualified local answering runtimes, missing/failure-aware metrics and
uncertainty; and a separate formal freeze. No human agreement, annotation-quality,
answering performance or new OOD result exists. Automatic evidence/consistency
checks establish software properties only.
