# Question and answer comparison

Same selected public question for every requested method. Numerical inference is fresh; each answer records cache reuse or fresh generation.

Answer policy: vanilla=cache; Phi-JEPA/numerical methods=cache. Shared provider cap: USD 0.0.

Phi-JEPA uses qualified forecast/readout Boolean outputs; vanilla GPT-5.6 Sol may attempt all requested components directly. Unsupported components and failures remain in denominators.

Assessment is partial and uncalibrated. Human-reviewed clarification is separate and is not invoked.

- phi_jepa: 4/4 valid answers; complete correct: 1; statuses: {'success': 4}
- vanilla_llm: 2/4 valid answers; complete correct: 1; statuses: {'success': 2, 'cache_miss': 2}

## driving — 1b17551c57d38101163d56c0cd8a7aaa

At 2 seconds from the initialized state, what are car forward_position (m), car forward_velocity (m/s), car stopped_by_T (1), under the public model, control law and scheduled intervention?

Scenario: `d2b5ec3f1c208b39618c6961045dd913`; partition: `test_id`.

### Gold and predicted answers

Gold values are evaluator references added after inference. Values retain their original precision.

| Target | Query / time (s) | Unit | Frame | Gold answer | phi_jepa | vanilla_llm |
| --- | --- | --- | --- | --- | --- | --- |
| car:forward_position | at_time: 2.0–2.0 | m | world | 4.039476433946182 | 3.874626398086548 | 4.0 |
| car:forward_velocity | at_time: 2.0–2.0 | m/s | world | 1.0863504657328382 | 1.423494577407837 | 1.01 |
| car:stopped_by_T | at_time: 2.0–2.0 | 1 | world | false | false | false |

[Typed gold answers](evaluation/private/gold_answers.json)

### phi_jepa

At t = 2.0 s, the forecast gives a forward position of 3.874626 m and a forward velocity of 1.423495 m/s. The sampled public-rule readout reports that the car has not stopped by this time.

Origin: validated_cache. [Raw answer](driving/1b17551c57d38101163d56c0cd8a7aaa/phi_jepa/answer.json)

Strict evaluation: not completely correct; 1/3 target components correct.

### vanilla_llm

At t=2.0 s, the car is predicted at 4.00 m with forward velocity 1.01 m/s and has not stopped.

Origin: validated_cache. [Raw answer](driving/1b17551c57d38101163d56c0cd8a7aaa/vanilla_llm/answer.json)

Strict evaluation: not completely correct; 1/3 target components correct.

## object_pushing_stacking — 00f8dbb71fbc1c280d2a69e2b60845fa

At 1 seconds from the initialized state, what are block_1 position (m), block_1 orientation (1), block_2 position (m), block_2 orientation (1), block_2 stable_stack (1), block_2 support_lost (1), block_2 left_table (1), under the public model, control law and scheduled intervention?

Scenario: `a19052f1edb2d16b16a3dc89b552271e`; partition: `test_id`.

### Gold and predicted answers

Gold values are evaluator references added after inference. Values retain their original precision.

| Target | Query / time (s) | Unit | Frame | Gold answer | phi_jepa | vanilla_llm |
| --- | --- | --- | --- | --- | --- | --- |
| block_1:position | at_time: 1.0–1.0 | m | world | [-0.1495761675808066, 1.1561483698673552e-05, 0.04998941279708887] | [-0.151275634765625, 0.007639611139893532, 0.05004465952515602] | [-0.14967, 2e-06, 0.049989] |
| block_1:orientation | at_time: 1.0–1.0 | 1 | world | [8.979339182394936e-07, -7.335376492746997e-06, 5.261743928224836e-05, 0.9999999985883955] | [-0.006156891118735075, -0.007215671706944704, 0.0037092682905495167, 1.0000355243682861] | [0, 0, 0, 1] |
| block_2:position | at_time: 1.0–1.0 | m | world | [0.04999860372842259, 1.0877367674931558e-05, 0.049989412791110285] | [0.05003571882843971, 0.010744769126176834, 0.04999954625964165] | [0.049999, 2e-06, 0.049989] |
| block_2:orientation | at_time: 1.0–1.0 | 1 | world | [8.974261795093534e-07, -7.335516259925915e-06, -1.9326942790551928e-05, 0.999999999785927] | [-0.008543865755200386, -0.0013506637187674642, 0.003950655460357666, 0.999978244304657] | [0, 0, 0, 1] |
| block_2:stable_stack | at_time: 1.0–1.0 | 1 | world | false | unsupported: missing_contact_force_and_history | false |
| block_2:support_lost | at_time: 1.0–1.0 | 1 | world | false | unsupported: missing_contact_force_and_history | false |
| block_2:left_table | at_time: 1.0–1.0 | 1 | world | false | false | false |

[Typed gold answers](evaluation/private/gold_answers.json)

### phi_jepa

At t=1.0 s, the forecast gives block_1 position [-0.151276, 0.007640, 0.050045] m and orientation [-0.006157, -0.007216, 0.003709, 1.000036]; block_2 position [0.050036, 0.010745, 0.050000] m and orientation [-0.008544, -0.001351, 0.003951, 0.999978]. The sampled rule readout says block_2 has not left the table. stable_stack and support_lost are unsupported because contact-force history is unavailable.

Origin: validated_cache. [Raw answer](object_pushing_stacking/00f8dbb71fbc1c280d2a69e2b60845fa/phi_jepa/answer.json)

Strict evaluation: not completely correct; 2/7 target components correct.

### vanilla_llm

At 1.0 s, block_1 has moved only slightly in +x; block_2 remains stationary and unstacked on the table.

