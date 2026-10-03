Phi-JEPA simulated validation examples: 1,000 questions

Counts: robotic_arm 388; driving 148; object_pushing_stacking 232; tethered_load 232.
All original robotic-arm validation questions are included. Other domains fill
1,000 total. Selection sorts existing scenario-group identifiers and retains all
questions from each selected group. Selection does not use outcome or accuracy.
This is a schema/data compatibility sample, not a new representative benchmark.
Only the already inspected validation split is included; no confirmation/test data.

Start with preview.html or preview.txt (six examples: three arm, one each other).
questions-and-public-inputs.jsonl: original public questions, observations,
physical properties, controls, events, coordinate conventions and target specs.
reference-answers.jsonl: correct simulator-derived answers, NOT model outputs.
model-predictions-and-errors.jsonl: selected trained-model outputs and typed errors.
robotic-arm-388-comparisons.jsonl: self-contained robot-focused full comparisons.
Join all files by sample_id; scenario_id/split_group_id preserve simulation groups.
JSONL has one complete JSON object per line. Units/frames/timestamps are explicit.
Null unsupported predictions must not be interpreted as physical zero.
Quaternion xyzw orientation is compared by sign-invariant rotation-angle error.
Predictions are numerical/readout outputs, not generated prose. They are often
inaccurate; original failures, unsupported targets and tolerances are preserved.

All examples originate from simulation. Compatibility with a real robot requires
checking its kinematics, sensors, units, frames, controls, observation timing and
requested target definitions; no equivalence to the collaborator's data is claimed.
Public inference inputs are separated from reference answers intentionally.
No training, inference, paid API calls or external transmission occurred in this
packaging step. This reuses today's verified selected-checkpoint replay.
