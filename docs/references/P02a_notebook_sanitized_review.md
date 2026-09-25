# Sanitized notebook implementation review — P02a

Source: local `Phi_JEPA_Final_+_Baselines.ipynb`, original hash recorded in
`docs/reviews/artifacts/P02a/preserved-source-hashes.json`. This reference contains
no notebook credentials, outputs, metadata or provider payloads. No cell was
executed and no notebook was copied into Git. This review is separately hashed
in P02a's final artifact inventory.

The notebook's adjacent-state direction and custom baselines are intentional
accepted choices. The following implementation mechanics are separate issues:

- Cell 13's nested numerical extraction tests `isinstance(value, (int, float))`:
  Python Booleans pass this test. Measurement vectors are skipped by its scalar
  branch. Keys built by joining path components can collide.
- Cells 23/26/29 use `state_dict.get(key, 0.0)` for absent numeric fields. Missing
  information is thereby replaced with a physical zero. Cell 34 similarly defaults
  missing timestamps to zero. The integration reader instead fails explicitly.
- Cells 5/50's path-only sanitizer retains values at existing paths without
  checking whether the original facts changed. Scalar items in lists can bypass
  its dictionary-leaf filtering. Dot-joined paths and generic list markers are
  insufficient provenance. It can also replace newly introduced leaf text with
  `unknown` without a declared enrichment role.

P02a tests cover missing/null rejection, vector preservation, Boolean exclusion,
collision-free keys, duplicate/unit/frame errors, unchanged original facts and
typed separate enrichment notes. These are bounded offline mechanics checks,
not claims of upstream baseline failures or empirical neural performance.

No architecture inference is made from notebook credentials or outputs. Upstream
CoConuT/CODI bug reports remain user-reported; this phase did not reproduce them.
