> **Active supersession — 2026-09-24:** Model work follows [training contract 2.0.0-candidate.1](../../MODEL_TRAINING_CONTRACT.md) and the user's revision-3 Stage 1/P02a request. Adjacent recorded-state training uses frozen E(Q,C), trainable P of width d, the same undetached p on both sides, and full predicted 2d-vector feedback. Conflicting terminal-only, tree/readout/semantic-head, E(Q,C,A), upstream-baseline substitution and truth-forbidden-in-training instructions below are historical. Custom Coconut-inspired/CODI-inspired variants are intentional. Future phases require separate authorization. Frozen dataset/export contracts remain unchanged.

# Source index and provenance

[Start](../README.md) · [Authority/context](01_context.md)

## Included primary sources

- [Active newer paper](../references/sources/active_paper.pdf): methodology/figures, subject to subsequent meeting corrections. Inference-minimization/repair passages are explicitly superseded. Placeholder/expected results are not measured evidence.
- [September 22 part 1](../references/sources/september_22_part_1.docx): reviewer concerns, structured encoding, regularization, OOD diagnosis and morning inference decisions.
- [September 22 part 2](../references/sources/september_22_part_2.docx): generic envelope discussion; final frozen-LLM decoding at 18:35–19:53; semantic regularizer ablation around 22:38 onward.
- [Professor's notebook source](../references/sources/professor_demo_source.ipynb): source cells unchanged; output/metadata stripped for this handoff. The whole source is prototype evidence, not an instruction to run its optimization/repair paths.
- [Original demo results archive](../references/sources/phi_jepa_results.zip): preserved user artifact, not final experimental data. Do not load serialized checkpoints unless their provenance/trust and loader format have been reviewed; reading JSON/CSV evidence suffices for the audit.
- [Exact approved prompt strings](../assets/prompts.json), [extraction schema](../assets/extract_schema.json), [judge schema](../assets/judge_schema.json), [answer schema](../assets/answer_schema.json).
- [Source manifest](../assets/source_manifest.json): original notebook hash, included-source hashes and exact per-prompt string hashes.

The latest explicit professor instruction to retain the morning decisions and the user's subsequent architecture/baseline/workstation clarifications were supplied in this conversation; they are summarized in the context/decision ledger. They override contrary draft or notebook passages. The removed older paper is deliberately not included.

Earlier September 20 transcripts and the original repo audit informed historical context; they are not necessary to start P00 and must not override September 22 corrections. The sole substantive extra rules file asks for a dataset list/creation procedure; the data specification includes both. No unrelated TaskCognition or decomposition-project instruction is imported.

## Repository evidence scope

User repository: https://github.com/chirix33/phi-jepa, private, default main. On September 23 the connector returned repository metadata and current requirements; root README.md and AGENTS.md reads returned 404. Current tree/head were not fully audited. P00 must inspect the actual checkout and any nested instructions. Do not treat the historical 6e5f7d0f35b44db32056476d9e3b1ed24878d393 audit as current-head verification.

Official baseline source was cloned/read at CoConuT 27273cb8cca4bb763c041a63b036d0c3b7cbbb48 and CODI 2c2314662c63e9f482ebc46614ffe9af17a241e5. Details and source-file links are in the [runbook](../references/baseline_runbook.md). No baseline GPU run was performed in preparing this handoff.

## Other primary technical references

- [MuJoCo overview](https://mujoco.readthedocs.io/en/stable/overview.html)
- [DeepMind Control Suite](https://github.com/google-deepmind/dm_control)
- [PDEBench](https://github.com/pdebench/PDEBench)
- [MiniLM encoder model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- [PyTorch Blackwell support](https://pytorch.org/blog/pytorch-2-7/) and [CUDA 12.8 wheel recipe](https://pytorch.org/get-started/previous-versions/)
- [NVIDIA WSL setup](https://docs.nvidia.com/cuda/wsl-user-guide/index.html) and [driver/runtime compatibility](https://docs.nvidia.com/deploy/cuda-compatibility/why-cuda-compatibility.html)

These sources support setup and candidate selection. They do not establish that the integrated Phi-JEPA implementation or proposed experiments have already been validated. Pin actual selected versions before use.
