# Phi-JEPA

P00 provides offline contracts and provenance; P01 adds passive-stopping benchmark data
and external numerical prediction evaluation. The implementation handoff is
in [docs/README.md](docs/README.md); progress is in [docs/PROGRESS.md](docs/PROGRESS.md).
The root Python scripts and notebooks remain historical prototype code.

Use Python 3.12. The core has no third-party runtime or test dependencies.
The verified build dependency is `setuptools==84.0.0`; legacy `requirements.txt`
does not describe this package. Keep future core, CoConuT and CODI environments separate.

```powershell
python -m pip install --no-deps --no-build-isolation -e .
phi-jepa --help
phi-jepa validate-config --config configs/offline.json
phi-jepa fixture --config configs/offline.json --input tests/fixtures/scenario.json --output results/p00
python -m unittest discover -s tests -v
```

`python -m phi_jepa` is equivalent to `phi-jepa`. A repeated identical run under
the same output root fails rather than overwriting evidence; use a new output root
to verify byte-for-byte reproducibility. Manifests contain input/config/source hashes,
environment, budgets, zero call/solve counters, and hashes of all artifacts. No timestamps
or absolute output paths enter run identity. Manifest publication is last; missing manifests
identify interrupted bundles. Immutability means API-level exclusive creation, not filesystem
tamper protection; hashes allow later verification. No credentials or environment dumps are saved.

Unknown observations stay null. The fixture returns no physical prediction or empirical
metric. Live configuration can be validated but P00 cannot execute live providers.
Allowlisted typed inputs reject extra label fields; free text is not a semantic leakage detector.

P01 runs entirely offline with no new dependencies:

```powershell
$dataset = phi-jepa generate-data --config configs/p01_fixture.json --output results/p01/data
phi-jepa validate-data --dataset $dataset --output results/p01/validation
phi-jepa evaluate --dataset $dataset --predictions "$dataset/oracle_predictions.json" --output results/p01/evaluation
phi-jepa evaluate --dataset $dataset --predictions "$dataset/corrupted_predictions.json" --output results/p01/evaluation
```

The 32-family wiring fixture contains 128 correlated records: two complete text variants
at each of two query times. Inputs, truth, partitions, training-only scaler and source
registry are separate files. Oracle prediction files verify the evaluator only; they are
not Phi-JEPA performance. Dataset validation checks hashes, labels, family separation,
oracle agreement and numerical refinement. Evaluation never calls a model or oracle.
External prediction JSON has `producer` and `predictions`; use the generated prediction
file as the numerical envelope example. Unknown/duplicate IDs reject the file; missing
or invalid rows are failures. Errors are valid-only with explicit coverage. Compatible
supplied trajectories have separate metrics; absent trajectories are never synthesized.
See [P01 decisions](docs/decisions/P01_data.md) for exact split/range/time/metric policies.

Later phase CLI names are reserved (not implemented):
`extract`, `train`, `predict`, `assess`, `baseline`, `pilot`, `study`. Each will use
`--config` and explicit input/output paths as appropriate. Their implementation requires
separate phase authorization.
