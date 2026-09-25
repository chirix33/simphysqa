# Post-P07 four-domain output and assessment coverage

25 September 2026. Source baseline `5810d1899007ae602c3db1ca486d43a1b7865ba4`.
Companion to [the focused audit](Post_P07_focused_audit.md).

The inventory reads all 8,038 **train/validation public question contexts** in the
frozen four-domain release: driving 888, object pushing/stacking 2,400, robotic arm
2,350, tethered load 2,400. It does not open test/OOD outcomes. The 20 bindings below
exhaust `simulation/records.py:CHANNELS` for these four domains. Quadruped source
is outside this accepted four-domain model scope.

“Qualified” counts exercise the current readout with a hypothetical complete,
finite numerical trajectory made from repeated public measurements. They measure
interface/evidence availability, **not forecast accuracy, event accuracy, model
readiness or actual forecast support on unseen outputs**. A real forecast must
pass the same checks. Raw counts and exact public rule strings are in
[coverage-inventory.json](artifacts/Post_P07/coverage-inventory.json).

All rows require exact entity/quantity binding, rule version/text, units, frame,
coordinate convention, numerical type/shape and requested time coverage. Missing
evidence returns `unsupported` with a reason; malformed/nonfinite/foreign forecasts
raise `InvalidForecast` separately. No unsupported value becomes false or zero.

