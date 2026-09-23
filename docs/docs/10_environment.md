# Environment and execution status

[Start](../README.md) · [Full baseline installation/runbook](../references/baseline_runbook.md)

## Confirmed from the user

Windows 11 Enterprise; one NVIDIA RTX 5090 with 32,607 MiB dedicated capacity; Windows driver/KMD 610.60. Ubuntu-24.04 is Running at WSL VERSION 2. Ubuntu NVIDIA-SMI sees the GPU and reports user-mode CUDA 13.3. That driver information does not require our Python CUDA runtime to have the same version.

C: has 1,887,890,018,304 bytes free (about 1.89 TB/1.72 TiB) of 2,025,740,824,576 bytes. Earlier RAM counters account for about 64 GB, but exact installed capacity and CPU/core count are unconfirmed. Intel shared graphics memory is not additional NVIDIA VRAM. The screenshot's 1,585 MiB GPU usage was one moment, not a permanent reserved amount.

**Pending:** the user will return the PyTorch 2.7.1+cu128 FP32/BF16 forward/backward check. Baseline model loading, FSDP behavior, physics training and performance remain unverified. Codex must not mark these complete on the basis of nvidia-smi alone.

## Implementation can start now

CPU tests can run wherever the coding agent has Python and suitable CPU dependencies. Keep lightweight contract/evaluator tests separate from PyTorch/model-download tests. CPU Torch builds are a separate development lock/profile; they do not need CUDA wheels. Model fixture mode must be explicit in manifests. Report actual tested interpreter and dependencies; do not misrepresent a local agent sandbox as the user's workstation.

For the workstation use Python 3.12 venvs under `~/phi-jepa/.venvs/`: main `phi-core`, `phi-coconut`, and `phi-codi`. The user has been given commands to create phi-coconut first; its execution is not yet confirmed. CoConuT and CODI require distinct Transformers versions and must not share all dependencies with the core. Store active code/data inside WSL's Linux filesystem.

Compatibility target for both latent baselines is Torch 2.7.1 with CUDA 12.8, with upstream Torch/CUDA package pins replaced in versioned requirement copies. This is an initial reviewed compatibility choice, not the latest release or an executed installation guarantee. Run package consistency checks and model smoke tests. Preserve working Windows driver; do not install a Linux NVIDIA display driver inside WSL.

Start worker count 2 and batch-one inference, then profile. Avoid optional FlashAttention, compilation, quantization and new GPU simulator backends in the first correctness slice. Add performance changes only against a stable measured reference. Main ODE training initially uses FP32; CODI follows its BF16 recipe. Any CoConuT BF16 change is labeled separately.

## Required progression

Environment/import → actual CUDA tensor gradients → checkpoint/model load → bounded model forward/backward → representative longest-sequence/stage profile → tiny fitting run → declared pilot → approved main run. An error at one gate does not invalidate completed CPU work; report the exact blocker and continue independent authorized substeps.

Use the full runbook for upstream configuration details, known author-script defects, official source URLs and commands. Do not install or run long jobs automatically just because they appear in an appendix.
