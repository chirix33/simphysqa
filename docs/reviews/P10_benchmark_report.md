# Integrated Phi-JEPA run — measured results

Bounded tethered_load run: 32 training scenarios, 8 selection/validation scenarios, 1 question(s) per scenario, seed 11. This training/selection report is not a sealed-test result, four-domain performance claim, convergence result or calibrated OOD evaluation. All failed and unsupported answer components remain in denominators.

Historical P07/P08/P09 evidence is unchanged. Base commit `5a375bdc7193d77b404e5e7459b5ffce7fbb6933`; this implementation is an uncommitted working-tree change. Per-stage source/config/data/checkpoint hashes identify execution versions.

## Numerical training and controlled remedies

Affine conditioning uses frozen training-input statistics inside the vector field only. Raw n/p state, derivatives, full-vector MSE, two current-p gradient paths and autonomous feedback are unchanged. A separately recorded initialization condition sets the existing numerical output bias from mean training adjacent derivatives; it remains trainable. The two factorials separate these conditions rather than attributing all effects to affine conditioning.

The coverage comparison fixes optimizer updates and batch size. Full coverage has twice as many distinct transitions and consequently lower exposure per pair; it tests that bounded allocation, not whether additional post-event supervision is inherently beneficial or harmful. All conditions retain equal question-conditioned pair weights.

After the small fitting check passed, one exposure continuation restored each of the five iterative numerical methods from its own 4,000-update model/optimizer state and extended the same sampler to at most 20,000 updates. These continued conditions are separate from the unchanged 4,000-update factorials. Frozen conditioning statistics, data, objectives and solver remain identical. Original checkpoints are retained; selection also retains the original candidate. LR reuses its original independent fit. Continued fit time is cumulative; the resource ledger charges each executed segment only once.

| Condition | Updates / selected | Selection split | Mean endpoint error / tolerance | Pairs | Selected exposure min–max | Seconds |
| --- | --- | --- | --- | --- | --- | --- |
| biasinit_conditioned_early | 4000 / 2000 | validation | 4.9101 | 640 | 62–63 | 56.11 |
| biasinit_conditioned_full | 4000 / 4000 | validation | 9.409 | 1280 | 62–63 | 55.37 |
| biasinit_constant_context_text_ode | 4000 / 4000 | validation | 11.336 | 1280 | 62–63 | 50.60 |
| biasinit_no_enrichment | 4000 / 4000 | validation | 8.4966 | 1280 | 62–63 | 52.17 |
| biasinit_no_text_conditioning | 4000 / 1000 | validation | 10.305 | 1280 | 15–16 | 46.22 |
| biasinit_raw_early | 4000 / 4000 | validation | 6.7886 | 640 | 125–125 | 55.55 |
| biasinit_raw_full | 4000 / 2000 | validation | 15.248 | 1280 | 31–32 | 55.59 |
| biasinit_small_fit | 4000 / 4000 | train_fitting_only | 0.40112 | 80 | 1000–1000 | 49.61 |
| conditioned_early | 4000 / 2000 | validation | 15.837 | 640 | 62–63 | 51.83 |
| conditioned_full | 4000 / 1000 | validation | 16.095 | 1280 | 15–16 | 52.28 |
| constant_context_text_rnn | 4000 / 4000 | validation | 9.69 | 1280 | 125–125 | 103.78 |
| continued_biasinit_conditioned_full | 20000 / 20000 | validation | 2.2201 | 1280 | 312–313 | 243.31 |
| continued_biasinit_constant_context_text_ode | 20000 / 10000 | validation | 1.5316 | 1280 | 156–157 | 239.06 |
| continued_biasinit_no_enrichment | 20000 / 20000 | validation | 2.3383 | 1280 | 312–313 | 247.71 |
| continued_biasinit_no_text_conditioning | 20000 / 20000 | validation | 1.9297 | 1280 | 312–313 | 217.28 |
| continued_constant_context_text_rnn | 20000 / 4000 | validation | 9.69 | 1280 | 125–125 | 510.73 |
| fixed_projection_lr | 0 / 0 | validation | 3.7964 | 1280 | 1–1 | 2.79 |
| raw_early | 4000 / 2000 | validation | 15.845 | 640 | 62–63 | 51.95 |
| raw_full | 4000 / 1000 | validation | 16.105 | 1280 | 15–16 | 51.68 |
| small_fit | 4000 / 2000 | train_fitting_only | 4.8499 | 80 | 500–500 | 48.51 |

