# GGUF CUDA setup and SPQ06 runtime receipt

The user supplied troubleshooting notes from another Windows PC on 9 October
2026. They are useful setup evidence, not qualification of a different GPU,
compiler or GGUF runtime. Keep the running SPQ06 environment pinned.

## Windows build checks retained from the user's handoff

Record `nvcc --version`, `cmake --version`, `nvidia-smi`, the selected Python and
`vswhere.exe -latest -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64
-property installationPath`. Inspect the actual installed MSVC toolsets. Select a
toolset supported by the installed CUDA release, rather than assuming the newest
MSVC is compatible. Run `vcvarsall.bat x64 -vcvars_ver=<installed-compatible-version>`
and the build in the same shell invocation, or explicitly import its environment.
Environment changes in one tool subprocess do not persist into another.

The user's previous setup encountered CUDA's compiler-version check with newer
MSVC versions, and a supported VS2022 toolset resolved it. The exact acceptable
compiler range is toolkit-specific: consult the installed toolkit's documentation.
For example, [NVIDIA's CUDA12.8 Windows guide](https://docs.nvidia.com/cuda/archive/12.8.1/cuda-installation-guide-microsoft-windows/index.html)
lists VS2022/MSVC193x and VS2019/MSVC192x. Do not treat a compiler range from another
machine as a universal CUDA13 rule.

For an RTX5090, verify that the toolkit and vendored llama.cpp support Blackwell
`sm_120`. The user recommends CUDA12.8 or later and, when needed, explicit CMake
configuration `-DGGML_CUDA=on -DCMAKE_CUDA_ARCHITECTURES=120`. Pin both
llama-cpp-python and its vendored llama.cpp revision; a pip package version alone
does not demonstrate architecture support. Investigate an unrecognized architecture
error before attempting a different backend.

The user's CUDA13 Windows installation placed runtime DLLs in `bin\x64`. Locate
the actual cudart/cublas DLLs. Before importing llama_cpp, use
`os.add_dll_directory(actual_cuda_dll_directory)` and retain the returned handle
for the module lifetime. A small import shim can centralize this. Python's
[DLL-directory documentation](https://docs.python.org/3/library/os.html#os.add_dll_directory)
explains its role in extension-module and ctypes dependency resolution. A PATH
entry alone is not evidence that Python resolved the intended dependent libraries.

After building, verify `llama_cpp.llama_supports_gpu_offload()` and an actual small
model load with all intended layers on GPU. Save the CUDA device discovery,
GPU name/VRAM, offload and peak-memory logs. Import success or a responsive server
alone does not prove GPU execution. Pin and qualify each workstation separately.

## Actual SPQ06 setup: WSL, not a Windows llama-cpp-python build

SPQ06 uses Ubuntu24.04 under WSL2, the official llama.cpp b11538 Ubuntu CUDA12.8
binary (commit79e2e74eb), and the official pinned Gemma3-27B QAT Q4_0 GGUF.
No Windows MSVC build or llama-cpp-python installation was used for this pilot.

An incomplete `LD_LIBRARY_PATH` allowed the first Gemma server to start with CPU
fallback. Three original direct stages were reserved: two timed out and one was
interrupted with unknown output. They remain in the denominator and are never
retried. The CoT process was interrupted before any item reservation.

Condition revision1.0.1 includes the bundled CUDA runtime/cublas directory, the
user-local OpenMP directory and `/usr/lib/wsl/lib` in the child process's search
path. It requires `CUDA0`, checks `--list-devices` for RTX5090, disables automatic
CPU fitting and requests all layers on GPU. This repair schedules only stages
that had never been reserved. Original CPU logs, reservations and invalid-runtime
receipts remain immutable. The corrected server logged the actual CUDA device
and substantial GPU memory use and produced task outputs. Exact pins, logs and
memory samples are external under SPQ06's `pilot-1.0.0`.

For a different RTX, record its actual compute capability and supported toolkit;
do not carry the RTX5090 architecture flag over without checking the hardware.
