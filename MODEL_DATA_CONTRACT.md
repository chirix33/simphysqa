# Φ-JEPA model–dataset contract — revision 1.1.0

This records the user's confirmed architecture clarification. It supersedes references in design revision 1.0.0 to physical terminal-state MSE as the current training target. It does not alter the underlying dataset JSON Schema version (1.0.0).

## Confirmed computation

Let Q be the question, C the public context, A the reference answer, and n the flattened numeric input JSON fields in a fixed domain registry order. Let E be the common text embedding function.

    e_problem  = E(serialize(Q, C))
    e_solution = E(serialize(Q, C, A))
    x0 = concat(n, e_problem)
    y  = concat(n, e_solution)
    x_hat_T = ODE_theta(x0, T)
    loss = mean((x_hat_T - y) ** 2)

The user explicitly confirmed:
1. Compare the predicted final ODE output against y; do not compute a training loss solely between the fixed x0 and y.
2. Embed each combined text once. E(Q,C) and E(Q,C,A) have identical output dimension. Do not concatenate two separate text embeddings on one side and three on the other.
3. The immediate added vector is computed by a trainable network from the current state and time. An Euler illustration is x_next = x + dt * f_theta(x, t). This is not a fixed learned offset shared indiscriminately by all scenarios. It does not require Euler as the final solver.

There is one terminal loss, with no losses at consecutive intermediate states. Gradients pass through the ODE rollout. The same numeric vector n appears in x0 and y; actual future simulator measurements must not replace n in this target.

Strings remain available to prepare the embeddings, registry mapping and readable answers. They are not supplied as raw strings to the numerical ODE. Text embeddings are numeric vectors and are part of its input. Fixed field names are administrative identifiers outside the dynamics, not additional learned field-name embeddings unless separately authorized.

## What the target means

The numeric block encourages endpoint reconstruction of the original numeric values. The embedding block encourages prediction of a representation containing the answer. Numeric coordinates need not be constant at intermediate integration times, but their target endpoint is their input value.

The ODE's integration trajectory is therefore not automatically a physical simulation trajectory. Its integration time must be distinguished from physical timestamps in the dataset. Keep the physical requested time explicitly in Q/C and/or its numeric input fields. A candidate reasoning integration interval can be chosen as a documented solver configuration during implementation; the user has not yet fixed its numerical value.

Actual future simulator states, terminal quantities, success outcomes and descriptive labels are still required as independent references. They define A and permit physical evaluation of generated answers. Low embedding loss alone does not establish correct physical answers, physical intermediate states, or successful OOD generalization.

This is a change from the older project ledger's terminal physical-readout objective. Do not silently combine the old physical MSE, semantic reconstruction regularizer or trainable tree encoder with the newly specified objective. Any extra objective, projection or representation module must be identified as an additional design choice. This dataset task does not implement or approve those extensions.

## Numeric vector and field registry

Flatten both supported input formats: (a) the public simulator-derived JSON and (b) the LLM-extracted JSON. Each adapter has a frozen source-schema revision and maps to a fixed registry per domain. Log which source supplies a given n. Supporting both adapters does not mean automatically concatenating duplicate versions of the same physical facts.

Scope: flatten the designated public state/schema object. Never recursively flatten the full dataset envelope, which includes reference states and target answers. The source root is an explicit, versioned adapter setting. Do not silently exclude numerical timestamps or step indices within that root: all its float/integer fields enter n and the terminal comparison. Numeric controls, properties and other fields within the chosen root likewise remain included. Private seeds, split annotations, reference values and runtime metadata stay outside the public root.

Registry entries define:
- column index, stable field key, source binding, scalar type;
- entity ID, quantity, vector component, unit and coordinate frame where applicable;
- observation slot/time role for repeated observations;
- domain, source-schema version and registry version/hash.

Use a collision-free canonical encoding of path segments or a structured tuple serialized unambiguously. Do not join arbitrary names with underscores and assume uniqueness. Resolve entity IDs and measurement names rather than depending on measurement array order. Generic arrays whose order conveys meaning retain their explicit index. Reject duplicate semantic keys.

Within one observation, quantity keys must be unique. Across observations, the same quantity retains its semantic identity; observation slot distinguishes the individual occurrence in a flattened history. All records for a given frozen domain adapter have the same observation grid and field count. A two-slot example might contain:

    (observation=0, entity=joint_1, quantity=angle)
    (observation=1, entity=joint_1, quantity=angle)

A vector coordinate such as position[0] also includes its declared component (x), keeping x/y/z distinct. Do not flatten strings that happen to contain digits. In JSON, booleans are distinct from numbers; do not let Python's bool subclassing int accidentally include them. Explicitly map booleans to numeric fields only if that schema change is approved and documented.

