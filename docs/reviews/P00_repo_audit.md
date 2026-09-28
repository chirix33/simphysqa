# P00 repository reconciliation — 2026-09-23

Initial checkout: clean `main` at `8e1cd56feb8f9fb0ec8aee92b0d0365b32722066`.
Working branch: `codex/p00-bootstrap`, same HEAD, uncommitted P00 changes.
The older audited `6e5f7d0f35b44db32056476d9e3b1ed24878d393` is not current HEAD.
Root `AGENTS.md` was present and was the only instruction file found by recursive
hidden-file inventory. Its applicable scientific and engineering policies were preserved.
No prior phase reports or standalone test suite existed. No remote operation was performed.

## Actual inventory and reuse boundary

| Existing paths | Observed role | P00 treatment |
| --- | --- | --- |
| `main.py`, `config.py` | Five-domain prototype driver, fixture/openai/manual settings, inline assertions, 400-epoch default | Preserve; do not execute training or reuse as new CLI |
| `training.py` | FP64 derivative supervision, normalization, guarded integration | Useful normalization/solver concepts; do not import as terminal latent predictor |
| `pipeline.py` | Contract generation, critique/repair rounds and mutable result writing | Preserve as legacy; exclusive-create P00 writer added separately |
| `agents.py`, `schemas.py` | Provider boundary, strict Pydantic messages, sourced unknown values, canonical hashes; imports reach domain registry | Reuse design ideas, not imports or legacy prompt contracts |
| `verification.py`, `problems/{base,driving,rocket,reactor,oscillator,sir}.py` | Authored domain constraints/physics and verification | Preserve and exclude from new core import graph; not a validated new benchmark |
| `display.py`, `metacognition_results/` | Legacy plots/reporting and 89 local filesystem entries under results | Preserve, not rerun or interpreted as new results |
| `requirements.txt` | Legacy OpenAI/Pydantic plus unpinned NumPy/Torch/Matplotlib | Unchanged; P00 uses separate package metadata and local CPU verification environment |
| `docs/` | Actual handoff root, specifications in `docs/docs/`, phase prompts/assets/references | Correct installation instructions in place; no duplicate handoff |

The prototype assertions in `main.py` remain intact. They require running legacy training
and do not verify this new slice, so they were not executed. Eight focused standard-library
tests were added under `tests/`; no existing checks were removed or weakened.

## Notebook and source evidence

| Local notebook | Bytes / cells | SHA-256 |
| --- | --- | --- |
| `Phi_JEPA_COMPLETE_OpenAI_MuJoCo_SMOKE20_WITH_ANSWERS_Colab.ipynb` (tracked) | 613674 / 71 | `15ffc46709d5e70a118dd02345d9957ce6d7c9a7f1bf77648ff048a4a4c2e46a` |
| `docs/references/sources/professor_demo_source.ipynb` (ignored source asset) | 64681 / 71 | `12517c51b3e7a6297386c1192659c6413770b9cb9c03f31a8fe650680c9ccc3d` |
| `phi_jepa_try.ipynb` (ignored legacy notebook) | 173858 / 47 | `2b908a5340fa9dacc8637e6168202d0c3c0e5a73365827b4d0693dba5e9736b1` |

The first two notebooks have identical concatenated code-cell SHA-256
`13253db311d5ca9f961c1ec2473223a3661a1e9d945c5f538eaa7937ccf01ed4`.
This establishes code-cell equivalence, not output/metadata equivalence. The tracked full
notebook's file hash differs from the historical original notebook hash
`a66b96b69c304268218d058235d4a1f5669164cd5cb0535323c6e6cce44668d6`
in the supplied audit; do not claim the full files are byte-identical.

All nine assets in `docs/assets/source_manifest.json` are present and match the supplied
hashes: four prompt/schema JSON files, paper PDF, results ZIP, stripped notebook, and both
meeting documents. The results ZIP has 14 entries; only its index was inspected, with no
checkpoint deserialization. The root handoff ZIP, runbook and prior review Markdown files
also exist as ignored historical material. No notebook or result was changed or executed.

## Conflict table

| Older statement or implementation | Current authority and resolution |
| --- | --- |
| Install under a nested implementation directory | Latest user says `docs/`; corrected root instructions, index, workflow and phase prompts; annotated historical decision ledger |
| PyTorch gradients pending | Active P00 prompt reports user PASS; current environment docs updated with attribution, model-specific checks remain pending |
| Legacy derivative loss/domain enforcement/repair | Settled method requires terminal physical MSE plus question alignment, fixed assessment, no inference optimization/repair; legacy isolated |
| Notebook target-state/trajectory losses and nonlinear decoder | Detailed audit and settled specification override notebook; no neural code adopted in P00 |
| Historical root README/AGENTS 404 and old audited commit | Local root AGENTS exists and current HEAD differs; new root README documents actual CLI |
| Fixture or saved demo could be read as empirical evidence | P00 result explicitly contains no physical prediction or metric; no empirical claim |

## Environment diagnosis

`python --version` and `python -m pip --version` initially failed because Python was absent
from PATH. Bounded discovery found the bundled Python 3.12.14 and setuptools 84.0.0 at
`C:/Users/aashraf/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`.
A local `.p00-venv` was created with `--system-site-packages` to reuse that build backend;
the package has zero third-party runtime/test dependencies. Editable installation used
`--no-index --no-deps --no-build-isolation` and succeeded. This Windows CPU verification is
distinct from the user-reported WSL CUDA check. No unresolved P00 environment blocker.

The initial branch creation was denied by the read-only `.git` sandbox; the same scoped
`git switch -c codex/p00-bootstrap` succeeded through approved escalation. No reset, clean,
commit, push or merge was performed.
