# Question and answer comparison

Same selected public question for every requested method. Numerical inference is fresh; each answer records cache reuse or fresh generation.

Answer policy: vanilla=cache; Phi-JEPA/numerical methods=cache. Shared provider cap: USD 0.0.

Phi-JEPA uses qualified forecast/readout Boolean outputs; vanilla GPT-5.6 Sol may attempt all requested components directly. Unsupported components and failures remain in denominators.

Assessment is partial and uncalibrated. Human-reviewed clarification is separate and is not invoked.

- phi_jepa: 12/12 valid answers; complete correct: 2; statuses: {'success': 12}
- vanilla_llm: 8/12 valid answers; complete correct: 6; statuses: {'success': 8, 'cache_miss': 4}

## driving — 1b17551c57d38101163d56c0cd8a7aaa

At 2 seconds from the initialized state, what are car forward_position (m), car forward_velocity (m/s), car stopped_by_T (1), under the public model, control law and scheduled intervention?

Scenario: `d2b5ec3f1c208b39618c6961045dd913`; partition: `test_id`.

### phi_jepa

At t = 2.0 s, the forecast gives a forward position of 3.874626 m and a forward velocity of 1.423495 m/s. The sampled public-rule readout reports that the car has not stopped by this time.

Origin: validated_cache. [Raw answer](driving/1b17551c57d38101163d56c0cd8a7aaa/phi_jepa/answer.json)

Strict evaluation: not completely correct; 1/3 target components correct.

### vanilla_llm

At t=2.0 s, the car is predicted at 4.00 m with forward velocity 1.01 m/s and has not stopped.

Origin: validated_cache. [Raw answer](driving/1b17551c57d38101163d56c0cd8a7aaa/vanilla_llm/answer.json)

Strict evaluation: not completely correct; 1/3 target components correct.

## driving — 1fe18e46f5bba9f1cbc18d0da12857e5

At 2 seconds from the initialized state, what are car forward_position (m), car forward_velocity (m/s), car stopped_by_T (1), under the public model, control law and scheduled intervention?

Scenario: `ec544ef6e5c551a1aeb9243def016215`; partition: `test_id`.

### phi_jepa

At t = 2.0 s, the forecast gives forward position 3.984564 m and forward velocity 1.169379 m/s. The sampled public-rule readout reports that the car had not stopped by this time.

Origin: validated_cache. [Raw answer](driving/1fe18e46f5bba9f1cbc18d0da12857e5/phi_jepa/answer.json)

Strict evaluation: not completely correct; 1/3 target components correct.

### vanilla_llm

At t=2.0 s: forward position ≈3.50 m, forward velocity ≈0.74 m/s, and the car has not stopped.

Origin: validated_cache. [Raw answer](driving/1fe18e46f5bba9f1cbc18d0da12857e5/vanilla_llm/answer.json)

Strict evaluation: not completely correct; 1/3 target components correct.

## driving — 405ccb429d10a4e5a9acc28ad0299b8d

At 2 seconds from the initialized state, what are car forward_position (m), car forward_velocity (m/s), car stopped_by_T (1), under the public model, control law and scheduled intervention?

Scenario: `b7e4bc73d4ec7eac058909ff57164067`; partition: `test_id`.

### phi_jepa

At t = 2.0 s, the forecast gives a forward position of 2.52154 m and forward velocity of -0.12468 m/s. The sampled public-rule readout reports stopped_by_T = false.

Origin: validated_cache. [Raw answer](driving/405ccb429d10a4e5a9acc28ad0299b8d/phi_jepa/answer.json)

Strict evaluation: not completely correct; 0/3 target components correct.

### vanilla_llm

At 2.0 s, the car is approximately at 1.10 m with zero forward velocity and has stopped by T.

Origin: validated_cache. [Raw answer](driving/405ccb429d10a4e5a9acc28ad0299b8d/vanilla_llm/answer.json)

Strict evaluation: complete correct; 3/3 target components correct.

## object_pushing_stacking — 00f8dbb71fbc1c280d2a69e2b60845fa