Origin: validated_cache. [Raw answer](object_pushing_stacking/00f8dbb71fbc1c280d2a69e2b60845fa/vanilla_llm/answer.json)

Strict evaluation: complete correct; 7/7 target components correct.

## robotic_arm — 0c065579c6abe4545b3d9a491308c982

At 1 seconds from the initialized state, what are joint_1 angle (rad), joint_1 angular_velocity (rad/s), joint_2 angle (rad), joint_2 angular_velocity (rad/s), tip position (m), arm joint_limit_by_T (1), under the public model, control law and scheduled intervention?

Scenario: `f776dc63f7d530344c669412ae69f7ea`; partition: `test_id`.

### Gold and predicted answers

Gold values are evaluator references added after inference. Values retain their original precision.

| Target | Query / time (s) | Unit | Frame | Gold answer | phi_jepa | vanilla_llm |
| --- | --- | --- | --- | --- | --- | --- |
| joint_1:angle | at_time: 1.0–1.0 | rad | joint_local | 2.3411365760495575 | 3.236398935317993 | cache_miss: cache_miss: fresh answer requires --max-api-usd greater than zero |
| joint_1:angular_velocity | at_time: 1.0–1.0 | rad/s | joint_local | -3.4244248944414446 | -13.468414306640625 | cache_miss: cache_miss: fresh answer requires --max-api-usd greater than zero |
| joint_2:angle | at_time: 1.0–1.0 | rad | joint_local | 1.2643347166890408 | 1.1729987859725952 | cache_miss: cache_miss: fresh answer requires --max-api-usd greater than zero |
| joint_2:angular_velocity | at_time: 1.0–1.0 | rad/s | joint_local | 2.071767922277103 | 41.71205520629883 | cache_miss: cache_miss: fresh answer requires --max-api-usd greater than zero |
| tip:position | at_time: 1.0–1.0 | m | world | [-0.5468489409512092, 0.0, 0.8471565595374988] | [-0.9159002304077148, -0.0030313213355839252, 1.136288046836853] | cache_miss: cache_miss: fresh answer requires --max-api-usd greater than zero |
| arm:joint_limit_by_T | at_time: 1.0–1.0 | 1 | world | false | true | cache_miss: cache_miss: fresh answer requires --max-api-usd greater than zero |

[Typed gold answers](evaluation/private/gold_answers.json)

### phi_jepa

At t = 1.0 s, the autonomous numerical forecast gives joint_1 angle 3.236399 rad and angular velocity -13.468414 rad/s; joint_2 angle 1.172999 rad and angular velocity 41.712055 rad/s; and tip position [-0.915900, -0.003031, 1.136288] m. The sampled public-rule readout reports joint_limit_by_T = true.

Origin: validated_cache. [Raw answer](robotic_arm/0c065579c6abe4545b3d9a491308c982/phi_jepa/answer.json)

Strict evaluation: not completely correct; 0/6 target components correct.

### vanilla_llm

No valid final answer. Status: cache_miss. Reason: cache_miss: fresh answer requires --max-api-usd greater than zero.

Origin: not_generated. [Raw answer](robotic_arm/0c065579c6abe4545b3d9a491308c982/vanilla_llm/answer.json)

Strict evaluation: not completely correct; 0/6 target components correct.

## tethered_load — 337b9ff1f5c00610845cea856af91c3d

At 1 seconds from the initialized state, what are load position (m), load swing_angle (rad), load angular_velocity (rad/s), load boundary_crossed (1), under the public model, control law and scheduled intervention?

Scenario: `ff1f70d36d059af6fbfbfb2cfb2058ba`; partition: `test_id`.

### Gold and predicted answers

Gold values are evaluator references added after inference. Values retain their original precision.

| Target | Query / time (s) | Unit | Frame | Gold answer | phi_jepa | vanilla_llm |
| --- | --- | --- | --- | --- | --- | --- |
| load:position | at_time: 1.0–1.0 | m | world | [0.05047588642485897, 0.0, 1.426361248206019] | [0.05461813881993294, -1.346789940726012e-05, 1.4274728298187256] | cache_miss: cache_miss: fresh answer requires --max-api-usd greater than zero |
| load:swing_angle | at_time: 1.0–1.0 | rad | world | 0.08285260157432975 | 0.08463044464588165 | cache_miss: cache_miss: fresh answer requires --max-api-usd greater than zero |
| load:angular_velocity | at_time: 1.0–1.0 | rad/s | world | -0.48077106495733646 | -0.46267205476760864 | cache_miss: cache_miss: fresh answer requires --max-api-usd greater than zero |
| load:boundary_crossed | at_time: 1.0–1.0 | 1 | world | false | false | cache_miss: cache_miss: fresh answer requires --max-api-usd greater than zero |

[Typed gold answers](evaluation/private/gold_answers.json)

### phi_jepa

At t = 1.0 s, the forecast gives load position [0.0546181, -0.0000135, 1.4274728] m, swing angle 0.0846304 rad, and angular velocity -0.4626721 rad/s. The sampled public-rule readout reports that the boundary was not crossed.

Origin: validated_cache. [Raw answer](tethered_load/337b9ff1f5c00610845cea856af91c3d/phi_jepa/answer.json)

Strict evaluation: complete correct; 4/4 target components correct.

### vanilla_llm

No valid final answer. Status: cache_miss. Reason: cache_miss: fresh answer requires --max-api-usd greater than zero.

Origin: not_generated. [Raw answer](tethered_load/337b9ff1f5c00610845cea856af91c3d/vanilla_llm/answer.json)

Strict evaluation: not completely correct; 0/4 target components correct.