| Training-only diagnostic | Checkpoint | Numeric correct / eligible | Complete questions | Mean endpoint error / tolerance |
| --- | --- | --- | --- | --- |
| biasinit_small_fit | initial | 0/6 | 0/2 | 4.8547 |
| biasinit_small_fit | selected | 6/6 | 2/2 | 0.40112 |
| small_fit | initial | 3/6 | 1/2 | 5.046 |
| small_fit | selected | 0/6 | 0/2 | 4.8499 |

| Selected numerical method | Predicted width | Registered parameters | Training objective |
| --- | --- | --- | --- |
| continued_biasinit_conditioned_full | 280 | 232228 | raw full augmented adjacent MSE |
| continued_biasinit_constant_context_text_ode | 140 | 214168 | raw numerical adjacent MSE |
| continued_biasinit_no_enrichment | 280 | 232228 | raw full augmented adjacent MSE |
| continued_biasinit_no_text_conditioning | 140 | 52748 | raw numerical adjacent MSE |
| continued_constant_context_text_rnn | 140 | 214040 | raw numerical adjacent MSE |
| fixed_projection_lr | 140 | 143500 | least-squares numerical next-state fit |

Parameter counts are registered model parameters, including fixed parameters where applicable; LR also stores fitted coefficients as buffers. Methods are not capacity matched. RNN retains its separate recurrent hidden state.

Loss curves: [numerical_learning.png](artifacts/P10/report/numerical_learning.png). Full data, coordinate decompositions, block gradients, initialization identities and exposure are exported; other-method losses have different coordinate counts/objectives and are not accuracy rankings.

Bounded selected-checkpoint diagnostics use two questions per split and their first/last adjacent intervals, without optimizer updates. Each table cell reports raw augmented loss contribution / parameter-gradient norm; magnitude and gradient influence are distinct. Saturation is the fraction of hidden activations with absolute value above 0.99.

| Method | Split | Tanh1/Tanh2 saturation | Physical loss / gradient | Time/index loss / gradient | Fixed loss / gradient | Context loss / gradient |
| --- | --- | --- | --- | --- | --- | --- |
| conditioned_full | train | 0.934/1.000 | 3.91e-07 / 7.72e-06 | 0.202 / 0.0122 | 6.32e-15 / 2.16e-09 | 5.69e-15 / 2.05e-09 |
| conditioned_full | validation | 0.938/1.000 | 1.94e-07 / 6.52e-06 | 0.202 / 0.0122 | 6.23e-15 / 2.14e-09 | 5.7e-15 / 2.05e-09 |
| biasinit_conditioned_full | train | 0.000/0.006 | 7.47e-09 / 1.17e-06 | 2.65e-12 / 7.28e-09 | 1.84e-10 / 9.4e-08 | 4.25e-11 / 4.32e-08 |
| biasinit_conditioned_full | validation | 0.000/0.004 | 7.42e-09 / 1.63e-06 | 1.82e-12 / 5.83e-09 | 2.62e-10 / 1.01e-07 | 6.67e-11 / 5.03e-08 |
| continued_biasinit_conditioned_full | train | 0.000/0.029 | 3.8e-09 / 4.28e-07 | 4.74e-12 / 1.22e-08 | 4.5e-11 / 3.63e-08 | 2.87e-11 / 2.9e-08 |
| continued_biasinit_conditioned_full | validation | 0.000/0.027 | 3.56e-09 / 4.36e-07 | 3.76e-12 / 1.07e-08 | 3.16e-11 / 2.83e-08 | 1.99e-11 / 2.11e-08 |

Derivative sensitivity and exact public scheduled-event coverage are in `diagnostics/`. They do not establish text usefulness or chaotic dynamics. [Per-time validation curves](artifacts/P10/report/validation_physical_curves.png) retain the early/late boundary.

## Physical validation errors

