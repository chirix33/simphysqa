# Focused repository cleanup — 9 October 2026

User-authorized cleanup and branch publication only; the user will merge PR #3.
Do not merge in this session. No SPQ06, scientific pipeline change or
experimental work. Branch `simphysqa-repo-cleanup` starts at current main/verified
GitHub main `ccfde9ee904ac5efdc330ba707ebf54843ffb135`, not a historical milestone.
All three checkouts were clean. Prefer and reuse the existing main checkout;
leave original archive and simphysqa-spq05 worktrees unchanged.

## Inventory before deletion

1. Retain all active src/simphysqa modules, five-family schemas, annotation/event/
   association/answer evidence, audit extraction/forms/import/sampling, evaluation
   interfaces and nine-condition plan; all existing relevant tests/scripts.
2. Remove 39 obsolete method configs/environment locks, two method setup launchers,
   four superseded root files, six execution guides, 27 method decisions, 12 method
   architecture docs, 16 phase prompts, four method reference commentaries and
   46 method reports. Remove 9,558 method-result files and 11 CLI outputs from Git
   tracking while preserving local bytes. Total: 9,725 paths.
3. Retain all exact SPQ prompt/procedure/payload archives and per-file mappings,
   accepted SPQ evidence, PDS generation/admission/freeze receipts, licensing,
   citations, original adopted prompt/schema assets and source distribution manifests.
   Verify archival `7dd4a64` and published pre-cleanup `ccfde9e` for recovery.
4. Investigate simulator namespace, extracted registries, frozen generation paths,
   quadruped exclusions and SPQ01 provider antecedents by actual imports/resource
   reads/test dependencies. All are retained for the specific reasons in
   [history.md](../history.md). No dependency uncertainty justifies another deletion.

Dependency inspection found no runtime imports of removed method material; prior
SPQ00 removed the method implementation already. Runtime and test source bytes,
pyproject dependencies/entry points and all scientific configs/schemas stay exact.
No scientific values, controllers, IDs, splits, answers, tolerances, cutoffs or
conclusions change. Only the path-example template becomes portable.

Historical method results use index-only removal plus specific ignore entries.
No git clean, reset, worktree removal or recursive filesystem deletion. Every
removed Git blob matches the archive; verify local preserved bytes after cleanup.
Keep two small old configs and one provider ledger because SPQ01 explicitly cites
them. Original adopted assets remain exact; no cosmetic payload rewrites.

Replace root/active documentation with current authority, setup, privacy and
branch → validation → review → merge workflow. Preserve completed-stage reports as
dated receipts. Repair the legacy source-index links to immutable historical URLs
and label optional absent source documents; preserve original source manifest.
SPQ05's no-calibration protocol/current verified delivery supersedes old 20/140
planning; human/answering results remain pending. SPQ06 is not started.

Validation and final integration receipts: [cleanup completion](../reviews/repo_cleanup_completion.md).