All physical numbers use canonical units before vectorization. Reject incompatible units/frames. Preserve original values and conversion provenance. Null is not zero. A missing registry field, extra unsupported numeric field, ambiguous entity match or nonfinite value fails vectorization in the first strict adapter. Do not repair an extraction with hidden oracle values. Report extraction coverage; later padding/masking policies would need explicit specification.

Registry construction uses domain manifests and development/training data only, never held-out answers. OOD examples with new entities/fields cannot silently expand a fixed readout; structural OOD remains disabled until an explicit policy exists. An extracted JSON can differ from the simulator format; the mapping must be tested, not presumed from matching field counts.

For each training example, copy the exact same resulting n to both x0 and y. Do not put simulator-corrected numeric values on the target side when the input used extracted values; that would introduce another objective. Separate extractor-accuracy diagnostics may compare available observed fields with their simulator references.

## Text and target construction

Proposed implementation binding, to be versioned in the adapter manifest:
- Q = input.question.
- C = deterministic serialization of public context: global_context plus the public entities/model prior, observations, controller, known events and answer_spec. No reference or metadata object is included.
- A = reference.label, rendered deterministically from reference.structured_label using named quantities, units and evaluation time.

Use delimiters and explicit field labels in serialize. Record tokenizer/model revision, output dimension, pooling, sequence length, truncation policy, precision and any embedding normalization. Both embeddings use the same encoder and settings. Retain the earlier frozen-encoder setting unless explicitly changed; targets are detached and no gold answer enters the inference branch. Reject overlength examples or use a previously declared public summarization rule; silent loss of late controls or answer tokens is unacceptable.

Do not include reference.explanation or a solution trace in A by default: the user confirmed question + context + answer, not additional reasoning supervision. Such extensions must be labeled. The trainable vector-field network remains the source of the state-dependent updates.

The gold answer is legitimately used in training target construction. Validation/test targets may be constructed privately for loss reporting, but cannot be used to initialize or adapt inference, construct its numeric registry or choose its output.

## MSE reduction and numerical scale

The agreed default is a mean over every coordinate of the final concatenated vector, followed by a mean over examples:

    loss_i = sum_j((prediction_ij - target_ij)^2) / D_domain
    batch_loss = mean_i(loss_i)

This supports separate domain-specific dimensions without giving a larger domain vector automatic multiplicative weight at the outer averaging step. Record domain sampling weights and the embedding dimension.

All float/integer coordinates in n enter this loss, including timestamps/step indices. The numeric and embedding blocks can have very different scales and numbers of coordinates. Report per-block sums, means, dimensions and optimization diagnostics during the model pilot. Raw combined MSE is the confirmed formula; scaling, normalization, weighted block losses, exclusion of known constants and integer rounding within the loss have not been approved. Canonical unit conversion is part of the public data definition, not learned normalization.

Physical evaluation can continue to report native-unit MAE/RMSE and training-normalized metrics, provided these are clearly evaluation metrics, not silently added optimization objectives.

## Inference and downstream answers

Inference builds x0 from public information, runs the ODE, and obtains its predicted final vector. The registry restores names to the numeric block. That numeric block is trained to reconstruct the supplied numbers, not to provide future physical predictions directly.

A downstream answer-generation/decoding interface must turn the predicted semantic representation into a usable answer. A generic sentence embedding is not directly invertible into text, and arbitrary embedding coordinates cannot be assumed to be valid input embeddings for another LLM. The precise adapter is not specified by the three confirmations. This is a model implementation dependency, not a reason to remove the dataset's reference answers or stall simulator development. Do not claim end-to-end answer accuracy until the adapter is defined and tested.

## Required contract checks for Codex

1. Both flatteners yield deterministic registry order and round-trip their numeric entries with identifiers/units.
2. Reordering JSON object keys or measurement rows does not change n when semantic identity is unchanged; changing a semantic array order does change the relevant binding.
3. Duplicate identities, missing values, nonfinite values and unsupported fields raise explicit errors.
4. n_initial equals n_target exactly; simulator future states do not alter n_target.
5. Embedding dimensions match; answer text changes target construction while leaving the input construction unchanged.
6. Altering reference or private metadata cannot alter exported public inputs or x0.
7. With a real trainable vector field, the final loss depends on its parameters and gradients reach them. A difference between fixed embeddings is not a substitute for this gradient check.
8. Intermediate predictions are not replaced by true future states, and no consecutive-state loss is added.
9. Real loss magnitude, field scales, embedding sensitivity to numeric answer changes and downstream answer accuracy are measured; none is guaranteed by these algebraic definitions.

This file is a design agreement and implementation specification, not a tested neural ODE implementation.
