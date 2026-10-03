# Qwen thinking-on completion allowance — 1 October 2026

The user authorized all eight original development cases once in a new versioned
run, increasing only Qwen thinking-on's total output allowance from 4,096 to 8,192
and supervised request limit from 240 to 360 seconds. Eight attempts and one hour
including setup are the limits; no retries or automatic further increases.

Preparation verifies full request equality after undoing those two field changes,
including messages, rendered template, input IDs and schema. The scientific source
identity stays `4e7da84dd47b8ba4a858307a31a8d3896685e3211c6f258bb5e26125f684a4ee`.
The new supervisor and reporting wrapper are separately hashed and retain the
same scientific evaluator. The native run is
`/home/aashraf/phi-jepa/p12-qwen-thinking-budget-8192-01`.

The budget-selection rule was recorded before generation: recommend the revised
allowance for the disabled fresh proposal if all eight finish with strict valid
answers without repair. Forecasting scores do not select the allowance. Otherwise
retain it as an unselected candidate requiring review; inspect saved incomplete
traces and do not escalate again.

Qwen off, Llama direct and Llama prompted CoT are not rerun or changed. Prompted
CoT's nonempty reasoning compliance is reported independently of answer validity;
all historical responses remain included. The fresh cohort is reused exactly,
without reselection, and its new proposal remains disabled: 32 requests, 112
minutes worst-case request time plus 38 minutes overhead in 150 minutes total.
Fresh execution and the expanded study remain separate review decisions.

Outcome: all eight completed strictly valid without repair in 14.91 minutes.
The predeclared completion criterion selected 8,192/360 for the disabled fresh v2
proposal; forecasting scores did not select it. Whole-answer correctness remains
1/8. All old output sequences are exact prefixes of new ones, with six unchanged
complete sequences and two natural extensions. No further budget increase is
proposed. The [completion report](../reviews/P12_qwen_completion_budget_completion.md)
records metrics and the frozen 150-minute fresh proposal. Llama prompted CoT's
5/8 nonempty reasoning compliance remains separately disclosed without filtering.
