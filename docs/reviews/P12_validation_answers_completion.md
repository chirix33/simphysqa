# P12 selected-checkpoint validation answer export — 29 September 2026

The user requested a replay of today's trained checkpoints to access questions,
model predictions and correct answers. This separate local export replays only
the validation-selected models; it does not train, select another checkpoint,
run local language models, open confirmation outcomes or use paid providers.

Checkout: `main`, `248575fd500947edd325836e636aebe41f9f65d0`. Existing uncommitted
work is preserved. Only a new export, this report, a decision note and an appended
progress entry were added for this side-conversation request.

## Access

- [Searchable answer viewer](artifacts/P12_validation_answers/answers.html)
- [All question/prediction/reference records](artifacts/P12_validation_answers/questions-predictions-references.jsonl)
- [Verification summary](artifacts/P12_validation_answers/summary.json)
- Raw predictions and full augmented trajectories: `artifacts/P12_validation_answers/predictions/<domain>/<sample_id>.json`.

The HTML viewer is self-contained and about 39 MB. Open it in a browser; filter by
domain or complete correctness, or search by sample ID/question. It displays the
first 100 matches. Expand a question for its prediction, reference, error,
tolerance, supported status and reason. Full public inputs are expandable.
The JSONL contains all 1,336 questions and is suitable for independent analysis.
These are numerical/readout answers, not generated LLM prose.

## Execution and checks

Fresh persisted cap: 1,200 seconds, at most 1,336 attempts, no retries or network.
Inference completed in 144.910 seconds using two CPU threads and the original
torch 2.7.1+cu128 WSL environment. Selected updates: driving 781, arm 4982,
objects 508, tether 508. Every checkpoint, frozen numerical source file and
context cache was checked against its recorded identity. A process audit guard
blocked reference/confirmation/credential access and networking during inference.
Reference answers were joined in a separate reporting process afterward.

All **1,336 replayed typed evaluation results exactly match** the saved historical
selected-checkpoint results. Complete successes: driving 0/148, arm 0/388,
objects 0/400, tether 19/400. Zero runtime failures, 90,540 solves and 362,160
field evaluations. Original tolerances and unsupported-target accounting remain
unchanged. The HTML JavaScript passed a Node VM check of execution, total count,
domain/status filtering, sample-ID search and answer table rendering.

Commands run with the original WSL core Python, `-B`:

```text
docs/reviews/artifacts/P12_validation_answers/replay.py infer
docs/reviews/artifacts/P12_validation_answers/replay.py report
```

Do not rerun these commands to overwrite the export. Files use exclusive creation;
completed inference requests are identity-checked and skipped, and interrupted
attempts are not automatically retried. The persisted deadline is not renewed.

No old-vs-new checkpoint comparison or end-of-pass-10 replay was performed:
this export corresponds to the four selected models discussed with the user.
