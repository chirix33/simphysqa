# P08 coordinate and named physical errors

All eight frozen validation questions remain in the denominator. Each successful rollout has 40 forecast samples on the external 0.22–1.00 s grid. Raw numerical MSE mixes units; it is not a physical accuracy score. No coordinates are reset or rescaled. One-step diagnostics consume recorded current states, while autonomous forecasts consume only their initial permitted observation and then predictions.

## Raw numerical and coordinate-group MSE

| Method | Mode | Raw numerical MSE | Fixed contribution (127) | Physical contribution (11) | Time/index contribution (2) |
| --- | --- | --- | --- | --- | --- |
| phi_jepa | autonomous | 225.1636 | 4.558061e-12 | 0.0006112818 | 225.163 |
| phi_jepa | one_step | 0.4068017 | 8.234978e-15 | 4.056013e-06 | 0.4067977 |
| constant_context_text_ode | autonomous | 225.224 | 3.050464e-07 | 0.0006108224 | 225.2234 |
| constant_context_text_ode | one_step | 0.406912 | 5.511228e-10 | 4.05552e-06 | 0.406908 |
| fixed_projection_lr | autonomous | 0.003167118 | 9.18721e-08 | 0.003133379 | 3.364685e-05 |
| fixed_projection_lr | one_step | 3.024867e-06 | 2.480876e-10 | 3.024181e-06 | 4.378663e-10 |
| constant_context_text_rnn | autonomous | 302.5089 | 0.002989037 | 0.0008914917 | 302.505 |
| constant_context_text_rnn | one_step | 302.5089 | 0.002989037 | 0.0008914918 | 302.505 |
| no_enrichment | autonomous | 225.1637 | 4.668002e-12 | 0.0006112818 | 225.163 |
| no_enrichment | one_step | 0.4068021 | 8.433607e-15 | 4.056013e-06 | 0.4067981 |
| no_text_conditioning | autonomous | 225.3229 | 1.854557e-07 | 0.0006108371 | 225.3223 |
| no_text_conditioning | one_step | 0.4070907 | 3.3506e-10 | 4.055533e-06 | 0.4070866 |

Contributions sum to raw MSE and each divides by d=140. Full per-coordinate units, target/prediction ranges, squared errors and contribution fractions are in `numerical/<method>/aggregate.json`; each question has a separate JSON alongside it.

## Largest primary coordinate contributions

| Mode | Coordinate | Unit | Target range | Prediction range | Contribution | Fraction |
| --- | --- | --- | --- | --- | --- | --- |
| one_step | key:state/key:step_index | integration_step_count | [110.0, 500.0] | [102.45336151123047, 492.453369140625] | 0.4067977 | 0.99999 |
| one_step | key:state/key:measurements/quantity:load:angular_velocity/key:value | rad/s | [-0.43043702840805054, 0.7458824515342712] | [-0.4206981360912323, 0.7445488572120667] | 3.496647e-06 | 8.595458e-06 |
| one_step | key:state/key:measurements/quantity:load:swing_angle/key:value | rad | [-0.1322353035211563, 0.1917538195848465] | [-0.1445131003856659, 0.19012212753295898] | 3.208053e-07 | 7.886035e-07 |
| one_step | key:state/key:measurements/quantity:load:position/key:value/index:0 | m | [-0.10920833051204681, 0.13344107568264008] | [-0.10939531773328781, 0.13325408101081848] | 1.471651e-07 | 3.617611e-07 |
| one_step | key:state/key:measurements/quantity:support:velocity/key:value/index:0 | m/s | [0.0, 0.05580376088619232] | [-0.00014099485997576267, 0.055662766098976135] | 9.006569e-08 | 2.213995e-07 |
| one_step | key:state/key:measurements/quantity:load:position/key:value/index:2 | m | [1.0639820098876953, 1.4095094203948975] | [1.0639196634292603, 1.4094470739364624] | 8.90256e-10 | 2.188427e-09 |
| one_step | key:state/key:measurements/quantity:support:position/key:value/index:0 | m | [0.0, 0.005812891758978367] | [-6.246830162126571e-05, 0.005750423762947321] | 4.392898e-10 | 1.079862e-09 |
| one_step | key:fixed_conditioning/key:entities/entity:support/key:properties/quantity:support:model_body_iquat/key:value/index:0 | 1 | [1.0, 1.0] | [0.9999995231628418, 0.9999995231628418] | 1.624098e-15 | 3.992357e-15 |
| autonomous | key:state/key:step_index | integration_step_count | [110.0, 500.0] | [102.45336151123047, 198.13433837890625] | 225.163 | 0.9999973 |
| autonomous | key:state/key:measurements/quantity:load:angular_velocity/key:value | rad/s | [-0.43043702840805054, 0.7458824515342712] | [-0.28719091415405273, 0.5109145641326904] | 0.0003266109 | 1.450549e-06 |
| autonomous | key:state/key:measurements/quantity:load:swing_angle/key:value | rad | [-0.1322353035211563, 0.1917538195848465] | [-0.20814909040927887, 0.09412544220685959] | 0.0001943703 | 8.632402e-07 |
| autonomous | key:state/key:measurements/quantity:load:position/key:value/index:0 | m | [-0.10920833051204681, 0.13344107568264008] | [-0.1042514517903328, 0.08930656313896179] | 8.903015e-05 | 3.95402e-07 |
| autonomous | key:state/key:measurements/quantity:support:velocity/key:value/index:0 | m/s | [0.0, 0.05580376088619232] | [-0.0056397803127765656, -0.00014099453983362764] | 1.087847e-06 | 4.831364e-09 |
| autonomous | key:state/key:measurements/quantity:support:position/key:value/index:0 | m | [0.0, 0.005812891758978367] | [-0.0024987251963466406, -6.246813427424058e-05] | 1.15568e-07 | 5.132622e-10 |
| autonomous | key:state/key:measurements/quantity:load:position/key:value/index:2 | m | [1.0639820098876953, 1.4095094203948975] | [1.0657756328582764, 1.4082919359207153] | 6.70205e-08 | 2.976524e-10 |
| autonomous | key:fixed_conditioning/key:entities/entity:support/key:properties/quantity:support:model_body_iquat/key:value/index:0 | 1 | [1.0, 1.0] | [0.9999809265136719, 0.9999995231628418] | 8.989381e-13 | 3.992377e-15 |

