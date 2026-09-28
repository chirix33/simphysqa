# Stage 4 output policy — 24 September 2026

Authority: explicit user reply in the coding session. Implement deterministic
public-rule outputs only. No new head/loss, Boolean casting, ODE state change or
training change. Answer provider is the same frozen OpenAI `gpt-5.6-sol` alias.
Original extraction/judge/answer assets are preserved; the new answer prompt is
`docs/assets/p04a_answer_v1.json` with a dynamically target-bound JSON schema.

Named forecasts contain registered state measurements only. Each vector retains
its ordered components and public unit/frame; physical sample time comes from
the solver clock. Predicted timestamp, step index, fixed-conditioning coordinates
and predicted p remain in the immutable full augmented trajectory, not the
physical payload. The LLM answer is a separate artifact, never numerical truth.

Support is qualified per target, with exact rule version/text, domain/entity,
query semantics, convention, units/frame, channel shape and time coverage. Event
histories require every 0.02-second sample. No interpolation is performed.
Events and duration breaks between samples can be missed. Supported means the
sampled rule can be evaluated, not that continuous-time event recovery is exact.

- `left_table`: requested endpoint COM x/y outside [-2,2], not exit-by-time.
- `joint_limit_by_T`: any sampled magnitude >=2.8 rad since initialized time 0;
  onset latch rearmed when both magnitudes <2.795. Complete public history starts
  at 0 to establish initial state. The Boolean is accumulated even after return.
- `boundary_crossed`: positive crossing above 0.105 m after cutoff, rearmed below
  0.095. Require observed cutoff x<0.095 to establish the initial untriggered
  state under the public rule. Other initial states are explicitly unsupported;
  do not import the simulator's private latch initialization convention.
- `stopped_by_T`: sampled forward speed strictly <0.02 m/s and planar speed
  strictly <0.03 m/s for a contiguous 0.2-second sampled span. Requires complete
  history from 0, full velocity vector and forward velocity with correct units.
- `stable_stack` and `support_lost`: unsupported due to missing contact force and
  contact history. These remain work toward complete dataset support.

Malformed/nonfinite/foreign forecasts raise `InvalidForecast`; missing target
evidence returns unsupported/null/reason. Public observed Boolean channels are
not consulted. Gold labels/events/references are absent from inference.

The answer parser requires every target exactly once and validates all bindings,
finite scalar/vector/Boolean types, dimensions and unsupported-null semantics.
Boolean outputs must exactly match the supplied rule readout. Public-only controls
may generate numerical estimates, but Boolean outputs remain unsupported without
the rule's forecast evidence. Consequently public-only complete-answer success is
not a fair unrestricted Boolean-solving comparison; report coverage separately.

Bounded validation profile: one existing P03 tether validation question, three
conditions (public-only, predicted, reversed forecast order with timestamps kept),
at most six attempts and 4096 output tokens/call. No additional training or ODE
solve. User spending authorization remains unlimited; these are engineering caps.
No calibration or final test selection occurs. Cached replies preserve actual
alias outputs; future fresh API calls cannot claim immutable model reproducibility.