| Domain / target | Supported now? Qualified / eligible | Required signals and history | Available in permitted inputs / predicted n? | Exact missing information or mechanism | Fix possible under current contract? | Scientific decision needed? |
| --- | --- | --- | --- | --- | --- | --- |
| Arm / joint_1 angle | Conditional; 2350/2350 | Scalar rad, joint_local, at T | Yes, observed and numerical prediction | None for endpoint readout; accuracy unqualified | Existing generic readout | No |
| Arm / joint_1 angular_velocity | Conditional; 2350/2350 | Scalar rad/s, joint_local, at T | Yes / yes | Same accuracy gap | Existing generic readout | No |
| Arm / joint_2 angle | Conditional; 2350/2350 | Scalar rad, joint_local, at T | Yes / yes | Same accuracy gap | Existing generic readout | No |
| Arm / joint_2 angular_velocity | Conditional; 2350/2350 | Scalar rad/s, joint_local, at T | Yes / yes | Same accuracy gap | Existing generic readout | No |
| Arm / tip position | Conditional; 2350/2350 | xyz m, world, at T | Yes / yes | Same accuracy gap | Existing generic readout | No |
| Arm / joint_limit_by_T | Conditional sampled event; 2350/2350 | Both joint angles from initialized t=0 through T, 0.02 s grid; onset magnitude >=2.8 rad, rearm <2.795 rad | Public history and future angles available | Between-sample events cannot be recovered exactly | Current accumulated event readout; no new head | No for current approximation; finer evidence would be new scope |
| Driving / forward_position | Conditional; 888/888 | Scalar m, world, at T | Yes / yes | Accuracy unqualified | Existing generic readout | No |
| Driving / forward_velocity | Conditional; 888/888 | Scalar m/s, world, at T | Yes / yes | Accuracy unqualified | Existing generic readout | No |
| Driving / stopped_by_T | Conditional sampled duration event; 888/888 | Forward speed and xyz velocity, m/s world; complete history from t=0; abs(forward)<0.02 and planar norm<0.03 continuously for 0.2 s; retain earliest qualifying interval end <=T | Both channels and public history available | Unsampled duration breaks cannot be excluded | Current dwell/latch readout | No for current approximation |
| Objects / block_1 position | Conditional; 2400/2400 | xyz m, world, at T | Yes / yes | Accuracy unqualified | Existing generic readout | No |
| Objects / block_1 orientation | Conditional; 2400/2400 | Quaternion xyzw, unit 1, world, at T | Yes / yes | Predicted quaternion may fail physical consistency; readout does not repair it | Existing vector output; evaluator uses sign-invariant rotation angle; norm check separate | No |
| Objects / block_2 position | Conditional; 2400/2400 | xyz m, world, at T | Yes / yes | Accuracy unqualified | Existing generic readout | No |
| Objects / block_2 orientation | Conditional; 2400/2400 | Quaternion xyzw, unit 1, world, at T | Yes / yes | Same quaternion/accuracy gap | Existing vector output/check | No |
| Objects / block_2 stable_stack | **Unsupported; 0/2400** | Supporting normal contact force/on-off latch; normal vertical component; both poses, lower local footprint, upper speed, uninterrupted 0.2 s dwell ending at T | Kinematics available; observed categorical relations only; future contact force/normal/latch absent from n | Contact onset >0.01 N, off <=0.005 N, normal vertical component >0.5; tilt <10 degrees, COM inside lower local footprint with 0.001 m margin, upper speed <0.02 m/s for 0.2 s. Current n cannot establish all predicates | No complete fix from present predicted channels; some geometric predicates alone are insufficient | Future sufficient-evidence mechanism/representation requires separate approval; current unsupported decision remains settled |
| Objects / block_2 support_lost | **Unsupported; 0/2400** | Initially stacked qualification and supporting-contact history/latch after cutoff through T | Public initial arrangement/relations may help; predicted future support forces/normals absent | Cannot establish loss of supporting contact or its accumulated event from coordinates alone | No complete current-channel fix; neither proximity nor guessed contact suffices | Same future mechanism decision; no change in this audit |
| Objects / block_2 left_table | Conditional endpoint condition; 2400/2400 | Upper COM xyz m/world at T; abs(x)>2 or abs(y)>2 | Yes / yes | No temporal latch required by this public rule | Existing endpoint readout | No; it is **not** “ever left by T” |
| Tether / load position | Conditional; 2400/2400 | xyz m, world, at T | Yes / yes | Accuracy beyond single pilot unqualified | Existing generic readout | No |
| Tether / load swing_angle | Conditional; 2400/2400 | Scalar rad, world, at T | Yes / yes | Same accuracy gap | Existing generic readout | No |
| Tether / load angular_velocity | Conditional; 2400/2400 | Scalar rad/s, world, at T | Yes / yes | Same accuracy gap | Existing generic readout | No |
| Tether / load boundary_crossed | Conditional sampled post-cutoff event; **2248/2400** | World COM x from cutoff to T at 0.02 s; initially rearmed x<0.095; trigger x>0.105, rearm x<0.095 | Coordinates available; **152** initial states fail the qualified rearm condition | Public rule does not resolve the initial latch when x>=0.095 at cutoff; no inference from private event history | Preserve explicit `initial_crossing_state_not_qualified`; relaxing it is not a routine fix | An additional public initial-event-state convention would require explicit review; not necessary to keep current subset |

## Temporal semantics and event information boundary

The implementation uses **0.02-second samples with no interpolation**. Bullet
events may be updated at finer integration steps; sampling can miss a crossing or
intervening dwell break. These are qualified sampled approximations, not exact
continuous-time recovery. Joint-limit and stopped-by-T outputs accumulate events;
boundary-crossed accumulates after cutoff; left-table is an endpoint condition;
stable-stack would require a qualifying dwell at the endpoint, not an earlier
completed dwell. A shared `at_time` schema field does not erase these differences.

All public `known_events` observed by the scan are `scheduled_intervention`, one
per context. They are public future controls/forcing, **not observations of future
outcomes**. Private simulator event logs (contact onset, stopping, etc.) are not
deployment inputs. Public Boolean measurements/history are retained in Q/C but
excluded from numerical MSE and are never cast to numbers or treated as future
forecasts. The generic numerical interface predicts neither contact relations nor
new event-log entries.

## Assessment and calibration inventory (separate from answer coverage)

