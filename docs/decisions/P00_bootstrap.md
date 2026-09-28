# P00 engineering decisions — 2026-09-23

Authority: user authorizes P00 only and places the handoff directly in `docs/`.
Base commit: `8e1cd56feb8f9fb0ec8aee92b0d0365b32722066`; branch `codex/p00-bootstrap`.
Changes are uncommitted for review.

| Choice | Alternatives and evidence | Impact / superseded instruction |
| --- | --- | --- |
| Retain handoff in `docs/`, instructions at root | Moving or duplicating would contradict the current user request | Replaces original installation destination; active links corrected, historical ledger annotated |
| Add `src/phi_jepa/`, preserve legacy modules | Legacy contracts and provider ideas are useful, but their imports transitively reach authored physics and incompatible training/repair | No legacy import or algorithm migration; legacy results and inline checks remain untouched |
| Python 3.12, frozen dataclasses, standard-library CLI/tests | Pydantic is permitted but unnecessary for the P00 contracts | Zero runtime/test dependency requirements; strict recursive conversion rejects coercion, nonfinite values and unknown fields |
| Pin build backend to setuptools 84.0.0 | This version is locally available and was tested without network | No unverified Torch/NumPy/model dependency lock; later numerical dependencies remain phase work |
| Content-addressed exclusive-create bundles | Append/update would allow accidental replacement of evidence | No timestamps in identity; record code hashes even with uncommitted changes; manifest written last; filesystem editing remains possible and detectable by hashes |
| Fixture is input round trip with no physical prediction | Fabricated numerical values could be mistaken for a model | Explicit fixture labels, null prediction/metrics, zero model/solve/retry counters; not empirical performance |
| Validate live configuration, reject live execution in fixture command | A fixture fallback after live failure would violate policy | Model/revision and positive budgets required; credentials never accepted or logged here; provider support belongs to P02 |
| Record GPU pass as user-reported | Active P00 prompt supersedes older environment prose | PyTorch 2.7.1+cu128 / CUDA 12.8 / RTX 5090 capability 12.0 / BF16 / FP32+BF16 gradients passed per user report; no agent GPU or baseline validation claim |

No scientific defaults D01–D15 or decisions Q1–Q4 changed. No target-latent mapping,
judge extension, learned objective, inference repair, or baseline implementation was added.
Future CLI names are reserved in the root README; they are not advertised as executable commands.

`docs/SHA256SUMS.txt` is preserved as the original package-distribution checksum snapshot.
It is not a checksum index of edited installed documentation, and its `AGENTS.md` entry
describes the original package-root template. Current installed instructions are `AGENTS.md`
at repository root. `docs/assets/source_manifest.json` remains unchanged and all nine source
file hashes and four prompt-string hashes are verified by `tools/verify_p00_handoff.py`.