RMSE uses named physical errors: Euclidean vector distance, scalar absolute error and quaternion angular distance. Public cutoff(s): [0.2] s; requested forecast endpoint(s): [1.0] s. Full horizon includes every reference time after each cutoff through its endpoint; early ends at 0.60 s and late includes later times through that endpoint. Hold-last is a diagnostic, not a new paper baseline. Invalid samples retain explicit coverage counts.

| Method | Quantity | Unit | Full RMSE | Early RMSE | Late RMSE | Valid / eligible |
| --- | --- | --- | --- | --- | --- | --- |
| continued_biasinit_conditioned_full | load/angular_velocity | rad/s | 0.079325 | 0.024119 | 0.10956 | 320/320 |
| continued_biasinit_conditioned_full | load/position | m | 0.014633 | 0.00623 | 0.019735 | 320/320 |
| continued_biasinit_conditioned_full | load/swing_angle | rad | 0.0098599 | 0.0035133 | 0.013494 | 320/320 |
| continued_biasinit_conditioned_full | support/position | m | 0.0027325 | 0.0015664 | 0.0035327 | 320/320 |
| continued_biasinit_conditioned_full | support/velocity | m/s | 0.029594 | 0.014686 | 0.03919 | 320/320 |
| continued_biasinit_constant_context_text_ode | load/angular_velocity | rad/s | 0.05518 | 0.030063 | 0.072013 | 320/320 |
| continued_biasinit_constant_context_text_ode | load/position | m | 0.0063745 | 0.0060941 | 0.006643 | 320/320 |
| continued_biasinit_constant_context_text_ode | load/swing_angle | rad | 0.0055647 | 0.0050154 | 0.0060646 | 320/320 |
| continued_biasinit_constant_context_text_ode | support/position | m | 0.00096907 | 0.0010245 | 0.00091026 | 320/320 |
| continued_biasinit_constant_context_text_ode | support/velocity | m/s | 0.011271 | 0.013031 | 0.0091796 | 320/320 |
| continued_biasinit_no_enrichment | load/angular_velocity | rad/s | 0.085803 | 0.022082 | 0.11932 | 320/320 |
| continued_biasinit_no_enrichment | load/position | m | 0.014187 | 0.0062334 | 0.01907 | 320/320 |
| continued_biasinit_no_enrichment | load/swing_angle | rad | 0.010294 | 0.0029472 | 0.014257 | 320/320 |
| continued_biasinit_no_enrichment | support/position | m | 0.0030404 | 0.0015422 | 0.0040137 | 320/320 |
| continued_biasinit_no_enrichment | support/velocity | m/s | 0.03386 | 0.01427 | 0.045709 | 320/320 |
| continued_biasinit_no_text_conditioning | load/angular_velocity | rad/s | 0.056323 | 0.021806 | 0.07661 | 320/320 |
| continued_biasinit_no_text_conditioning | load/position | m | 0.0094639 | 0.0073789 | 0.011166 | 320/320 |
| continued_biasinit_no_text_conditioning | load/swing_angle | rad | 0.0097771 | 0.0061861 | 0.012366 | 320/320 |
| continued_biasinit_no_text_conditioning | support/position | m | 0.0011052 | 0.00087932 | 0.0012922 | 320/320 |
| continued_biasinit_no_text_conditioning | support/velocity | m/s | 0.017178 | 0.0099103 | 0.02218 | 320/320 |
| continued_constant_context_text_rnn | load/angular_velocity | rad/s | 0.29048 | 0.36974 | 0.17901 | 320/320 |
| continued_constant_context_text_rnn | load/position | m | 0.13201 | 0.12538 | 0.13832 | 320/320 |
| continued_constant_context_text_rnn | load/swing_angle | rad | 0.079217 | 0.052274 | 0.099086 | 320/320 |
| continued_constant_context_text_rnn | support/position | m | 0.015273 | 0.020347 | 0.0072476 | 320/320 |
| continued_constant_context_text_rnn | support/velocity | m/s | 0.019162 | 0.020302 | 0.01795 | 320/320 |
| fixed_projection_lr | load/angular_velocity | rad/s | 0.063116 | 0.02838 | 0.084628 | 320/320 |
| fixed_projection_lr | load/position | m | 0.028877 | 0.012959 | 0.038728 | 320/320 |
| fixed_projection_lr | load/swing_angle | rad | 0.017928 | 0.0035973 | 0.025097 | 320/320 |
| fixed_projection_lr | support/position | m | 0.0011761 | 0.0010182 | 0.0013151 | 320/320 |
| fixed_projection_lr | support/velocity | m/s | 0.0095819 | 0.010405 | 0.0086808 | 320/320 |
| hold_last_diagnostic | load/angular_velocity | rad/s | 0.2183 | 0.10794 | 0.28924 | 320/320 |
| hold_last_diagnostic | load/position | m | 0.11016 | 0.066735 | 0.14077 | 320/320 |
| hold_last_diagnostic | load/swing_angle | rad | 0.14827 | 0.091391 | 0.18872 | 320/320 |
| hold_last_diagnostic | support/position | m | 0.0026425 | 0.00092096 | 0.0036218 | 320/320 |
| hold_last_diagnostic | support/velocity | m/s | 0.010818 | 0.012281 | 0.0091236 | 320/320 |

