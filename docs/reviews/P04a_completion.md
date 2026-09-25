# Stage 4/P04a completion — 24 September 2026

Status: **complete for the approved initial readout and bounded answer diagnostic**.
This is not complete dataset Boolean support or a predictive-performance study.
Branch `full-phi-jepa-from-dataset`, base/current HEAD
`7f2553ca6591301de588bd3362e72838354169a0`; changes uncommitted.
Stage 3 completed before this stage; Stage 5 has not started at this handoff.

## Implemented behavior

`inference/readout.py` maps registry columns to named physical channels without
changing full predictions. It implements the user-approved public-rule subset,
target-specific evidence qualification and explicit unsupported contact outcomes.
Invalid forecasts are distinct from unsupported targets. The 0.02-second grid,
no-interpolation policy and initial-state limitations are recorded in
[the method decision](../decisions/P04a_readout.md).

`providers/openai_answer.py` uses immutable public inputs, a separate forecast
payload and separately identified readout outputs. A new versioned prompt and
target-bound schema preserve original assets. Strict parsing rejects missing,
duplicate, wrong-time/type/unit/frame answers and Boolean inventions. API versus
parser failures and all attempt/usage costs are recorded. Cache replay is exact.
No extraction repair, fallback substitution, training change or private inference
access was added. Prose remains LLM output, not a mechanically proven semantic
guarantee; the three live responses were manually inspected.

## Verification and measurements

Twelve new offline behavior tests cover registry separation, preserved values,
event versus endpoint semantics, threshold/hysteresis/dwell behavior, missing
channels/units/frames/time/initial state, contact abstention, strict parsing,
private-payload rejection, cache/accounting and complete failure denominators.
Final P00–P04a regression: 84 tests passed in 13.745 seconds with zero skips;
evidence is `artifacts/P04a/tests-wsl.log`.

Four real public validation schemas were checked with explicitly synthetic
constant trajectories: arm 6/6 targets supported, driving 3/3, objects 5/7,
tether 4/4. These are binding/support checks, **not empirical accuracy**. Objects'
two unsupported contact components remain in complete-answer denominators.

Actual one-question tether diagnostic using the existing tiny P03 checkpoint:

| Condition | Position error (m) | Angle error (rad) | Angular velocity error (rad/s) | Boolean coverage | Boolean accuracy on supported | Complete success/all eligible |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Public only | 0.000005326 | 0.000003226 | 0.000001262 | 0/1 | unavailable | 0/1 |
| Predicted forecast | 0.001775776 | 0.005894898 | 0.018610896 | 1/1 | 1/1 | 1/1 |
| Reversed forecast | 0.001560141 | 0.000860300 | 0.009942073 | 1/1 | 1/1 | 1/1 |

All three numerical targets pass their public tolerances in every condition.
The predicted-condition LLM numbers exactly equal the original named numerical
endpoint. Reversing the forecast changes its numerical answers to the changed
endpoint. This demonstrates payload use on this question, **not a learned forecast
benefit**: public-only numerical estimates are more accurate. Public-only Boolean
coverage is deliberately constrained by the approved output policy. Do not treat
the resulting complete-answer difference as evidence of improved reasoning.

This target-specific physical evaluation differs from P03's high mixed-coordinate
MSE, which includes drifting step index and fixed-conditioning coordinates. Neither
result is suppressed; numerical target success does not validate all state blocks.

Three live calls, no retries/failures, 36,816 input tokens and 2,466 output tokens;
usage-priced USD **0.196584**, 37.487456 seconds summed API wall time. Zero new
encoder calls, ODE solves or training updates. Fresh cache replay: three exact
hits, zero transport attempts. Alias `gpt-5.6-sol` has no pinned immutable snapshot.

## Reproduction and artifacts

Run from repository root in the isolated WSL core environment:

```text
python tools/run_p04a_answers.py --profile /home/aashraf/phi-jepa/p02b-profile --run /home/aashraf/phi-jepa/p03-correctness-01 --output /home/aashraf/phi-jepa/p04a-answers-01
python tools/evaluate_p04a_answers.py --run /home/aashraf/phi-jepa/p04a-answers-01
python tools/audit_p04a_bindings.py --profile /home/aashraf/phi-jepa/p02b-profile --output /home/aashraf/phi-jepa/p04a-answers-01/public-bindings.json
python tools/verify_p04a_cache.py --run /home/aashraf/phi-jepa/p04a-answers-01
PYTHONPATH=src python -m unittest discover -s tests -p 'test_p0*.py' -v
python tools/collect_p04a_evidence.py --run /home/aashraf/phi-jepa/p04a-answers-01
python tools/verify_p00_handoff.py
```

The final guards against private payloads and mismatched supplied readouts were
verified using the exact cached responses without repeating paid calls. Source
inventories distinguish the live-run and final source. Compact manifests, results
and native artifact hashes are in `docs/reviews/artifacts/P04a/`. Raw public inputs,
named predictions and final responses remain under the native run directory.
Original asset hashes are verified by the handoff checker. Credentials stay in
the ignored key file referenced by ignored `.env`; no secret enters artifacts.

Remaining limitations: contact outcomes unsupported, sampled events not exact,
one empirical domain/question, tiny predictor, no full benchmark, alias snapshot
unavailable. No Stage 4 algorithm deviation; no later stage launched here.
Next: Stage 5 fixed assessment under the user's newly approved full-2d
`development_r1_v1` adaptation, with high-score numerical replacement disabled.
