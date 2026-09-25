# Stage 7/P06 custom baselines

Status: **complete for implementation and bounded correctness validation**.
Longest-selected-input GPU qualification, independent fits/resume, fresh-process
generation and failure-preserving typed evaluation are complete. This is not a
trained benchmark-performance result: generated answers fail after two updates.
Branch `full-phi-jepa-from-dataset`, starting HEAD
`7f2553ca6591301de588bd3362e72838354169a0`; changes remain uncommitted. No push,
publication, full study, or primary Phi-JEPA contract change.

## Implemented method and boundaries

The [decision ledger](../decisions/P06_custom_baselines.md) records exact user
approvals, notebook/publisher hashes, method table, target/transport policies,
shared T5 teacher/student backbone, fixed teacher projection, and post-answer EOS
alignment. Independent modules are in `src/phi_jepa/baselines/custom_t5.py`,
`custom_io.py`, `custom_checkpoint.py`, and `t5_memory.py`; explicit preparation,
bounded execution, evaluation and evidence collection are separate CLI tools.

The frozen publisher model is Flan-T5-small revision
`0fc9ddf78a1e988dac52e2dac162b0ede4fd74ab`; seven downloaded files total
311,089,056 bytes. Separate native environments have pinned dependency lock files.
Public Q/C and existing enrichment are complete, with exact reversible tokenizer
round trips and no unknown/truncated tokens in the eight selected contexts.
Their input lengths are 10,107–22,323; selected training teacher targets 425–1,025,
student targets 394–994. This is bounded-selection qualification, not a claim that
the entire release fits. No private reference is opened by generation.

Actual tether teacher EOS label index is 553, student index 522 (zero based).
The shifted decoder input at each EOS-prediction index is the preceding final
serialized-output token, `Q`, ending the reversible newline escape. There is no
padding or missing-EOS substitution. CPU tests establish absent alignment gradients
on the teacher graph, nonzero student backbone/projection gradients, and retained
teacher CE gradients on the notebook's shared backbone. Fixed teacher projection
is absent from optimizers and saved/reloaded unchanged.

## Actual bounded GPU evidence

RTX 5090, FP32 parameters/BF16 autocast, microbatch one, query blocks of 512,
gradient checkpointing, seed 11. One longest-context qualification per final method
and two training updates on one tether training question, disjoint from the same
held-out tether question used in Stages 3–6. Qualification does not update weights.

| Measurement | Coconut-inspired | CODI-inspired |
| --- | ---: | ---: |
| Parameters | 79,858,560 | 79,859,584 |
| Trainable parameters | 79,858,560 | 79,595,904 |
| Longest selected context | 22,323 tokens | 22,323 tokens |
| Qualification seconds | 28.713 | 55.345 |
| Qualification peak allocated bytes | 2,856,586,752 | 3,888,676,864 |
| Fit updates | 2 | 2 |
| Fit seconds, including checkpoint/resume | 16.237 | 25.031 |
| Fit peak allocated bytes | 2,414,692,352 | 2,959,402,496 |
| First / second pre-update total loss | 8.863120 / 9.448321 | 12.259123 / 4.365937 |

Both fits loaded the actual checkpoint after update one before update two. Coconut
loss increased; no successful-fitting claim is inferred. Different objective
values are not comparable performance metrics. CODI student-projection clipped
gradient norms were 0.002569 and 0.030233; fixed teacher projection remained exactly
unchanged. Adam state, all parameters, losses and clipped gradients stayed finite.
The final checkpoint is selected by the predetermined update cap, without held-out
tuning. Full numerical forecast metrics do not exist for these generative models;
shared typed answer metrics are the common comparison.

Fresh-process Coconut generation took 6.222 seconds overall (peak allocated
892,358,656 bytes), with two calls, 20,216 input tokens and 329 generated tokens.
Both outputs failed typed JSON parsing. CODI generation took 51.946 seconds overall
(peak allocated 892,379,648 bytes): four unique calls, 40,432 input tokens and
8,192 generated tokens. Both student and teacher reached the 2,048-token cap
without EOS on each question. Original token IDs are preserved for every failure.

All three reported conditions (Coconut, primary CODI student-only, separate hybrid)
have **0/1 complete answers and 0/4 valid targets on training and on validation**.
Hybrid fallback triggers on both questions (100%), but neither generated teacher
label is valid, so successful fallback usage is 0/2. Hybrid branch time is 24.356
seconds for training and 24.436 for validation, with two model calls per question;
student generations are physically reused across the paired conditions. These
failures remain in every denominator. No correctness-based fallback, private-label
repair, parser weakening, silent token extension or full training was attempted.