## Generation learning and strict evaluation

Custom conditions use new branch/output-inventory instructions consistently in training and generation. Shared CODI backbone and objectives are unchanged; teacher projection is frozen. Small-fit and broader runs start independently. Strict parsing, 2,048-token generation limits and EOS requirements are unchanged.

Compared with historical P08, both instructions and training exposure changed. This qualification measures the implemented condition; it does not isolate a causal instruction effect. The CODI teacher/student backbone is shared: detaching the teacher alignment target blocks that branch of alignment gradients, while teacher cross-entropy, student cross-entropy and student-side alignment can still update shared backbone parameters through their own paths.

| Job | Updates / selected | Training questions | Selected exposure min–max | Seconds | Peak allocated GB |
| --- | --- | --- | --- | --- | --- |
| coconut_broad | 441 / 441 | 32 | 13–14 | 2897.9 | 2.64 |
| coconut_small | 40 / 40 | 1 | 40–40 | 291.0 | 2.62 |
| codi_broad | 444 / 300 | 32 | 9–10 | 5807.7 | 3.25 |
| codi_small | 40 / 40 | 1 | 40–40 | 572.1 | 3.24 |

| Job / scope / split / branch / update | Typed valid | EOS | Cap termination | Complete answers | Fallback attempted / used | Calls / seconds |
| --- | --- | --- | --- | --- | --- | --- |
| coconut_broad / milestone / train / coconut / 100 | 0/1 | 1 | 0 | 0/1 | 0/0 | 1 / 4.29 |
| coconut_broad / milestone / train / coconut / 300 | 1/1 | 1 | 0 | 1/1 | 0/0 | 1 / 3.56 |
| coconut_broad / milestone / train / coconut / 441 | 1/1 | 1 | 0 | 1/1 | 0/0 | 1 / 3.57 |
| coconut_broad / milestone / validation / coconut / 100 | 0/2 | 2 | 0 | 0/2 | 0/0 | 2 / 8.53 |
| coconut_broad / milestone / validation / coconut / 300 | 2/2 | 2 | 0 | 0/2 | 0/0 | 2 / 7.12 |
| coconut_broad / milestone / validation / coconut / 441 | 2/2 | 2 | 0 | 1/2 | 0/0 | 2 / 7.15 |
| coconut_broad / selected_validation / validation / coconut / 441 | 8/8 | 8 | 0 | 1/8 | 0/0 | 8 / 29.04 |
| coconut_small / milestone / train / coconut / 0 | 0/1 | 0 | 1 | 0/1 | 0/0 | 1 / 11.76 |
| coconut_small / milestone / train / coconut / 20 | 0/1 | 1 | 0 | 0/1 | 0/0 | 1 / 5.48 |
| coconut_small / milestone / train / coconut / 40 | 0/1 | 0 | 1 | 0/1 | 0/0 | 1 / 11.97 |
| codi_broad / milestone / train / hybrid / 100 | 1/1 | N/A (composition) | N/A (composition) | 1/1 | 0/0 | 2 / 7.08 |
| codi_broad / milestone / train / hybrid / 300 | 1/1 | N/A (composition) | N/A (composition) | 1/1 | 0/0 | 2 / 6.95 |
| codi_broad / milestone / train / hybrid / 444 | 1/1 | N/A (composition) | N/A (composition) | 1/1 | 0/0 | 2 / 6.89 |
| codi_broad / milestone / train / student / 100 | 1/1 | 1 | 0 | 1/1 | 0/0 | 1 / 3.40 |
| codi_broad / milestone / train / student / 300 | 1/1 | 1 | 0 | 1/1 | 0/0 | 1 / 3.42 |
| codi_broad / milestone / train / student / 444 | 1/1 | 1 | 0 | 1/1 | 0/0 | 1 / 3.37 |
| codi_broad / milestone / train / teacher / 100 | 1/1 | 1 | 0 | 1/1 | 0/0 | 1 / 3.68 |
| codi_broad / milestone / train / teacher / 300 | 1/1 | 1 | 0 | 1/1 | 0/0 | 1 / 3.54 |
| codi_broad / milestone / train / teacher / 444 | 1/1 | 1 | 0 | 1/1 | 0/0 | 1 / 3.52 |
| codi_broad / milestone / validation / hybrid / 100 | 2/2 | N/A (composition) | N/A (composition) | 0/2 | 0/0 | 4 / 14.18 |
| codi_broad / milestone / validation / hybrid / 300 | 2/2 | N/A (composition) | N/A (composition) | 1/2 | 0/0 | 4 / 13.96 |
| codi_broad / milestone / validation / hybrid / 444 | 0/2 | N/A (composition) | N/A (composition) | 0/2 | 2/0 | 4 / 13.94 |
| codi_broad / milestone / validation / student / 100 | 2/2 | 2 | 0 | 0/2 | 0/0 | 2 / 6.99 |
| codi_broad / milestone / validation / student / 300 | 2/2 | 2 | 0 | 1/2 | 0/0 | 2 / 6.81 |
| codi_broad / milestone / validation / student / 444 | 0/2 | 2 | 0 | 0/2 | 0/0 | 2 / 6.76 |
| codi_broad / milestone / validation / teacher / 100 | 2/2 | 2 | 0 | 0/2 | 0/0 | 2 / 7.19 |
| codi_broad / milestone / validation / teacher / 300 | 2/2 | 2 | 0 | 1/2 | 0/0 | 2 / 7.16 |
| codi_broad / milestone / validation / teacher / 444 | 0/2 | 2 | 0 | 0/2 | 0/0 | 2 / 7.18 |
| codi_broad / selected_validation / validation / hybrid / 300 | 8/8 | N/A (composition) | N/A (composition) | 2/8 | 0/0 | 16 / 55.63 |
| codi_broad / selected_validation / validation / student / 300 | 8/8 | 8 | 0 | 2/8 | 0/0 | 8 / 27.34 |
| codi_broad / selected_validation / validation / teacher / 300 | 8/8 | 8 | 0 | 2/8 | 0/0 | 8 / 28.29 |
| codi_small / milestone / train / hybrid / 0 | 0/1 | N/A (composition) | N/A (composition) | 0/1 | 1/0 | 2 / 23.84 |
| codi_small / milestone / train / hybrid / 20 | 0/1 | N/A (composition) | N/A (composition) | 0/1 | 1/0 | 2 / 20.52 |
| codi_small / milestone / train / hybrid / 40 | 0/1 | N/A (composition) | N/A (composition) | 0/1 | 1/0 | 2 / 7.50 |
| codi_small / milestone / train / student / 0 | 0/1 | 0 | 1 | 0/1 | 0/0 | 1 / 12.01 |
| codi_small / milestone / train / student / 20 | 0/1 | 1 | 0 | 0/1 | 0/0 | 1 / 8.44 |
| codi_small / milestone / train / student / 40 | 0/1 | 1 | 0 | 0/1 | 0/0 | 1 / 3.34 |
| codi_small / milestone / train / teacher / 0 | 0/1 | 0 | 1 | 0/1 | 0/0 | 1 / 11.84 |
| codi_small / milestone / train / teacher / 20 | 0/1 | 0 | 1 | 0/1 | 0/0 | 1 / 12.08 |
| codi_small / milestone / train / teacher / 40 | 0/1 | 1 | 0 | 0/1 | 0/0 | 1 / 4.16 |