## Autonomous physical trajectory errors

Pooled RMSE over the same 8×40 samples. Vector errors are Euclidean norms in native units. Valid-question counts are shown explicitly; failures are not converted to zero. Hold-last is an evaluation diagnostic, not a new trained/paper baseline.

| Method | Entity | Quantity | Unit | Valid / 8 | Pooled RMSE |
| --- | --- | --- | --- | --- | --- |
| phi_jepa | load | angular_velocity | rad/s | 8 | 0.2138353 |
| phi_jepa | load | position | m | 8 | 0.1116853 |
| phi_jepa | load | swing_angle | rad | 8 | 0.1649601 |
| phi_jepa | support | position | m | 8 | 0.004022377 |
| phi_jepa | support | velocity | m/s | 8 | 0.01234093 |
| constant_context_text_ode | load | angular_velocity | rad/s | 8 | 0.2138459 |
| constant_context_text_ode | load | position | m | 8 | 0.1115246 |
| constant_context_text_ode | load | swing_angle | rad | 8 | 0.1648695 |
| constant_context_text_ode | support | position | m | 8 | 0.003538948 |
| constant_context_text_ode | support | velocity | m/s | 8 | 0.01236389 |
| fixed_projection_lr | load | angular_velocity | rad/s | 8 | 0.5694944 |
| fixed_projection_lr | load | position | m | 8 | 0.05688677 |
| fixed_projection_lr | load | swing_angle | rad | 8 | 0.06418947 |
| fixed_projection_lr | support | position | m | 8 | 0.02731693 |
| fixed_projection_lr | support | velocity | m/s | 8 | 0.3259548 |
| constant_context_text_rnn | load | angular_velocity | rad/s | 8 | 0.3078671 |
| constant_context_text_rnn | load | position | m | 8 | 0.1496947 |
| constant_context_text_rnn | load | swing_angle | rad | 8 | 0.07870526 |
| constant_context_text_rnn | support | position | m | 8 | 0.002096433 |
| constant_context_text_rnn | support | velocity | m/s | 8 | 0.03767329 |
| no_enrichment | load | angular_velocity | rad/s | 8 | 0.2138353 |
| no_enrichment | load | position | m | 8 | 0.1116853 |
| no_enrichment | load | swing_angle | rad | 8 | 0.1649601 |
| no_enrichment | support | position | m | 8 | 0.00402242 |
| no_enrichment | support | velocity | m/s | 8 | 0.01234093 |
| no_text_conditioning | load | angular_velocity | rad/s | 8 | 0.2138454 |
| no_text_conditioning | load | position | m | 8 | 0.1115287 |
| no_text_conditioning | load | swing_angle | rad | 8 | 0.1648726 |
| no_text_conditioning | support | position | m | 8 | 0.003585906 |
| no_text_conditioning | support | velocity | m/s | 8 | 0.01236377 |
| hold_last_diagnostic | load | angular_velocity | rad/s | 8 | 0.2183019 |
| hold_last_diagnostic | load | position | m | 8 | 0.1101581 |
| hold_last_diagnostic | load | swing_angle | rad | 8 | 0.148269 |
| hold_last_diagnostic | support | position | m | 8 | 0.002642495 |
| hold_last_diagnostic | support | velocity | m/s | 8 | 0.0108181 |

## Queried endpoint errors

Mean and maximum absolute/Euclidean errors at T=1 s, with unchanged answer tolerances.

