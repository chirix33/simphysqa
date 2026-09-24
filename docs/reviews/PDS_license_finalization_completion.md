# License finalization — 24 September 2026

Branch `dataset-prep`. User confirmed **Kaushik Roy** as rights-holder and answered
**yes** to the explicit authority question for scoped CC BY 4.0 dataset/assets
and MIT generation code, including applicable co-owner/institutional rights.
This is recorded user authorization, not an independent ownership investigation.

Authorization/notices/tooling commit: `9df13b4d715b8a0d367ebe023c763fdc418aa9bb`.
The following freeze commit binds the final legal artifacts and this report.

Finalized `LICENSE.md`, `licenses/decision.json`, `MIT-generation.txt`,
`ATTRIBUTION.md`, `scope.json`, third-party boundary wording and current inventory
licensing metadata. Original third-party notices and standard license texts are
unchanged. The four frozen domain manifests now record `validated_frozen`,
`asset_license_status=granted`, CC-BY-4.0 and rights-holder Kaushik Roy, with no
remaining domain licensing gate. The configuration records CC-BY-4.0 and MIT.

The freeze helper now verifies a recorded grant before carrying it into a freeze;
it retains pending status when authorization is absent. Inventory refresh also
respects that distinction. Earlier reports describe the historical pending state;
the [authorization decision](../decisions/License_authorization.md) supersedes it.

Verification actually executed:

- WSL targeted release/freeze suite: **10 tests passed in 2.264 seconds**, including
  a confirmed-grant test that leaves generation disabled.
- WSL freeze preparation/verification passed, including installed runtime pins.
- Windows actual grant and freeze verification passed (runtime check omitted there).
- Compared with `12ded02`: the complete generation contract, 24 partition plans
  and all 480 historical asset entries are unchanged. Sampling, 6,800-attempt
  budget, thresholds, rejection policy and numeric/model-data contract are intact.
- All four actual frozen domain manifests have matching granted status, named
  rights-holder and cleared licensing gates. `git diff --check` passed after
  normalizing the authored decision JSON to LF; license source texts were not edited.

**Licensing is resolved for the documented scope. Production remains disabled**
(`final_generation_enabled=false`). No simulator runs, production generation,
quadruped experiments, training, push or publication occurred. No further licensing
input is needed. The next operational step requires a request to start generation;
the existing command and runtime/storage estimates remain in the preparation report.
