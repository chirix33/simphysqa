# Dataset and generation-code licensing

Copyright (c) 2026 Kaushik Roy.

The user confirmed the rights-holder name and authority to grant the scoped
licenses, including applicable co-owner or institutional rights, on 24 September
2026. The exact confirmation is recorded in `licenses/decision.json`.

- The Phi-JEPA Four-Domain Research Dataset and project-authored scene/model
  assets are licensed under **CC BY 4.0**; see `licenses/CC-BY-4.0.txt` and
  `licenses/ATTRIBUTION.md`.
- Project-authored generation code is licensed under **MIT**; see
  `licenses/MIT-generation.txt`.
- Exact file coverage and exclusions are in `licenses/scope.json`. This is not
  a blanket license for the entire repository. Authored model definitions in
  generator files are also offered as CC BY 4.0 assets as specified there.
- Third-party notices and preserved adopted references retain their original
  terms; see `licenses/THIRD_PARTY.md` and `licenses/third-party/`. They are not
  relicensed by these grants. `MIT-template.txt` is a retained standard-text
  reference; `MIT-generation.txt` is the applicable copyright notice.

The dataset scope includes inputs, references, labels, evaluator metadata and
explicitly quarantined failures. Private-for-evaluation references remain separate
from model inputs even when distributed publicly for research. Failed examples
are never silently admitted as training data.

Licensing is finalized for this scope. Production generation remains disabled,
and no dataset publication, public download URL or DOI is claimed. The license
authorization does not launch generation, publish the repository, or extend the
grant to excluded third-party or unrelated materials.