Per-example raw outputs, token IDs, losses, branch inputs, checkpoint selections and generation costs are retained. Training-example fitting and validation results are separate. No output repair is used. Teacher/student generation work is counted in hybrid cost.

## Integrated answer benchmark

| Condition | Method | Split | Complete answers | Numeric correct | Typed valid targets | Boolean coverage | Boolean correct supported |
| --- | --- | --- | --- | --- | --- | --- | --- |
| numerical_readout | continued_biasinit_conditioned_full | train | 4/32 | 51/96 | 127/128 | 31/32 | 31/31 |
| numerical_readout | continued_biasinit_conditioned_full | validation | 1/8 | 11/24 | 32/32 | 8/8 | 8/8 |
| numerical_readout | continued_biasinit_constant_context_text_ode | train | 9/32 | 57/96 | 127/128 | 31/32 | 30/31 |
| numerical_readout | continued_biasinit_constant_context_text_ode | validation | 2/8 | 13/24 | 32/32 | 8/8 | 8/8 |
| numerical_readout | fixed_projection_lr | train | 16/32 | 78/96 | 127/128 | 31/32 | 31/31 |
| numerical_readout | fixed_projection_lr | validation | 0/8 | 5/24 | 32/32 | 8/8 | 6/8 |
| numerical_readout | continued_constant_context_text_rnn | train | 0/32 | 6/96 | 127/128 | 31/32 | 7/31 |
| numerical_readout | continued_constant_context_text_rnn | validation | 0/8 | 1/24 | 32/32 | 8/8 | 3/8 |
| numerical_readout | continued_biasinit_no_enrichment | train | 3/32 | 45/96 | 127/128 | 31/32 | 30/31 |
| numerical_readout | continued_biasinit_no_enrichment | validation | 2/8 | 13/24 | 32/32 | 8/8 | 7/8 |
| numerical_readout | continued_biasinit_no_text_conditioning | train | 4/32 | 44/96 | 127/128 | 31/32 | 31/31 |
| numerical_readout | continued_biasinit_no_text_conditioning | validation | 0/8 | 10/24 | 32/32 | 8/8 | 6/8 |
| runtime_forecast_intervention | reversed_primary_forecast_readout | validation | 0/8 | 0/24 | 32/32 | 8/8 | 8/8 |
| frozen_answer_llm | continued_biasinit_conditioned_full | validation | 1/8 | 11/24 | 32/32 | 8/8 | 8/8 |
| frozen_answer_llm | continued_biasinit_constant_context_text_ode | validation | 2/8 | 13/24 | 32/32 | 8/8 | 8/8 |
| frozen_answer_llm | fixed_projection_lr | validation | 0/8 | 5/24 | 32/32 | 8/8 | 6/8 |
| frozen_answer_llm | continued_constant_context_text_rnn | validation | 0/8 | 1/24 | 32/32 | 8/8 | 3/8 |
| frozen_answer_llm | continued_biasinit_no_enrichment | validation | 2/8 | 13/24 | 32/32 | 8/8 | 7/8 |
| frozen_answer_llm | continued_biasinit_no_text_conditioning | validation | 0/8 | 10/24 | 32/32 | 8/8 | 6/8 |
| frozen_answer_llm | public_only | validation | 0/8 | 24/24 | 24/32 | 0/8 | 0/0 |
| custom_answer | coconut_coconut | validation | 1/8 | 10/24 | 32/32 | 8/8 | 6/8 |
| custom_answer | codi_student | validation | 2/8 | 11/24 | 32/32 | 8/8 | 6/8 |
| custom_answer | codi_teacher | validation | 2/8 | 11/24 | 32/32 | 8/8 | 6/8 |
| custom_answer | codi_hybrid | validation | 2/8 | 11/24 | 32/32 | 8/8 | 6/8 |

