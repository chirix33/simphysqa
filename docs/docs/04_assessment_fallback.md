# Fixed assessment, diagnosis and fallback

[Start](../README.md) · [Defaults/open decisions](08_defaults_decisions.md) · [Metrics](03_data_evaluation.md)

## What is fixed

Inference may read a frozen predictor, stored training references, generic contract checks and frozen LLM judges. It must not train an EBM, change predictor weights, optimize the latent state or rewrite input constraints to reduce a score. All score weights and thresholds are validation-selected configuration. Assessment is not physical energy in joules and its reduction is not a safety guarantee.

## Development reference bank (R1)

After selecting a predictor checkpoint, run it once on training inputs and store frozen question embeddings, original schemas, permitted task metadata and its predicted latent trajectories. Record checkpoint/split/encoder/schema hashes. Reference retrieval never sees the current test target. The first retrieval rule is nearest frozen question embedding among compatible observable layouts and normalized horizons, with stable ID tie breaking and k=1. Exclude the same family for training-set diagnostic checks; use the training bank directly for validation/test. Brute-force exact cosine retrieval is sufficient initially; no vector database is needed.

At each selected normalized time, development latent energy is `1 - cosine(z_test(t), z_ref_pred(t))`, range [0,2]. Reject zero-norm/nonfinite latent states as unavailable. Use matched normalized times and log physical horizons. Evaluate terminal score initially; optional five-point changes across the rollout are diagnostic outputs, not automatic proofs of instability or chaos.

**Limitation R1:** these are predicted training latents. The manuscript writes a target latent, but no unique physical-label-to-latent mapping is specified, and physical readout is many-to-one. R1 measures familiarity with learned trajectories, not agreement with a ground-truth latent or certified physics. Do not add an unapproved target encoder/EMA, reverse the readout with an unexplained pseudoinverse, or label R1 as ground-truth latent guidance. Store training physical labels for evaluator diagnostics separately; they do not solve this representational ambiguity.

R1 is an explicitly labeled development default that permits module implementation. Before publishing results under the manuscript's exact reference-target equation, the owner must choose: describe this reference construction honestly in the paper, or specify and validate an alternative mapping. This scientific decision is not required to build P00–P03.

## Contract score

Separate two ideas: (a) a prediction violating an applicable scenario constraint, and (b) a test scenario differing from a training scenario. Difference alone is not invalidity. Do not enforce a training example's friction or bound as the current scenario's truth.

Use generic typed operators `eq`, `le`, `ge`, `between` after a finite explicit operator normalization. Bind extracted names/units to `ObservableSpec` by stable exact IDs/names and generic unit conversion; if ambiguous, mark unsupported. Evidence must support an applicable bound on that observable, not merely a number in the initial state. No fuzzy name match may silently change quantity meaning. General free-text physics laws remain unavailable to this deterministic scorer unless implemented in a disclosed independent evaluator.

For a one-sided bound, normalized excess is `max(0, observed-bound)/scale` (reverse for lower bounds). Equality uses an explicit tolerance, then normalized absolute excess. Scale is the supported range or a fixed train-derived observable scale with epsilon; never current test labels. Aggregate means over applicable checks and report count/coverage. Values can exceed 1; do not pretend severity is a probability. Preserve raw severity and any configured cap separately.

## Judge scope: preserve V1 and distinguish extensions

The adopted [JUDGE_PROMPT](../assets/prompts.json) asks whether **scenario and schema** agree, explicitly excluding trajectory accuracy. Use its exact string and exact `{score,reason}` response for `semantic_scope=scenario_schema_v1`. Validate score in [0,1] in application code and retain evidence input hashes. It does not compare retrieved schemas and does not provide a full cause diagnosis. Requesting different inputs does not magically change the task defined by that prompt.

Development JSON energy may combine this V1 score with contract severity as `alpha*contract + (1-alpha)*semantic_v1`; default alpha=0.5. Total is `latent + lambda_json*json`, default lambda_json=1. All components remain logged. Name the profile `development_r1_v1` and expose its semantics in reports. If a required component is unavailable, return partial assessment and a reason; do not replace the missing term with zero and apply the full-score threshold. Any partial-score detector needs its own validation calibration and explicit label.

For full retrieved-schema semantics and evidence-supported diagnosis, add separate **versioned** provider interfaces and draft prompt contracts. A diagnosis response should include possible cause, cited input/reference evidence IDs, limitations and abstention, not an unexplained confident label. The user adopted supplied prompts; these new tasks must be reviewed before a live experiment uses them. Codex can implement typed interfaces and fixtures now, without pretending the new prompt is supplied/approved. It must not call the archived repair prompt to diagnose.

## Calibration and evaluation

Freeze reference bank and checkpoint, then calibrate on held-out ID calibration families. Initial false-alarm target 5% uses the empirical 95th percentile with a specified quantile algorithm and strict `score > threshold` trigger. Report finite-sample observed calibration/test rates; this is not a conformal or robustness guarantee. Calibrate separately for each score profile/layout and version. Hyperparameter selection occurs on selection validation; calibration examples do not tune weights. If calibration is too small or all scores degenerate, label the detector uncalibrated and do not claim controlled false alarms.

Test high energy as an anomaly signal, not an automatic reason to trust a fallback. Evaluate original and returned predictions side by side. No reuse of the demo's arbitrary 0.05 threshold. A changed checkpoint, score definition, judge prompt or retrieval rule invalidates cached calibration.

## Runtime state machine

| Condition | Bounded action | Preserve/report |
| --- | --- | --- |
| Valid extraction and predictor solve | Fixed assessment, then answer generation | Original schema/prediction, components and returned prediction |
| Extraction fails | Use separately trained text-only ODE if available; otherwise one text-only answer attempt | Extraction failure and changed output/metric coverage |
| Primary readout/solver fails | Try the separately trained fallback once if its prerequisites hold | Numerical failure, both solve costs; no clamping of failed state |
| Valid calibrated high score | Optional one fallback prediction under the declared policy; diagnosis if configured | Original and fallback outputs; policy, reasons, cost and limitations |
| Judge/reference missing | Partial/unavailable assessment; do not report OOD-negative | Component failure and available numeric prediction |
| Answer LLM fails but numeric prediction exists | Deterministic numeric formatter | Narrative unavailable, no fabricated LLM answer |
| No supported numerical or text output | Terminal failure record | Count failure in denominators; never return a fake correct answer |

Default high-score action is assessment/diagnosis without overwriting the numerical prediction until validation supports a fixed fallback trigger policy. This prevents recreating the demo's all-fallback collapse. Technical extraction/solver fallbacks remain separately defined. P07 may enable high-score fallback using validation evidence and a frozen policy, with paired correction/harm reporting. The active policy is always recorded.

No recursive retries. Initial per-stage transport retry cap 2; content attempts 1. Fallback solve cap 1, text fallback generation cap 1, diagnosis cap 1. A budget-exhausted record remains a failure/partial result. Full/no-fallback ablations explicitly disable the relevant branch and expose failures. Without-energy disables all energy-triggered decisions; it may retain technical-failure handling under a separately documented common reliability policy.

## Acceptance

Synthetic monotonic bound checks; zero/empty coverage; missing judge behavior; frozen bank provenance; no test-label access; no mutable schema writes; no optimizer in inference; distinct profiles/thresholds; content-sensitive cache invalidation; fallback call caps; paired original/returned predictions; all calls and NFE counted. Stub judge tests show integration only. Real scoring/diagnosis validity remains unverified until the live pilot and prompt decisions are complete.
