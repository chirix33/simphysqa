# Phi-JEPA: CoConuT and CODI baseline runbook

Reviewed 22 September 2026; updated 23 September 2026 with workstation command results. Status: source-reviewed preparation, not an executed training recipe. Upstream repositories were cloned and inspected; the user has verified Ubuntu 24.04 on WSL2 and NVIDIA GPU visibility; baseline dependencies, weights, PyTorch execution, and physics adapters have not yet been verified. Proposed experiment settings below are recommendations, not additional decisions attributed to Professor Kaushik. The workstation-specific installation below supersedes the original direct upstream requirements installation.

## Decision and scope

Add both methods to the mandatory comparison. Each requires trainable local model internals; these are not prompt modes that can be applied to a closed model API. Start with a matched GPT-2 pair and six latent steps. Keep the separately requested high-, moderate-, and non-reasoning LLM categories. Do not multiply every latent method by every CoT/ReAct prompt condition.

Separate two activities:

1. **Native verification:** establish that the upstream implementation loads and works on its original arithmetic benchmark. CODI's released weights make this inexpensive relative to training. A short CoConuT run verifies mechanics; it does not reproduce published accuracy.
2. **Physics comparison:** train both on the agreed physics training partition, with common, verified worked-solution annotations and final targets. Select settings/checkpoints using validation only. GSM8K-trained weights evaluated directly on physics may be a labeled transfer experiment, but are not the sole main comparison.

Our frozen-LLM policy applies to Phi-JEPA. It does not prohibit training the backbone/adapters required by these baselines. Report that difference, their annotation requirements, and training cost.

## Pinned sources

| Method | Official repository | Inspected commit |
| --- | --- | --- |
| CoConuT | https://github.com/facebookresearch/coconut | `27273cb8cca4bb763c041a63b036d0c3b7cbbb48` |
| CODI | https://github.com/zhenyi4/codi | `2c2314662c63e9f482ebc46614ffe9af17a241e5` |

Use separate environments and retain upstream license files. Pin model and dataset revisions as well as code. Changing upstream versions later requires a recorded review.

```bash
git clone https://github.com/facebookresearch/coconut.git
git -C coconut checkout 27273cb8cca4bb763c041a63b036d0c3b7cbbb48
git clone https://github.com/zhenyi4/codi.git
git -C codi checkout 2c2314662c63e9f482ebc46614ffe9af17a241e5

```

Run from a new working directory inside WSL2/Ubuntu on the workstation. CoConuT pins PyTorch 2.5.1/Transformers 4.46.2; CODI pins PyTorch 2.7.1/Transformers 4.52.4 and CUDA 12.6 package dependencies. **Do not install these original requirements unchanged on the RTX 5090.** It uses Blackwell; PyTorch 2.7 introduced Blackwell support with CUDA 12.8 wheels. Our compatibility starting point is **PyTorch 2.7.1+cu128 in both environments**, retaining separate Transformers/other packages. This is a hardware compatibility deviation from the original environment, not a claim of bitwise reproduction or the latest PyTorch release.

Use Ubuntu Python 3.12 virtual environments to avoid requiring a separate Conda installation. If environments have already been created with Conda, use those consistently instead; do not install into both. The following venv path is the current walkthrough. Generate copies of requirements that let the selected PyTorch wheel resolve its own CUDA dependencies. Preserve originals. Run the repository installation commands from the directory containing the two cloned repositories:

```bash
sudo apt update
sudo apt install -y python3.12-venv git
python3.12 -m venv ~/phi-jepa/.venvs/phi-coconut
python3.12 -m venv ~/phi-jepa/.venvs/phi-codi

python3 - <<'PY'
from pathlib import Path
for repo in ('coconut', 'codi'):
    source = Path(repo) / 'requirements.txt'
    lines = source.read_text().splitlines()
    excluded = ('torch==', 'triton==', 'nvidia-')
    kept = [line for line in lines if not line.strip().startswith(excluded)]
    (source.parent / 'requirements.rtx5090.txt').write_text('\n'.join(kept) + '\n')
Path('constraints.rtx5090.txt').write_text('torch==2.7.1+cu128\n')
PY

~/phi-jepa/.venvs/phi-coconut/bin/python -m pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cu128
~/phi-jepa/.venvs/phi-coconut/bin/python -m pip install -c constraints.rtx5090.txt -r coconut/requirements.rtx5090.txt pyyaml
~/phi-jepa/.venvs/phi-coconut/bin/python -m pip check

~/phi-jepa/.venvs/phi-codi/bin/python -m pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cu128
~/phi-jepa/.venvs/phi-codi/bin/python -m pip install -c constraints.rtx5090.txt -r codi/requirements.rtx5090.txt
~/phi-jepa/.venvs/phi-codi/bin/python -m pip check
```