| Component / domain | Supported now? | Required inputs/history | Permitted availability | Exact gap | Current-contract implementation fix? | Scientific decision? |
| --- | --- | --- | --- | --- | --- | --- |
| Full-2d reference familiarity / all four | Mechanism implemented; one tether query measured | Train-only predicted references; same model/P/E; exact domain/layout/cutoff/grid/horizon; k=1 frozen-context retrieval; exclude entire query scenario for train queries | Public contexts and independent trained predictions are permitted | Other-domain trained banks and ID/OOD detection evidence absent; zero-norm/nonfinite/no-compatible-reference explicit | Build only within a separately authorized training/evaluation budget; no score change | Calibration/evaluation scope, not architecture reopening |
| V1 scenario/schema judge / all four | Original prompt/schema implemented; one tether result measured | Original public scenario and schema | Available public information | It judges scenario/schema consistency, not trajectory correctness or a physical OOD cause | Retain unchanged; do not relabel its task | New clarification task would need a separate definition |
| Required typed assessment contracts / arm | Operator boundary implemented; **unavailable** | Immutable public constraint declarations, evidence substring, scalar channel, units/frame, bounds, operator, tolerance, positive scale | **0 declarations in 2350 public contexts** | No public typed bounds/semantics to score | Cannot invent contracts from observed values or turn an answer threshold into a general constraint | Reviewed public evidence/contract-authoring policy needed before claiming complete assessment |
| Required typed assessment contracts / driving | Same; unavailable | Same | **0 in 888** | Same | Same | Same |
| Required typed assessment contracts / objects | Same; unavailable | Same | **0 in 2400** | Same; contact mechanisms also missing | Same | Same |
| Required typed assessment contracts / tether | Same; unavailable | Same | **0 in 2400** | Same; a cable consistency check is not a supplied typed contract | Same | Same |
| Independent physical checks / arm | Limited mechanism; no empirical arm forecast result here | Registered world xyzw orientation if present | Eligible channels determine coverage | No joint dynamics/torque residual check; empty eligible set gives null PCVR | No hidden oracle import or new physics residual | Any broader authored check needs disclosure/qualification |
| Independent physical checks / driving | Limited mechanism | World quaternion norm; forward-position/velocity consistency with corresponding vector x channels | Available when exact registered channels exist | No force-law correctness check | Existing checks only | Same |
| Independent physical checks / objects | Limited mechanism | Both quaternion norms | Available | Does not verify support, contact or stability | Existing checks only | Same |
| Independent physical checks / tether | Limited mechanism; **40/40 evaluated, 0 violations** on saved primary path | Load/support positions and positive public cable length; tolerance 0.001 m | Available | No dynamics correctness proof; underfit/constant paths can pass | Existing check only | No new inference from PCVR=0 |
| Combined assessment / all four | **Partial** when any required component absent | Familiarity + typed contract + unchanged V1 judge | Contract component missing here | No combined score/threshold decision | Preserve partial status, never renormalize remaining components | No decision to override settled policy |
| Calibration / all four | Algorithm implemented; **uncalibrated** | Complete assessments; independent validation-ID calibration scenarios, exact identity, scenario maxima; 0.95 higher quantile, strict-greater trigger | One measured query; next proposal has eight validation scenarios | Configured minimum **20** separate calibration scenarios, nondegenerate scores, no selection overlap; contracts missing | Cannot calibrate on partial or test results, or lower minimum silently | Separate calibration allocation/contract policy before detection-performance claims |
| OOD clarification / all four | **No operational implementation** | Intended explanation target/evidence boundary not yet defined | Technical reasons/component diagnostics exist | No qualified user-facing explanation of why a scenario is OOD; no localization/cause verification | Document existing diagnostics; do not invent clarification semantics | Define evidence-bounded clarification and its evaluation before implementing it |

Supported Boolean accuracy and Boolean coverage must be reported separately.
Complete-answer success retains every eligible component, including all unsupported
ones. The pilot has one supported Boolean and 1/1 success; this says nothing about
event accuracy across these inventories. Object questions cannot currently obtain
a completely supported forecast-based answer because two requested components
remain unsupported. The 152 tether cases must likewise remain in the denominator.
