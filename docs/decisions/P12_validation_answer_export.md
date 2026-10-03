# Validation answer replay

29 September 2026: user explicitly requested inference replay to expose today's
trained-model answers. Use the existing validation-selected checkpoints for all
1,336 original validation questions; freeze selection and tolerances. Set a fresh
20-minute, 1,336-request local CPU cap. No training, provider calls, new baseline
generation or confirmation access. Keep raw predictions/augmented trajectories
separate from the subsequent reference join. Save all outputs in the new
`docs/reviews/artifacts/P12_validation_answers/` directory and verify every typed
result against the previously saved validation results. This request does not
activate any pending parent-thread experiment or renew its execution budgets.