Public-only and forecast answers share original public inputs/model/decoding and evaluation references. Forecast Boolean values are constrained to qualified rule readouts; public-only has no forecast evidence. Common numerical targets are compared separately; whole-answer results retain Boolean components and this policy difference.

On common numerical targets, public-only achieves 24/24 and the primary forecast condition achieves 11/24. Whole-answer differences must not be interpreted as a forecasting benefit when they reflect the different Boolean evidence policy. These are selection-split observations, not sealed-test method rankings.

Reversed-forecast offline control changes 24/24 queried numerical values by more than their existing tolerance. Exact per-target changes are exported. This is a readout intervention, not independent training or a paid answer condition. Removing assessment or inactive fallback is a no-op and is not counted as independent evidence.

## Four-domain capability matrix

| Public preflight domain | Split | Compatible / eligible | Failure reasons |
| --- | --- | --- | --- |
| driving | train | 740/740 | {} |
| driving | validation | 148/148 | {} |
| object_pushing_stacking | train | 2000/2000 | {} |
| object_pushing_stacking | validation | 400/400 | {} |
| robotic_arm | train | 1962/1962 | {} |
| robotic_arm | validation | 388/388 | {} |
| tethered_load | train | 2000/2000 | {} |
| tethered_load | validation | 400/400 | {} |