At 1 seconds from the initialized state, what are block_1 position (m), block_1 orientation (1), block_2 position (m), block_2 orientation (1), block_2 stable_stack (1), block_2 support_lost (1), block_2 left_table (1), under the public model, control law and scheduled intervention?

Scenario: `a19052f1edb2d16b16a3dc89b552271e`; partition: `test_id`.

### phi_jepa

At t=1.0 s, the forecast gives block_1 position [-0.151276, 0.007640, 0.050045] m and orientation [-0.006157, -0.007216, 0.003709, 1.000036]; block_2 position [0.050036, 0.010745, 0.050000] m and orientation [-0.008544, -0.001351, 0.003951, 0.999978]. The sampled rule readout says block_2 has not left the table. stable_stack and support_lost are unsupported because contact-force history is unavailable.

Origin: validated_cache. [Raw answer](object_pushing_stacking/00f8dbb71fbc1c280d2a69e2b60845fa/phi_jepa/answer.json)

Strict evaluation: not completely correct; 2/7 target components correct.

### vanilla_llm

At 1.0 s, block_1 has moved only slightly in +x; block_2 remains stationary and unstacked on the table.

Origin: validated_cache. [Raw answer](object_pushing_stacking/00f8dbb71fbc1c280d2a69e2b60845fa/vanilla_llm/answer.json)

Strict evaluation: complete correct; 7/7 target components correct.

## object_pushing_stacking — 0ddf0f310b2c9574f2360c3685a75c88

At 1 seconds from the initialized state, what are block_1 position (m), block_1 orientation (1), block_2 position (m), block_2 orientation (1), block_2 stable_stack (1), block_2 support_lost (1), block_2 left_table (1), under the public model, control law and scheduled intervention?

Scenario: `08065f0c04265c6b9c0c9b32b4ee17f5`; partition: `test_id`.

### phi_jepa

At t = 1.0 s, the autonomous numerical forecast gives block_1 position [-0.151306, 0.006970, 0.049886] m and orientation [-0.005336, -0.005896, 0.003852, 1.000029] (xyzw); block_2 position [0.050037, 0.005852, 0.049988] m and orientation [-0.005642, -0.003166, 0.005140, 0.999990] (xyzw). The sampled rule readout says block_2 has not left the table. stable_stack and support_lost are unsupported because contact-force history is missing.

Origin: validated_cache. [Raw answer](object_pushing_stacking/0ddf0f310b2c9574f2360c3685a75c88/phi_jepa/answer.json)

Strict evaluation: not completely correct; 3/7 target components correct.

### vanilla_llm

At t=1.0 s, both blocks remain essentially at their initial resting poses; block_2 is not stacked, has not lost support, and remains on the table.

Origin: validated_cache. [Raw answer](object_pushing_stacking/0ddf0f310b2c9574f2360c3685a75c88/vanilla_llm/answer.json)

Strict evaluation: complete correct; 7/7 target components correct.

## object_pushing_stacking — 13e3010fe7015400ed940c026fb73c46

At 1 seconds from the initialized state, what are block_1 position (m), block_1 orientation (1), block_2 position (m), block_2 orientation (1), block_2 stable_stack (1), block_2 support_lost (1), block_2 left_table (1), under the public model, control law and scheduled intervention?

Scenario: `3e43bce3fdf8294b2f4952a9f38386be`; partition: `test_id`.

### phi_jepa

At t=1.0 s, the autonomous numerical forecast gives block_1 position [-0.147566, 0.008000, 0.049500] m and orientation [-0.001409, -0.005507, 0.001776, 1.000000] (xyzw); block_2 position [0.050048, 0.000766, 0.049987] m and orientation [0.004168, 0.000756, 0.002554, 1.000032] (xyzw). The sampled public-rule readout says block_2 left_table is false. stable_stack and support_lost are unsupported because contact-force history is missing.

Origin: validated_cache. [Raw answer](object_pushing_stacking/13e3010fe7015400ed940c026fb73c46/phi_jepa/answer.json)

Strict evaluation: not completely correct; 4/7 target components correct.

### vanilla_llm

