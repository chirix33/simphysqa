# Proposed broader tether pilot — not launched

This proposal follows the user's request for a concrete next budget. It is not
authorization to execute it and is not a full-study budget.

Select 32 existing training scenarios and eight distinct existing validation
scenarios from the frozen tethered-load release, seed 11. Freeze the exact IDs
before work; one deterministic question per scenario, preserving the existing
split groups. Use the first 20 post-cutoff adjacent transitions per training
question: 640 question-conditioned examples and physical transitions, 32 training
questions/scenarios, eight validation questions/scenarios. Retain the accepted
equal-per-transition weights, complete numerical blocks, primary 2d objective and
feedback. Do not introduce a new loss, normalization, head, teacher forcing at
autonomous evaluation, schema repair or undefined schema ablation.

| Component | Proposed hard cap |
| --- | --- |
| Primary, constant-context ODE, RNN, no_enrichment, no_text_conditioning | 1,000 updates and 10 CPU minutes each, whichever first; fixed seed/config; documented chronological RNN batches |
| LR | One least-squares fit to the frozen training pairs, 5 CPU minutes; unchanged seeded fixed P and rank reporting |
| Custom Coconut | 200 updates, microbatch one, 45 GPU minutes |
| Custom CODI | 200 updates, microbatch one, 90 GPU minutes, including teacher work |
| Frozen Qwen encoding, custom generation and diagnostics | 45 additional GPU minutes total, one GPU job at a time |
| Aggregate local budget | Three GPU hours; one CPU hour; 20 GB additional native artifacts; stop at any cap |
| Provider operations | At most 120 attempts including retries, 2,000,000 input tokens, 100,000 output tokens, and USD 15 usage-priced spend, whichever first |
| Decoding | Existing greedy settings and 2,048 new tokens; no automatic extension or answer repair |
| Tuning | No hyperparameter search; checkpoints at updates 50/100/200 for custom-model learning diagnostics, not repeated validation selection; final predeclared checkpoint reports all eight questions |

Measured basis: two-update fits including startup/checkpoint I/O took 16.24 seconds
for Coconut and 25.03 seconds for CODI on the 10,107-token tether input. Simple
linear extrapolation gives approximately 27 and 42 minutes for 200 updates,
respectively; these are rough planning figures, not throughput guarantees. The
45/90-minute caps leave headroom without declaring convergence. Per validation
question, both CODI branches at the token cap cost about 24.44 seconds together.
Longer-context qualification peaked at 2.86/3.89 GB allocated, while larger target
shapes/batches still require validation. Keep microbatch one and query blocks.

For the proposed 40 public contexts, allow up to 40 enrichment requests. Eight
validation questions across six numerical methods plus direct and reversed controls
require at most 64 answer requests; eight V1 judges add eight. The 120-attempt cap
leaves eight attempts for explicit retries. Reuse valid caches. The existing
17-call qualification total was USD 0.831996, but included different context sizes
and shared four-domain preparation. The USD 15 ceiling is a control limit, not a
price promise or extrapolated final-study bill. Record actual provider model IDs,
tokens, failures and usage-price basis again.

Before running: approve this scope, freeze deterministic scenario/question IDs and
train/validation iteration policy, and preflight complete target/input lengths.
Length failures stay explicit; no hidden field removal or target truncation.
The same parsed-target and EOS checks must pass before any quality interpretation.
Do not increase updates/limits automatically when outputs remain invalid.

Assessment stays partial/uncalibrated: eight validation scenarios do not meet the
recorded minimum of 20 separate calibration scenarios, and missing required typed
contracts remain unresolved. No threshold tuning is part of this proposal.

After this larger diagnostic, propose the final four-domain ID/OOD matrix and
separate budget. That work still needs all-release token/support audits, meaningful
independent training, validation-only checkpoint/calibration policy, multiple seeds
(candidate 11/22/33), scenario-grouped uncertainty, and explicit treatment of
stable_stack/support_lost and any other unsupported targets. Sealed test/OOD
results, convergence, method rankings and four-domain readiness remain pending.