This preflight opens public train/validation inputs only. It validates accepted layouts, not physical forecast quality, enrichment truthfulness, or long-context model performance.

| Domain | Entity / quantity | Implemented readout | Required evidence / gap |
| --- | --- | --- | --- |
| robotic_arm | joint_1 / angle | True | Registered finite named numerical channel with exact unit/frame/type at requested physical time; quaternion rotation error uses xyzw. |
| robotic_arm | joint_1 / angular_velocity | True | Registered finite named numerical channel with exact unit/frame/type at requested physical time; quaternion rotation error uses xyzw. |
| robotic_arm | joint_2 / angle | True | Registered finite named numerical channel with exact unit/frame/type at requested physical time; quaternion rotation error uses xyzw. |
| robotic_arm | joint_2 / angular_velocity | True | Registered finite named numerical channel with exact unit/frame/type at requested physical time; quaternion rotation error uses xyzw. |
| robotic_arm | tip / position | True | Registered finite named numerical channel with exact unit/frame/type at requested physical time; quaternion rotation error uses xyzw. |
| robotic_arm | arm / joint_limit_by_T | True | Both joint angles (rad/joint_local), initialized at t=0 through T, trigger >=2.8 rad, rearm <2.795 rad. |
| driving | car / forward_position | True | Registered finite named numerical channel with exact unit/frame/type at requested physical time; quaternion rotation error uses xyzw. |
| driving | car / forward_velocity | True | Registered finite named numerical channel with exact unit/frame/type at requested physical time; quaternion rotation error uses xyzw. |
| driving | car / stopped_by_T | True | Forward and planar speed (m/s), complete history, abs(forward)<0.02 and planar<0.03 for 0.2 s; accumulate earliest qualifying interval. |
| object_pushing_stacking | block_1 / position | True | Registered finite named numerical channel with exact unit/frame/type at requested physical time; quaternion rotation error uses xyzw. |
| object_pushing_stacking | block_1 / orientation | True | Registered finite named numerical channel with exact unit/frame/type at requested physical time; quaternion rotation error uses xyzw. |
| object_pushing_stacking | block_2 / position | True | Registered finite named numerical channel with exact unit/frame/type at requested physical time; quaternion rotation error uses xyzw. |
| object_pushing_stacking | block_2 / orientation | True | Registered finite named numerical channel with exact unit/frame/type at requested physical time; quaternion rotation error uses xyzw. |
| object_pushing_stacking | block_2 / stable_stack | False | Supporting normal contact force/on-off latch and vertical normal, both poses, lower local footprint, upper speed and uninterrupted 0.2 s endpoint dwell. Future force/normal/latch are absent from predicted n. |
| object_pushing_stacking | block_2 / support_lost | False | Qualified initial support and supporting contact-force/normal latch history after cutoff. Future contact history is absent; proximity is insufficient. |
| object_pushing_stacking | block_2 / left_table | True | World upper-block COM at T; outside [-2,2] m on x or y. Endpoint only, not ever-left event. |
| tethered_load | load / position | True | Registered finite named numerical channel with exact unit/frame/type at requested physical time; quaternion rotation error uses xyzw. |
| tethered_load | load / swing_angle | True | Registered finite named numerical channel with exact unit/frame/type at requested physical time; quaternion rotation error uses xyzw. |
| tethered_load | load / angular_velocity | True | Registered finite named numerical channel with exact unit/frame/type at requested physical time; quaternion rotation error uses xyzw. |
| tethered_load | load / boundary_crossed | True | World load COM x from cutoff to T; qualified initial x<0.095 m, trigger x>0.105 m, rearm x<0.095 m. |