At t=1.0 s, block 1 is predicted to have shifted slightly in +x without contacting block 2; both blocks remain upright on the table.

Origin: validated_cache. [Raw answer](object_pushing_stacking/13e3010fe7015400ed940c026fb73c46/vanilla_llm/answer.json)

Strict evaluation: complete correct; 7/7 target components correct.

## robotic_arm — 0c065579c6abe4545b3d9a491308c982

At 1 seconds from the initialized state, what are joint_1 angle (rad), joint_1 angular_velocity (rad/s), joint_2 angle (rad), joint_2 angular_velocity (rad/s), tip position (m), arm joint_limit_by_T (1), under the public model, control law and scheduled intervention?

Scenario: `f776dc63f7d530344c669412ae69f7ea`; partition: `test_id`.

### phi_jepa

At t = 1.0 s, the autonomous numerical forecast gives joint_1 angle 3.236399 rad and angular velocity -13.468414 rad/s; joint_2 angle 1.172999 rad and angular velocity 41.712055 rad/s; and tip position [-0.915900, -0.003031, 1.136288] m. The sampled public-rule readout reports joint_limit_by_T = true.

Origin: validated_cache. [Raw answer](robotic_arm/0c065579c6abe4545b3d9a491308c982/phi_jepa/answer.json)

Strict evaluation: not completely correct; 0/6 target components correct.

### vanilla_llm

No valid final answer. Status: cache_miss. Reason: cache_miss: fresh answer requires --max-api-usd greater than zero.

Origin: not_generated. [Raw answer](robotic_arm/0c065579c6abe4545b3d9a491308c982/vanilla_llm/answer.json)

Strict evaluation: not completely correct; 0/6 target components correct.

## robotic_arm — 1106cfc41a5cb3feee37de48eff42c2b

At 1 seconds from the initialized state, what are joint_1 angle (rad), joint_1 angular_velocity (rad/s), joint_2 angle (rad), joint_2 angular_velocity (rad/s), tip position (m), arm joint_limit_by_T (1), under the public model, control law and scheduled intervention?

Scenario: `f6402906c55e2736aa26e7767d1726e6`; partition: `test_id`.

### phi_jepa

At t=1.0 s, the numerical forecast gives joint_1 angle 3.95936 rad and angular velocity -14.48846 rad/s; joint_2 angle 0.47976 rad and angular velocity 54.79391 rad/s; and tip position [-0.750647, 0.002106, -0.323395] m. The sampled public-rule readout reports that a joint limit was reached by T: true.

Origin: validated_cache. [Raw answer](robotic_arm/1106cfc41a5cb3feee37de48eff42c2b/phi_jepa/answer.json)

Strict evaluation: not completely correct; 0/6 target components correct.

### vanilla_llm

No valid final answer. Status: cache_miss. Reason: cache_miss: fresh answer requires --max-api-usd greater than zero.

Origin: not_generated. [Raw answer](robotic_arm/1106cfc41a5cb3feee37de48eff42c2b/vanilla_llm/answer.json)

Strict evaluation: not completely correct; 0/6 target components correct.

## robotic_arm — 1c3be88d25644692348082004d98aa77

At 1 seconds from the initialized state, what are joint_1 angle (rad), joint_1 angular_velocity (rad/s), joint_2 angle (rad), joint_2 angular_velocity (rad/s), tip position (m), arm joint_limit_by_T (1), under the public model, control law and scheduled intervention?

Scenario: `7e13ee10f2e759ee3ac7d181cdc7a903`; partition: `test_id`.

### phi_jepa

At t = 1.0 s, the autonomous numerical forecast gives joint_1 = 3.331106 rad at -14.014019 rad/s, joint_2 = 0.268348 rad at 56.474358 rad/s, and tip position = [-0.645769, 0.001811, 0.120873] m. The sampled public-rule readout reports joint_limit_by_T = true.

Origin: validated_cache. [Raw answer](robotic_arm/1c3be88d25644692348082004d98aa77/phi_jepa/answer.json)

Strict evaluation: not completely correct; 1/6 target components correct.

