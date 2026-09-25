# P08 generation diagnostics

Diagnostic rows are six checks on one repeatedly trained training example. Broader rows are eight distinct held-out scenarios from a separate fresh initialization. Hybrid reuses existing student/teacher outputs; it is not an additional generation call. Hybrid label success does not guarantee a valid teacher explanation; the teacher branch is reported separately.

| Method | Phase | Branch | Expected | Attempted | Typed valid | EOS | At token cap | Missing EOS | Fallback attempts | Recoveries | Complete answers |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| coconut | diagnostic | coconut | 6 | 6 | 0 | 2 | 4 | 4 | 0 | 0 | 0 |
| coconut | broad | coconut | 8 | 8 | 4 | 8 | 0 | 0 | 0 | 0 | 1 |
| codi | diagnostic | student | 6 | 6 | 0 | 0 | 6 | 6 | 0 | 0 | 0 |
| codi | diagnostic | teacher | 6 | 6 | 0 | 0 | 6 | 6 | 0 | 0 | 0 |
| codi | diagnostic | hybrid | 6 | 6 | 0 | branch-specific | branch-specific | branch-specific | 6 | 0 | 0 |
| codi | broad | student | 8 | 8 | 0 | 8 | 0 | 0 | 0 | 0 | 0 |
| codi | broad | teacher | 8 | 8 | 8 | 8 | 0 | 0 | 0 | 0 | 1 |
| codi | broad | hybrid | 8 | 8 | 8 | branch-specific | branch-specific | branch-specific | 8 | 8 | 1 |

## Training-only milestone accuracy

| Method / branch | Update | Complete / 1 | Correct targets / 4 | Typed valid | EOS | Failure reason |
| --- | --- | --- | --- | --- | --- | --- |
| coconut/coconut | 0 | 0 | 0 | False | True | Expecting value: line 1 column 1 (char 0) |
| coconut/coconut | 1 | 0 | 0 | False | False | generation_missing_EOS |
| coconut/coconut | 2 | 0 | 0 | False | True | Expecting value: line 1 column 1 (char 0) |
| coconut/coconut | 5 | 0 | 0 | False | False | generation_missing_EOS |
| coconut/coconut | 10 | 0 | 0 | False | False | generation_missing_EOS |
| coconut/coconut | 20 | 0 | 0 | False | False | generation_missing_EOS |
| codi/student | 0 | 0 | 0 | False | False | generation_missing_EOS |
| codi/teacher | 0 | 0 | 0 | False | False | generation_missing_EOS |
| codi/hybrid | 0 | 0 | 0 | False | None | generation_missing_EOS |
| codi/student | 1 | 0 | 0 | False | False | generation_missing_EOS |
| codi/teacher | 1 | 0 | 0 | False | False | generation_missing_EOS |
| codi/hybrid | 1 | 0 | 0 | False | None | generation_missing_EOS |
| codi/student | 2 | 0 | 0 | False | False | generation_missing_EOS |
| codi/teacher | 2 | 0 | 0 | False | False | generation_missing_EOS |
| codi/hybrid | 2 | 0 | 0 | False | None | generation_missing_EOS |
| codi/student | 5 | 0 | 0 | False | False | generation_missing_EOS |
| codi/teacher | 5 | 0 | 0 | False | False | generation_missing_EOS |
| codi/hybrid | 5 | 0 | 0 | False | None | generation_missing_EOS |
| codi/student | 10 | 0 | 0 | False | False | generation_missing_EOS |
| codi/teacher | 10 | 0 | 0 | False | False | generation_missing_EOS |
| codi/hybrid | 10 | 0 | 0 | False | None | generation_missing_EOS |
| codi/student | 20 | 0 | 0 | False | False | generation_missing_EOS |
| codi/teacher | 20 | 0 | 0 | False | False | generation_missing_EOS |
| codi/hybrid | 20 | 0 | 0 | False | None | generation_missing_EOS |

## Failure categories

| Method | Phase | Branch | Reason | Count |
| --- | --- | --- | --- | --- |
| coconut | diagnostic | coconut | Expecting value: line 1 column 1 (char 0) | 2 |
| coconut | diagnostic | coconut | generation_missing_EOS | 4 |
| coconut | broad | coconut | target_count | 4 |
| codi | diagnostic | student | generation_missing_EOS | 6 |
| codi | diagnostic | teacher | generation_missing_EOS | 6 |
| codi | diagnostic | hybrid | generation_missing_EOS | 6 |
| codi | broad | student | answer_envelope | 8 |

## Validation answers

| Method | Complete / 8 | Numeric correct / 24 | Boolean coverage / 8 | Boolean correct / supported |
| --- | --- | --- | --- | --- |
| phi_jepa | 0 | 1 | 8 | 6/8 |
| constant_context_text_ode | 0 | 1 | 8 | 6/8 |
| fixed_projection_lr | 0 | 0 | 8 | 6/8 |
| constant_context_text_rnn | 0 | 3 | 8 | 6/8 |
| no_enrichment | 0 | 1 | 8 | 6/8 |
| no_text_conditioning | 0 | 1 | 8 | 6/8 |
| public_only | 0 | 21 | 0 | 0/0 |
| reversed_forecast | 0 | 0 | 8 | 6/8 |

Public-only Booleans are explicitly unsupported by that control policy. Forecast conditions apply qualified deterministic public rules. Compare their common 24 numerical targets separately; full answers keep all 32 target components and all eight questions. Custom typed-answer conditions are separate direct-generative baselines, including their Boolean predictions and all failures.
