# SimPhysQA

SimPhysQA provides simulator-grounded trajectories, language annotations and five
QA families—direct, predictive, counterfactual, explanation and clarification—with
reproducible evidence, human-audit tooling and evaluation interfaces. Current domains
are robotic arm, driving, object pushing/stacking and tethered load.

Start with the [foundation contract](docs/simphysqa/foundation.md),
[documentation index](docs/README.md) and [current status](docs/PROGRESS.md).
Learned dynamics and representation-learning experiments are outside this project.

The accepted engineering set contains 56 QA in 16 train groups. The original source
release contains 11,105 predictive QA in 6,340 groups. SPQ05 delivered a separate
verified, blinded 140-item internal audit package with 420 blank reviewer assignments.
Human judgments, answering-model results and release-wide enriched language remain
pending. These are development/processing receipts, not performance claims.
SPQ06 has not been sent or started.

| Location | Purpose |
| --- | --- |
| [src/simphysqa](src/simphysqa) | Five families, annotation/event/association/evidence, audit, provenance and scoring |
| [src/phi_jepa](src/phi_jepa) | Retained simulator compatibility, admission, extraction and hashing; no learned method |
| [configs/simphysqa](configs/simphysqa) | Annotation, audit, evaluation, exclusions, artifact aliases and CPU pins |
| [tests](tests) | Existing offline behavior and saved-evidence integration |
| [tests/simulator](tests/simulator) | Separate optional simulator checks |
| [scripts](scripts) | Export, archive, verification and setup entry points |
| [docs/simphysqa](docs/simphysqa) | Current scientific contracts and prompt/procedure archives |
| [licenses](licenses) | Scoped licenses and original third-party notices |

Supported setup is Python >=3.11 and an editable source checkout. Root schemas,
assets and configs are required; a wheel away from the checkout is not qualified.

```powershell
python -m venv C:/external/simphysqa-cpu
& C:/external/simphysqa-cpu/Scripts/python.exe -m pip install -e .
& C:/external/simphysqa-cpu/Scripts/python.exe -m pip check
& C:/external/simphysqa-cpu/Scripts/python.exe -m simphysqa --help
& C:/external/simphysqa-cpu/Scripts/python.exe -m simphysqa.spq01 --help
& C:/external/simphysqa-cpu/Scripts/python.exe -m phi_jepa.simulation.cli --help
```

[Exact CPU pins and offline reconstruction](docs/simphysqa/foundation.md#reproducible-setup)
are separate from optional simulator, numerical-audit and local answering runtimes.
Simulator and audit numpy pins conflict; install them in separate environments.
CLI help/CPU tests do not qualify engines, GPUs, audit statistics or model runtimes.

Set `SIMPHYSQA_DATA_ROOT` to the existing external source release. Pass external
`--output` paths (or `SIMPHYSQA_OUTPUT_ROOT` where supported). Artifact aliases live
in [development_artifacts.json](configs/simphysqa/development_artifacts.json);
[paths.example.json](configs/simphysqa/paths.example.json) documents path conventions,
not an automatically loaded settings file. The
[56-item registry](docs/simphysqa/development-index.json) records relative aliases
and hashes; its Markdown counterpart contains historical machine-specific receipts.
Keep data, weights, environments, caches and results outside tracked source.

Public views contain permitted observed language and declared controls. Organizer
records, gold answers/explanations, simulator outcomes, witness completions and audit
identity mappings stay private. Explanation QA intentionally supplies its identified
comparison. Annotation providers and private verification are separate from tool-free
answering requests. [Privacy/family boundaries](docs/simphysqa/foundation.md#data-privacy-and-family-boundaries).

Preserve [executed prompt payloads and per-file lineage](docs/simphysqa/prompt_archive/README.md)
and [SPQ05 execution provenance](docs/simphysqa/prompt_archive/SPQ05/README.md).
Prepared requests are not executed answering experiments. Live runs require separate
authorization and a configured budget.

For changes: branch from current main → validate relevant existing tests and resources
→ review the complete diff → commit → merge/publish through the configured workflow.
Preserve other worktrees and checkouts. [Agent policy](AGENTS.md),
[historical recovery and compatibility notes](docs/history.md),
[cleanup inventory](docs/decisions/repo_cleanup.md).