| Method | Target | Unit | Valid / 8 | Mean error | Maximum error |
| --- | --- | --- | --- | --- | --- |
| phi_jepa | load:position | m | 8 | 0.1158481 | 0.2128446 |
| phi_jepa | load:swing_angle | rad | 8 | 0.1725865 | 0.3627357 |
| phi_jepa | load:angular_velocity | rad/s | 8 | 0.3937007 | 0.8893414 |
| constant_context_text_ode | load:position | m | 8 | 0.1156505 | 0.2120896 |
| constant_context_text_ode | load:swing_angle | rad | 8 | 0.1724408 | 0.3624442 |
| constant_context_text_ode | load:angular_velocity | rad/s | 8 | 0.3937006 | 0.8895965 |
| fixed_projection_lr | load:position | m | 8 | 0.09687677 | 0.1800125 |
| fixed_projection_lr | load:swing_angle | rad | 8 | 0.1307059 | 0.3925426 |
| fixed_projection_lr | load:angular_velocity | rad/s | 8 | 0.8034942 | 1.443376 |
| constant_context_text_rnn | load:position | m | 8 | 0.145018 | 0.2256583 |
| constant_context_text_rnn | load:swing_angle | rad | 8 | 0.07774545 | 0.1387939 |
| constant_context_text_rnn | load:angular_velocity | rad/s | 8 | 0.1701641 | 0.416264 |
| no_enrichment | load:position | m | 8 | 0.1158479 | 0.2128447 |
| no_enrichment | load:swing_angle | rad | 8 | 0.1725865 | 0.3627357 |
| no_enrichment | load:angular_velocity | rad/s | 8 | 0.3937007 | 0.8893414 |
| no_text_conditioning | load:position | m | 8 | 0.1156509 | 0.2121117 |
| no_text_conditioning | load:swing_angle | rad | 8 | 0.1724459 | 0.3624543 |
| no_text_conditioning | load:angular_velocity | rad/s | 8 | 0.3937006 | 0.8895846 |
| hold_last_diagnostic | load:position | m | 8 | 0.1139035 | 0.2053368 |
| hold_last_diagnostic | load:swing_angle | rad | 8 | 0.1508319 | 0.297468 |
| hold_last_diagnostic | load:angular_velocity | rad/s | 8 | 0.4017234 | 0.9426852 |

## Named one-step physical errors

Derived from the coordinate MSEs against FP32 training-format references; the autonomous table uses the original saved reference precision. This precision distinction is explicit and does not change time alignment.

| Method | Entity | Quantity | Unit | Valid / 8 | Pooled one-step RMSE |
| --- | --- | --- | --- | --- | --- |
| phi_jepa | load | angular_velocity | rad/s | 8 | 0.02212534 |
| phi_jepa | load | position | m | 8 | 0.004552773 |
| phi_jepa | load | swing_angle | rad | 8 | 0.006701696 |
| phi_jepa | support | position | m | 8 | 0.0002479931 |
| phi_jepa | support | velocity | m/s | 8 | 0.003550943 |
| constant_context_text_ode | load | angular_velocity | rad/s | 8 | 0.02212611 |
| constant_context_text_ode | load | position | m | 8 | 0.004547203 |
| constant_context_text_ode | load | swing_angle | rad | 8 | 0.006698209 |
| constant_context_text_ode | support | position | m | 8 | 0.0002354435 |
| constant_context_text_ode | support | velocity | m/s | 8 | 0.003551012 |
| fixed_projection_lr | load | angular_velocity | rad/s | 8 | 0.01733644 |
| fixed_projection_lr | load | position | m | 8 | 0.00144467 |
| fixed_projection_lr | load | swing_angle | rad | 8 | 0.0001870159 |
| fixed_projection_lr | support | position | m | 8 | 0.0001276051 |
| fixed_projection_lr | support | velocity | m/s | 8 | 0.01098613 |
| constant_context_text_rnn | load | angular_velocity | rad/s | 8 | 0.3078671 |
| constant_context_text_rnn | load | position | m | 8 | 0.1496947 |
| constant_context_text_rnn | load | swing_angle | rad | 8 | 0.07870527 |
| constant_context_text_rnn | support | position | m | 8 | 0.002096338 |
| constant_context_text_rnn | support | velocity | m/s | 8 | 0.03767315 |
| no_enrichment | load | angular_velocity | rad/s | 8 | 0.02212534 |
| no_enrichment | load | position | m | 8 | 0.004552772 |
| no_enrichment | load | swing_angle | rad | 8 | 0.006701697 |
| no_enrichment | support | position | m | 8 | 0.0002479942 |
| no_enrichment | support | velocity | m/s | 8 | 0.003550943 |
| no_text_conditioning | load | angular_velocity | rad/s | 8 | 0.02212607 |
| no_text_conditioning | load | position | m | 8 | 0.004547327 |
| no_text_conditioning | load | swing_angle | rad | 8 | 0.006698332 |
| no_text_conditioning | support | position | m | 8 | 0.0002365922 |
| no_text_conditioning | support | velocity | m/s | 8 | 0.003551012 |
