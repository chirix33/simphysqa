# Prepared licensing — not yet an authorized grant

The intended public dataset is the **Phi-JEPA Four-Domain Research Dataset**.
The user selected CC BY 4.0 for the dataset and project-authored scene/model
assets, and MIT for project-authored generation code. The exact rights-holder
name and confirmation of authority are still missing. No ownership is inferred
from Git authorship, repository access, or the phrase “Creative Commons”.

Until `licenses/decision.json` records that confirmation, the texts below are
prepared for review only. No project license grant is asserted by their presence.

- `licenses/CC-BY-4.0.txt`: unmodified standard license text, intended for the
  generated dataset and authored MJCF/URDF/JSON model descriptions.
- `licenses/MIT-generation.txt`: prepared MIT notice with an explicit unresolved
  rights-holder field. Applies only to the files enumerated in `licenses/scope.json`
  once authorized; this is not a blanket license for the repository.
- `licenses/ATTRIBUTION.md`: dataset attribution and reuse notice template.
- `licenses/THIRD_PARTY.md` and `licenses/third-party/`: separate original notices
  and provenance. No third-party material is relicensed under our proposed grants.

The full dataset includes inputs, private-for-evaluation references, metadata,
and numerical labels. “Private” describes the model-evaluation boundary, not a
promise to withhold reference files from a future public research download.
Quarantined failures remain explicitly rejected, never admitted training examples.
No dataset download, DOI, publication or ownership grant is claimed yet.

Internal generation and public redistribution are distinct. Inspection found no
third-party scene assets or concrete scene-asset restriction preventing internal
generation. It did not establish ownership or a permission grant. The existing
project policy gates `generate` on redistribution licensing; that policy remains
in place. Production generation and public release are both still disabled.