This matrix describes the primary/comparator numerical readout, not proven four-domain performance. Per-target units, frame, history, initial event state and sampling checks can still yield unsupported. Stable-stack and support-lost require future contact/support evidence absent from the accepted state; the forecast answer layer cannot invent these values. Separately approved custom direct-generation baselines predict their typed training targets; such outputs do not implement or qualify the missing deterministic contact readout.

Assessment: train-only predicted reference bank is rebuilt for the selected checkpoint/projection/encoder/layout/time grid. Familiarity is not physical correctness or calibrated uncertainty. Required immutable typed public contract declarations are absent; answer-spec thresholds are not substituted for them. V1 and supported physical checks remain separate. Calibration IDs are disjoint from checkpoint selection; test/OOD outcomes remain sealed. Calibration is ineligible while required components are missing.

Clarification: the separate human-reviewed one-question/one-reply workflow is available but disabled in this autonomous benchmark. No OOD alarm, human-assistance accuracy claim or automatic reforecasting follows from this run.

## Research-question status

**RQ1, forecasting/QA:** the tables measure small-set fitting and validation separately; neither is a four-domain generalization claim. **Domain engineering:** accepted state layouts, named channel/unit/frame bindings, public event rules, physical consistency checks and output schemas are manually authored and disclosed. No force equations or benchmark oracle are imported into the vector field. **Richer outputs:** raw/named trajectories, typed answers, unsupported/failure reasons and assessment components are available, but their usefulness/accuracy must be judged against the retained forecast/answer failures.

**RQ2, recognition:** the implemented mechanism retrieves a compatible training prediction with frozen public-context embeddings and reports terminal full-vector familiarity, V1 and supported checks. This run does not establish OOD detection performance; complete contracts, eligible calibration and sealed evaluation remain pending. **Clarification:** actual-user interaction, human reply routing and a single frozen-answer refinement are implemented separately. Inputs are original public facts and existing prediction/readout evidence plus an attributed reply; outputs are preserved initial/refined answers and explicit unresolved/reforecast/revised-task statuses. Software fixtures verify boundaries. They do not show that it detects OOD, recovers hidden causes or improves empirical accuracy.

## Resource accounting

Charged CPU 37.12/60 minutes; GPU 161.36/180 minutes; artifacts 11.753/20 GB; provider attempts 49/120, input tokens 727013/2,000,000, output tokens 21655/100,000, conservative USD 4.0682/15. Whole worker wall time is charged to its CPU/GPU bucket; provider waiting time is reported separately and provider process CPU time is charged. Unknown usage retains its reservation. One worker runs at a time; a supervisor enforces aggregate and component time/artifact caps. Official pricing basis: https://developers.openai.com/api/docs/models/gpt-5.6-sol (checked 2026-09-25).

Final authoritative resource totals are in budget.json and completed stage records. This report records a snapshot taken during report generation; the supervisor subsequently charges its small remaining execution overhead. Provider charges are conservative upper-rate accounting, not a billing invoice.

A reused frozen-output cache hit has zero new provider charge in this ledger. That is an incremental execution cost, not a claim that the original LLM inference was free or instantaneous; historical P08 provider evidence remains separate. Per-request ledgers identify cache hits and newly dispatched calls.

## Remaining gates

- **Missing evidence:** robust held-out physical/answer quality, multiple seeds, other-domain training, sealed ID/OOD performance and live independently reviewed clarification effectiveness. Small-fit learning does not establish these.

- **Scientific decisions:** sufficient contact/support evidence or an approved mechanism for contact-dependent outputs; typed assessment contract declarations and their source. Existing public readouts are implemented. No new head, loss, schema repair or EBM was introduced.

- **Implementation limits:** staged workflow validates accepted fixed layouts and rejects incompatible inputs rather than coercing them. Optional heterogeneous-horizon pair/sequence sampling has software tests; larger empirical workloads remain unqualified. Sealed evaluation is not executed by the qualification command.

- **Unresolved hypotheses:** learning effects may depend on initialization, sampled control regimes and optimization. Error magnitude/familiarity do not diagnose chaos or establish text usefulness.

See [the executable workflow](../P10_pipeline.md) and [next full-study plan](P10_next_full_study.md).