The requirements-copy block uses Ubuntu's `python3` and only its standard library; model packages are installed into the separate virtual environments. Activate the desired one with `source ~/phi-jepa/.venvs/phi-coconut/bin/activate` or the corresponding `phi-codi` path; use `deactivate` when switching. Do not subsequently reinstall the original requirements over these environments. Installation/dependency resolution remains to be verified on the workstation. Record the resulting `pip freeze`, GPU driver, and environment patch. Test CoConuT checkpoint loading, FSDP execution, forward/backward, and CODI model loading under this stack; address concrete compatibility failures with reviewed patches. Do not combine either environment with the main project.

Primary compatibility references: [PyTorch Blackwell support](https://pytorch.org/blog/pytorch-2-7/) and [official 2.7.1 CUDA 12.8 installation](https://pytorch.org/get-started/previous-versions/#v271).

## CoConuT: native workflow and configuration

From the CoConuT directory, activate `phi-coconut`, configure the repository's W&B logging, and run `bash preprocessing/gsm_icot.bash`. Its dataset is a JSON list of records with `question`, `answer`, and `steps` (a list of solution-step strings).

Copy the three GSM YAML configurations to distinct local files. Set a fresh writable `save_path` and unique `name` in each. Avoid reusing a populated run directory: `run.py` automatically inspects it for resumable checkpoints.

1. Run CoT training using the edited `args/gsm_cot.yaml` configuration.
2. Set the latent-training configuration's `load_model_path` to the selected CoT checkpoint, then train CoConuT.
3. Set the evaluation configuration's `load_model_path` to the validation-selected CoConuT checkpoint. Its `val_path` supplies the test file when `only_eval` is true.

```bash
# Run inside coconut with phi-coconut active, after preparing these YAML files.
torchrun --standalone --nnodes=1 --nproc_per_node=1 run.py args/local_gsm_cot.yaml
# Set load_model_path to the selected CoT checkpoint before the next command.
torchrun --standalone --nnodes=1 --nproc_per_node=1 run.py args/local_gsm_coconut.yaml
# Set load_model_path to the selected CoConuT checkpoint before evaluation.
torchrun --standalone --nnodes=1 --nproc_per_node=1 run.py args/local_gsm_coconut_eval.yaml
```

The code initializes NCCL/distributed execution even with one GPU; use `torchrun`. The authors describe four A100 80GB GPUs and permit batch/accumulation adjustments. This is their reference machine, not a minimum requirement.

| Setting | Checked upstream GPT-2 configuration |
| --- | --- |
| Backbone | `openai-community/gpt2`, full tuning |
| CoT stage | 25 epochs, LR 1e-4, weight decay 0.01 |
| Latent curriculum | 2 continuous tokens per removed step; maximum 3 stages; 3 epochs per stage; padding to maximum enabled |
| Latent phase | LR 1e-4; optimizer reset enabled; `resume: 3`, `num_epochs: 25` |
| Precision / seed | `bf16: false`, seed 0 |
| Reference batch | 32 per GPU × 4 GPUs × accumulation 1 = 128 |
| Single-GPU starting batch | Proposed microbatch 4 × accumulation 32 = 128; reduce microbatch if needed |

**Epoch nuance:** `run.py` iterates from `resume` to `num_epochs`. The supplied latent settings therefore execute epochs indexed 3–24: 22 iterations after the independently trained CoT model. `resume` also determines curriculum stage. Preserve this behavior for the pinned-repository reference; do not silently set it to zero or describe it as 25 executed latent epochs. The CODI paper describes a 25+25 CoConuT comparison, so paper-level reproduction and this repository configuration are not identical schedules.

Inspect source: [CoT settings](https://github.com/facebookresearch/coconut/blob/27273cb8cca4bb763c041a63b036d0c3b7cbbb48/args/gsm_cot.yaml), [latent settings](https://github.com/facebookresearch/coconut/blob/27273cb8cca4bb763c041a63b036d0c3b7cbbb48/args/gsm_coconut.yaml), [execution/evaluation](https://github.com/facebookresearch/coconut/blob/27273cb8cca4bb763c041a63b036d0c3b7cbbb48/run.py).

## CODI: released-checkpoint verification

Official released models: [zen-E/CODI-gpt2](https://huggingface.co/zen-E/CODI-gpt2) and [zen-E/CODI-llama3.2-1b-Instruct](https://huggingface.co/zen-E/CODI-llama3.2-1b-Instruct). They are arithmetic-trained checkpoints, not physics-trained models.

In the CODI environment, download the GPT-2 checkpoint into an explicit local directory using `huggingface_hub.snapshot_download`; record the resolved revision. Example inside the CODI directory:

```bash
python - <<'PY'
from huggingface_hub import HfApi, snapshot_download
repo = 'zen-E/CODI-gpt2'
revision = HfApi().model_info(repo).sha
print('checkpoint revision:', revision)
snapshot_download(repo_id=repo, revision=revision, local_dir='checkpoints/codi-gpt2')
PY

python test.py \
  --data_name gsm8k --output_dir runs/codi-gpt2-native \
  --model_name_or_path gpt2 --seed 11 --model_max_length 512 \
  --bf16 --lora_r 128 --lora_alpha 32 --lora_init \
  --batch_size 1 --greedy True --num_latent 6 \
  --use_prj True --prj_dim 768 --prj_no_ln False --prj_dropout 0.0 \
  --inf_latent_iterations 6 --inf_num_iterations 1 \
  --remove_eos True --use_lora True --ckpt_dir checkpoints/codi-gpt2
```

This evaluates the native benchmark, not a bounded few-example smoke test. Add an explicit sample limit in a reviewed wrapper before using it as a tiny smoke test. The checkpoint architecture is reconstructed by `test.py`; a plain `AutoModelForCausalLM` load is not sufficient. Audit missing/unexpected state keys because the loader uses `strict=False`.

The command requires CUDA with working BF16. `test.py` explicitly moves the model to CUDA and BF16; removing `--bf16` alone does not change that. If the workstation lacks support, implement and verify an explicit dtype/device option first.

The README's `script/test_gpt2.sh` path is a typo; the directory is `scripts/`. Its test scripts also use an unset output variable and author-specific checkpoint paths. Use explicit paths as above. Training scripts contain author-specific output locations and a copy command referring to an absent script; preserve their actual model flags in a clean launcher.

Sources: [evaluation script](https://github.com/zhenyi4/codi/blob/2c2314662c63e9f482ebc46614ffe9af17a241e5/scripts/test_gpt2.sh), [checkpoint loading and evaluator](https://github.com/zhenyi4/codi/blob/2c2314662c63e9f482ebc46614ffe9af17a241e5/test.py).

## CODI: training settings

CODI self-distills a text-solution teacher path into a continuous student path in the same model. It still requires question/solution/answer data. There is no separate CoConuT-style staged warm-up requirement.

| Setting | GPT-2 author script | Llama-3.2-1B-Instruct author script |
| --- | --- | --- |
| Epochs / LR | 40 / 3e-3 | 10 / 8e-4 |
| Batch / accumulation | 64 / 2 | 32 / 4 |
| LoRA | rank 128, alpha 32 | rank 128, alpha 32 |
| Latent steps | 6 | 6 |
| Projection width | 768 | 2048 |
| Distillation multiplier | default 1 | 20 |
| Precision | BF16 | BF16 |
| Length setting | 512 | 512 |
| Other | weight decay 0.1, warm-up 0.03, cosine LR, gradient clip 2 | same |

Use these as initial reference configurations, not universal optimum physics settings. The GPT-2 launcher is `scripts/train_gpt2_gsm8k-aug.sh`; the 1B launcher is `scripts/train_llama1b_gsm8k-aug.sh`. Both filenames were verified in the pinned tree. Keep original files and create clean project-specific launchers. Check base-model download access and applicable license terms before the optional Llama run.

The upstream scripts disable intermediate saving with `save_strategy=no`; the trainer saves at the end. Add validation/checkpoint selection for our experiments. Retain a distinct upstream-reproduction configuration. Keep the documented `fix_attn_mask=False` in that reproduction configuration; any attention-mask correction must be an explicit reviewed code change with a separately labeled result.

For planning only, the [CODI paper, Appendix A](https://arxiv.org/html/2502.21074v2#A1) reports about 36 hours for GPT-2 and 48 hours for 1B on one A100 80GB for its full training runs. These are not estimates for our workstation or physics dataset.

Sources: [training implementation](https://github.com/zhenyi4/codi/blob/2c2314662c63e9f482ebc46614ffe9af17a241e5/train.py), [GPT-2 launcher](https://github.com/zhenyi4/codi/blob/2c2314662c63e9f482ebc46614ffe9af17a241e5/scripts/train_gpt2_gsm8k-aug.sh), and the pinned repository's `src/model.py` and `scripts/` directory.

## Required physics integration

1. **One dataset contract:** scenario ID, family/split, question, initial facts, requested observables/units/frame/horizon, verified solution steps, canonical terminal targets, and separately stored evaluator-only trajectories/OOD labels. No gold answers or solution traces in inference requests.
2. **Training adapters:** CoConuT needs its `steps` list; CODI needs the corresponding `cot` representation. CODI currently routes to named benchmark datasets, not an arbitrary physics file. Implement a local loader rather than passing an invented existing CLI option. Its arithmetic branch extracts the final answer token and rejects answers not beginning with a digit; that would discard negative-valued physics answers.
3. **Answer parser:** preserve signs, scientific notation, units, multiple named components, and missing values. CoConuT strips commas and uses exact string matching; CODI extracts a last numeric match. Neither is an acceptable physics evaluator. Parse into the shared typed physical prediction. A fixed output envelope is an interface, not a handwritten physics solver.
4. **Sequence audit:** count token lengths with each tokenizer before training; include question, trace, targets, and special/latent tokens. Explicitly count filtered/truncated records. CODI's 1B launcher additionally uses a 200-token filter. Make CoConuT's path-dependent 64/128 generation limit configurable. Increase budgets only under a recorded fair policy.
5. **Workstation controls:** expose worker count (CoConuT hard-codes 32 dataset processes), device/dtype, batch/accumulation, cache paths, checkpoint intervals, seed, and generation limits. Test a longest-stage batch before a long run.
6. **Validation:** select checkpoints by the same physical validation objective. Use a modest, declared method-specific LR search if defaults fail; provide equal tuning opportunities, not identical learning rates for unlike losses. Never tune on OOD test results.
7. **Evaluation scope:** start with terminal-state predictions at a specified horizon. Report full-trajectory metrics only when each method actually produces the same evaluated time grid. Multiple time-query calls are an extension with all calls charged to the method.
8. **Cost and fairness:** record all training stages, trainable parameters, annotation generation/verification, training GPU-hours, inference latent steps, emitted tokens, model calls, batch-one latency and throughput separately. Include CoConuT's CoT stage. Six latent steps do not imply equal computational work across architectures.
9. **No privileged wrapper:** these baselines should not receive Phi-JEPA's decoded answer or ground-truth schema fields. If applying a shared final text renderer, score numeric outputs before it and report its cost uniformly. Keep baseline-native predictions distinct from a new hybrid method.
10. **Experiment repetitions:** proposed pilot seed 11 for both; retain author seeds in reproduction configs. After feasibility, proposed main seeds 11/22/33 with common partitions and scenario-family uncertainty estimates. These are planning defaults, not completed runs.

Training traces are a real data dependency: simulator endpoints alone are insufficient for the documented methods. Create concise worked explanations supported by verified labels, audit them, and keep their cost and any domain-specific authoring visible. Never manufacture plausible-looking incorrect traces to satisfy the format.

## Workstation decision and launch gates

### User-supplied hardware

| Component | Reported information | Planning interpretation |
| --- | --- | --- |
| Training GPU | NVIDIA GeForce RTX 5090; nvidia-smi reports 32,607 MiB and driver 610.60 | One nominal 32 GB NVIDIA GPU; Windows and Ubuntu NVIDIA visibility confirmed; PyTorch execution not yet tested |
| Other graphics | Intel Graphics; shared-memory limit 47.5 GB | Not a second CUDA training GPU; do not add this shared RAM to NVIDIA VRAM |
| OS | Windows 11 Enterprise | Recommend WSL2 with Ubuntu 24.04 LTS for these Linux/CUDA-oriented repositories |
| System RAM | 16.7 GB in use; 46.7 GB available | Approximately 63.4 GB accounted for; likely a roughly 64 GB usable configuration, but installed capacity needs confirmation |
| System disk C: | 2,025,740,824,576 bytes total; 1,887,890,018,304 bytes free | About 1.89 TB (1.72 TiB) free; adequate initial working-space capacity |

The Intel shared-memory limit does not reconcile cleanly with the supplied RAM counters. Preserve both observations instead of inferring a larger installed RAM total. Exact current VRAM use is also unclear from the typed `1/0/31.5GB`; no allocation decision depends on that transcription.

**Feasibility judgment:** the hardware is suitable for starting both GPT-2 baselines and the planned compact Phi-JEPA components. CODI's 1B LoRA run is a realistic next profile; CoConuT 1B full tuning also merits a small-batch profile before scheduling. Neither larger run's memory/time has been measured. Do not procure cloud compute for the initial pilot solely because the authors used A100s. Model choice for any locally hosted frozen LLM remains a separate memory decision; run jobs sequentially initially.

### Windows and WSL setup

Driver 610.60 is installed. Ubuntu nvidia-smi now detects the RTX 5090 and reports NVIDIA-SMI 610.47.03, KMD 610.60, and CUDA UMD 13.3. Keep this functioning driver and verify PyTorch execution next; the driver-reported CUDA UMD version is not the Python package CUDA runtime and does not require switching our cu128 build. Newer NVIDIA drivers support older CUDA runtimes; see https://docs.nvidia.com/deploy/cuda-compatibility/why-cuda-compatibility.html. The Windows driver supplies WSL's GPU access; **do not install a Linux NVIDIA display driver inside WSL**. A separate CUDA compiler/toolkit is not part of the initial prebuilt-wheel path; add one only if a required extension must be compiled. Docker is optional and not required here.

Check existing setup in PowerShell first:

```powershell
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
wsl --status
wsl --list --verbose
Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory
Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors
Get-Volume | Select-Object DriveLetter,Size,SizeRemaining
```

If WSL/Ubuntu is absent, use administrator PowerShell, then restart if requested and complete Ubuntu user creation:

```powershell
wsl --install -d Ubuntu-24.04
wsl --update
```

For an existing installation, update it and confirm the selected Ubuntu distribution is version 2. Do not reinstall or unregister an existing distro. If Enterprise management blocks virtualization or installation, use the administrator-supported setup route.

Store active repositories, environments, caches, and datasets inside the Linux filesystem, for example `~/phi-jepa`, for Linux-tool I/O performance. Keep durable checkpoints backed up. The reported C: free space is about 1.89 TB; an initial 100–200 GB working-space allowance is a planning reserve, not a measured requirement. Do not interpret a virtual disk's displayed maximum as physically available storage.

Begin with WSL's existing/default memory cap and inspect `free -h` inside Ubuntu. The documented default is half of Windows RAM. A 32 GB cap should be a reasonable initial GPT-2 target if usable host RAM is about 64 GB. Raise it only after observing CPU-memory pressure and confirming host headroom. Start dataset workers at 2, profile 4 later, and remove CoConuT's hard-coded 32-process setting. CPU model/count is still unconfirmed.

References: [NVIDIA WSL driver guidance](https://docs.nvidia.com/cuda/wsl-user-guide/index.html), [Microsoft WSL installation](https://learn.microsoft.com/en-us/windows/wsl/install), [WSL memory settings](https://learn.microsoft.com/en-us/windows/wsl/wsl-config), [Linux filesystem performance](https://learn.microsoft.com/en-us/windows/wsl/setup/environment), [RTX 5090 specifications](https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5090/).

### September 23 update: WSL2 blocker resolved

The user supplied successful output: Ubuntu-24.04 is Running at VERSION 2. Inside Ubuntu, NVIDIA-SMI detects the RTX 5090, 32,607 MiB total, 1,585 MiB used at that snapshot, and KMD 610.60/CUDA UMD 13.3. This verifies WSL2 startup and NVIDIA management visibility. It does not yet verify PyTorch kernels, gradients, checkpoint loading or model training. Do not ask the user to repeat firmware changes or reinstall Ubuntu.

Next, create the first Python environment and install only the selected Torch build plus NumPy, then run the CUDA check below. This can happen before cloning repositories. In the Ubuntu terminal:

```bash
sudo apt update
sudo apt install -y python3.12-venv git
python3.12 -m venv ~/phi-jepa/.venvs/phi-coconut
source ~/phi-jepa/.venvs/phi-coconut/bin/activate
python -m pip install --upgrade pip
python -m pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cu128
python -m pip install numpy==2.1.3
```

This is the CoConuT environment's initial runtime setup, not a third temporary environment. Once its CUDA check passes, install the remaining baseline packages through the adapted requirements above. CODI retains its separate environment and NumPy/Transformers versions. Initial driver/runtime validation does not depend on having model weights or physics datasets.

The original virtualization failure is historical and resolved by the user's subsequent output; no driver, boot, or security change is currently required by an observed problem.

### Initial run settings

| Workload | Initial precision | Microbatch / accumulation | Other settings |
| --- | --- | --- | --- |
| CoConuT GPT-2 | FP32 for upstream-reference check; BF16 only as a validated, recorded change | 4 / 32 | One GPU; six final latents; verify the longest curriculum stage |
| CODI GPT-2 | BF16, as upstream | 4 / 32 | Six latents, LoRA rank 128/alpha 32, projection 768 |
| CODI 1B follow-up | BF16 | Profile 1–2 first; 128–64 accumulation if keeping batch 128 | Projection 2048; its own author LR/distillation multiplier |
| CoConuT 1B follow-up | Profile BF16 as a documented variant | Profile 1 first | Validate matching model/configuration and full-tuning memory before committing |
| Evaluation/latency | Match each trained configuration | Batch 1 | Measure throughput separately at larger batches |

Effective training batch is GPU count × microbatch × accumulation. These are starting allocations, not measured maxima. Adjust microbatch upward after profiling if beneficial; retain the target effective batch and log the change. Six latent steps and a 512-token audit target remain the starting comparison; inspect actual encoded lengths before fixing limits. Do not add quantization or an unofficial LoRA conversion to CoConuT merely to fit memory without labeling the methodological change. Keep optional compilation and fused-attention additions out of the first correctness check.

Inside each activated environment, verify actual CUDA execution before launching a model:

```bash
python - <<'PY'
import torch
assert torch.cuda.is_available(), 'CUDA unavailable'
print('torch:', torch.__version__, 'runtime:', torch.version.cuda)
print('GPU:', torch.cuda.get_device_name(0))
print('capability:', torch.cuda.get_device_capability(0))
print('compiled architectures:', torch.cuda.get_arch_list())
print('BF16 supported:', torch.cuda.is_bf16_supported())
for dtype in (torch.float32, torch.bfloat16):
    if dtype == torch.bfloat16 and not torch.cuda.is_bf16_supported():
        raise RuntimeError('BF16 unavailable for the planned CODI configuration')
    x = torch.randn(512, 512, device='cuda', dtype=dtype, requires_grad=True)
    loss = (x @ x.T).float().square().mean()
    loss.backward()
    torch.cuda.synchronize()
    assert torch.isfinite(loss) and torch.isfinite(x.grad).all()
print('CUDA forward/backward passed')
PY
```

The NVIDIA card may be `cuda:0` even though Task Manager labels it GPU 1; select by the CUDA-reported identity, not the Windows display index. This tensor check does not replace each repository's model/checkpoint/solver tests.

Launch gates, in order:

1. Dependency/import check, CUDA/BF16 check, source/model/data revision capture.
2. CODI released-checkpoint native check with audited key loading; bounded CoConuT training/checkpoint round trip.
3. Shared physics loader and evaluator checks, including negative/scientific/multi-component outputs and split leakage.
4. Small-set overfit sanity check for each method; this is a mechanics check, not a scientific result.
5. Representative 20–50 optimizer-step profile at the largest planned sequence/latent stage. Measure peak allocated/reserved VRAM and time per optimizer step, then estimate training and validation cost.
6. Complete one-domain pilot with validation-selected checkpoints, followed by the agreed ID/OOD matrix and additional seeds/domains.

No outstanding baseline question currently needs to return to Professor Kaushik. The hardware class is now known. WSL2 and Ubuntu GPU visibility are confirmed. Remaining machine work is verifying PyTorch kernels and the model environments; exact installed RAM/CPU can be recorded during setup; the verified physics/trace dataset and execution gates remain necessary. No training, paid model calls, workstation installation, or user-repository modifications were performed during this review.
