# Development rehearsal commands and main prerequisites

All answering commands below require explicit development scope; the old executed ledger is exhausted in eligible stage attempts and must not be recreated to retry it.

Set `PYTHONDONTWRITEBYTECODE=1` before starting Python, including WSL and all portable adapters. Frozen packages reject added bytecode/cache files. Configure interpreter/cache/snapshot/device explicitly; preserve pinned condition settings.

```powershell
python -m unittest test_development_execution test_execution_readiness test_spq06 test_spq06_execution test_spq06_main test_spq06_analysis -v
python -m simphysqa.development_execution prepare-package --proposal PROPOSAL --main-package SEALED_MAIN_PUBLIC --output NEW_PUBLIC_ROOT
python -m simphysqa.development_execution validate --package NEW_PUBLIC_ROOT
python -m simphysqa.development_runtime --package PUBLIC_ROOT --condition CID --representation enriched --bindings BINDINGS --executor Ashraf --output NEW_QUAL_ROOT
python -m simphysqa.development_execution init --ledger NEW_DEV_LEDGER --package PUBLIC_ROOT
python -m simphysqa.development_execution issue --ledger DEV_LEDGER --executor Ashraf --shard CID--enriched --output NEW_ASSIGNMENT
python -m simphysqa.development_execution approve --ledger DEV_LEDGER --receipt QUAL_RECEIPT
python -m simphysqa.development_execution pending --ledger DEV_LEDGER --executor Ashraf --assignment ASSIGNMENT_ID
python -m simphysqa.development_execution prepare-job --ledger DEV_LEDGER --executor Ashraf --assignment ASSIGNMENT_ID --qualification QUAL_SHA --keys EXPLICIT_KEYS_JSON --bindings BINDINGS --output NEW_JOB
python PUBLIC_ROOT/procedures/development_execution.py launch --package PUBLIC_ROOT --job NEW_JOB --authorize-development
python -m simphysqa.development_execution export-return --job JOB --output NEW_RETURN
python -m simphysqa.development_execution import --ledger DEV_LEDGER --source RETURN --output EXCLUSIVE_IMPORT_ROOT
python -m simphysqa.development_execution route --ledger DEV_LEDGER --key ACTUAL_INITIAL_KEY --pilot ORGANIZER_PILOT --output NEW_ROUTE
python -m simphysqa.development_execution analyse --ledger DEV_LEDGER --pilot ORGANIZER_PILOT --output NEW_PRIVATE_ANALYSIS
```

These templates describe a newly authorized scope, not permission to create another ledger for the same reserved attempts. The actual run was organized by archived `development-src/manage_rehearsal.py`: prepare; qualify each named shard; run stage1; then run only supported stage2. Exact WSL argument arrays/logs are in the delivery commands index. Startup-only qualification used `development-src/run_startup_repair.py`, a 600s process ticket, zero keys and zero answering calls. It was not a failed-stage retry.

Device binding: Transformers supports the exact UUID binding. Pinned vLLM 0.11 requires numeric CUDA visibility; configure `cuda_visible_devices:"0"` only after the current physical index/UUID and Torch-selected UUID both match `device_uuid`. New runtime preflight constructs the exact vLLM model configuration before stage reservation. It does not load answering weights. Loading uses a separately bounded process. Do not change quantization to awq_marlin; the frozen configuration explicitly uses awq.

Future main procedure (NOT executable authorization): use a separately versioned MAIN package with cache/index fix backported and main task-qualified receipts, then the existing main coordinator's init/issue/prepare-job/launch/export/import/route/analyse operations. Main launcher still requires main authorization; do not use it for rehearsal. Current sealed main1.0.0 adapter has the observed HF symlink/UUID limitations and must not be launched unmodified. All source requests/selected identities/scientific settings stay unchanged during that backport. Main rejects development envelopes; startup-only receipts are never model answers.

Ashraf's planned future shard filter is qwen3_8b_direct--enriched, qwen3_8b_thinking--enriched, llama31_8b_direct--enriched, llama31_8b_cot--enriched, qwen3_32b_awq_off--enriched, qwen3_32b_awq_on--enriched, qwen3_8b_direct--structured_only, qwen3_32b_awq_on--structured_only. No main assignments/reservations have been issued. Use one organizer ledger for both machines and aggregate172800s, never independent per-machine ledgers. Each condition/representation covers all 200 frozen items; main uncertainty/endpoints remain unchanged.
