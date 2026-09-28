# Gold answers in answer-pipeline outputs

Branch: `full-phi-jepa-from-dataset`; base HEAD
`d2e9fe3daba63cc0b5295fa108177628c4319098`. Local uncommitted follow-up; existing
staged changes and historical P10/P11 evidence are preserved. No push occurred.

The user's requested gold answers now appear in the standard `answer_pipeline`
report and terminal output, beside each method's typed predictions. Each row
identifies the target, query kind/time, unit and frame. Original float precision,
vector components and Boolean types are preserved. Unsupported predictions and
failed generations remain explicit; no missing prediction is replaced by gold.

The separately launched evaluator exports
`evaluation/private/gold_answers.json`, keyed by sample ID. It includes only
requested typed reference values and their bindings, tolerances, public-input
identity and reference-file provenance. Future reference trajectories are not
copied. The existing deployment guard rejects paths containing `private`.
Prompts, provider requests, model outputs and scoring rules are unchanged.
`--skip-evaluation` leaves gold export pending. Running `evaluate --output DIR`
adds comparisons to an existing manual run without new inference or paid calls.

Changed files: `tools/answer_pipeline.py`, `tests/test_answer_pipeline.py`,
`docs/Run_answers_WSL.md`, `docs/PROGRESS.md`, `docs/decisions/Answer_runner.md`,
and this report/evidence folder.

Verification completed in WSL:

```bash
python -m unittest discover -s tests -p test_answer_pipeline.py -v
python tools/answer_pipeline.py run --domains all --questions-per-domain 1 \
  --max-api-usd 0 --vanilla-answers cache \
  --output /home/aashraf/phi-jepa/manual-outputs/gold-answer-check-01
python tools/answer_pipeline.py evaluate \
  --output /home/aashraf/phi-jepa/manual-outputs/gold-answer-check-01
```

All **11 targeted tests passed**, including three new checks for typed gold
fidelity, reference identity, failure/unsupported rendering, and evaluator-only
export without generation or answer mutation. The four-domain end-to-end check
exported **four gold answers with 20 target components** and four comparison
tables. Re-evaluation preserved all **eight answer JSON files byte-for-byte**.
New paid requests, tokens and cost were zero; no training was run. Existing
cached-answer failures remain in the output and denominator; the check is
`complete_with_failures`, not a new performance success claim.

See the [sample report](artifacts/Answer_runner_gold/report.md),
[typed gold](artifacts/Answer_runner_gold/evaluation/private/gold_answers.json),
and [verification record](artifacts/Answer_runner_gold/verification.json).
The source identity is preserved with the new evidence. No scientific policy
decision or unresolved implementation blocker is introduced by this change.
