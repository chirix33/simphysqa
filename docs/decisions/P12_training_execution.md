# P12 authorized numerical execution — 29 September 2026

The user explicitly authorized the completed-context training-only proposal with
SHA-256 `13cc4b3cbe8578abe22ebe8faa0987b2de2b3309639bf5e7a9988f4e0542add3`.
This supersedes the preparation report's pending numerical authorization only.
The original proposal, preparation reports, checkpoints and other experiments
remain historical artifacts. No paper work, paid calls, push or merge is included.

The authorized copy changes only the three fields permitted by the existing
`require_training_authorization` mechanism: `training_enabled`,
`training_authorization`, and `authorized_proposal_sha256`. Its SHA-256 is
`985ee2c11bc0212275cac95620044ea7e4742fc90581edbacf31deace1aaec5c`.
Global `enabled` and `evaluation_enabled` remain false. The frozen numerical
implementation digest remains
`f22e7646a6f39ef74e84be0d10dd7b3935933721f625e4a897640485d91b9829`.

Proposal-time fields such as `training_started` and `executed_optimizer_updates`
are immutable snapshot metadata, not a live status ledger. Actual execution is
recorded in each domain's history, `complete.json`, and the separate execution
control directory; use `python tools/p12_training_report.py --status` for progress.

`tools/p12_training_execution.py` wraps the unchanged trainer. It runs driving,
robotic_arm, object_pushing_stacking and tethered_load sequentially, with a durable
14,400-second aggregate deadline, a conservative 3,600-second dispatch window
per domain (including its preflight), and the 16 GB aggregate artifact limit.
The trainer's own domain deadline, checkpoint reserve and integrity checks remain
in force. A stopped dispatch is not automatically retried or granted a new budget.
Preflight report destinations are redirected to the new execution directory;
the original proposal path and every bound input are unchanged. This preserves
the original preparation preflight and export without overwriting them.

The control directory is `/home/aashraf/phi-jepa/p12-training-execution-01`;
training artifacts stay in the approved
`/home/aashraf/phi-jepa/p12-expanded-study-seed11`. The launcher records its own
source hash separately; it does not regenerate the approved scientific proposal.
Existing unrelated answer-interface debugging files remain untouched.

The seed, population, equal-pair objective, batch size 256, ten passes plus the
documented final full-batch tails, checkpoint milestones, and validation-only
selection all remain fixed. No test outcomes or new model generation enter this run.

## Subsequent evaluation requirement

The latest user instruction requires four independently labeled direct-baseline
conditions: Qwen3-8B native thinking off, Qwen3-8B native thinking on, Llama-3.1-8B
direct answer, and **Llama-3.1-8B prompted CoT**. Llama CoT is a prompting condition,
not a native Qwen-style thinking switch. Its reasoning/final separation, output
budget, template and parser require independent qualification and freezing.

The old three-condition evaluation allowance is not authorization for these four
conditions. A future finalized 500-question evaluation would require 2,000 local
attempts before any retries, plus independently measured runtime bounds. The
current training proposal is not edited to incorporate that future evaluation.
Confirmation evaluation and all baseline generation remain disabled here.

## Execution outcome

All four fits completed sequentially in 3,270.541 seconds (54.51 minutes), without
a restart, retry, runtime failure or budget extension. Every domain completed ten
passes and ten validation sweeps. Total exposure was 17,742 updates / 4,541,952
pairs. Validation selected driving pass 3, arm pass 10, object pass 1 and tether
pass 1. All 255 checkpoint files passed hash verification, and selected deployment
models plus final optimizer/RNG states reloaded successfully. The completed-run
wrapper returned without additional optimizer updates when invoked again.

The frozen history writer emits blank separators that its strict incomplete-run
resume reader rejects. A read-only probe confirmed this nonblocking limitation.
No restart was needed; raw logs and the authorized source were preserved. Future
incomplete-run recovery requires explicit parser/budget reconciliation. This
finding is not a reason to silently replace the approved implementation.

Validation outcomes do not establish convergence or satisfactory task accuracy.
Unsupported contact targets remain explicit; the accepted state/readout contract
was not changed to improve scores. See the [completion report](../reviews/P12_training_completion.md).
