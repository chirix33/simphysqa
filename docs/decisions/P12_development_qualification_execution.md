# P12 development qualification execution — 30 September 2026

The user explicitly authorized the prepared 32-request development qualification,
including 4,096 total output tokens for Qwen thinking-on and Llama CoT. This is
authorization for the frozen development manifest only. The original disabled
proposals and preparation freeze are preserved; the separate native execution
root contains an authorized copy bound to their hashes.

The execution wrapper adds hard supervision, a durable nonrenewable ledger and
an observational token streamer. It imports the frozen prompt/schema/adapter/
decoder unchanged. Token logging changes neither logits nor stopping criteria;
its overhead is included in request runtime. Failed/interrupted attempts remain
counted and are not retried. No more than 32 requests and no more than the shared
7,200-second model window are allowed, including 1,440 seconds of setup/other
overhead. Request maxima remain 120/240 seconds and 1,024/4,096 tokens.

The supervisor and tests are separately source-hashed in the execution
authorization. Reference evaluation occurs only after generation closes, and
parses reference values only for the eight selected development questions.
Fresh validation, confirmation outcomes, expanded study, prompt tuning and
automatic 8,192-token escalation remain outside this authorization.

The round completed in 18.28 minutes with 32 attempts, no retries and no runtime
failures. Strict contract-valid counts are 8/8, 6/8, 8/8, 8/8 in the proposed order.
The two failures exhausted Qwen thinking's 4,096-token allowance. Three Llama CoT
responses omitted reasoning prose while still producing a valid delimiter/answer.
The [completion report](../reviews/P12_development_qualification_completion.md)
records the separate forecasting results and remaining freeze decisions. No
larger-budget or fresh-validation run was initiated.
