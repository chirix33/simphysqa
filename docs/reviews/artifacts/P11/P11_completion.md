# P11 completion report

Bounded execution finished; generation/learning failures retained.

This is not a claim of convergence, superior performance, calibrated OOD recognition or four-domain readiness. See the [measured benchmark](P11_benchmark_report.md), [frozen decision](../decisions/P11_deadline_study.md), [commands](../P11_pipeline.md) and [export manifest](artifacts/P11/manifest.json).

| Cohort | Method | Complete / questions | Typed valid / questions | Unsupported targets | Failed targets |
| --- | --- | --- | --- | --- | --- |
| main | Phi-JEPA | 9/48 | 48/48 | 26 | 0 |
| main | gpt-5.6-sol direct | 22/48 | 36/48 | 0 | 70 |
| appendix | Phi-JEPA | 0/16 | 16/16 | 8 | 0 |
| appendix | custom Coconut | 0/16 | 1/16 | 0 | 77 |
| appendix | custom CODI student | 0/16 | 4/16 | 0 | 68 |

Population: main 48 training + eight separate selection + 12 original test_id trajectories per domain; appendix 16 training + four test trajectories per domain, nested in the frozen main cohort. One outcome-blind earliest-horizon question per trajectory and seed 11. Main test population is 48 questions; appendix test population is 16 questions for each of its three methods. All failures and unsupported components remain in complete-answer denominators.

Main numerical models were freshly trained per accepted domain layout. Selection uses only the separate validation scenarios at predefined 5k/10k/20k milestones. Appendix Phi-JEPA is separately initialized/trained on appendix training trajectories and uses the fixed final 20k checkpoint. Custom Coconut and CODI each use fresh pinned Flan-T5-small initialization, 64 trajectory questions and two complete passes (128 updates), with final-checkpoint selection. The timing probe used 16 discarded updates across separate models and is charged as preparation, not counted as study exposure.

Resource snapshot: GPU worker 120.115 minutes; CPU worker wall 37.913 minutes; 344 provider attempts; 3,997,538 input and 200,708 output tokens; USD 24.001850 conservative metered estimate. Local/remote elapsed intervals overlap. Exact ledger, operation logs, per-condition costs, peaks and caps are exported; usage estimates are not invoices. Reporting work after the snapshot is retained in operation records.

Implementation changes: tools/p11_* provide the frozen-cohort preparation, timing, training, checkpoint selection, reference-free inference, separate evaluation, assessment, strict generation diagnostics, deadline supervision and result export. openai_answer.py adds an explicit public-only direct_prediction Boolean policy; the default readout policy and historical caches remain unchanged. The new prompt asset identifies this direct condition. Primary model/solver/objective source was not changed for P11.

Verification: 37 targeted offline tests passed (test_p11, test_p10, test_p04a). All P11 entrypoints compiled. Saved-artifact verification status: passed_available_artifacts; its detailed checks validate scenario separation, pair exposure, checkpoint integrity/selection, complete text passes and retained denominators. Mock/offline tests are not counted as model accuracy.

Remaining issues:

- Missing evidence: broader-sample and multi-seed generalization, convergence, robustness of training/checkpoint choices, and controlled OOD detection/clarification efficacy. This exploratory appendix has limited exposure and may not generalize to larger samples.
- Measured learning/generation limitations: see per-domain numerical/hold-last errors, typed-output failures, output-cap/EOS diagnostics and strict complete-answer results. A lower teacher-forced loss does not guarantee valid autonomous generation; more updates are not assumed to solve failures.
- Unsupported capability: Phi-JEPA stable_stack/support_lost lack required predictive contact evidence. Required typed assessment contracts/V1 components remain missing; partial familiarity is not a calibrated alarm.
- Deferred by the frozen deadline scope: new ablation retraining, custom hybrid/teacher evaluation, sealed OOD evaluation, calibration and human-reviewed clarification evaluation. Existing P09 clarification remains a separate implemented condition.
- Scientific decisions: any new contact mechanism/head, loss/state-layout change, schema repair, learned EBM, inference optimization or calibrated OOD/clarification connection needs separate authorization. No such change was made to meet the deadline.

Source/provenance: branch full-phi-jepa-from-dataset, starting/current base commit d2e9fe3daba63cc0b5295fa108177628c4319098. P10 was committed by the user before P11; its original run-time reports and checkpoints were preserved. P11 changes are local and uncommitted; no push or merge was performed. Each execution stage has a source/configuration identity, archived blobs and exact checkpoint hashes. The native run is /home/aashraf/phi-jepa/p11-tonight-01; the export contains source-evidence.zip and resumable checkpoint pointers.

No further decision was needed to execute the settled frozen study. Larger-scale comparisons remain future work and are not activated by this report.

Delivery verification: all exported file hashes and source blobs matched. Recorded final worker time including reporting/export: 120.115 GPU minutes and 39.137 CPU worker-wall minutes. Final elapsed time 147.376 minutes. See [closure accounting](artifacts/P11/closure.json). The deadline was met.