Final-profile logical work: six training/qualification calls comprising nine
teacher/student forward graphs and six backward calls, four optimizer updates,
and six unique generation calls (60,648 input / 8,521 generated tokens). Checkpoint
recomputation is included in measured time, not misreported as additional independent
examples. The abandoned eager forward is an additional attempted call with no
backward/update. There were no API calls in Stage 7; no GPU-dollar cost is invented.

## Failures and engineering changes

Initial eager Coconut attention did not complete its first forward pass within
the shortened approximately 600-second diagnostic cap. nvidia-smi observed
31,726 MiB used; exact PyTorch peak was unavailable after termination. This is a
timeout, not a claimed CUDA OOM. No backward/update completed. The failed native
`p06-correctness-01` report is preserved. Equivalent full-key query-block attention
was then validated against eager multi-layer outputs and every parameter gradient;
it changes memory/recomputation and dropout RNG consumption, not weights, token
coverage, relative positions, attention connectivity or objectives. Final evidence
is under `p06-correctness-02`. See the ledger for exact policy and caps.

A draft notebook hash was incorrect; verification against the original P02a hash
manifest corrected the configuration. Notebook bytes were unchanged. Old preparation
and abandoned-attempt config digests remain preserved and explicitly distinguished.

An over-broad core-environment regression invocation ran 164 tests and reported
15 errors/3 skips because historical simulation tests require the separate
simulation environment (`jsonschema`, `psutil`, `mujoco`). No simulation code was
changed or dependencies injected into the pinned model environments. The appropriate
model/handoff suite passed **118 tests in 10.939 s**; see
[test log](artifacts/P06/tests-model-regression-final.log). The failed broad log
is retained as `artifacts/P06/tests-core.log`. Handoff validation passed nine
preserved source hashes, four prompt strings and installed Markdown links;
`git diff --check` passed (existing line-ending warnings only).

## Reproduction and artifacts

Run from the repository in WSL Ubuntu-24.04, using each method's own
`/home/aashraf/phi-jepa/.venvs/phi-{coconut,codi}-custom/bin/python`.

```text
bash tools/setup_p06_custom.sh
python tools/download_p06_model.py --cache-dir /home/aashraf/phi-jepa/model-cache --output /home/aashraf/phi-jepa/p06-profile/model-download.json
python tools/prepare_p06.py --profile /home/aashraf/phi-jepa/p02b-profile --output /home/aashraf/phi-jepa/p06-profile --cache-dir /home/aashraf/phi-jepa/model-cache
python tools/launch_p06_bounded.py --mode qualify --method METHOD --profile /home/aashraf/phi-jepa/p06-profile --output /home/aashraf/phi-jepa/p06-correctness-02/METHOD --cache-dir /home/aashraf/phi-jepa/model-cache
python tools/launch_p06_bounded.py --mode fit --method METHOD --profile /home/aashraf/phi-jepa/p06-profile --output /home/aashraf/phi-jepa/p06-correctness-02/METHOD --cache-dir /home/aashraf/phi-jepa/model-cache
python tools/launch_p06_bounded.py --mode infer --method METHOD --profile /home/aashraf/phi-jepa/p06-profile --output /home/aashraf/phi-jepa/p06-correctness-02/METHOD --cache-dir /home/aashraf/phi-jepa/model-cache
python tools/evaluate_p06.py --run /home/aashraf/phi-jepa/p06-correctness-02 --profile /home/aashraf/phi-jepa/p06-profile
python tools/collect_p06_evidence.py --run /home/aashraf/phi-jepa/p06-correctness-02 --profile /home/aashraf/phi-jepa/p06-profile
CUDA_VISIBLE_DEVICES= PYTHONPATH=src python -m unittest discover -s tests -p 'test_p*.py' -v
```

METHOD is `coconut_inspired_t5_gru` or `codi_inspired_t5_distillation`.
The launcher refuses to overwrite an existing attempt. Native weights and complete
public/target preparations stay outside Git; compact reports and hashes belong in
`docs/reviews/artifacts/P06`. No API calls or new enrichment are needed in this phase.

An initial evaluator invocation read the first completed generation row while the
second row was still running. The finalized evaluator now refuses an unfinished
attempt and was rerun after both processes exited; final evidence includes both
questions and both fallback triggers. No generation was repeated for this correction.

Next: Stage 8 bounded existing-profile evidence package. Full-study expansion,
all-release token qualification and full supervised baseline training remain
separate work. Negative answer results are preserved rather than made an acceptance
gate demanding a desired outcome.
