# Complement execution commands and provenance

These are the actual bounded procedures; execution is already performed. Do not rerun
reserved keys. The controller selects only never-reserved keys and enforces the
approved cumulative ledger allocations and result-import cutoff. A rerun command
does not authorize extra attempts, later cutoffs or collaborator inference.

Use the existing CPU interpreter and immutable source paths listed below. WSL/GPU
bindings, pinned environments and fresh preflight receipts are saved in the run root.

```powershell
$spqCpu = "C:/Users/aashraf/.codex/visualizations/2026/10/09/01a12258-7d16-7ac3-861b-c7326aff811e/cpu-venv/Scripts/python.exe"
$env:PYTHONPATH = "C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-live-src-1.0.1/src"
& $spqCpu "C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-live-src-1.0.1/complement_run.py" run
$env:PYTHONPATH = "C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-analysis-src-1.0.1/src"
& $spqCpu "C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-analysis-src-1.0.1/finish_complement.py" --output "C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-analysis-1.0.1"
```

The analysis output uses exclusive creation: the completed root must not be overwritten. The analysis routine invokes no models. Immutable return export/import, request validation, central scoring and actual-history routing are called by the controller, with exact procedure hashes in the execution archive. Final settlement and manifests are linked in the completion review.
