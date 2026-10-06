# Foundation merge-review decisions and historical preservation

Preparation starts at52f47ace928d339239a262836cff67818d6d68da on simphysqa-naacl.
Main remains7dd4a64e90cfb18be743503ac8345cabf2f6e28b. This document proposes a
later preservation/merge sequence; it does not authorize or perform a merge/push.

1. Preserve the original main tip and its reachable history. The existing original
   checkout at `C:/Users/aashraf/Desktop/Work/phi-jepa/phi-jepa` is unchanged and
   retains ignored data/results. The separate SimPhysQA worktree is
   `C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa`.
2. Before any later authorized merge, recheck both statuses and pin the old tip with
   an explicitly reviewed archival branch/tag (proposed name `archive/phi-jepa-pre-simphysqa`).
   Optional `git bundle` of reachable historical commits is an independent backup;
   ignored data/weights are not in a bundle. No archival ref/bundle was created by
   this preparation. Do not rewrite history or delete the historical checkout.
3. Keep all external release/data/run/annotation manifests and original artifact
   roots in place. The foundation registry supplies aliases/hashes rather than
   moving/copying large datasets. Preserve exact bytes and private permissions.
   A future public dataset release requires its own provenance/privacy/licensing
   review and storage plan; the development packets are organizer-private.
4. The complete accepted diff contains276 inventoried unrelated source/test/tool
   deletions and five byte-identical simulator-test relocations. Main/history retain
   all original blobs; no generated dataset was deleted. The source compatibility
   namespace retains simulator imports only. Freeze/qualify new generation source
   separately before any full-release regeneration.
5. Root instructions/README now lead with the final five-family authority and label
   older stage text historical. Original dated scientific findings remain unchanged.
   The sealed prompt archive1.0.7 is not regenerated; current scope is reconciled in
   the foundation/version matrix and index. The direct build packaging omission
   for clarification.schema.json is fixed without changing scientific schemas.
6. The supported reproducibility target is an editable source installation. A fresh
   isolated CPU venv was reconstructed from seven pinned local distributions and
   installed through actual pip editable build with no index. This does not verify
   online resolution, optional simulator/audit runtimes or standalone wheel assets.
   Audit and simulator numpy pins conflict; use separate environments, no repinning.

Before a later merge: review the proposed body, accepted diff ledger, new preparation
diff, preservation receipts and outstanding scope. Resolve scientific release/audit
and model qualification decisions separately; do not hide them behind a software
test pass. This branch is prepared for code/document review, not claimed to contain
empirical answering/human quality results. No mandatory generation approval gate.