### vanilla_llm

No valid final answer. Status: cache_miss. Reason: cache_miss: fresh answer requires --max-api-usd greater than zero.

Origin: not_generated. [Raw answer](robotic_arm/1c3be88d25644692348082004d98aa77/vanilla_llm/answer.json)

Strict evaluation: not completely correct; 0/6 target components correct.

## tethered_load — 337b9ff1f5c00610845cea856af91c3d

At 1 seconds from the initialized state, what are load position (m), load swing_angle (rad), load angular_velocity (rad/s), load boundary_crossed (1), under the public model, control law and scheduled intervention?

Scenario: `ff1f70d36d059af6fbfbfb2cfb2058ba`; partition: `test_id`.

### phi_jepa

At t = 1.0 s, the forecast gives load position [0.0546181, -0.0000135, 1.4274728] m, swing angle 0.0846304 rad, and angular velocity -0.4626721 rad/s. The sampled public-rule readout reports that the boundary was not crossed.

Origin: validated_cache. [Raw answer](tethered_load/337b9ff1f5c00610845cea856af91c3d/phi_jepa/answer.json)

Strict evaluation: complete correct; 4/4 target components correct.

### vanilla_llm

No valid final answer. Status: cache_miss. Reason: cache_miss: fresh answer requires --max-api-usd greater than zero.

Origin: not_generated. [Raw answer](tethered_load/337b9ff1f5c00610845cea856af91c3d/vanilla_llm/answer.json)

Strict evaluation: not completely correct; 0/4 target components correct.

## tethered_load — 3ef2c2fd13bee92be2971a2e1a152484

At 1 seconds from the initialized state, what are load position (m), load swing_angle (rad), load angular_velocity (rad/s), load boundary_crossed (1), under the public model, control law and scheduled intervention?

Scenario: `a6fb0ec3a6e8f5a584639b7ba5617186`; partition: `test_id`.

### phi_jepa

At t = 1.0 s, the forecast gives load position [-0.0699091, -2.55709e-7, 1.3113737] m, swing angle -0.112357 rad, and angular velocity 0.325737 rad/s. The sampled public-rule readout reports boundary_crossed = false.

Origin: validated_cache. [Raw answer](tethered_load/3ef2c2fd13bee92be2971a2e1a152484/phi_jepa/answer.json)

Strict evaluation: complete correct; 4/4 target components correct.

### vanilla_llm

At t=1.0 s: position ≈ [-0.0769, 0, 1.3084] m, swing angle ≈ -0.1159 rad, angular velocity ≈ 0.3188 rad/s, and the boundary was not crossed.

Origin: validated_cache. [Raw answer](tethered_load/3ef2c2fd13bee92be2971a2e1a152484/vanilla_llm/answer.json)

Strict evaluation: complete correct; 4/4 target components correct.

## tethered_load — 4e83f57c0c70dda7d9910ab8935fe6cb

At 1 seconds from the initialized state, what are load position (m), load swing_angle (rad), load angular_velocity (rad/s), load boundary_crossed (1), under the public model, control law and scheduled intervention?

Scenario: `803c2b38ec1badf7071cf82a15836ab2`; partition: `test_id`.

### phi_jepa

At t = 1.0 s, the load position is [-0.05638845, 0.00003265, 1.45144308] m, swing angle is -0.11822569 rad, and angular velocity is 0.58181489 rad/s. The sampled public-rule readout reports boundary_crossed = false.

Origin: validated_cache. [Raw answer](tethered_load/4e83f57c0c70dda7d9910ab8935fe6cb/phi_jepa/answer.json)

Strict evaluation: not completely correct; 1/4 target components correct.

### vanilla_llm

At t=1.0 s, the predicted load position is [-0.0408, 0, 1.4474] m, swing angle is -0.0834 rad, angular velocity is 0.6547 rad/s, and the boundary has not been crossed.

Origin: validated_cache. [Raw answer](tethered_load/4e83f57c0c70dda7d9910ab8935fe6cb/vanilla_llm/answer.json)

Strict evaluation: complete correct; 4/4 target components correct.
