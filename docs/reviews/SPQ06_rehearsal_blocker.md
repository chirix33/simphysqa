# SPQ06 rehearsal qualification blocker

- Phase/substep and status: implemented; partial actual development task qualification.15 reserved AWQ initials have no model responses; stage2 absent for AWQ and Llama CoT.
- Repository branch/commit and relevant paths: simphysqa-spq06, starting a1dd726; final receipt linked from the rehearsal report. development_execution.py / development_runtime.py; external development-rehearsal1.0.3 jobs/immutable returns.
- Expected behavior and source requirement: same five frozen train tasks, exact main representation, pinned settings, actual dialogue, single reserved scientific attempt, no automatic retry.
- Exact command/minimal reproducer: saved AWQ launch.json/command indices pass CUDA_VISIBLE_DEVICES=GPU-33a65a33-cb7a-f2f9-5697-93b058670d4b to pinned vLLM 0.11; its ModelConfig constructor fails before weights/answering.
- Observed behavior/sanitized error: ValueError invalid literal for int() with base10: GPU-33a65a33-cb7a-f2f9-5697-93b058670d4b. All 3 batches retained. Llama CoT requested_information:null is unroutable under the unchanged actual router.
- Environment: local WSL Ubuntu24.04, RTX5090/32607MiB, driver610.60; AWQ torch2.8.0/CUDA12.8/vLLM 0.11/transformers4.57.1/tokenizers0.22.1; exact official Qwen32 AWQ revision0499c3ac83fdef8810b907a23894ba91e95eddd8.
- Attempts/outcomes:3 failed startup workers, no scientific retries. Verified numeric index0/UUID mapping and exact ModelConfig; one52.562s startup-only load passed, zero answering calls.29 actual other-stage outputs imported, parsed/scored and token-verified.
- Confirmed root cause: vLLM integer visibility parser incompatible with the original UUID-only adapter. Cache symlink and bytecode-preflight issues were separately corrected/archived before answering. No model/quantization/prompt substitution.
- Impact: AWQ task/decode/timing and live continuation coverage remain unavailable despite successful load. The full updated48h forecast is not established.200/400 selection and historical forecast stay frozen.
- Option A/tradeoff: carry the preserved shortfall and require a separately scoped subsequent qualification disposition before AWQ main launch; no failed attempts are erased.
- Option B/tradeoff: keep main preparation frozen and postpone AWQ execution; do not silently drop conditions or change denominators/size.
- Recommended: retain all failed reservations, review the additive adapter/backport and obtain subsequent task-execution evidence only under explicit new scope; keep science unchanged.
- Smallest planner decision: disposition and explicitly bounded subsequent development qualification scope for the15 already-reserved failures, if completing task qualification is desired. No automatic request/retry is performed here.
- Evidence to close: exact revised-runtime task/decode/stop/history receipts and measured AWQ family/continuation timings, preserving historical failures and a feasible combined48h forecast.
