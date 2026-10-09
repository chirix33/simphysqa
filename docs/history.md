# Historical recovery and compatibility

The preserved local branch `archive/phi-jepa-pre-simphysqa` resolves to
`7dd4a64e90cfb18be743503ac8345cabf2f6e28b`. It owns the original checkout and ignored
local data. It was verified before cleanup; no remote archival branch was present.
Every one of the 9,725 removed blobs exactly matches that archival revision.
The published pre-cleanup main `ccfde9ee904ac5efdc330ba707ebf54843ffb135` independently
contains every removed file, including the original Phi-JEPA/SCLD method plans,
configs, run results and prototype notebook. No Git history was rewritten.

```powershell
git show archive/phi-jepa-pre-simphysqa:MODEL_TRAINING_CONTRACT.md
git show ccfde9ee904ac5efdc330ba707ebf54843ffb135:README-old.md
git log --all -- path/to/historical/file
```

For byte-exact recovery, use Git tooling to export a blob; avoid PowerShell text
redirection when recovering binary payloads. The original checkout, SimPhysQA
worktree and external artifact roots remain in place. Obsolete tracked result/output
files were removed from the index only and are ignored locally. They were not
physically deleted. Ignored/untracked data, environments, weights and results are
not backed up by Git; retain those roots independently.

Historical milestones: foundation preparation `d21ff35e8a81e7a260887de483afab965eafe83f`,
local foundation merge `ff2fe26d178883a2cbc68938d661bb157342b5fc`.
These identify history, not the current tip. Start future work from current main.

Remaining legacy paths have specific uses:

| Path | Reason retained |
| --- | --- |
| src/phi_jepa/simulation/ | Generation, admission, private matched verification, numeric registries and extraction compatibility |
| src/phi_jepa/artifacts.py and validation.py | Transitive JSON/hash/provenance dependencies of simulator and source validation |
| configs/dataset*, configs/frozen_dataset_domains/, pilot_config.json | Source-generation/rejection/controller records, optional regression resources and frozen evidence |
| configs/quadruped* and simulator MJX/quadruped modules/tests | Deferred-domain exclusion/failure evidence and retained compatibility; not a fifth active domain |
| MODEL_DATA_CONTRACT.md, SPECIFICATION.md, VALIDATION.md | Original numeric/extraction/source-generation contracts; downstream learned-method prose is historical |
| docs/assets/, docs/docs/09_sources.md, SHA256SUMS.txt and docs/SHA256SUMS.txt | Adopted exact schemas/prompts/source manifest and original distribution provenance; checksums are historical snapshots |
| configs/model_context_p02b.json, configs/enrichment_p12_pilot.json, docs/reviews/artifacts/P02b/provider-ledger.json | SPQ01's historical provider identity/pricing antecedents; no training/model launchers remain |
| docs/reviews/PDS*, docs/reviews/artifacts/PDS*, dataset/license decisions | Original generation, admission, rejected-domain, release freeze and licensing receipts |

The optional adopted source documents under docs/references/sources/ were ignored
and not present in the main checkout at cleanup. Their identities/hashes remain in
docs/assets/source_manifest.json and historical source records. No placeholder files
were invented. Two `None` links in the byte-sealed prompt catalogue describe unavailable
preliminary procedure sources; they are retained provenance gaps, not executable inputs.
Archived machine paths and unavailable producer revisions remain explicitly historical.

Frozen full-release generation binds old source/config/license hashes; cleanup does
not qualify another release or repair those snapshots. A new authorized generation
requires a new freeze and runtime qualification. The supported install remains editable
checkout, and the `phi_jepa` import namespace remains unchanged.
