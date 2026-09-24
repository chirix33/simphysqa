# Validation of the design package

Performed 24 September 2026.

Passed:
- Parsed all supplied JSON documents.
- Checked JSON Schema Draft 2020-12 validity with Python jsonschema.
- Validated complete illustrative record, public export and keyed bundle.
- Negative structural cases rejected: missing measurement unit, label inserted into input, negative timestamp, fluid domain, missing reference label.
- Verified allowlisted public export is unaffected by changes to private label and metadata.
- Checked example cutoff boundaries and time-zero observation.
- Checked five-domain configuration, disabled release generation, and proposed arithmetic: 1,700 scenarios/domain, 8,500 total, up to 17,000 questions.

Not performed:
- Simulator installation or execution; model-asset selection or pinning.
- RTX 5090 compatibility, speed, memory or disk measurements.
- Physics, controller, convergence, label correctness or real-dataset semantic validation.
- Dataset generation, model training or baseline evaluation.

The example values are explicitly illustrative. Structural validation does not establish a physically correct or sufficiently specified simulation. Codex must implement and test the production semantic/release gates listed in SPECIFICATION.md.

## Revision 1.1.0 checks

- Rechecked the unchanged Draft 2020-12 schema and all three illustrative examples.
- Checked the revised config's equal numeric input/target policy, combined-text embedding mode, five-domain scope and disabled final generation.
- Rechecked public export isolation from private answer text.
- Reviewed specification and Codex prompt for stale physical-MSE training instructions and revised them to distinguish physical evaluation from the new objective.
- Rebuilt artifact checksums and tested the revised ZIP for corruption.

No actual embedding encoder, flattening implementation, neural ODE, gradient propagation, answer decoder or simulator was executed for this revision. Their required tests are specified in MODEL_DATA_CONTRACT.md; they are not claimed as passed.
